@echo off
REM UltraSpeed Copy - Modern UI Quick Launch Script
REM Double-click this file to start the modern animated GUI

echo ================================================
echo UltraSpeed Copy - Modern Edition
echo ================================================
echo.
echo Starting modern animated GUI...
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

REM Check if ttkbootstrap is installed
python -c "import ttkbootstrap" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ================================================
    echo NOTICE: ttkbootstrap not installed
    echo ================================================
    echo.
    echo The modern UI requires ttkbootstrap for the best experience.
    echo Install it now for animated themes and modern styling.
    echo.
    echo Install command: pip install ttkbootstrap
    echo.
    set /p INSTALL="Install ttkbootstrap now? (y/n): "
    if /i "%INSTALL%"=="y" (
        echo.
        echo Installing ttkbootstrap...
        pip install ttkbootstrap
        echo.
        echo Installation complete!
        echo.
        pause
    ) else (
        echo.
        echo Running in standard mode (without animations)
        echo.
    )
)

REM Launch Modern GUI
python gui/app_modern.py

REM If GUI exits with error
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code: %ERRORLEVEL%
    echo Check logs/ directory for details
    pause
)
