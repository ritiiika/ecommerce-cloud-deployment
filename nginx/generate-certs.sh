#!/usr/bin/env bash
# Generate self-signed TLS certificate for local development
set -e
CERT_DIR="./nginx/certs"
mkdir -p "$CERT_DIR"
openssl req -x509 -nodes -newkey rsa:4096 \
    -keyout "$CERT_DIR/server.key" \
    -out "$CERT_DIR/server.crt" \
    -days 365 \
    -subj "/C=US/ST=Local/L=Local/O=EcomDev/CN=localhost"
echo "Self-signed cert generated at $CERT_DIR"
