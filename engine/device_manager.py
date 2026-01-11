"""
Device Manager - Detects and manages all storage devices including MTP/PTP devices
Handles mobile phones, tablets, cameras, and other portable devices
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Optional


class DeviceType:
    """Device type constants"""
    LOCAL_DRIVE = "local"
    NETWORK_DRIVE = "network"
    USB_DRIVE = "usb"
    MTP_DEVICE = "mtp"
    PORTABLE_DEVICE = "portable"


class StorageDevice:
    """Represents a storage device"""
    
    def __init__(self, name: str, path: str, device_type: str, 
                 size: int = 0, free_space: int = 0, description: str = ""):
        self.name = name
        self.path = path
        self.device_type = device_type
        self.size = size
        self.free_space = free_space
        self.description = description
    
    def __repr__(self):
        return f"<StorageDevice: {self.name} ({self.device_type}) - {self.path}>"
    
    def is_accessible(self) -> bool:
        """Check if device is currently accessible"""
        if self.device_type in [DeviceType.LOCAL_DRIVE, DeviceType.USB_DRIVE]:
            return os.path.exists(self.path)
        elif self.device_type == DeviceType.NETWORK_DRIVE:
            try:
                return os.path.exists(self.path)
            except:
                return False
        elif self.device_type == DeviceType.MTP_DEVICE:
            # MTP devices require special handling
            return self._check_mtp_accessible()
        return False
    
    def _check_mtp_accessible(self) -> bool:
        """Check if MTP device is accessible"""
        # MTP devices in Windows are accessible via shell namespace
        # but not via standard file paths
        return True  # Assume accessible if detected


class DeviceManager:
    """
    Manages detection and enumeration of all storage devices
    including MTP/PTP portable devices
    """
    
    def __init__(self):
        self.devices = []
    
    def detect_all_devices(self) -> List[StorageDevice]:
        """
        Detect all available storage devices
        
        Returns:
            List of StorageDevice objects
        """
        devices = []
        
        # Detect local drives
        devices.extend(self._detect_local_drives())
        
        # Detect network drives
        devices.extend(self._detect_network_drives())
        
        # Detect MTP/Portable devices
        devices.extend(self._detect_portable_devices())
        
        self.devices = devices
        return devices
    
    def _detect_local_drives(self) -> List[StorageDevice]:
        """Detect local and USB drives"""
        devices = []
        
        try:
            import string
            import psutil
            
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        usage = psutil.disk_usage(drive_path)
                        partitions = psutil.disk_partitions()
                        
                        label = "Local Disk"
                        device_type = DeviceType.LOCAL_DRIVE
                        
                        # Determine drive type
                        for partition in partitions:
                            if partition.device.startswith(letter):
                                # Check if removable
                                if 'removable' in partition.opts.lower():
                                    device_type = DeviceType.USB_DRIVE
                                    label = "Removable Disk"
                                else:
                                    label = partition.opts if partition.opts else "Local Disk"
                                break
                        
                        # Try to get volume label
                        try:
                            result = subprocess.run(
                                ['cmd', '/c', 'vol', f'{letter}:'],
                                capture_output=True,
                                text=True,
                                timeout=2
                            )
                            if result.returncode == 0:
                                lines = result.stdout.strip().split('\n')
                                for line in lines:
                                    if 'Volume in drive' in line and 'is' in line:
                                        vol_label = line.split('is')[-1].strip()
                                        if vol_label and vol_label != "has no label":
                                            label = vol_label
                                        break
                        except:
                            pass
                        
                        device = StorageDevice(
                            name=f"{letter}: - {label}",
                            path=drive_path,
                            device_type=device_type,
                            size=usage.total,
                            free_space=usage.free,
                            description=f"{self._format_bytes(usage.total)} total, {self._format_bytes(usage.free)} free"
                        )
                        devices.append(device)
                        
                    except Exception as e:
                        # Drive might be inaccessible
                        pass
        except Exception as e:
            print(f"Error detecting local drives: {e}")
        
        return devices
    
    def _detect_network_drives(self) -> List[StorageDevice]:
        """Detect mapped network drives"""
        devices = []
        
        try:
            result = subprocess.run(
                ['net', 'use'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                for line in lines:
                    # Parse network drive mappings
                    if ':' in line and '\\\\' in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            drive_letter = parts[1] if ':' in parts[1] else parts[0]
                            network_path = [p for p in parts if '\\\\' in p]
                            
                            if network_path and ':' in drive_letter:
                                device = StorageDevice(
                                    name=f"{drive_letter} - Network Drive",
                                    path=drive_letter.replace(':', ':\\'),
                                    device_type=DeviceType.NETWORK_DRIVE,
                                    description=network_path[0]
                                )
                                devices.append(device)
        except Exception as e:
            print(f"Error detecting network drives: {e}")
        
        return devices
    
    def _detect_portable_devices(self) -> List[StorageDevice]:
        """
        Detect MTP/PTP portable devices (phones, tablets, cameras)
        Uses PowerShell to query Windows Shell namespace
        """
        devices = []
        seen_paths = set()
        
        try:
            # Use PowerShell to enumerate portable devices from This PC
            ps_script = r"""
