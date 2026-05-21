$ErrorActionPreference = "Stop"

docker build -t pm-app .
try { docker rm -f pm-app | Out-Null } catch {}
docker run -d --name pm-app -p 8000:8000 pm-app
