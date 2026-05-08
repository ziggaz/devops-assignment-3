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
