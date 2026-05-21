$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $PSScriptRoot

docker build -t pm-app $Root
try { docker rm -f pm-app | Out-Null } catch {}
docker run -d --name pm-app -p 8000:8000 --env-file "$Root\.env" pm-app

try {
    Write-Host "Waiting for container..."
    $attempts = 0
    while ($attempts -lt 30) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) { break }
        } catch {}
        Start-Sleep -Seconds 1
        $attempts++
    }

    Set-Location "$Root\frontend"
    $env:DOCKER_TEST = "1"
    npm run test:e2e
} finally {
    try { docker rm -f pm-app | Out-Null } catch {}
}
