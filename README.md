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

Core operations
