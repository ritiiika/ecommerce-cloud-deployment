#!/usr/bin/env bash
# Restore PostgreSQL database from a backup file
# Usage: ./scripts/restore.sh <backup_file.sql.gz>
set -euo pipefail

BACKUP_FILE="${1:-}"
if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file.sql.gz>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "[restore] WARNING: This will drop and recreate ecomdb. Press CTRL+C to cancel."
sleep 5

echo "[restore] Dropping existing database..."
docker exec ecom_db psql -U ecom -c "DROP DATABASE IF EXISTS ecomdb;"
docker exec ecom_db psql -U ecom -c "CREATE DATABASE ecomdb;"

echo "[restore] Restoring from $BACKUP_FILE..."
gunzip -c "$BACKUP_FILE" | docker exec -i ecom_db psql -U ecom -d ecomdb

echo "[restore] Restore complete."
