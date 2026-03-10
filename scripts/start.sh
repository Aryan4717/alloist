#!/usr/bin/env bash
# Alloist pilot deployment – start services and create signing key (first run).

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if ! command -v docker &>/dev/null; then
  echo "Docker is required. Install Docker and try again." >&2
  exit 1
fi

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example"
  else
    echo "Warning: .env not found. Create .env with TOKEN_SERVICE_API_KEY, POLICY_SERVICE_API_KEY, JWT_SECRET" >&2
  fi
fi

echo "Starting Alloist services..."
docker compose up -d

echo "Waiting for token service..."
for i in $(seq 1 30); do
  if curl -sf http://localhost:8000/keys >/dev/null 2>&1; then
    echo "Token service is ready"
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "Token service did not become ready in time" >&2
    exit 1
  fi
  sleep 2
done

echo "Creating signing key (first run only)..."
docker compose exec -T token_service python -m app.cli.rotate_key 2>/dev/null || true

echo ""
echo "=== Alloist is ready ==="
echo "Token Service:  http://localhost:8000  (docs: http://localhost:8000/docs)"
echo "Policy Service: http://localhost:8001 (docs: http://localhost:8001/docs)"
echo ""
echo "Create a token:  python examples/create_token.py"
echo "Apply policies:  python examples/apply_policies.py"
echo ""
