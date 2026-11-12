# Assessment Submission Package
## Algions AI Labs Private Limited — DevOps & Cloud Engineering
### Project: Cloud Deployment & CI/CD – E-Commerce Platform

---

## 1. Candidate Identification & Assignment Details

| Form Section | Candidate Details |
|---|---|
| **Student Name** | *(Enter your full name)* |
| **Registration Number** | *(Enter your college/university registration number)* |
| **University Email** | *(Enter your university/institutional email)* |
| **Internship Role** | DevOps & Cloud Engineering |
| **Assigned Project Title** | Cloud Deployment & CI/CD – E-Commerce Platform |
| **Domain Allocated** | E-Commerce (Product and Order API) |

---

## 2. Code & Version Control

| Field | Submission Value | Notes |
|---|---|---|
| **Repository URL** | `https://github.com/<your-username>/ecommerce-platform` | *Replace with your GitHub repository link* |
| **Primary Branch** | `main` | Production branch with CI/CD triggers |
| **Final Commit ID** | `HEAD` *(or commit hash from `git rev-parse HEAD`)* | Pushed to GitHub |
| **Reviewer Access** | Public (or grant access to Algions evaluation team) | Ensure repository visibility |

---

## 3. Technology Stack & Limitations

### Technology Stack
- **API Framework**: Python 3.11+, FastAPI 0.115, Pydantic v2 & Pydantic-Settings
- **ORM & Data Layer**: SQLAlchemy 2.0 (Async), `asyncpg` for PostgreSQL, `aiosqlite` for tests
- **Database**: PostgreSQL 16 Alpine with persistent named Docker volume (`postgres_data`)
- **Reverse Proxy & Ingress**: Nginx Alpine with TLS 1.2/1.3 termination, rate-limiting (`limit_req_zone`), and security headers
- **Containerization**: Multi-stage Dockerfile (`builder` + minimal `runtime`), non-root user (`appuser`, UID 10001), Docker healthcheck
- **Orchestration**: Docker Compose v2 with healthcheck-based service startup (`condition: service_healthy`)
- **CI/CD Automation**: GitHub Actions (`.github/workflows/ci.yml`) featuring:
  - Ruff linting and formatting verification
  - Pytest test execution with coverage reports
  - Aquasecurity Trivy container security & vulnerability scan
  - Docker buildx multi-stage build, commit-SHA and semver tagging
  - Image push to GitHub Container Registry (`ghcr.io`)
- **Cloud & AWS Infrastructure (IaC)**:
  - Automated **Amazon S3** offsite backup sync with server-side AES256 encryption & 30-day Glacier lifecycle policy
  - Complete **Terraform** configuration (`infra/terraform/`) provisioning VPC, ECS Fargate, RDS PostgreSQL, ALB, S3, and least-privilege IAM roles
- **Reliability & Ops**: Automated shell & PowerShell scripts for backup (`pg_dump` + gzip), S3 sync, restore (database recreation and import), and container rollback to previous image tags.

### Architecture Diagram
```
                          +-------------------------------------------------+
                          |                   CLIENT BROWSER / API CONSUMER  |
                          +-------------------------------------------------+
                                                   |
                                       HTTPS (443) / HTTP (80 Redirect)
                                                   v
                          +-------------------------------------------------+
                          |             NGINX REVERSE PROXY (:443)          |
                          |  - TLS Termination (server.crt / server.key)    |
                          |  - Rate Limiting: 30 requests/min               |
                          |  - Security Headers: HSTS, X-Frame, X-Content   |
                          +-------------------------------------------------+
                                                   |
                                       Internal Docker Network
                                       proxy_pass: http://api:8000
                                                   v
                          +-------------------------------------------------+
                          |             FASTAPI APPLICATION (:8000)         |
                          |  - Non-root Container User (appuser)            |
                          |  - Structured JSON Logging Middleware           |
                          |  - Liveness (/health) & Readiness (/readiness)  |
                          |  - Admin Auth Middleware (X-API-Key)            |
                          |  - Business Logic & Idempotency Layer           |
                          +-------------------------------------------------+
                                                   |
                                       SQLAlchemy Async (asyncpg)
                                       Port 5432
                                                   v
                          +-------------------------------------------------+
                          |            POSTGRESQL 16 DATABASE (:5432)        |
                          |  - Tables: products, orders, order_items        |
                          |  - Persistent Volume: postgres_data             |
                          |  - Row-Level Locking: SELECT ... FOR UPDATE     |
                          +-------------------------------------------------+
                                                   |
                                      Automated Backup Pipeline
                                                   v
                          +-------------------------------------------------+
                          |         LOCAL BACKUP STORAGE (backups/)         |
                          |  - Timestamped Gzipped SQL Dumps                |
                          |  - Managed via scripts/backup.sh & restore.sh   |
                          +-------------------------------------------------+
```

### Known Incomplete Features & Intentional Scope Boundaries
1. **Frontend / Storefront**: Per Section 1 of the assessment brief, this service deliberately implements only the Product and Order backend API, avoiding extraneous frontend marketplace bloat.
2. **Payment Gateway Integration**: Payment processing is represented through checkout snapshotting and order confirmation statuses rather than live third-party PSP webhooks, matching the assignment requirements.
3. **TLS Certificates in Local Demo**: Uses an automated 4096-bit RSA self-signed certificate (`nginx/generate-certs.sh`) for HTTPS testing in local/free-tier container environments; production would replace this with Let's Encrypt / Certbot or an AWS ACM / Cloudflare certificate.

