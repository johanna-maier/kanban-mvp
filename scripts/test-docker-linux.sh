#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$SCRIPT_DIR/.."

docker build -t pm-app "$ROOT"
docker rm -f pm-app >/dev/null 2>&1 || true
docker run -d --name pm-app -p 8000:8000 --env-file "$ROOT/.env" pm-app

trap 'docker rm -f pm-app >/dev/null 2>&1 || true' EXIT

echo "Waiting for container..."
until curl -sf http://127.0.0.1:8000/api/health > /dev/null; do sleep 1; done

cd "$ROOT/frontend"
DOCKER_TEST=1 npm run test:e2e
