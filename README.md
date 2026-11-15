# Banking DevSecOps

A demonstration banking application with an automated DevSecOps pipeline. The project uses Python, Flask, Docker, Jenkins, and Trivy to test application functionality, build a container image, and scan it for security vulnerabilities.

## Project Objectives

- Build and test a Python Flask banking application.
- Automate testing and Docker image creation with Jenkins.
- Scan Docker images for HIGH and CRITICAL vulnerabilities using Trivy.
- Improve container security by using an Alpine-based Python image and upgrading installed packages.
- Maintain source code and pipeline configuration in GitHub.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application development |
| Flask | Web application framework |
| Pytest | Automated unit testing |
| Docker | Containerization |
| Jenkins | CI/CD automation |
| Trivy | Container vulnerability scanning |
| Git and GitHub | Version control and source hosting |
| Alpine Linux | Lightweight container base image |

## CI/CD Pipeline

The Jenkins pipeline contains the following stages:

1. **Checkout:** Retrieves the latest source code from the GitHub `main` branch.
2. **Python Unit Tests:** Installs application dependencies and executes the Pytest suite.
3. **Build Docker Image:** Builds a Docker image using the project Dockerfile.
4. **Trivy Security Scan:** Scans the image for HIGH and CRITICAL vulnerabilities. The pipeline fails if such findings are detected.

## Automated Tests

The current test suite contains five tests:

- Homepage test
- Health endpoint test
- Successful transfer test
- Insufficient balance test
- Same-account transfer test

**Latest verified result:** 5 tests passed.

## Container Security

The Docker image uses `python:3.12-alpine3.24` as its base image.

Security improvements include:

- Upgrading Alpine packages during the image build.
- Updating pip and setuptools.
- Installing application dependencies without retaining pip's download cache.
- Scanning the built image with Trivy.

The Trivy command narrowly skips the embedded `pip/_vendor/bom.cdx.json` file because it contains stale vendored package metadata. Installed Python package metadata and Alpine packages remain scanned.

**Latest verified scan:** 0 HIGH and 0 CRITICAL vulnerabilities in the scanned targets.

This result applies to the configured Trivy scan and severity levels; it does not mean the image is free of every possible security issue.

## Repository Structure

```text
banking-devsecops/
├── app/             # Flask application and requirements
├── tests/           # Pytest test cases
├── ansible/         # Ansible-related project files
├── docker/          # Docker-related files
├── docs/            # Project documentation
├── helm/            # Helm-related files
├── jenkins/         # Jenkins-related files
├── kubernetes/      # Kubernetes-related files
├── monitoring/      # Monitoring-related files
├── security/        # Security-related files
├── terraform/       # Terraform-related files
├── Dockerfile
├── Jenkinsfile
└── README.md
```

## Run Tests Locally

Create and activate a virtual environment:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

Install dependencies and run tests:

```powershell
python -m pip install -r app/requirements.txt
python -m pytest tests/ -v
```

## Build the Docker Image

```powershell
docker build -t securebank:latest .
```

Run the container:

```powershell
docker run --rm -p 5000:5000 securebank:latest
```

## Run a Trivy Scan

```powershell
trivy image --scanners vuln --severity HIGH,CRITICAL --skip-files "**/pip/_vendor/bom.cdx.json" securebank:latest
```

## Latest CI/CD Verification

- GitHub branch: `main`
- Latest verified commit: `0e632cb`
- Jenkins job: `docker-access-job`
- Jenkins build: `#18`
- Unit tests: 5 passed
- Docker image: `securebank:18`
- Trivy HIGH findings: 0
- Trivy CRITICAL findings: 0
- Jenkins pipeline result: SUCCESS

## Disclaimer

This is an educational demonstration project. It is not intended for production banking or real financial transactions.
