"""
MTP Copy Handler - Handles copying from/to MTP devices (mobile phones, tablets)
Since ROBOCOPY cannot directly access MTP devices, this module provides
a two-stage copy process: MTP -> Temp -> Destination
"""

import os
import sys
import shutil
import tempfile
import subprocess
from pathlib import Path
from typing import Callable, Optional
from datetime import datetime


class MTPCopyHandler:
    """
    Handles file copying to/from MTP devices
    Uses PowerShell to interface with Windows Portable Device API
    """
    
    def __init__(self, log_callback: Optional[Callable] = None, 
                 progress_callback: Optional[Callable] = None):
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.temp_dir = None
        self.is_cancelled = False
    
    def copy_from_mtp(self, mtp_path: str, destination: str) -> tuple[bool, str]:
        """
        Copy files from MTP device to destination
        Uses two-stage process: MTP -> Temp -> Final Destination
        
        Args:
            mtp_path: MTP device path (e.g., wpd://... or ::...)
            destination: Final destination path
            
        Returns:
            Tuple of (success, temp_folder_path or error_message)
        """
        try:
            self._log("🔄 Starting MTP device copy...")
            self._log(f"Source: {mtp_path}")
            self._log(f"Destination: {destination}")
            
            # Create temp staging area
            self.temp_dir = tempfile.mkdtemp(prefix='ultraspeed_mtp_')
            self._log(f"📂 Created staging folder: {self.temp_dir}")
            
            # Stage 1: Copy from MTP to temp using PowerShell
            self._log("⏳ Stage 1: Copying from mobile device to staging folder...")
            success = self._copy_mtp_to_temp(mtp_path, self.temp_dir)
            
            if not success:
                self._log("❌ Failed to copy from MTP device")
                return False, "Failed to copy from mobile device"
            
            self._log("✅ Stage 1 complete: Files staged in temporary folder")
            
            # Stage 2: Use standard file copy or return temp path for ROBOCOPY
            # Return temp path so calling code can use ROBOCOPY for fast copy
            return True, self.temp_dir
            
        except Exception as e:
            self._log(f"❌ Error in MTP copy: {str(e)}")
            return False, str(e)
    
    def _copy_mtp_to_temp(self, mtp_path: str, temp_dir: str) -> bool:
        """
        Copy files from MTP device to temporary folder using PowerShell
        
        Args:
            mtp_path: MTP device path (e.g., Computer\DeviceName\Path)
            temp_dir: Temporary destination folder
            
        Returns:
            True if successful
        """
        try:
            # PowerShell script to copy from MTP device
            # This script properly navigates MTP device hierarchy
            ps_script = r"""
$ErrorActionPreference = 'Continue'

$SourcePath = "''' + mtp_path + r'''"
$DestPath = "''' + temp_dir + r'''"

Write-Host "=== Starting MTP Copy ==="
Write-Host "Source: $SourcePath"
Write-Host "Destination: $DestPath"
Write-Host ""

# Create COM object for Shell
$shell = New-Object -ComObject Shell.Application

# Parse the path to get device and folders
if ($SourcePath -match '^Computer\\([^\\]+)\\(.+)$') {
    $deviceName = $matches[1].Trim()
    $folderPath = $matches[2]
    
    Write-Host "Device: '$deviceName'"
    Write-Host "Folder path: '$folderPath'"
    Write-Host ""
} else {
    Write-Error "Invalid path format. Expected: Computer\DeviceName\Path"
    Write-Error "Got: $SourcePath"
    exit 1
}

# Get This PC (MyComputer)
$computer = $shell.Namespace(17)
if ($computer -eq $null) {
    Write-Error "Cannot access This PC"
    exit 1
}

# Find the device
Write-Host "Looking for device..."
$device = $null
foreach ($item in $computer.Items()) {
    $itemName = $item.Name.Trim()
    if ($itemName -eq $deviceName) {
        $device = $item
        Write-Host "Found device: $($device.Name)"
        break
    }
}

if ($device -eq $null) {
    Write-Error "Device '$deviceName' not found!"
    Write-Host "Available devices:"
    foreach ($item in $computer.Items()) {
        Write-Host "  - $($item.Name)"
    }
    exit 1
}

# Navigate to the folder within the device
$currentFolder = $shell.Namespace($device.Path)
if ($currentFolder -eq $null) {
    Write-Error "Cannot access device root"
    exit 1
}

# Split the folder path and navigate
$folders = $folderPath -split '\\'
Write-Host "Navigating to target folder..."

$currentItem = $null
foreach ($folderName in $folders) {
    if ([string]::IsNullOrWhiteSpace($folderName)) { continue }
    
    Write-Host "  Looking for: $folderName"
    $found = $false
    
    foreach ($item in $currentFolder.Items()) {
        if ($item.Name -eq $folderName) {
            Write-Host "    Found: $($item.Name)"
            $currentItem = $item
            
            # For MTP devices, navigate carefully
            if ($item.IsFolder) {
                # Try to get folder as namespace
                $tempNS = $shell.Namespace($item.Path)
                if ($tempNS -ne $null) {
                    $currentFolder = $tempNS
                    $found = $true
                    break
                } else {
                    Write-Host "    Using alternative navigation"
                    $currentItem = $item
                    $found = $true
                    break
                }
            }
        }
    }
    
    if (-not $found) {
        Write-Error "Folder not found: $folderName"
        Write-Host "Available items:"
        foreach ($item in $currentFolder.Items()) {
            Write-Host "  - $($item.Name)"
        }
        exit 1
    }
}

Write-Host ""
Write-Host "Successfully navigated to target folder"
Write-Host "Items to copy: $($currentFolder.Items().Count)"
Write-Host ""

# Ensure destination exists
if (-not (Test-Path $DestPath)) {
    New-Item -ItemType Directory -Path $DestPath -Force | Out-Null
}

$destFolder = $shell.Namespace($DestPath)
if ($destFolder -eq $null) {
    Write-Error "Cannot access destination: $DestPath"
    exit 1
}

# Copy all items from source to destination
$copiedCount = 0
$errorCount = 0
$totalItems = $currentFolder.Items().Count

Write-Host "=== Starting copy operation ==="
foreach ($item in $currentFolder.Items()) {
    try {
        $itemName = $item.Name
        $itemType = if ($item.IsFolder) { "Folder" } else { "File" }
        Write-Host "[$copiedCount/$totalItems] Copying $itemType`: $itemName"
        
        # Flags: 4 = No progress dialog, 16 = Yes to all, 1024 = No confirmation
        $copyFlags = 4 + 16 + 1024
        $destFolder.CopyHere($item, $copyFlags)
        
        # Wait for copy to complete
        Start-Sleep -Milliseconds 200
        
        $copiedCount++
    } catch {
        Write-Error "Error copying $($item.Name): $_"
        $errorCount++
    }
}

Write-Host ""
Write-Host "=== Copy Complete ==="
Write-Host "Copied: $copiedCount"
Write-Host "Errors: $errorCount"
Write-Host ""

if ($errorCount -gt 0) {
    exit 1
} else {
    exit 0
}
"""
            
            self._log("🚀 Executing PowerShell script to copy from MTP device...")
            
            # Execute PowerShell script
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            # Log output
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self._log(line.strip())
            
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip() and 'WARNING' not in line:
                        self._log(f"⚠️ {line.strip()}")
            
            if result.returncode == 0:
                self._log("✅ MTP copy successful")
                return True
            else:
                self._log(f"❌ MTP copy failed with code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self._log("⏰ MTP copy timeout - operation took too long")
            return False
        except Exception as e:
            self._log(f"❌ Error in PowerShell MTP copy: {str(e)}")
            return False
    
    def copy_to_mtp(self, source: str, mtp_path: str) -> bool:
        """
        Copy files to MTP device
        
        Args:
            source: Source folder path (C:\\Users\\Photos)
            mtp_path: MTP device destination path (Computer\\Device\\Internal storage\\Pictures)
            
        Returns:
            True if successful
        """
        try:
            self._log("🔄 Starting copy TO mobile device...")
            self._log(f"Source: {source}")
            self._log(f"Destination: {mtp_path}")
            
            # Escape paths for PowerShell
            source_escaped = source.replace("'", "''")
            dest_escaped = mtp_path.replace("'", "''")
            
            # PowerShell script to copy TO MTP device
            ps_script = f"""
$ErrorActionPreference = 'Continue'

$SourcePath = '{source_escaped}'
$DestPath = '{dest_escaped}'

Write-Host "=== Copying TO Mobile Device ==="
Write-Host "Source: $SourcePath"
Write-Host "Destination: $DestPath"
Write-Host ""

# Validate source exists
if (-not (Test-Path $SourcePath)) {{
    Write-Error "Source path does not exist: $SourcePath"
    exit 1
}}

# Create COM object
$shell = New-Object -ComObject Shell.Application

# Parse MTP destination path
if ($DestPath -match '^Computer\\\\([^\\\\]+)\\\\(.+)$') {{
    $deviceName = $matches[1].Trim()
    $folderPath = $matches[2]
    
    Write-Host "Device: '$deviceName'"
    Write-Host "Folder path: '$folderPath'"
    Write-Host ""
}} else {{
    Write-Error "Invalid MTP path format. Expected: Computer\\DeviceName\\Path"
    exit 1
}}

# Find device
$computer = $shell.Namespace(17)
$device = $null

foreach ($item in $computer.Items()) {{
    if ($item.Name.Trim() -eq $deviceName) {{
        $device = $item
        Write-Host "Found device: $($device.Name)"
        break
    }}
}}

if ($device -eq $null) {{
    Write-Error "Device '$deviceName' not found"
    exit 1
}}

# Navigate to destination folder
$currentFolder = $shell.Namespace($device.Path)
$folders = $folderPath -split '\\\\'

foreach ($folderName in $folders) {{
    if ([string]::IsNullOrWhiteSpace($folderName)) {{ continue }}
    
    Write-Host "Navigating to: $folderName"
    $found = $false
    
    foreach ($item in $currentFolder.Items()) {{
        if ($item.Name -eq $folderName) {{
            if ($item.IsFolder) {{
                $tempNS = $shell.Namespace($item.Path)
                if ($tempNS -ne $null) {{
                    $currentFolder = $tempNS
                    $found = $true
                    break
                }}
            }}
        }}
    }}
    
    if (-not $found) {{
        Write-Error "Folder not found: $folderName"
        exit 1
    }}
}}

Write-Host "Successfully navigated to destination"
Write-Host ""

# Get source items
$sourceFolder = $shell.Namespace($SourcePath)
if ($sourceFolder -eq $null) {{
    Write-Error "Cannot access source folder"
    exit 1
}}

# Copy items to MTP device
$itemCount = 0
$errorCount = 0

Write-Host "=== Starting copy operation ==="
foreach ($item in $sourceFolder.Items()) {{
    try {{
        $itemName = $item.Name
        $itemType = if ($item.IsFolder) {{ "Folder" }} else {{ "File" }}
        Write-Host "Copying $itemType`: $itemName"
        
        # Copy flags: 4 = No dialog, 16 = Yes to all, 1024 = No confirmation
        $copyFlags = 4 + 16 + 1024
        $currentFolder.CopyHere($item, $copyFlags)
        
        # Wait for copy
        Start-Sleep -Milliseconds 500
        
        $itemCount++
    }} catch {{
        Write-Error "Error copying $($item.Name): $_"
        $errorCount++
    }}
}}

Write-Host ""
Write-Host "=== Copy Complete ==="
Write-Host "Copied: $itemCount items"
Write-Host "Errors: $errorCount"

if ($errorCount -gt 0) {{
    exit 1
}} else {{
    exit 0
}}
"""
            
            self._log("🚀 Executing PowerShell script to copy TO MTP device...")
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            # Log output
            if result.stdout:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self._log(line.strip())
            
            if result.stderr:
                for line in result.stderr.split('\n'):
                    if line.strip() and 'WARNING' not in line:
                        self._log(f"⚠️ {line.strip()}")
            
            if result.returncode == 0:
                self._log("✅ Successfully copied TO mobile device!")
                return True
            else:
                self._log(f"❌ Copy to MTP failed with code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            self._log("⏰ Copy timeout - operation took too long")
            return False
        except Exception as e:
            self._log(f"❌ Error copying to MTP: {str(e)}")
            return False
    
    def cleanup_temp(self):
        """Clean up temporary staging folder"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                self._log(f"🗑️ Cleaning up staging folder: {self.temp_dir}")
                shutil.rmtree(self.temp_dir)
                self._log("✅ Staging folder cleaned up")
            except Exception as e:
                self._log(f"⚠️ Failed to cleanup staging folder: {str(e)}")
    
    def cancel(self):
        """Cancel the MTP copy operation"""
        self.is_cancelled = True
        self._log("🛑 MTP copy cancelled")
    
    def _log(self, message: str):
        """Internal logging function"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self.log_callback:
            self.log_callback(log_message)
        else:
            print(log_message)


def is_mtp_path(path: str) -> bool:
    """
    Check if a path represents an MTP device
    
    Args:
        path: Path to check
        
    Returns:
        True if it's an MTP path
    """
    if not path:
        return False
    
    # Check for MTP indicators
    mtp_indicators = [
        'wpd://',           # Windows Portable Device protocol
        '::',               # Shell namespace paths
        'USB\\VID_',        # USB device IDs
        '20D04FE0-3AEA',   # MyComputer GUID
        '6ac27878-a6fa',   # Portable device GUID
    ]
    
    return any(indicator in path for indicator in mtp_indicators)


def test_mtp_handler():
    """Test MTP copy handler"""
    def log_callback(msg):
        print(msg)
    
    handler = MTPCopyHandler(log_callback=log_callback)
    
    # Test MTP path detection
    test_paths = [
        "C:\\Users\\Test",
        "wpd://USB\\VID_04E8&PID_6860",
        "::{20D04FE0-3AEA-1069-A2D8-08002B30309D}\\test",
        "D:\\Backup"
    ]
    
    print("\n=== Testing MTP Path Detection ===")
    for path in test_paths:
        result = is_mtp_path(path)
        print(f"{path}: {'MTP' if result else 'Regular'}")


if __name__ == '__main__':
    test_mtp_handler()
