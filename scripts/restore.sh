#!/usr/bin/env bash
# Restore PostgreSQL database from a local backup file or AWS S3 URI
# Usage: ./scripts/restore.sh <backup_file.sql.gz | s3://bucket/path/backup.sql.gz>
set -euo pipefail

SOURCE="${1:-}"
if [ -z "$SOURCE" ]; then
    echo "Usage: $0 <backup_file.sql.gz | s3://bucket/path/backup.sql.gz>"
    echo "Example (local): $0 ./backups/ecomdb_20261110_120000.sql.gz"
    echo "Example (AWS S3): $0 s3://my-ecom-backup-bucket/backups/ecomdb_20261110_120000.sql.gz"
    exit 1
fi

TEMP_RESTORE_FILE=""
if [[ "$SOURCE" =~ ^s3:// ]]; then
    echo "[restore] Detected S3 source URI: $SOURCE"
    TEMP_RESTORE_FILE="/tmp/ecom_s3_restore_$(date +%s).sql.gz"
    
    AWS_EXTRA_ARGS=""
    if [ -n "${AWS_ENDPOINT_URL:-}" ]; then
        AWS_EXTRA_ARGS="--endpoint-url $AWS_ENDPOINT_URL"
    fi
    
    echo "[restore] Downloading backup from AWS S3 to $TEMP_RESTORE_FILE..."
    aws s3 cp "$SOURCE" "$TEMP_RESTORE_FILE" $AWS_EXTRA_ARGS
    BACKUP_FILE="$TEMP_RESTORE_FILE"
else
    BACKUP_FILE="$SOURCE"
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[restore] WARNING: This will drop and recreate ecomdb. Press CTRL+C within 5 seconds to cancel."
sleep 5

echo "[restore] Dropping and recreating database ecomdb..."
docker exec ecom_db psql -U ecom -c "DROP DATABASE IF EXISTS ecomdb;"
docker exec ecom_db psql -U ecom -c "CREATE DATABASE ecomdb;"

echo "[restore] Restoring schema and data from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i ecom_db psql -U ecom -d ecomdb

# Cleanup temp S3 download if applicable
if [ -n "$TEMP_RESTORE_FILE" ] && [ -f "$TEMP_RESTORE_FILE" ]; then
    rm -f "$TEMP_RESTORE_FILE"
fi

echo "[restore] Restore complete."
