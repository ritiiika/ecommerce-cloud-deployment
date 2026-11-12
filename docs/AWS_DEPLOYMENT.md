# AWS Cloud Architecture & S3 Integration Guide
## E-Commerce Product & Order Platform

This document details the **AWS Cloud Architecture**, **Amazon S3 backup shipping**, and **Terraform Infrastructure as Code (IaC)** for the E-Commerce Platform.

---

## 1. Cloud Architecture Overview

In an enterprise AWS deployment, the containerized application scales across multiple Availability Zones with full managed resilience:

```
                            INTERNET / USERS
                                   │
                                   ▼
                       [ AWS Route 53 (DNS) ]
                                   │
                                   ▼
                   [ AWS Application Load Balancer ]
                    - SSL/TLS Termination (ACM)
                    - Health Check Probe: /health
                                   │
        ┌──────────────────────────┴──────────────────────────┐
        ▼ (AZ-1a)                                             ▼ (AZ-1b)
[ ECS Fargate Task 1 ]                                [ ECS Fargate Task 2 ]
  - Container: ecom_api                                 - Container: ecom_api
  - Non-root user: appuser                              - Non-root user: appuser
  - CloudWatch Logs: /ecs/ecom                          - CloudWatch Logs: /ecs/ecom
        └──────────────────────────┬──────────────────────────┘
                                   │
                                   ▼
                    [ AWS RDS PostgreSQL 16 ]
                    - Multi-AZ High Availability
                    - Storage Encrypted (AWS KMS)
                    - Port 5432 Ingress restricted to ECS SG
                                   │
                      Automated Offsite Backup Sync
                                   ▼
                    [ Amazon S3 Backup Bucket ]
                    - AES256 Server-Side Encryption
                    - Versioning Enabled
                    - Public Access Blocked (Zero Trust)
                    - Lifecycle: 30-day Glacier transition
```

---

## 2. Amazon S3 Backup & Disaster Recovery

### Key S3 Security & Lifecycle Features
1. **Server-Side Encryption**: All backup files pushed to S3 are encrypted at rest using `AES256` (`--sse AES256`).
2. **Object Versioning**: Prevents accidental overwrites or ransomware deletion of database state.
3. **Public Access Block**: All four AWS S3 public access block flags are enabled.
4. **Lifecycle Tiering**: Backups older than 30 days automatically transition to **Amazon S3 Glacier** to reduce storage costs by up to 80%; objects expire after 90 days.
5. **TLS Enforcement**: S3 bucket policy explicitly denies any unencrypted HTTP requests (`aws:SecureTransport = false`).

### Performing S3 Backups & Restores

#### Step 1: Configure Environment
In your `.env` file (or environment variables):
```bash
S3_BUCKET_NAME=your-production-ecom-backups
AWS_REGION=us-east-1
```

#### Step 2: Trigger Backup to S3
- **Linux / macOS / Git Bash**:
  ```bash
  ./scripts/backup.sh
  ```
- **Windows PowerShell**:
  ```powershell
  .\scripts\backup.ps1
  ```
*Output:*
```
[backup] Starting PostgreSQL backup from ecom_db container...
[backup] Local backup complete: ./backups/ecomdb_20261112_140000.sql.gz (1.2 MB)
[backup] S3_BUCKET_NAME configured: s3://your-production-ecom-backups
[backup] Uploading backup to AWS S3 with AES256 server-side encryption...
[backup] AWS S3 upload successful: s3://your-production-ecom-backups/backups/ecomdb_20261112_140000.sql.gz
```

#### Step 3: Disaster Recovery / Restore from S3
To restore directly from an S3 backup URI:
- **Linux / macOS / Git Bash**:
  ```bash
  ./scripts/restore.sh s3://your-production-ecom-backups/backups/ecomdb_20261112_140000.sql.gz
  ```
- **Windows PowerShell**:
  ```powershell
  .\scripts\restore.ps1 -Source "s3://your-production-ecom-backups/backups/ecomdb_20261112_140000.sql.gz"
  ```
The script will automatically download the archive from S3, verify integrity, drop/recreate `ecomdb`, and reload the entire database.

---

## 3. Infrastructure as Code (Terraform)

All AWS cloud infrastructure is declaratively defined in `infra/terraform/`:

| File | Purpose |
|---|---|
| `main.tf` | AWS Provider configuration and minimum version constraints |
| `variables.tf` | Customizable variables (regions, CIDRs, credentials) |
| `s3.tf` | Disaster recovery S3 bucket with encryption and lifecycle policies |
| `vpc.tf` | High-availability VPC across 2 AZs (public & private subnets) |
| `rds.tf` | AWS RDS PostgreSQL 16 instance with automated 7-day backups |
| `ecs.tf` | AWS ECS Fargate cluster, task definition, and 2-replica service |
| `alb.tf` | Application Load Balancer with HTTP/HTTPS listeners and health check routing |
| `iam.tf` | Least-privilege IAM task execution and S3-backup scoped roles |
| `outputs.tf` | Exported endpoints (ALB DNS name, S3 bucket ARN, RDS endpoint) |

### Deploying to AWS via Terraform

```bash
cd infra/terraform

# 1. Initialize Terraform plugins
terraform init

# 2. Review the execution plan
terraform plan -var-file="terraform.tfvars.example"

# 3. Apply the infrastructure
terraform apply -var-file="terraform.tfvars.example" -auto-approve
```

---

## 4. Free-Tier & LocalStack (Local S3 Emulation)

If you wish to demonstrate AWS S3 upload and download **locally without incurring AWS fees**:

1. You can test against LocalStack or MinIO by setting `AWS_ENDPOINT_URL`:
   ```bash
   export AWS_ENDPOINT_URL="http://localhost:4566"
   export S3_BUCKET_NAME="demo-backup-bucket"
   ```
2. Run `.\scripts\backup.ps1` or `./scripts/backup.sh`. The scripts detect `AWS_ENDPOINT_URL` and pass `--endpoint-url` automatically to the AWS CLI.
