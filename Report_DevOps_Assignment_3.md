# DevOps Assignment 3 Report

## Introduction
This report outlines the development, testing, and continuous integration pipeline for a simple web application designed to fulfill the requirements of DevOps Assignment 3. The objective was to implement an automated testing suite using Selenium and integrate it into a Jenkins CI/CD pipeline using a containerized approach with Docker.

---

## Part I: Automated Test Cases Using Selenium

### 1. Application Architecture
A simple "User Registry" web application was developed. The application is built with the following technologies:
- **Backend:** Python (Flask)
- **Database:** SQLite (Relational Database Server)
- **Frontend:** HTML5 with basic CSS

The application supports CRUD operations allowing users to be created, read, updated, and deleted. A search functionality is also included. 

### 2. Selenium Test Cases
15 automated test cases have been developed to ensure the UI flows correctly. Since the pipeline will run on an AWS EC2 instance without a GUI, the tests use **headless Chrome**. 
The test suite utilizes `pytest` and `selenium-webdriver`. The tests execute as follows:

1. **Page Title:** Verifies the page loads correctly and title matches.
2. **Main Header:** Verifies that the H1 tag has the correct text.
3. **Form Elements:** Asserts that the form fields (Name, Email, Submit button) are present on the page.
4. **Data Table:** Verifies that the user records table renders correctly.
5. **Name Field Validation:** Verifies the `required` HTML5 constraint is on the Name field.
6. **Email Field Validation:** Verifies the `required` HTML5 constraint is on the Email field.
7. **Add First User:** Automatically fills and submits the form, checking if the new user appears in the registry.
8. **Add Second User:** Automates adding a secondary user to populate the list.
9. **List Rendering:** Verifies that multiple rows exist in the user list table.
10. **Search Existing User:** Uses the search bar to find a specific user and verifies that the table filters correctly.
11. **Search Non-Existing User:** Inputs a random string and verifies the "No users found" message is displayed.
12. **Clear Search:** Automates clicking the clear search button and verifies all rows are restored.
13. **Edit User:** Finds an existing user, clicks edit, inputs a modified name, and submits.
14. **Verify Edit:** Checks the data table to ensure the newly modified name replaces the old one.
15. **Delete User:** Clicks the delete button for a specific record and verifies it is removed from the DOM.

*(Please take screenshots of the tests running and passing via `pytest` and place them here)*

---

## Part II: Automation Pipeline with Test Stage

### 1. Containerization
To ensure environment consistency, two services are defined in `docker-compose.yml`:
1. **web:** Builds the Flask application.
2. **test:** Uses the pre-built `joyzoursky/python-chromedriver:3.9` image containing Python, Chrome, and ChromeDriver to spin up a container alongside the web container. This container executes the `pytest` test suite automatically against the running web application.

### 2. Jenkins Pipeline Configuration
The pipeline is designed to trigger upon a push to the GitHub repository. It pulls the repository and executes tests inside Docker.

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
                        // Bring up web app in the background
                        sh 'docker-compose up -d web'
                        
                        // Wait for app to be ready
                        sleep time: 10, unit: 'SECONDS'
                        
                        // Run test container 
                        sh 'docker-compose run --rm test'
                        
                    } catch (Exception e) {
                        currentBuild.result = 'FAILURE'
                        throw e
                    } finally {
                        // Clean up containers
                        sh 'docker-compose down -v'
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
   - `docker-compose up -d web` starts the application.
   - The pipeline sleeps for 10 seconds to allow the web server to start up.
   - `docker-compose run --rm test` executes the test container, running `pytest`.
4. The `always` post-block captures the author email of the last commit using `git log`.
5. An email is formulated outlining the build status and sent directly to the email of the person who pushed the changes.

*(Please take screenshots of your Jenkins Console Output, specifically showing the `git push` webhook trigger, the tests passing, and the email being sent)*

## Final Submission Steps Undertaken
1. **Repository Hosted:** The code has been pushed to a public GitHub repository.
2. **Collaborator Added:** `qasimalik@gmail.com` has been added as a collaborator to the repository.
3. **Pipeline Integrated:** The webhook is fully operational, linking GitHub to the AWS EC2 instance where Jenkins resides.
4. **Email Configured:** Jenkins has SMTP configured, actively pushing out emails containing test status links upon completion.
 
