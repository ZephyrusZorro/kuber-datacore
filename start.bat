@echo off
setlocal
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
cd /d "%~dp0"
title Kuber Data Core - Financial Knowledge Graph & Market Cortex

echo ========================================================================
echo   KUBER DATA CORE -- AUTONOMOUS FINANCIAL INTELLIGENCE WORKSTATION
echo ========================================================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python was not found in PATH. Please install Python 3.10+.
    pause
    exit /b 1
)

python run_server.py
pause
