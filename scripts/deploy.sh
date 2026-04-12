#!/bin/bash
# Deploy script for GSH-V2 on Saltbox
# Usage: deploy.sh [version-tag]
# Example: deploy.sh main (default) or deploy.sh v1.0.0

set -e  # Exit on error

VERSION=${1:-main}
REPO=/opt/gsh/repo
MAX_RETRIES=30
RETRY_DELAY=2

echo ""
echo "════════════════════════════════════════════════════════════"
echo "  GSH Deploy Script"
echo "════════════════════════════════════════════════════════════"
echo "  Version: $VERSION"
echo "  Repo: $REPO"
echo ""

# 1. Check repo exists
if [ ! -d "$REPO" ]; then
  echo "  ✗ ERROR: repo not found at $REPO"
  exit 1
fi
cd "$REPO"

# 2. Fetch latest from GitHub
echo "  [1/5] Fetching from GitHub..."
git fetch --all --tags > /dev/null 2>&1 || { echo "  ✗ ERROR: git fetch failed"; exit 1; }

# 3. Checkout version
echo "  [2/5] Checking out $VERSION..."
git checkout "$VERSION" > /dev/null 2>&1 || git checkout "refs/tags/$VERSION" > /dev/null 2>&1 || { echo "  ✗ ERROR: checkout failed"; exit 1; }

# 4. Pull latest images and restart containers
echo "  [3/5] Pulling latest Docker images from GHCR..."
docker compose pull > /dev/null 2>&1 || { echo "  ✗ ERROR: docker compose pull failed"; exit 1; }

echo "  [4/5] Starting Docker containers..."
docker compose up -d > /dev/null 2>&1 || { echo "  ✗ ERROR: docker compose up failed"; exit 1; }

# 5. Wait for backend to be healthy
echo "  [5/5] Waiting for backend to be ready..."
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  if docker compose logs gsh-backend 2>/dev/null | grep -q "Application startup complete\|Uvicorn running"; then
    echo ""
    echo "  ✓ Backend is ready!"
    break
  fi
  RETRY_COUNT=$((RETRY_COUNT + 1))
  if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo ""
    echo "  ⚠ Backend health check timeout. Check logs with: docker compose logs gsh-backend"
  fi
  sleep $RETRY_DELAY
done

# Show final status
echo ""
echo "════════════════════════════════════════════════════════════"
echo "  Deployment Complete"
echo "════════════════════════════════════════════════════════════"
docker compose ps
echo ""
echo "  Useful commands:"
echo "    • View logs:     docker compose logs -f gsh-backend"
echo "    • Stop services: docker compose down"
echo "    • Restart:       docker compose restart"
echo ""
