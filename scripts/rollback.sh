#!/usr/bin/env bash
# Rollback to a previously tagged Docker image version
# Usage: ./scripts/rollback.sh <image_tag>
set -euo pipefail

IMAGE_TAG="${1:-}"
if [ -z "$IMAGE_TAG" ]; then
    echo "Usage: $0 <image_tag>"
    echo "Example: $0 ecommerce-api:v1.0.0"
    exit 1
fi

echo "[rollback] Rolling back API to image: $IMAGE_TAG"

docker stop ecom_api || true
docker rm ecom_api || true
docker run -d \
    --name ecom_api \
    --network ecommerce-platform_default \
    --env-file .env \
    -p 8000:8000 \
    --restart unless-stopped \
    "$IMAGE_TAG"

echo "[rollback] Waiting for health check..."
sleep 10
docker exec ecom_api curl -f http://localhost:8000/health && echo "[rollback] Service healthy after rollback."
