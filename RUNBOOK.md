# E-Commerce API — Operations Runbook

**Service:** `ecommerce-api`  
**Stack:** FastAPI + PostgreSQL 16 + Nginx (Docker Compose)  
**Maintainer:** Platform Engineering  
**Last Updated:** 2024-11-10

---

## Table of Contents

1. [Service Overview](#1-service-overview)
2. [Health Checks](#2-health-checks)
3. [Logs & Observability](#3-logs--observability)
4. [Incident Response](#4-incident-response)
5. [Backup & Restore](#5-backup--restore)
6. [Scaling](#6-scaling)
7. [Rollback Procedure](#7-rollback-procedure)
8. [Database Operations](#8-database-operations)
9. [Common Issues & Fixes](#9-common-issues--fixes)
10. [Maintenance Procedures](#10-maintenance-procedures)
11. [Contacts & Escalation](#11-contacts--escalation)

---

## 1. Service Overview

| Component | Container | Port | Image |
|---|---|---|---|
| PostgreSQL 16 | `ecom_db` | 5432 | `postgres:16-alpine` |
| FastAPI API | `ecom_api` | 8000 | Local build |
| Nginx reverse proxy | `ecom_nginx` | 80, 443 | `nginx:alpine` |

### Key paths

| Path | Description |
|---|---|
| `/health` | Liveness probe — returns `{"status":"ok"}` if the process is alive |
| `/readiness` | Readiness probe — pings the database, returns 503 if unreachable |
| `/api/v1/products` | Product catalogue endpoints |
| `/api/v1/orders` | Order management endpoints |
| `/docs` | Interactive Swagger UI |

### Dependencies

- PostgreSQL must be healthy before the API container starts (enforced by `depends_on: condition: service_healthy`)
- Nginx depends on the API container

---

## 2. Health Checks

### Manual liveness check

```bash
curl -sf http://localhost:8000/health && echo "OK" || echo "FAIL"
```

Expected response:

```json
{"status": "ok", "service": "ecommerce-api"}
```

### Manual readiness check (includes DB ping)

```bash
curl -sf http://localhost:8000/readiness && echo "OK" || echo "FAIL"
```

Expected response:

```json
{"status": "ready", "database": "connected"}
```

**If readiness returns 503**, the API cannot reach the database. See [Section 9 — Common Issues](#9-common-issues--fixes).

### Docker health status

```bash
docker inspect --format='{{.State.Health.Status}}' ecom_api
docker inspect --format='{{.State.Health.Status}}' ecom_db
```

Values: `healthy`, `unhealthy`, `starting`

### Check all container states

```bash
docker compose ps
```

---

## 3. Logs & Observability

### Stream live API logs

```bash
docker compose logs -f api
```

### Stream live DB logs

```bash
docker compose logs -f db
```

### Stream Nginx access logs

```bash
docker compose logs -f nginx
```

### Log format

The API emits structured JSON per request:

```json
{
  "request_id": "uuid-v4",
  "method": "POST",
  "path": "/api/v1/orders",
  "status_code": 201,
  "duration_ms": 42.3,
  "client_ip": "172.18.0.1"
}
```

Each response also includes the `X-Request-ID` header for correlation.

### Filter logs by status code

```bash
docker compose logs api | grep '"status_code": 5'
```

### Filter logs by path

```bash
docker compose logs api | grep '"path": "/api/v1/orders"'
```

---

## 4. Incident Response

### Severity levels

| Level | Criteria | Response time |
|---|---|---|
| P1 — Critical | API down, DB unreachable, all orders failing | Immediate |
| P2 — High | Elevated 5xx rate (> 1%), single endpoint degraded | < 30 min |
| P3 — Medium | Elevated latency, non-critical feature broken | < 2 hours |
| P4 — Low | Cosmetic, documentation, monitoring gaps | Next sprint |

### P1 response steps

1. **Assess** — Check container status and health endpoints.
   ```bash
   docker compose ps
   curl http://localhost:8000/health
   curl http://localhost:8000/readiness
   ```

2. **Check recent logs** for errors.
   ```bash
   docker compose logs --tail=200 api
   docker compose logs --tail=100 db
   ```

3. **Restart the API** (if the process is hung or in a bad state).
   ```bash
   docker compose restart api
   ```

4. **If DB is unreachable**, restart the DB and wait for it to become healthy.
   ```bash
   docker compose restart db
   docker compose logs -f db
   ```

5. **If still broken**, roll back to the last known-good image (see [Section 7](#7-rollback-procedure)).

6. **Post-incident** — Capture logs, write an incident report, file a ticket.

---

## 5. Backup & Restore

### Create a backup (Local & AWS S3)

- **Linux / macOS**:
  ```bash
  bash scripts/backup.sh
  ```
- **Windows PowerShell**:
  ```powershell
  .\scripts\backup.ps1
  ```

Backups are written to `./backups/ecomdb_<YYYYMMDD_HHMMSS>.sql.gz`. If `S3_BUCKET_NAME` is defined in `.env`, the script automatically uploads the encrypted archive to `s3://$S3_BUCKET_NAME/backups/`.

### List available backups
- Local:
  ```bash
  ls -lh ./backups/
  ```
- AWS S3:
  ```bash
  aws s3 ls s3://$S3_BUCKET_NAME/backups/
  ```

### Restore from backup (Local or AWS S3)

> **WARNING**: This will drop and recreate the database. All current data will be lost.

- **From Local File**:
  ```bash
  bash scripts/restore.sh ./backups/ecomdb_20241110_120000.sql.gz
  ```
- **From AWS S3 Directly**:
  ```bash
  bash scripts/restore.sh s3://my-ecom-backups/backups/ecomdb_20241110_120000.sql.gz
  ```
- **Windows PowerShell**:
  ```powershell
  .\scripts\restore.ps1 -Source "s3://my-ecom-backups/backups/ecomdb_20241110_120000.sql.gz"
  ```

The script pauses for 5 seconds before dropping the database — press Ctrl+C to cancel.

### Automated backup (cron example)

Add to crontab to run daily at 2 AM:

```
0 2 * * * cd /srv/ecommerce-platform && bash scripts/backup.sh >> /var/log/ecom_backup.log 2>&1
```

### Backup retention policy

- Keep daily backups for 7 days
- Keep weekly backups for 4 weeks
- Keep monthly backups for 12 months

Clean up old backups:

```bash
find ./backups -name "*.sql.gz" -mtime +7 -delete
```

---

## 6. Scaling

### Horizontal API scaling (multiple workers)

The `CMD` in the Dockerfile already runs with `--workers 2`. To increase:

```bash
# In docker-compose.yml, override the command:
command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Restart:

```bash
docker compose up -d api
```

### Scale API replicas (requires Docker Swarm or Kubernetes)

For Docker Swarm:

```bash
docker service scale ecommerce-platform_api=3
```

### Database connection pool tuning

Adjust in `.env`:

```
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

The API reads these at startup. Restart required:

```bash
docker compose restart api
```

### Nginx upstream scaling

If running multiple API replicas, update `nginx/nginx.conf`:

```nginx
upstream api_backend {
    server api1:8000;
    server api2:8000;
    server api3:8000;
    keepalive 32;
}
```

---

## 7. Rollback Procedure

Use this when a bad deployment causes P1/P2 incidents.

### Step 1: Identify the last good image tag

```bash
# List recent pushed images (GitHub Container Registry)
# Or check your CI/CD pipeline for the previous successful build tag
```

Tags follow the pattern: `sha-<short-commit-sha>`, e.g., `sha-abc1234`.

### Step 2: Execute rollback

```bash
bash scripts/rollback.sh ghcr.io/<org>/<repo>/ecommerce-api:sha-abc1234
```

The script will:
1. Stop and remove the current `ecom_api` container.
2. Start the target image with the same network and environment.
3. Wait 10 seconds and perform a health check.

### Step 3: Verify

```bash
curl http://localhost:8000/health
curl http://localhost:8000/readiness
docker compose logs --tail=50 api
```

### Step 4: Notify the team

Send a message to the engineering channel with:
- Incident time
- Rolled back from (bad tag) → (good tag)
- Impact assessment

---

## 8. Database Operations

### Connect to the database directly

```bash
docker exec -it ecom_db psql -U ecom -d ecomdb
```

### Common DBA queries

**Check active connections:**

```sql
SELECT pid, usename, application_name, state, query_start
FROM pg_stat_activity
WHERE datname = 'ecomdb';
```

**Check table sizes:**

```sql
SELECT
  relname AS table_name,
  pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
```

**Check long-running queries (> 30s):**

```sql
SELECT pid, now() - query_start AS duration, query
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '30 seconds';
```

**Kill a long-running query:**

```sql
SELECT pg_terminate_backend(<pid>);
```

**Check product stock:**

```sql
SELECT sku, name, stock_quantity, is_active FROM products ORDER BY sku;
```

**Check recent orders:**

```sql
SELECT id, customer_email, status, total_amount, created_at
FROM orders
ORDER BY created_at DESC
LIMIT 20;
```

### Reset test data

```bash
# Drop and recreate tables (warning: destroys all data)
docker exec -it ecom_db psql -U ecom -d ecomdb -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
# Then restart the API to trigger table creation
docker compose restart api
# Optionally re-seed
docker compose exec api python -m app.seed
```

---

## 9. Common Issues & Fixes

### Issue: API returns 503 on `/readiness`

**Cause:** API cannot reach PostgreSQL.

**Diagnosis:**
```bash
docker compose ps db
docker inspect --format='{{.State.Health.Status}}' ecom_db
docker compose logs --tail=50 db
```

**Fix:**
```bash
docker compose restart db
# Wait for healthy status
docker compose restart api
```

---

### Issue: `connection refused` or `ECONNREFUSED` to port 8000

**Cause:** API container crashed or not started.

**Diagnosis:**
```bash
docker compose ps api
docker compose logs --tail=100 api
```

**Fix:**
```bash
docker compose up -d api
```

---

### Issue: 401 on admin endpoints

**Cause:** Missing or incorrect `X-API-Key` header.

**Fix:** Ensure the request includes:
```
X-API-Key: <value-matching-API_KEY_ADMIN-env-var>
```

Check the current key:
```bash
docker compose exec api printenv API_KEY_ADMIN
```

---

### Issue: 422 on order creation — "Insufficient stock"

**Cause:** Requested quantity exceeds available stock.

**Fix:** Adjust stock via admin endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/products/<product-id>/stock \
  -H "X-API-Key: <admin-key>" \
  -H "Content-Type: application/json" \
  -d '{"quantity_delta": 50, "reason": "manual restock"}'
```

---

### Issue: Duplicate order attempt returns existing order

**Cause:** This is **expected behavior** — idempotency is working correctly. The same `idempotency_key` always returns the original order.

**Fix:** Use a new unique `idempotency_key` for a new order.

---

### Issue: Nginx 502 Bad Gateway

**Cause:** Nginx cannot reach the API backend.

**Diagnosis:**
```bash
docker compose logs nginx
docker compose ps api
```

**Fix:**
```bash
docker compose restart api
# If persists:
docker compose restart nginx
```

---

### Issue: SSL certificate errors

**Cause:** Self-signed certificates expired or not generated.

**Fix:**
```bash
bash nginx/generate-certs.sh
docker compose restart nginx
```

For production, use Let's Encrypt certificates.

---

### Issue: Database migrations not applied

**Cause:** Schema changes not reflected in database (this project uses `create_all` on startup for simplicity; use Alembic for production).

**Fix (development only — drops data):**
```bash
docker compose restart api
```

**Fix (production — use Alembic):**
```bash
alembic upgrade head
```

---

## 10. Maintenance Procedures

### Routine weekly tasks

- [ ] Check container health: `docker compose ps`
- [ ] Review error logs: `docker compose logs api | grep '"status_code": 5'`
- [ ] Verify backup completed and test backup integrity
- [ ] Review disk usage: `df -h` and `docker system df`

### Docker system cleanup (remove unused images/volumes)

```bash
# Remove unused images (not currently running)
docker image prune -f

# Remove unused volumes (careful — verify nothing important)
docker volume prune -f

# Full cleanup (use with care)
docker system prune -f
```

### Rotating the admin API key

1. Generate a new key: `openssl rand -hex 32`
2. Update `.env`: `API_KEY_ADMIN=<new-key>`
3. Restart the API: `docker compose up -d api`
4. Update all clients and secrets stores.

### Updating dependencies

1. Update version pins in `requirements.txt`.
2. Run tests locally: `pytest tests/ -v`
3. Build the Docker image: `docker build -t ecommerce-api:test .`
4. Push to a feature branch and let CI validate before merging to `main`.

---

## 11. Contacts & Escalation

| Role | Contact | For |
|---|---|---|
| On-call Engineer | PagerDuty rotation | P1/P2 incidents |
| Platform Lead | platform-lead@example.com | Architecture decisions |
| DBA | dba@example.com | Database issues |
| Security | security@example.com | Credential rotation, CVEs |

### Escalation path

```
On-call Engineer (15 min)
  → Platform Lead (30 min)
    → Engineering Manager (45 min)
      → VP Engineering (60 min)
```

### Useful links

- **Swagger UI:** http://localhost:8000/docs
- **GitHub Actions:** https://github.com/<org>/<repo>/actions
- **Container Registry:** https://ghcr.io/<org>/<repo>
- **Incident tracker:** https://your-jira-or-linear-instance/
