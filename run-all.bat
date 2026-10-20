@echo off
title BQAS Launcher
echo ==========================================================
echo   Beverage Quality Analysis System (BQAS) - Launch Script
echo ==========================================================
echo.
echo [1/2] Starting Backend (FastAPI on http://127.0.0.1:8000)...
start "BQAS Backend (FastAPI)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\activate && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [2/2] Starting Frontend (Vite on http://localhost:5173)...
start "BQAS Frontend (Vite)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Both servers have been launched in separate windows!
echo   Frontend Web:   http://localhost:5173
echo   Backend API:    http://127.0.0.1:8000
echo   API Swagger:    http://127.0.0.1:8000/docs
echo.
pause
