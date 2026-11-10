#!/usr/bin/env bash
# Backup PostgreSQL database to a timestamped file
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-./backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/ecomdb_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[backup] Starting backup to $BACKUP_FILE"
docker exec ecom_db pg_dump \
    -U ecom \
    -d ecomdb \
    --no-owner \
    --no-acl \
    | gzip > "$BACKUP_FILE"

echo "[backup] Backup complete: $BACKUP_FILE"
echo "[backup] Size: $(du -sh "$BACKUP_FILE" | cut -f1)"
