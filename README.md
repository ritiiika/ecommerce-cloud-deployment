# E-Commerce Product & Order API
### Cloud Deployment & CI/CD | ALGIONS AI LABS PRIVATE LIMITED

A containerized e-commerce backend built with **FastAPI, PostgreSQL, Docker, Nginx, and GitHub Actions**. This project demonstrates backend API development, automated testing, containerization, CI/CD automation, container image publishing, and database backup and recovery practices.

---

## 1. Project Overview

This project implements a RESTful Product and Order API with a focus on reliable order processing, inventory management, database persistence, and automated deployment workflows.

The application is containerized using Docker and orchestrated through Docker Compose. Nginx acts as a reverse proxy and provides HTTPS access to the API. GitHub Actions automates code quality checks, testing, container security scanning, and Docker image publishing to GitHub Container Registry (GHCR).

The project also includes database backup, restore, and rollback scripts to demonstrate disaster recovery practices.

## 2. Key Features

- **Product Management:** Create, retrieve, list, and search products.
- **Order Management:** Create orders and retrieve order information.
- **Inventory Management:** Validate available stock and prevent negative inventory.
- **Idempotent Order Processing:** Prevent duplicate orders when the same idempotency key is reused.
- **Audit Logging:** Maintain audit events for important operations.
- **Authentication:** Protect administrative operations using API key authentication.
- **Database Persistence:** Store application data in PostgreSQL using Docker volumes.
- **Containerization:** Package the FastAPI application using Docker.
- **Reverse Proxy:** Route incoming requests through Nginx.
- **HTTPS:** Enable encrypted local access using a self-signed development certificate.
- **Health Monitoring:** Provide health, readiness, and metrics endpoints.
- **Automated CI/CD:** Run linting, formatting, automated tests, and container security checks.
- **Container Registry:** Publish versioned Docker images to GitHub Container Registry.
- **Disaster Recovery:** Include database backup, restore, and rollback scripts.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11, FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy |
| Database Driver | asyncpg |
| Containerization | Docker |
| Container Orchestration | Docker Compose |
| Reverse Proxy | Nginx |
| CI/CD | GitHub Actions |
| Container Registry | GitHub Container Registry (GHCR) |
| Code Quality | Ruff |
| Testing | Pytest |
| Infrastructure as Code | Terraform |
| Version Control | Git and GitHub |

## 4. System Architecture

```text
                  Client
                    |
                    v
             HTTPS / HTTP
                    |
                    v
              Nginx Proxy
                    |
                    v
              FastAPI App
               /       \
              v         v
        PostgreSQL    API Routes
              |
              v
         Audit Events

       GitHub Repository
               |
               v
        GitHub Actions
               |
       +-------+-------+
       |       |       |
      Ruff   Pytest  Security
       |       |       |
       +-------+-------+
               |
               v
        Docker Image
               |
               v
              GHCR
```

## 5. Project Structure

```text
ecommerce-platform/
│
├── app/
│   ├── models/          # Database models
│   ├── schemas/         # Request and response schemas
│   ├── services/        # Business logic
│   ├── api/             # API routes
│   ├── core/            # Application configuration
│   ├── main.py          # FastAPI application entry point
│   └── seed.py          # Database seed utilities
│
├── tests/               # Automated tests
│
├── nginx/
│   ├── certs/           # Local TLS certificates
│   └── nginx.conf       # Reverse proxy configuration
│
├── scripts/
│   ├── backup.ps1
│   ├── backup.sh
│   ├── restore.ps1
│   ├── restore.sh
│   ├── rollback.ps1
│   └── rollback.sh
│
├── backups/             # Local database backup files
│
├── infra/
│   └── terraform/       # Infrastructure configuration
│
├── .github/
│   └── workflows/
│       └── ci.yml       # GitHub Actions pipeline
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── .env.example
└── README.md
```

## 6. Prerequisites

Install the following tools before running the project:

- Python 3.11 or later
- Docker Desktop
- Git
- GitHub account

Docker Desktop must be running before starting the containers.

## 7. Environment Configuration

Clone the repository:

```bash
git clone https://github.com/ritiiika/ecommerce-cloud-deployment.git
cd ecommerce-cloud-deployment
```

Create a local environment file:

**Windows CMD:**

```cmd
copy .env.example .env
```

**Linux/macOS:**

```bash
cp .env.example .env
```

Update the `.env` file with your own strong local credentials.

Example configuration:

```dotenv
POSTGRES_PASSWORD=your-strong-password
API_KEY_ADMIN=your-admin-api-key

LOG_LEVEL=INFO
APP_ENV=production

COMPOSE_PROJECT_NAME=ecommerce-platform

AWS_REGION=us-east-1
S3_BUCKET_NAME=my-ecommerce-platform-backups
```

Do not commit `.env` files, passwords, API keys, or private certificates to GitHub.

The AWS variables are optional for local development. AWS deployment is not required to run the local Docker environment.

## 8. Run the Application Using Docker

Build and start all services:

```bash
docker compose up --build -d
```

This starts:

- PostgreSQL database
- FastAPI backend
- Nginx reverse proxy

Check container status:

```bash
docker compose ps
```

View application logs:

```bash
docker compose logs --tail=50
```

Follow logs continuously:

```bash
docker compose logs -f
```

Stop the services:

```bash
docker compose down
```

**Note:** Do not use `docker compose down -v` unless you intentionally want to delete the persistent database volume.

## 9. Access the Application

Once the containers are running, access:

| Resource | URL |
|---|---|
| Swagger API Documentation | https://localhost/docs |
| Health Check | https://localhost/health |
| Readiness Check | https://localhost/readiness |
| Metrics | https://localhost/metrics |
| OpenAPI Specification | https://localhost/openapi.json |

