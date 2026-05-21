$ErrorActionPreference = "Stop"

try { docker rm -f pm-app | Out-Null } catch {}
