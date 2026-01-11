@echo off
REM UltraSpeed Copy - Quick Setup for Task Scheduler
REM This script provides an easy way to register scheduled tasks

echo ========================================
echo UltraSpeed Copy - Quick Setup
echo ========================================
echo.
echo This script will help you create a scheduled backup task.
echo.
echo Requirements:
echo   - Administrator privileges
echo   - PowerShell 5.0 or higher
echo.

REM Check for admin privileges
net session >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: This script requires Administrator privileges.
    echo Please right-click and select "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo Admin privileges: OK
echo.

REM Check PowerShell version
powershell -Command "$PSVersionTable.PSVersion.Major" > temp_ps_version.txt
set /p PS_VERSION=<temp_ps_version.txt
del temp_ps_version.txt

if %PS_VERSION% LSS 5 (
    echo ERROR: PowerShell 5.0 or higher is required.
    echo Current version: %PS_VERSION%
    echo Please update PowerShell and try again.
    echo.
    pause
    exit /b 1
)

echo PowerShell version: %PS_VERSION% - OK
echo.

REM Run interactive setup
echo Starting interactive setup...
echo.
powershell -ExecutionPolicy Bypass -File "%~dp0register_task.ps1" -Interactive

echo.
echo Setup complete!
pause
