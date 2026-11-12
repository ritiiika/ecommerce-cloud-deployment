#!/usr/bin/env bash
# Backup PostgreSQL database to a timestamped file and optionally push to AWS S3
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ecomdb_$TIMESTAMP.sql.gz"
S3_BUCKET="${S3_BUCKET_NAME:-}"

mkdir -p "$BACKUP_DIR"

echo "[backup] Starting PostgreSQL backup to $BACKUP_FILE..."
docker exec ecom_db pg_dump \
    -U ecom \
    -d ecomdb \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

echo "[backup] Local backup complete: $BACKUP_FILE"
echo "[backup] Size: $(du -sh "$BACKUP_FILE" 2>/dev/null | cut -f1 || wc -c < "$BACKUP_FILE" | awk '{print $1 " bytes"}')"

# Optional AWS S3 upload
if [ -n "$S3_BUCKET" ]; then
    echo "[backup] S3_BUCKET_NAME configured: s3://$S3_BUCKET"
    echo "[backup] Uploading backup to AWS S3..."
    
    AWS_EXTRA_ARGS=""
    if [ -n "${AWS_ENDPOINT_URL:-}" ]; then
        AWS_EXTRA_ARGS="--endpoint-url $AWS_ENDPOINT_URL"
    fi
    
    aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/ecomdb_$TIMESTAMP.sql.gz" \
        --sse AES256 \
        $AWS_EXTRA_ARGS
    
    echo "[backup] AWS S3 upload complete: s3://$S3_BUCKET/backups/ecomdb_$TIMESTAMP.sql.gz"
else
    echo "[backup] Note: S3_BUCKET_NAME not set. Backup stored locally."
    echo "[backup] Tip: Set S3_BUCKET_NAME=<your-bucket> in .env to enable automatic AWS S3 cloud offsite sync."
fi
