# DevOps Assignment 3 Report

## Introduction
This report outlines the development, testing, and continuous integration pipeline for the **Elite Car Rental** web application designed to fulfill the requirements of DevOps Assignment 3. The objective was to implement an automated testing suite using Selenium and integrate it into a Jenkins CI/CD pipeline using a containerized approach with Docker.

---

## Part I: Automated Test Cases Using Selenium

### 1. Application Architecture
The **Elite Car Rental** web application was developed as a full-featured car rental platform. The application is built with the following technologies:
- **Backend:** Python (Flask)
- **Database:** SQLite (Relational Database Server)
- **Frontend:** HTML5 with CSS (Dark gradient glassmorphism design)

The application supports the following features:
- **User Authentication:** Login and Signup with session management
- **Car Browsing:** Dashboard displaying available cars with pricing
- **Search:** Search cars by name or brand
- **Car Rental:** One-click rental of available vehicles
- **Rental Management:** View active and returned rentals
- **Car Return:** Return rented cars back to availability
- **Profile Management:** Edit user full name and email
- **Logout:** Secure session termination

### 2. Selenium Test Cases
15 automated test cases have been developed to ensure all UI flows work correctly. Since the pipeline runs on an AWS EC2 instance without a GUI, the tests use **headless Chrome**.
The test suite utilizes `pytest` and `selenium-webdriver`. The tests execute as follows:

1. **Login Page Title:** Verifies the login page loads correctly and the title contains "Elite Car Rental".
2. **Login Form Elements:** Asserts that the username field, password field, and login button are present on the page.
3. **Signup Link Navigation:** Clicks the "Sign Up" link on the login page and verifies navigation to the signup page.
4. **Signup Form Elements:** Verifies that full name, email, username, password fields and signup button are present.
5. **Register New User:** Fills out the signup form with test data, submits it, and verifies redirect to login with a "Account created" success message.
6. **Login with Valid Credentials:** Logs in with the newly registered user and verifies redirect to the dashboard.
7. **Dashboard Welcome Message:** Verifies the dashboard shows a personalized welcome message with the user's full name.
8. **Cars Grid Display:** Verifies the dashboard displays a grid of available car cards for rental.
9. **Search Car by Brand:** Uses the search bar to search for "BMW" and verifies only matching results appear.
10. **Clear Search:** Clicks the clear button and verifies all cars are restored in the listing.
11. **Rent a Car:** Clicks the "Rent Now" button on the first available car and verifies redirect to My Rentals with a success message.
12. **Rental Appears in My Rentals:** Verifies the rented car appears in the My Rentals table with "Active" status.
13. **Return a Car:** Clicks the "Return" button on the active rental and verifies a "returned successfully" message.
14. **Edit Profile:** Navigates to the profile page, updates the full name, and verifies a "Profile updated" success message.
15. **Logout:** Clicks logout and verifies redirect back to the login page.

*(Screenshots of all 15 tests passing in Jenkins Console Output are attached below)*

---

## Part II: Automation Pipeline with Test Stage

### 1. Containerization
To ensure environment consistency, two services are defined in `docker-compose.yml`:
1. **web:** Builds the Elite Car Rental Flask application using the project `Dockerfile`.
2. **test:** Uses the pre-built `joyzoursky/python-chromedriver:3.9` image containing Python, Chrome, and ChromeDriver to spin up a container alongside the web container. This container executes the `pytest` test suite automatically against the running web application.

### 2. Jenkins Pipeline Configuration
The pipeline is designed to trigger automatically upon a push to the GitHub repository via a webhook. It pulls the repository and executes tests inside Docker.

**Pipeline Script (Jenkinsfile):**
```groovy
pipeline {
    agent any

    triggers {
        githubPush()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build and Test Containerized') {
            steps {
                script {
                    try {
                        // Stop any old containers and rebuild with latest code
                        sh 'docker-compose down -v || true'
                        sh 'docker-compose build web'

                        // Bring up web app in the background
                        sh 'docker-compose up -d web'

                        // Wait for app to be ready
                        sleep time: 10, unit: 'SECONDS'

                        // Run test container
                        sh 'docker-compose run --rm test'

                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        throw e
                    }
                }
            }
        }
    }

    post {
        always {
            script {
                // Fetch the author email of the last commit
                def authorEmail = sh(script: "git log -1 --pretty=format:'%ae'", returnStdout: true).trim()

                def subject = "Jenkins Pipeline ${currentBuild.result ?: 'SUCCESS'}: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
                def body = "The automated test pipeline for ${env.JOB_NAME} finished with status: ${currentBuild.result ?: 'SUCCESS'}.\n\nPlease check the build logs here: ${env.BUILD_URL}"

                if (authorEmail) {
                    echo "Sending email notification to collaborator: ${authorEmail}"
                    mail to: authorEmail,
                         subject: subject,
                         body: body
                } else {
                    echo "Could not find author email to send notification."
                }
            }
        }
    }
}
```

### 3. Pipeline Execution
When a collaborator pushes code:
1. GitHub triggers the webhook targeting the Jenkins server on AWS EC2.
2. Jenkins fetches the code from the `main` branch.
3. The `Build and Test Containerized` stage starts:
   - `docker-compose down -v` stops any previously running containers.
   - `docker-compose build web` rebuilds the web application image with the latest code.
   - `docker-compose up -d web` starts the application.
   - The pipeline sleeps for 10 seconds to allow the web server to start up.
   - `docker-compose run --rm test` executes the test container, running all 15 `pytest` test cases.
4. The `always` post-block captures the author email of the last commit using `git log`.
5. An email is formulated outlining the build status and sent directly to the email of the person who pushed the changes.

*(Screenshots of Jenkins Console Output showing the webhook trigger, tests passing, and email notification are attached below)*

## Final Submission Steps Undertaken
1. **Repository Hosted:** The code has been pushed to a public GitHub repository.
2. **Collaborator Added:** `qasimalik@gmail.com` has been added as a collaborator to the repository.
3. **Pipeline Integrated:** The webhook is fully operational, linking GitHub to the AWS EC2 instance where Jenkins resides.
4. **Email Configured:** Jenkins has SMTP configured, actively pushing out emails containing test status links upon completion.