---

## 4. Key Acceptance Criteria & Evidence

### Rule 1: Idempotency & Negative Stock Prevention
- **Implementation**: Order creation checks `idempotency_key` against existing records before acquiring product locks. Re-submitting the same key returns the previously created order without creating duplicates or deducting inventory twice.
- **Stock Protection**: Uses PostgreSQL row-level locks (`SELECT ... FOR UPDATE`) during checkout. If stock is insufficient, the transaction rolls back cleanly with HTTP 422.
- **Test Evidence**:
  - `tests/test_orders.py::test_order_idempotency`
  - `tests/test_orders.py::test_order_insufficient_stock`
  - `tests/test_products.py::test_adjust_stock_prevents_negative`

### Rule 2: Container Security & Reproducibility
- Multi-stage Docker build produces a lean runtime image.
- Process runs under `appuser` (non-root UID/GID).
- Compose defines dependency healthchecks ensuring `db` is fully initialized before `api` binds ports.

### Rule 3: Observability & Health Probes
- `/health`: Instant process liveness check (HTTP 200).
- `/readiness`: Active database ping (`SELECT 1`) returning HTTP 200 when ready, HTTP 503 when disconnected.
- Request middleware logs every incoming request in structured JSON format including `request_id`, `method`, `path`, `status_code`, `duration_ms`, and `client_ip`.

### Rule 4: Data Recovery & Rollback
- Database backup script: `./scripts/backup.sh` creates timestamped gzip dumps.
- Database restore script: `./scripts/restore.sh <file>` cleanly drops, recreates, and re-imports data.
- Container rollback script: `./scripts/rollback.sh <image_tag>` performs controlled rollbacks to prior tagged releases.

---

## 5. 3–5 Minute Video Demonstration Script

Use this structured walkthrough script when recording your 3–5 minute presentation:

```
[0:00 - 0:45] INTRODUCTION & ARCHITECTURE OVERVIEW
- "Hello, I am [Your Name], presenting my DevOps & Cloud Engineering assessment for Algions AI Labs."
- Show the architecture diagram: Client -> Nginx HTTPS (443) -> FastAPI (8000) -> PostgreSQL (5432).
- Briefly highlight the multi-stage Dockerfile running as non-root and the Docker Compose setup.

[0:45 - 1:45] CI/CD PIPELINE & AUTOMATED CHECKS
- Open GitHub Actions tab in your repository.
- Walk through the pipeline stages: Lint (Ruff) -> Unit & Integration Tests (Pytest) -> Security Scan (Trivy) -> Buildx Container Build -> Push to ghcr.io.
- Show test results proving 100% pass on idempotency, stock deductions, and health checks.

[1:45 - 2:45] LIVE SERVICE DEPLOYMENT & ACCEPTANCE TESTS
- Run `docker compose ps` showing healthy containers: ecom_nginx, ecom_api, ecom_db.
- Test liveness and readiness:
  curl -k https://localhost/health
  curl -k https://localhost/readiness
- Demonstrate Idempotency:
  Submit an order with key "DEMO-KEY-100". Show order created.
  Re-send the EXACT same request with "DEMO-KEY-100".
  Show that the API returns HTTP 200/201 with the original order ID and stock is deducted ONLY ONCE.
- Demonstrate Admin Protection:
  Attempt product stock update without X-API-Key (HTTP 401/422).
  Add valid X-API-Key and show successful stock adjustment with audit log output.

[2:45 - 4:00] FAILURE INJECTION, OBSERVABILITY & RECOVERY
- Stream API logs: `docker compose logs -f api` showing structured JSON logs.
- Simulate DB failure: `docker stop ecom_db`
- Query readiness: `curl -k https://localhost/readiness` -> returns HTTP 503 Service Unavailable.
- Recover DB: `docker start ecom_db` -> readiness recovers to HTTP 200 automatically.

[4:00 - 4:45] BACKUP, RESTORE & ROLLBACK (LOCAL & AWS S3)
- Trigger backup: `./scripts/backup.sh` (or `.\scripts\backup.ps1`) -> displays newly created timestamped gzip dump.
- Point out optional AWS S3 sync: with S3_BUCKET_NAME set, the backup is encrypted with AES256 and pushed to AWS S3.
- Drop or alter test data, then execute `./scripts/restore.sh backups/<file>.sql.gz` (or `restore.sh s3://<bucket>/<file>.sql.gz`).
- Verify database records are restored.
- Show Terraform infrastructure in `infra/terraform/` (ECS, RDS, S3, ALB) and conclude with the runbook (`RUNBOOK.md`).
```

---

## 6. AI Attribution & Compliance Declarations

| Declaration Field | Candidate Statement |
|---|---|
| **Originality** | I confirm that the architecture, configuration, implementation logic, and operational runbooks were created and validated for this assessment. |
| **Explainability** | I am prepared to explain any part of the architecture, codebase, pipeline, and containerization configuration during the technical walkthrough and live debugging interview. |
| **Sensitive Data** | No live production secrets, real passwords, private keys, or API tokens are committed to this repository. All credentials use environment variable substitution via `.env.example`. |
| **AI Tool Attribution** | Antigravity AI coding assistant was used for codebase scaffolding, test fixture generation, and Markdown documentation generation. All code was reviewed, verified, and tested. |
