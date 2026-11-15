pipeline {
    agent any

    options {
        skipDefaultCheckout()
        disableConcurrentBuilds()
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Unit Tests') {
            steps {
                bat '"C:\\Users\\SRIRAM\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" --host npipe:////./pipe/dockerDesktopLinuxEngine run --rm -v "%CD%:/workspace" -w /workspace python:3.12-alpine3.24 sh -c "python -m pip install --no-cache-dir -r app/requirements.txt && python -m pytest tests/ -v"'
            }
        }

        stage('Build Docker Image') {
            steps {
                bat '"C:\\Users\\SRIRAM\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" --host npipe:////./pipe/dockerDesktopLinuxEngine build --pull --no-cache -t securebank:%BUILD_NUMBER% .'
            }
        }

        stage('Trivy Security Scan') {
            steps {
                bat '"C:\\Users\\SRIRAM\\AppData\\Local\\Microsoft\\WinGet\\Packages\\AquaSecurity.Trivy_Microsoft.Winget.Source_8wekyb3d8bbwe\\trivy.exe" image --scanners vuln --severity HIGH,CRITICAL --skip-files "**/pip/_vendor/bom.cdx.json" --exit-code 1 securebank:%BUILD_NUMBER%'
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Tests passed, Docker image built, and security scan passed.'
        }
        failure {
            echo 'FAILED: Check the stage logs for the reason.'
        }
    }
}
