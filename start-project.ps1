$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$pythonCandidates = @(
    (Join-Path $projectRoot '.venv\Scripts\python.exe'),
    (Get-Command python -ErrorAction SilentlyContinue).Source
)
$pythonPath = $null
foreach ($candidate in $pythonCandidates) {
    if ($candidate -and (Test-Path $candidate)) {
        & $candidate -c 'import uvicorn' 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonPath = $candidate
            break
        }
    }
}
if (-not $pythonPath) {
    throw 'A Python interpreter with uvicorn was not found. Install backend/requirements.txt before starting the backend.'
}

Write-Host 'Starting Spam Email Detection services...' -ForegroundColor Cyan

function Test-LocalPort($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-LocalPort 8000)) {
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-ExecutionPolicy', 'Bypass',
        '-Command', "Set-Location '$projectRoot'; & '$pythonPath' -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000"
    )
} else {
    Write-Host 'Backend already running on port 8000.' -ForegroundColor Yellow
}

if (-not (Test-LocalPort 5173)) {
    Start-Process powershell -ArgumentList @(
        '-NoExit',
        '-ExecutionPolicy', 'Bypass',
        '-Command', "Set-Location '$projectRoot/frontend'; npm run dev -- --host 127.0.0.1 --port 5173"
    )
} else {
    Write-Host 'Frontend already running on port 5173.' -ForegroundColor Yellow
}

Write-Host 'Backend:  http://127.0.0.1:8000' -ForegroundColor Green
Write-Host 'Frontend: http://127.0.0.1:5173/#/dashboard' -ForegroundColor Green
Start-Process 'http://127.0.0.1:5173/#/dashboard'
