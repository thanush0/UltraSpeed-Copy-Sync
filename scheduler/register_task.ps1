# UltraSpeed Copy - Task Scheduler Registration Script
# This script creates scheduled tasks for automated backup and sync operations

param(
    [Parameter(Mandatory=$false)]
    [string]$TaskName = "UltraSpeed-DailyBackup",
    
    [Parameter(Mandatory=$false)]
    [string]$ScriptPath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$SourcePath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$DestPath = "",
    
    [Parameter(Mandatory=$false)]
    [string]$Schedule = "Daily",
    
    [Parameter(Mandatory=$false)]
    [string]$Time = "02:00",
    
    [Parameter(Mandatory=$false)]
    [string]$Mode = "incremental",
    
    [Parameter(Mandatory=$false)]
    [int]$Threads = 16,
    
    [Parameter(Mandatory=$false)]
    [switch]$NetworkOptimized,
    
    [Parameter(Mandatory=$false)]
    [switch]$Interactive
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "UltraSpeed Copy - Task Scheduler Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for admin privileges
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script requires Administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Interactive mode
if ($Interactive) {
    Write-Host "=== Interactive Configuration ===" -ForegroundColor Green
    Write-Host ""
    
    $TaskName = Read-Host "Task Name (default: UltraSpeed-DailyBackup)"
    if ([string]::IsNullOrWhiteSpace($TaskName)) {
        $TaskName = "UltraSpeed-DailyBackup"
    }
    
    $SourcePath = Read-Host "Source Path"
    while ([string]::IsNullOrWhiteSpace($SourcePath) -or -not (Test-Path $SourcePath)) {
        Write-Host "Invalid source path. Please try again." -ForegroundColor Red
        $SourcePath = Read-Host "Source Path"
    }
    
    $DestPath = Read-Host "Destination Path"
    while ([string]::IsNullOrWhiteSpace($DestPath)) {
        Write-Host "Destination path cannot be empty." -ForegroundColor Red
        $DestPath = Read-Host "Destination Path"
    }
    
    Write-Host ""
    Write-Host "Schedule options: Daily, Weekly, Monthly" -ForegroundColor Yellow
    $Schedule = Read-Host "Schedule (default: Daily)"
    if ([string]::IsNullOrWhiteSpace($Schedule)) {
        $Schedule = "Daily"
    }
    
    $Time = Read-Host "Time (HH:MM format, default: 02:00)"
    if ([string]::IsNullOrWhiteSpace($Time)) {
        $Time = "02:00"
    }
    
    Write-Host ""
    Write-Host "Copy modes: full, incremental, mirror" -ForegroundColor Yellow
    $Mode = Read-Host "Copy Mode (default: incremental)"
    if ([string]::IsNullOrWhiteSpace($Mode)) {
        $Mode = "incremental"
    }
    
    $ThreadsInput = Read-Host "Number of Threads (default: 16)"
    if (-not [string]::IsNullOrWhiteSpace($ThreadsInput)) {
        $Threads = [int]$ThreadsInput
    }
    
    $netOpt = Read-Host "Enable Network Optimization? (y/n, default: n)"
    $NetworkOptimized = $netOpt -eq "y" -or $netOpt -eq "Y"
}

# Validate inputs
if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    Write-Host "ERROR: Source path is required." -ForegroundColor Red
    Write-Host "Usage: .\register_task.ps1 -SourcePath 'C:\Source' -DestPath 'D:\Backup'" -ForegroundColor Yellow
    exit 1
}

if ([string]::IsNullOrWhiteSpace($DestPath)) {
    Write-Host "ERROR: Destination path is required." -ForegroundColor Red
    exit 1
}

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Create batch file for the task
$batchFile = Join-Path $scriptDir "scheduled_backup.bat"
$logDir = Join-Path $projectRoot "logs"

# Ensure log directory exists
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Build robocopy command
$robocopyCmd = "robocopy `"$SourcePath`" `"$DestPath`""

# Add mode-specific options
switch ($Mode.ToLower()) {
    "mirror" {
        $robocopyCmd += " /MIR"
    }
    "incremental" {
        $robocopyCmd += " /E /XO"
    }
    default {
        $robocopyCmd += " /E"
    }
}

# Add threading
$robocopyCmd += " /MT:$Threads"

# Add network optimization if enabled
if ($NetworkOptimized) {
    $robocopyCmd += " /Z /ZB /R:5 /W:10"
} else {
    $robocopyCmd += " /R:3 /W:5"
}

