#!/usr/bin/env bash
set -euo pipefail

docker build -t pm-app .
docker rm -f pm-app >/dev/null 2>&1 || true
docker run -d --name pm-app -p 8000:8000 pm-app
