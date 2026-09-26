@echo off
REM STAMAS Windows Command Prompt Startup Script
title STAMAS GeM Procurement Compliance Platform

echo =================================================================
echo   STAMAS -- AI-Powered Bid Compliance Verification Platform
echo   SIH26100 GeM Procurement Platform -- Quick Startup Script
echo =================================================================
echo.

if not exist ".env" (
    echo [+] Creating .env from .env.example...
    copy .env.example .env >nul
)

echo [+] Starting Backend API Server (Port 8000)...
start "STAMAS Backend Server" cmd /k "cd /d %~dp0backend && .\venv\Scripts\python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [+] Starting Frontend Server (Port 3000)...
start "STAMAS Frontend UI" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo -----------------------------------------------------------------
echo   STAMAS Platform Running Successfully!
echo   - Frontend UI:    http://localhost:3000
echo   - Backend API:    http://localhost:8000
echo   - API Docs:       http://localhost:8000/docs
echo   - Health Check:   http://localhost:8000/api/v1/health
echo -----------------------------------------------------------------
echo.
pause
