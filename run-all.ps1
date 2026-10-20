# BQAS: Start Frontend & Backend Together
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Beverage Quality Analysis System (BQAS) - Launch Script" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition

Write-Host "`n[1/2] Starting Backend (FastAPI) on http://127.0.0.1:8000..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath\backend'; .venv\Scripts\Activate.ps1; uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

Start-Sleep -Seconds 2

Write-Host "[2/2] Starting Frontend (Vite) on http://localhost:5173..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$RootPath\frontend'; npm run dev"

Write-Host "`n✔ Both servers launched in dedicated process windows!" -ForegroundColor Yellow
Write-Host "  - Frontend: http://localhost:5173" -ForegroundColor Green
Write-Host "  - Backend API: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "  - Swagger Docs: http://127.0.0.1:8000/docs`n" -ForegroundColor DarkGray
