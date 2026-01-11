@echo off
REM UltraSpeed Copy - Quick Launch Script
REM Double-click this file to start the GUI application

echo ========================================
echo UltraSpeed Smart Copy ^& Sync System
echo ========================================
echo.
echo Starting GUI application...
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8 or higher from python.org
    echo.
    pause
    exit /b 1
)

REM Launch GUI
python gui/app.py

REM If GUI exits with error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code: %ERRORLEVEL%
    echo Check logs/ directory for details
    pause
)
