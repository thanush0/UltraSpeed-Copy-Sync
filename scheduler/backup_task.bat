@echo off
REM UltraSpeed Copy - Manual Backup Script Template
REM This is a template for creating custom backup scripts

echo ========================================
echo UltraSpeed Copy - Manual Backup
echo ========================================
echo.

REM ====================================
REM CONFIGURATION - EDIT THESE VALUES
REM ====================================

REM Source and destination paths
SET SOURCE=C:\Users\YourUsername\Documents
SET DEST=D:\Backup\Documents

REM Copy mode: FULL, INCREMENTAL, or MIRROR
SET MODE=INCREMENTAL

REM Number of threads (1-128, recommended: 8-16 for local, 16-32 for network)
SET THREADS=16

REM Network optimization (YES or NO)
SET NETWORK_OPT=NO

REM ====================================
REM DO NOT EDIT BELOW THIS LINE
REM ====================================

echo Source: %SOURCE%
echo Destination: %DEST%
echo Mode: %MODE%
echo Threads: %THREADS%
echo Network Optimized: %NETWORK_OPT%
echo.
echo Started: %date% %time%
echo ========================================
echo.

REM Validate paths
if not exist "%SOURCE%" (
    echo ERROR: Source path does not exist: %SOURCE%
    pause
    exit /b 1
)

REM Create destination if it doesn't exist
if not exist "%DEST%" (
    echo Creating destination directory: %DEST%
    mkdir "%DEST%"
)

REM Build robocopy command
SET ROBOCOPY_CMD=robocopy "%SOURCE%" "%DEST%"

REM Add mode-specific options
if /I "%MODE%"=="MIRROR" (
    SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /MIR
    echo WARNING: Mirror mode will DELETE files in destination that don't exist in source!
    echo Press Ctrl+C to cancel, or
    pause
) else if /I "%MODE%"=="INCREMENTAL" (
    SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /E /XO
) else (
    SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /E
)

REM Add threading
SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /MT:%THREADS%

REM Add network optimization
if /I "%NETWORK_OPT%"=="YES" (
    SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /Z /ZB /R:5 /W:10
) else (
    SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /R:3 /W:5
)

REM Add common options
SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /COPYALL /DCOPY:DAT /V /NP /TEE /BYTES /TS /FP

REM Add logging
SET LOG_DIR=%~dp0..\logs
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
SET LOG_FILE=%LOG_DIR%\manual_backup_%date:~0,4%%date:~5,2%%date:~8,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log
SET LOG_FILE=%LOG_FILE: =0%
SET ROBOCOPY_CMD=%ROBOCOPY_CMD% /LOG+:"%LOG_FILE%"

echo Command: %ROBOCOPY_CMD%
echo.
echo Executing...
echo.

REM Execute robocopy
%ROBOCOPY_CMD%

REM Check exit code
REM Robocopy exit codes: 0-7 = success, 8+ = failure
if %ERRORLEVEL% LSS 8 (
    echo.
    echo ========================================
    echo Backup completed successfully!
    echo Exit Code: %ERRORLEVEL%
    echo Completed: %date% %time%
    echo Log file: %LOG_FILE%
    echo ========================================
    echo.
) else (
    echo.
    echo ========================================
    echo ERROR: Backup failed!
    echo Exit Code: %ERRORLEVEL%
    echo Failed: %date% %time%
    echo Log file: %LOG_FILE%
    echo ========================================
    echo.
)

pause
exit /b %ERRORLEVEL%
