#!/usr/bin/env bash
# Rollback the API service to a previously verified image tag using Docker Compose
# Usage: ./scripts/rollback.sh <image_tag>
set -euo pipefail

IMAGE_TAG="${1:-}"
if [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <image_tag>"
    echo "Example: $0 ghcr.io/your-org/ecommerce-api:sha-a553bf9"
    exit 1
fi

echo "[rollback] Target rollback image: $IMAGE_TAG"
echo "[rollback] Checking/pulling image..."
docker pull "$IMAGE_TAG" 2>/dev/null || echo "[rollback] Using local image: $IMAGE_TAG"

echo "[rollback] Creating temporary compose override for target image..."
cat <<EOF > docker-compose.rollback.yml
version: "3.9"
services:
  api:
    image: $IMAGE_TAG
    build: !reset null
EOF

echo "[rollback] Applying rollback via Docker Compose..."
docker compose -f docker-compose.yml -f docker-compose.rollback.yml up -d --no-deps api
rm -f docker-compose.rollback.yml

echo "[rollback] Awaiting container health check..."
for i in {1..12}; do
    if docker exec ecom_api curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "[rollback] SUCCESS: Service healthy on rollback image $IMAGE_TAG"
        exit 0
    fi
    echo "[rollback] Probe check ($i/12)..."
    sleep 5
done

echo "[rollback] ERROR: Health check timed out after rollback." >&2
exit 1
