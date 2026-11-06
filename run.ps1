# Kuber Data Core (कुबेर) PowerShell Startup Launcher
Set-Location -Path $PSScriptRoot

Write-Host "========================================================================" -ForegroundColor Yellow
Write-Host "  KUBER DATA CORE (कुबेर) — FINANCIAL KNOWLEDGE GRAPH & MARKET CORTEX   " -ForegroundColor White
Write-Host "========================================================================" -ForegroundColor Yellow
Write-Host ""

$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "[ERROR] Python was not found in PATH. Please install Python 3.10+." -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Python detected at $($pythonCmd.Source)" -ForegroundColor Green
Write-Host "[OK] Launching Kuber Intelligent Server on port 8002..." -ForegroundColor Green
Write-Host ""

python run_server.py
