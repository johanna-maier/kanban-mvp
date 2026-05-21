#!/usr/bin/env bash
set -euo pipefail

sudo docker build -t pm-app .
sudo docker rm -f pm-app >/dev/null 2>&1 || true
sudo docker run -d --name pm-app -p 8000:8000 --env-file .env pm-app
