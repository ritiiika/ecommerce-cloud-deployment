# E-Commerce Product & Order API

A production-ready REST API for managing products and orders, built with **FastAPI**, **SQLAlchemy (async)**, and **PostgreSQL**. Features include idempotent order creation, admin-protected mutations, structured JSON logging, Nginx TLS termination, Docker Compose orchestration, and a full CI/CD pipeline via GitHub Actions.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Development Setup](#development-setup)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Docker](#docker)
- [CI/CD](#cicd)
- [API Reference](#api-reference)
- [Database Seeding](#database-seeding)
- [Backup and Restore (Local & AWS S3)](#backup-and-restore-local--aws-s3)
- [AWS Cloud & Terraform IaC](#aws-cloud--terraform-iac)
- [Rollback](#rollback)
- [Security Notes](#security-notes)

---

## Overview

### Key Features

| Feature | Details |
|---|---|
| **Framework** | FastAPI 0.115 with async SQLAlchemy 2.0 |
| **Database** | PostgreSQL 16 (asyncpg driver) |
| **Auth** | API Key header (`X-API-Key`) for admin endpoints |
| **Idempotency** | Orders deduplicated by `idempotency_key` |
| **Logging** | Structured JSON middleware logging per request |
| **Containerization** | Multi-stage Dockerfile with non-root user |
| **Reverse Proxy** | Nginx with TLS, rate-limiting, and security headers |
| **CI/CD** | GitHub Actions: lint → test → security scan → build → deploy |
| **Cloud & IaC** | AWS S3 offsite backups + complete Terraform IaC (ECS, RDS, ALB, S3) |
| **Testing** | pytest-asyncio with SQLite in-memory test DB |

### Project Layout

```
ecommerce-platform/
├── app/
│   ├── main.py                   # FastAPI app, lifespan, middleware
│   ├── config.py                 # Pydantic settings
│   ├── database.py               # Async engine + session factory
│   ├── seed.py                   # Database seeder script
│   ├── auth/
│   │   └── dependencies.py       # Admin API key dependency
│   ├── middleware/
│   │   └── logging_middleware.py # Structured JSON request logging
│   ├── models/
│   │   ├── product.py            # Product ORM model
│   │   └── order.py              # Order + OrderItem ORM models
│   ├── routers/
│   │   ├── health.py             # /health, /readiness
│   │   ├── products.py           # Product CRUD endpoints
│   │   └── orders.py             # Order create + status endpoints
│   ├── schemas/
│   │   ├── product.py            # Product Pydantic schemas
│   │   └── order.py              # Order Pydantic schemas
│   └── services/
│       ├── product_service.py    # Product business logic
│       └── order_service.py      # Order business logic + idempotency
├── tests/
│   ├── conftest.py               # Fixtures, test DB, test client
│   ├── test_health.py
│   ├── test_products.py
│   └── test_orders.py
├── nginx/
│   ├── nginx.conf                # Nginx reverse proxy configuration
│   └── generate-certs.sh        # Self-signed TLS cert generator
├── scripts/
│   ├── backup.sh                 # PostgreSQL backup script
│   ├── restore.sh                # PostgreSQL restore script
│   └── rollback.sh               # Docker image rollback
├── .github/
│   └── workflows/ci.yml         # GitHub Actions CI/CD pipeline
├── Dockerfile                   # Multi-stage production image
├── docker-compose.yml           # Full stack: db + api + nginx
├── docker-compose.test.yml      # Test runner compose
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development/test dependencies
├── pyproject.toml               # Pytest + ruff + coverage config
└── .env.example                 # Environment variable template
```

---

## Architecture

```
Client
  │
  ▼
Nginx (port 80/443)
  │  TLS termination, rate limiting, security headers
  ▼
FastAPI API (port 8000)
  │  Auth middleware, structured logging middleware
  ├─► /health, /readiness
  ├─► /api/v1/products  (GET public, POST/PATCH/stock admin)
  └─► /api/v1/orders    (POST public with idempotency, GET by ID)
         │
         ▼
   AsyncSession → PostgreSQL 16
```

---

## Quick Start

### Prerequisites

- Docker & Docker Compose v2
- `openssl` (for TLS cert generation)

### 1. Clone & configure

```bash
git clone <your-repo-url> ecommerce-platform
cd ecommerce-platform
cp .env.example .env
# Edit .env to set strong passwords and API key
```

### 2. Generate TLS certificates (dev only)

```bash
bash nginx/generate-certs.sh
```

### 3. Start the full stack

```bash
docker compose up -d --build
```

### 4. Verify it's running

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"ecommerce-api"}

curl http://localhost:8000/readiness
# {"status":"ready","database":"connected"}
```

### 5. Access interactive API docs

Open [http://localhost:8000/docs](http://localhost:8000/docs) in your browser.

### 6. Seed initial product data

```bash
docker compose exec api python -m app.seed
```

---

## Development Setup

### Python environment

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
```

### Local database (optional, with Docker)

```bash
docker compose up db -d
```

### Run the API locally

```bash
export DATABASE_URL="postgresql+asyncpg://ecom:ecom_pass@localhost:5432/ecomdb"
export API_KEY_ADMIN="dev-key"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Code quality

```bash
# Lint
ruff check app/ tests/

# Format check
ruff format --check app/ tests/

# Auto-fix
ruff check --fix app/ tests/
ruff format app/ tests/
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://ecom:ecom_pass@db:5432/ecomdb` | Async PostgreSQL URL |
| `DATABASE_POOL_SIZE` | `10` | SQLAlchemy connection pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | Max extra connections above pool size |
| `API_KEY_ADMIN` | `changeme-admin-key` | Admin API key (must override in prod) |
| `LOG_LEVEL` | `INFO` | Python log level (DEBUG, INFO, WARNING, ERROR) |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins (JSON list) |
| `APP_ENV` | `development` | Environment name |
| `APP_VERSION` | `1.0.0` | Application version |
| `POSTGRES_PASSWORD` | `ecom_pass` | Postgres password (Compose only) |

---

## Testing

Tests use **SQLite + aiosqlite** so no external database is required.

### Run all tests

```bash
pytest tests/ -v
```

### Run with coverage

```bash
pytest tests/ --cov=app --cov-report=term-missing --cov-report=html
```

### Test categories

| File | What it tests |
|---|---|
| `test_health.py` | Liveness and readiness endpoints |
| `test_products.py` | Product CRUD, search, stock adjustment, auth |
| `test_orders.py` | Order creation, idempotency, insufficient stock, status fetch |

### Key test cases

- **`test_create_product_requires_admin`** — Verifies `POST /api/v1/products` returns 422 without `X-API-Key`.
- **`test_order_idempotency`** — Posts the same `idempotency_key` twice and verifies same order ID is returned and stock is deducted only once.
- **`test_adjust_stock_prevents_negative`** — Verifies that a delta that would make stock < 0 returns HTTP 422.
- **`test_order_insufficient_stock`** — Verifies that ordering more than available stock returns HTTP 422.

---

## Docker

### Build only

```bash
docker build -t ecommerce-api:latest .
```

### Full stack

```bash
docker compose up -d --build
docker compose logs -f api
docker compose down
```

### Run tests in Docker

```bash
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit
```

### Services

| Service | Port | Description |
|---|---|---|
| `db` | 5432 | PostgreSQL 16 |
| `api` | 8000 | FastAPI application |
| `nginx` | 80, 443 | Reverse proxy with TLS |

---

## CI/CD

The `.github/workflows/ci.yml` pipeline runs on every push to `main`/`develop` and on PRs to `main`.

### Pipeline stages

```
push/PR
  │
  ├─► lint           (ruff check + format check)
  │
  ├─► test           (pytest with SQLite, coverage upload)
  │
  ├─► security-scan  (Trivy container vulnerability scan)
  │
  └─► build-and-push (GHCR image, only on main push)
        │
        └─► deploy   (SSH-based production deploy, only on main push)
```

### Setup requirements

1. **GitHub Container Registry** — Automatically used via `GITHUB_TOKEN`.
2. **Codecov** — Set `CODECOV_TOKEN` secret for coverage uploads.
3. **Production deploy** — Customize the `deploy` job step with your SSH credentials/cloud CLI.

---

## API Reference

### Health

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | None | Liveness check |
| GET | `/readiness` | None | Readiness check (DB ping) |

### Products

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/api/v1/products` | None | List/search products |
| GET | `/api/v1/products/{id}` | None | Get product by ID |
| POST | `/api/v1/products` | Admin | Create product |
| PATCH | `/api/v1/products/{id}` | Admin | Update product fields |
| POST | `/api/v1/products/{id}/stock` | Admin | Adjust stock quantity |

**Query parameters for GET `/api/v1/products`:**
- `q` — Search term (matches name or SKU, case-insensitive)
- `page` — Page number (default: 1)
- `page_size` — Items per page (default: 20, max: 100)

**Admin authentication:** Pass `X-API-Key: <your-key>` header.

### Orders

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/orders` | None | Create order (idempotent) |
| GET | `/api/v1/orders/{id}` | None | Get order status |

**Idempotency:** Include a unique `idempotency_key` string in the POST body. Submitting the same key again returns the existing order without side effects.

### Example: Create a product (admin)

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme-admin-key" \
  -d '{
    "sku": "LAPTOP-001",
    "name": "Pro Laptop 15\"",
    "description": "High-performance laptop",
    "price": "1299.99",
    "stock_quantity": 50
  }'
```

### Example: Create an order

```bash
curl -X POST http://localhost:8000/api/v1/orders \
  -H "Content-Type: application/json" \
  -d '{
    "idempotency_key": "order-20241110-001",
    "customer_email": "customer@example.com",
    "items": [
      {"product_id": "<product-uuid>", "quantity": 2}
    ]
  }'
```

---

## Database Seeding

The `app/seed.py` script populates the database with 8 sample products.

```bash
# In Docker:
docker compose exec api python -m app.seed

# Locally:
python -m app.seed
```

Seeded SKUs: `LAPTOP-001`, `PHONE-001`, `TABLET-001`, `HEADPHONE-001`, `KEYBOARD-001`, `MOUSE-001`, `MONITOR-001`, `SSD-001`.

---

## Backup and Restore (Local & AWS S3)

The backup and restore suite supports both local storage and remote **Amazon S3** offsite syncing with AES-256 encryption.

### Creating a Backup
- **Bash**:
  ```bash
  ./scripts/backup.sh
  ```
- **PowerShell (Windows)**:
  ```powershell
  .\scripts\backup.ps1
  ```
If `S3_BUCKET_NAME` is set in `.env`, the archive is automatically encrypted and pushed to `s3://$S3_BUCKET_NAME/backups/ecomdb_<timestamp>.sql.gz`.

### Restoring a Backup
You can restore from a local file or directly from an AWS S3 URI:
- **From Local**:
  ```bash
  ./scripts/restore.sh ./backups/ecomdb_20261112_140000.sql.gz
  ```
- **From AWS S3**:
  ```bash
  ./scripts/restore.sh s3://my-ecom-bucket/backups/ecomdb_20261112_140000.sql.gz
  ```
- **Windows PowerShell**:
  ```powershell
  .\scripts\restore.ps1 -Source "s3://my-ecom-bucket/backups/ecomdb_20261112_140000.sql.gz"
  ```

---

## AWS Cloud & Terraform IaC

A complete, enterprise-grade Terraform setup is available in `infra/terraform/`:
- **Amazon S3**: Offsite encrypted backup bucket with versioning, public access blocks, and 30-day Glacier lifecycle rules.
- **AWS ECS Fargate**: High-availability container cluster running `ecommerce-api` across multiple AZs.
- **AWS RDS PostgreSQL 16**: Multi-AZ managed database with KMS encryption and automated snapshots.
- **Application Load Balancer (ALB)**: TLS termination with health check routing to `/health`.
- **IAM Roles**: Least-privilege task execution and S3-backup scoped permissions.

For detailed provisioning steps, see [AWS Cloud Architecture & S3 Integration Guide](docs/AWS_DEPLOYMENT.md).

---

## Rollback

To roll back the API to a previously pushed image tag:

```bash
bash scripts/rollback.sh ghcr.io/<org>/<repo>/ecommerce-api:sha-<commit>
```

The script stops the current container, starts the target image, and performs a health check.

---

## Security Notes

- **Change `API_KEY_ADMIN`** before deploying to production. The default value is intentionally weak.
- **Change `POSTGRES_PASSWORD`** in `.env` before deploying.
- **Never commit `.env`** — it is in `.gitignore`.
- **TLS certificates** in `nginx/certs/` are also gitignored — generate real certs (e.g., via Let's Encrypt) for production.
- The API Docker container runs as a **non-root user** (`appuser`).
- Nginx applies **rate limiting** (30 requests/minute per IP) on API routes.
- Security headers are set: `X-Frame-Options`, `X-Content-Type-Options`, `HSTS`, `X-XSS-Protection`.