# Add common options
$robocopyCmd += " /COPYALL /DCOPY:DAT /V /NP /TEE /BYTES /TS /FP"

# Add logging
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = Join-Path $logDir "scheduled_backup_%date:~0,8%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
$robocopyCmd += " /LOG+:`"$logFile`""

# Create batch file content
$batchContent = @"
@echo off
REM UltraSpeed Copy - Scheduled Backup Task
REM Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
REM Task Name: $TaskName

echo ========================================
echo UltraSpeed Copy - Scheduled Backup
echo ========================================
echo Task: $TaskName
echo Started: %date% %time%
echo Source: $SourcePath
echo Destination: $DestPath
echo Mode: $Mode
echo ========================================
echo.

REM Execute robocopy
$robocopyCmd

REM Check exit code
if %ERRORLEVEL% LSS 8 (
    echo.
    echo Backup completed successfully (Code: %ERRORLEVEL%)
    echo Completed: %date% %time%
    exit /b 0
) else (
    echo.
    echo ERROR: Backup failed with code: %ERRORLEVEL%
    echo Failed: %date% %time%
    exit /b %ERRORLEVEL%
)
"@

# Write batch file
Set-Content -Path $batchFile -Value $batchContent -Encoding ASCII
Write-Host "Created batch file: $batchFile" -ForegroundColor Green

# Parse time
$timeParts = $Time -split ":"
$hour = [int]$timeParts[0]
$minute = [int]$timeParts[1]

# Create scheduled task
try {
    Write-Host ""
    Write-Host "Creating scheduled task: $TaskName" -ForegroundColor Yellow
    
    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existingTask) {
        Write-Host "Task '$TaskName' already exists. Removing..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    }
    
    # Create action
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$batchFile`""
    
    # Create trigger based on schedule
    switch ($Schedule.ToLower()) {
        "daily" {
            $trigger = New-ScheduledTaskTrigger -Daily -At $(Get-Date -Hour $hour -Minute $minute -Second 0)
        }
        "weekly" {
            $trigger = New-ScheduledTaskTrigger -Weekly -At $(Get-Date -Hour $hour -Minute $minute -Second 0) -DaysOfWeek Sunday
        }
        "monthly" {
            $trigger = New-ScheduledTaskTrigger -Weekly -At $(Get-Date -Hour $hour -Minute $minute -Second 0) -WeeksInterval 4
        }
        default {
            $trigger = New-ScheduledTaskTrigger -Daily -At $(Get-Date -Hour $hour -Minute $minute -Second 0)
        }
    }
    
    # Create settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -ExecutionTimeLimit (New-TimeSpan -Hours 8)
    
    # Create principal (run whether user is logged on or not)
    $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
    
    # Register task
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "UltraSpeed Copy automated backup task. Source: $SourcePath, Destination: $DestPath, Mode: $Mode" | Out-Null
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Task Details:" -ForegroundColor Cyan
    Write-Host "  Name: $TaskName"
    Write-Host "  Schedule: $Schedule at $Time"
    Write-Host "  Source: $SourcePath"
    Write-Host "  Destination: $DestPath"
    Write-Host "  Mode: $Mode"
    Write-Host "  Threads: $Threads"
    Write-Host "  Network Optimized: $NetworkOptimized"
    Write-Host ""
    Write-Host "To view the task in Task Scheduler, run: taskschd.msc" -ForegroundColor Yellow
    Write-Host "To test the task manually, run:" -ForegroundColor Yellow
    Write-Host "  Start-ScheduledTask -TaskName '$TaskName'" -ForegroundColor White
    Write-Host ""
    Write-Host "To remove the task, run:" -ForegroundColor Yellow
    Write-Host "  Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host ""
    Write-Host "ERROR: Failed to create scheduled task." -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# Create uninstall script
$uninstallScript = Join-Path $scriptDir "unregister_task.ps1"
$uninstallContent = @"
# Unregister scheduled task: $TaskName
`$taskName = "$TaskName"

Write-Host "Removing scheduled task: `$taskName" -ForegroundColor Yellow
try {
    Unregister-ScheduledTask -TaskName `$taskName -Confirm:`$false -ErrorAction Stop
    Write-Host "Task removed successfully." -ForegroundColor Green
} catch {
    Write-Host "Error: `$(`$_.Exception.Message)" -ForegroundColor Red
}
"@

Set-Content -Path $uninstallScript -Value $uninstallContent
Write-Host "Created uninstall script: $uninstallScript" -ForegroundColor Green

exit 0
