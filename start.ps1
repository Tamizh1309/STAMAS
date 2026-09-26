# STAMAS Windows PowerShell 1-Command Startup Script
# Usage: .\start.ps1

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  STAMAS — AI-Powered Bid Compliance Verification Platform" -ForegroundColor BrightWhite
Write-Host "  SIH26100 GeM Procurement Platform — Quick Startup Script" -ForegroundColor Yellow
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# 1. Environment file setup
if (-not (Test-Path "$ScriptDir\.env")) {
    Write-Host "[+] Creating .env from .env.example..." -ForegroundColor Green
    Copy-Item "$ScriptDir\.env.example" "$ScriptDir\.env"
}

# 2. Check Backend Virtual Environment
$VenvPython = "$ScriptDir\backend\venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[!] Virtual environment not found at backend\venv. Setting up..." -ForegroundColor Yellow
    Set-Location "$ScriptDir\backend"
    python -m venv venv
    & "$VenvPython" -m pip install --upgrade pip
    & "$VenvPython" -m pip install -r requirements.txt
    Set-Location $ScriptDir
}

Write-Host "[+] Starting STAMAS Backend API Server on http://localhost:8000..." -ForegroundColor Green
$BackendProcess = Start-Process -FilePath $VenvPython -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port 8000" -WorkingDirectory "$ScriptDir\backend" -PassThru

Start-Sleep -Seconds 3

Write-Host "[+] Starting STAMAS Frontend Dev Server on http://localhost:3000..." -ForegroundColor Green
$FrontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "$ScriptDir\frontend" -PassThru

Write-Host ""
Write-Host "-----------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "  STAMAS Platform Running Successfully!" -ForegroundColor Green
Write-Host "  - Frontend UI:    http://localhost:3000" -ForegroundColor White
Write-Host "  - Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "  - API Swagger:    http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health Check:   http://localhost:8000/api/v1/health" -ForegroundColor White
Write-Host "  - Readiness:      http://localhost:8000/api/v1/health/ready" -ForegroundColor White
Write-Host "-----------------------------------------------------------------" -ForegroundColor Cyan
Write-Host "Press Ctrl+C or close terminal windows to stop STAMAS." -ForegroundColor Gray