The local HTTPS certificate is self-signed and intended for development and demonstration purposes. Browsers may display a security warning.

For production deployment, configure a trusted TLS certificate.

## 10. API Functionality

The application provides product and order management functionality.

Core operations include:

- Creating and listing products.
- Searching for products.
- Retrieving product information.
- Adjusting inventory.
- Creating orders.
- Retrieving order status.
- Recording audit events.

Use the interactive Swagger documentation at `/docs` to inspect the actual request schemas, available endpoints, and response formats.

Administrative operations require the configured API key.

## 11. Automated Testing

The project uses Pytest for automated testing.

Run the test suite:

```bash
python -m pytest tests/ -v
```

Run code quality checks:

```bash
ruff check app/ tests/
```

Verify formatting:

```bash
ruff format --check app/ tests/
```

Apply formatting when necessary:

```bash
ruff format app/ tests/
```

The local test suite has passed **16 automated tests**, covering health checks, product operations, order processing, idempotency, inventory validation, and audit events.

## 12. CI/CD Pipeline

GitHub Actions automates the project's CI/CD workflow.

The pipeline is triggered when code is pushed to the repository.

### Pipeline stages

1. **Lint and Format Check**
   - Run Ruff linting.
   - Verify Python formatting.

2. **Unit and Integration Tests**
   - Execute the automated test suite.
   - Validate application functionality.

3. **Container Security Scan**
   - Perform automated container security checks.

4. **Build and Push Image**
   - Build the Docker image.
   - Tag the image with version information.
   - Publish the image to GitHub Container Registry.

5. **Deployment Stage**
   - Run the configured deployment workflow when its required conditions and configuration are available.

### GitHub Actions

Repository:

https://github.com/ritiiika/ecommerce-cloud-deployment

GitHub Actions:

https://github.com/ritiiika/ecommerce-cloud-deployment/actions

The CI pipeline has successfully completed its linting, testing, security scanning, image publishing, and configured workflow stages.

## 13. Docker Image Registry

The project publishes its Docker image to GitHub Container Registry (GHCR).

Registry:

```text
ghcr.io/ritiiika/ecommerce-cloud-deployment/ecommerce-api
```

Example versioned image:

```bash
docker pull ghcr.io/ritiiika/ecommerce-cloud-deployment/ecommerce-api:sha-f276708
```

The published image can be viewed through the repository's GitHub Packages section.

## 14. Database Backup and Disaster Recovery

The project includes scripts for database backup, restoration, and rollback.

### Available scripts

| Script | Purpose |
|---|---|
| `backup.ps1` | Create a database backup on Windows |
| `backup.sh` | Create a database backup on Linux |
| `restore.ps1` | Restore a database backup on Windows |
| `restore.sh` | Restore a database backup on Linux |
| `rollback.ps1` | Perform database rollback on Windows |
| `rollback.sh` | Perform database rollback on Linux |

### Backup

Windows:

```powershell
.\scripts\backup.ps1
```

Linux:

```bash
bash scripts/backup.sh
```

### Restore and rollback

The restore and rollback scripts can replace existing database contents.

**Important:** Do not execute them against a database containing important data without first creating and verifying a separate backup. Test recovery using an isolated test database.

The project includes local backup files for recovery demonstrations.

## 15. Security Considerations

Security measures implemented or configured in the project include:

- Environment-based configuration.
- API key protection for administrative operations.
- Non-root application container execution.
- Internal Docker networking for the API and database.
- Nginx reverse proxy.
- HTTPS for local access.
- PostgreSQL health checks.
- Container security scanning in CI.
- Restricted public access and encryption settings in the Terraform S3 backup configuration.

Production deployment should additionally use managed secrets, trusted TLS certificates, restricted IAM permissions, and appropriate cloud security controls.

## 16. Infrastructure as Code

Terraform configuration is included under:

```text
infra/terraform/
```

It describes AWS infrastructure resources for a potential cloud deployment, including networking, ECS, RDS, IAM, and S3 backup components.

Terraform configuration validation was performed successfully.

**Deployment status:** The AWS infrastructure is configured as project code but has not been deployed to AWS. No AWS resources are required for the local Docker demonstration.

## 17. Verification Status

| Requirement | Status |
|---|---|
| FastAPI application | Verified locally |
| PostgreSQL database | Running locally |
| Docker containerization | Verified |
| Docker Compose | Verified |
| Nginx reverse proxy | Running locally |
| HTTPS local access | Verified |
| Swagger documentation | Verified |
| Automated tests | 16 passed |
| Ruff linting and formatting | Passed |
| GitHub Actions pipeline | Passed |
| GHCR image publishing | Verified |
| Terraform configuration | Validated |
| Backup files | Present |
| Restore and recovery test | Pending |
| Production AWS deployment | Not performed |
| Final demo and documentation evidence | Pending |

## 18. Future Improvements

- Complete an isolated database restore and recovery demonstration.
- Verify rollback behavior using a test environment.
- Improve production deployment automation.
- Configure trusted TLS certificates for public deployment.
- Add structured monitoring and alerting.
- Integrate cloud-managed secrets and IAM-based access.
- Complete deployment and recovery documentation.

## 19. Author

**Project:** E-Commerce Product & Order API  
**Organization:** ALGIONS AI LABS PRIVATE LIMITED  
**Focus:** Cloud Deployment and CI/CD  
**Backend:** Python and FastAPI  
**Repository:** https://github.com/ritiiika/ecommerce-cloud-deployment

---

*This project demonstrates the development, containerization, testing, CI/CD automation, image publishing, and recovery preparation of an e-commerce backend application.*