$shell = New-Object -ComObject Shell.Application
$computer = $shell.Namespace(17)  # 17 = MyComputer

foreach ($item in $computer.Items()) {
    $path = $item.Path
    $name = $item.Name
    $type = $item.Type
    
    # Check if it's a portable device
    if ($type -match "Mobile|Phone|Tablet|Portable|Device|Camera" -or $path -match "::{" -or $path -match "usb#") {
        # Don't include regular drives
        if ($path -notmatch "^[A-Z]:\\$") {
            Write-Output "$name|$path|$type"
        }
    }
}
"""
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if '|' in line and line.strip():
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name = parts[0].strip()
                            path = parts[1].strip()
                            device_type_str = parts[2].strip()
                            
                            # Skip empty or duplicate paths
                            if not path or path in seen_paths:
                                continue
                            
                            seen_paths.add(path)
                            
                            # Create device with better name
                            display_name = name if name and name != "UNKNOWN" else "Mobile Device"
                            
                            device = StorageDevice(
                                name=f"📱 {display_name}",
                                path=path,
                                device_type=DeviceType.MTP_DEVICE,
                                description=f"{device_type_str}"
                            )
                            devices.append(device)
                            print(f"Found MTP device: {display_name} at {path}")
        
        except Exception as e:
            print(f"Error detecting portable devices: {e}")
        
        return devices
    
    def get_mtp_device_folders(self, device_path: str, folder_breadcrumb: List[str] = None) -> List[Dict[str, str]]:
        """
        Get accessible storage locations from MTP device
        (e.g., Internal Storage, SD Card, folders, files)
        
        FIXED: Uses GetFolder() method recursively for all MTP navigation
        
        Args:
            device_path: Root device GUID path
            folder_breadcrumb: List of folder names to navigate (e.g., ['DCIM', 'Camera'])
        """
        folders = []
        
        if folder_breadcrumb is None:
            folder_breadcrumb = []
        
        try:
            # Escape single quotes in path for PowerShell
            escaped_path = device_path.replace("'", "''")
            breadcrumb_str = "|".join(folder_breadcrumb)
            
            ps_script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$shell = New-Object -ComObject Shell.Application
$devicePath = '{escaped_path}'
$breadcrumb = '{breadcrumb_str}'

# Parse breadcrumb
$folderNames = if ($breadcrumb -ne '') {{ $breadcrumb -split '\\|' }} else {{ @() }}

# Start from device root
$device = $shell.Namespace($devicePath)

if ($device -eq $null) {{
    Write-Error "Cannot access device"
    exit 1
}}

# Find Internal storage
$currentFolder = $null
foreach ($item in $device.Items()) {{
    if ($item.IsFolder -and $item.Name -match "Internal|Storage|SD|Card") {{
        try {{
            $currentFolder = $item.GetFolder
            if ($currentFolder -ne $null) {{
                Write-Output "STORAGE_START|$($item.Name)"
                break
            }}
        }} catch {{
            continue
        }}
    }}
}}

if ($currentFolder -eq $null) {{
    Write-Error "No storage found"
    exit 1
}}

# Navigate through breadcrumb
foreach ($targetName in $folderNames) {{
    $found = $false
    foreach ($item in $currentFolder.Items()) {{
        if ($item.Name -eq $targetName -and $item.IsFolder) {{
            try {{
                $nextFolder = $item.GetFolder
                if ($nextFolder -ne $null) {{
                    $currentFolder = $nextFolder
                    $found = $true
                    break
                }}
            }} catch {{
                continue
            }}
        }}
    }}
    
    if (-not $found) {{
        Write-Error "Folder not found: $targetName"
        exit 1
    }}
}}

# List contents of current folder
foreach ($item in $currentFolder.Items()) {{
    try {{
        $name = $item.Name
        $isFolder = $item.IsFolder
        $size = 0
        
        if (-not $isFolder) {{
            try {{
                $size = $item.Size
            }} catch {{
                $size = 0
            }}
        }}
        
        Write-Output "$name|FOLDER|$isFolder|$size"
    }} catch {{
        continue
    }}
}}

Write-Output "STORAGE_END|Done"
"""
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                storage_active = False
                storage_name = ""
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    if line.startswith('STORAGE_START|'):
                        storage_active = True
                        storage_name = line.split('|')[1]
                        print(f"Found storage: {storage_name}")
                        continue
                    
                    if line.startswith('STORAGE_END|'):
                        storage_active = False
                        location = " > ".join(folder_breadcrumb) if folder_breadcrumb else "Internal storage"
                        print(f"✅ Successfully accessed! Found {len(folders)} items in {location}")
                        continue
                    
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 3:
                            name = parts[0].strip()
                            # parts[1] is marker "FOLDER"
                            is_folder = parts[2].strip().lower() == 'true'
                            size = int(parts[3].strip()) if len(parts) >= 4 and parts[3].strip().isdigit() else 0
                            
                            # Build breadcrumb for this item
                            if is_folder:
                                item_breadcrumb = folder_breadcrumb + [name]
                            else:
                                item_breadcrumb = folder_breadcrumb
                            
                            folders.append({
                                'name': name,
                                'is_folder': is_folder,
                                'size': size,
                                'breadcrumb': item_breadcrumb
                            })
                
                if not storage_active and len(folders) == 0:
                    location = " > ".join(folder_breadcrumb) if folder_breadcrumb else "device root"
                    print(f"No items found in {location}")
                elif not storage_active and len(folders) > 0:
                    location = " > ".join(folder_breadcrumb) if folder_breadcrumb else "device root"
                    print(f"Found {len(folders)} items in {location}")
                    
            else:
                print(f"No items found or error accessing MTP path")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                    
        except Exception as e:
            print(f"Error getting MTP folders: {e}")
        
        return folders
    
    def get_device_folders(self, device: StorageDevice) -> List[Dict[str, str]]:
        """
        Get accessible folders from a device
        
        Args:
            device: StorageDevice object
            
        Returns:
            List of folder dictionaries with 'name' and 'path'
        """
        folders = []
        
        if device.device_type in [DeviceType.LOCAL_DRIVE, DeviceType.USB_DRIVE, DeviceType.NETWORK_DRIVE]:
            # Standard file system - can enumerate directly
            try:
                if os.path.exists(device.path):
                    for item in os.listdir(device.path):
                        item_path = os.path.join(device.path, item)
                        if os.path.isdir(item_path):
                            folders.append({
                                'name': item,
                                'path': item_path
                            })
            except Exception as e:
                print(f"Error listing folders: {e}")
        
        elif device.device_type == DeviceType.MTP_DEVICE:
            # MTP device - use PowerShell to enumerate
            folders = self._get_mtp_folders(device)
        
        return folders
    
    def _get_mtp_folders(self, device: StorageDevice) -> List[Dict[str, str]]:
        """
        Get folders from MTP device using PowerShell
        UPDATED: Now uses the same GetFolder() method as get_mtp_device_folders()
        """
        # Simply call the main method with the device path
        return self.get_mtp_device_folders(device.path)
    
    def is_mtp_device(self, path: str) -> bool:
        """Check if a path represents an MTP device"""
        # Check for various MTP device path patterns
        if path.startswith('wpd://') or path.startswith('::'):
            return True
        
        # Check if path starts with Computer\ (Windows shell namespace for devices)
        if path.startswith('Computer\\') or path.startswith('Computer/'):
            return True
        
        # Check for device keywords
        if any(keyword in path.lower() for keyword in ['phone', 'tablet', 'android', 'iphone', 'ipad']):
            return True
        
        return False
    
    def prepare_mtp_copy(self, source_path: str, temp_dir: str = None) -> str:
        """
        Prepare MTP device for copying by creating a temporary staging area
        
        Args:
            source_path: MTP device path
            temp_dir: Temporary directory (defaults to system temp)
            
        Returns:
            Path to temporary staging directory
        """
        if temp_dir is None:
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix='ultraspeed_mtp_')
        
        # Copy from MTP to temp using PowerShell
        # This is a placeholder - actual implementation would copy files
        print(f"Staging MTP files from {source_path} to {temp_dir}")
        
        return temp_dir
    
    @staticmethod
    def _format_bytes(bytes_val: int) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


def test_device_detection():
    """Test device detection"""
    print("=== Testing Device Detection ===\n")
    
    manager = DeviceManager()
    devices = manager.detect_all_devices()
    
    print(f"Found {len(devices)} devices:\n")
    
    for device in devices:
        print(f"Device: {device.name}")
        print(f"  Type: {device.device_type}")
        print(f"  Path: {device.path}")
        print(f"  Description: {device.description}")
        print(f"  Accessible: {device.is_accessible()}")
        print()


if __name__ == '__main__':
    test_device_detection()
