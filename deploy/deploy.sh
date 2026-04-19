#!/usr/bin/env bash
# Deploy / upgrade script.  Run as root on the VPS.
# Usage: ./deploy/deploy.sh [--first-run]
set -euo pipefail

REPO_DIR="/opt/shitposter"
SERVICE="shitposter"

echo "==> Pulling latest code..."
git -C "$REPO_DIR" pull --ff-only

echo "==> Building Docker image..."
docker compose -f "$REPO_DIR/docker-compose.yml" build --pull

echo "==> Running Alembic migrations..."
docker compose -f "$REPO_DIR/docker-compose.yml" run --rm app alembic upgrade head

if [[ "${1:-}" == "--first-run" ]]; then
  echo "==> Seeding sources table..."
  docker compose -f "$REPO_DIR/docker-compose.yml" run --rm app python -m scripts.seed_sources
fi

echo "==> Restarting services..."
systemctl reload-or-restart "$SERVICE"

echo "==> Checking health..."
sleep 5
curl -sf http://localhost:8000/healthz && echo " OK" || echo " UNHEALTHY — check logs"
echo "==> Done."
