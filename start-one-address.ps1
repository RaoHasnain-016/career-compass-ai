$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$frontendPath = Join-Path $projectRoot "frontend"
$backendPath = Join-Path $projectRoot "backend"
$backendPython = Join-Path $backendPath "venv\Scripts\python.exe"

Write-Host "Building frontend..."
Push-Location $frontendPath
try {
    npm.cmd run build
}
finally {
    Pop-Location
}

if (-not (Test-Path $backendPython)) {
    $backendPython = "python"
}

Write-Host "Starting Career Compass at http://localhost:8000"
Push-Location $backendPath
try {
    & $backendPython -m uvicorn app.main:app --host 0.0.0.0 --port 8000
}
finally {
    Pop-Location
}
