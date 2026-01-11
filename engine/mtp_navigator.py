"""
MTP Navigator - Navigate MTP devices using folder names instead of paths
Since MTP GUID paths cannot be reopened with Namespace(), we use a name-based
navigation system that rebuilds the hierarchy on each request.
"""

import subprocess
from typing import List, Dict, Optional


class MTPNavigator:
    """
    Navigate MTP devices using folder name breadcrumbs
    Instead of using paths, we track the folder hierarchy and navigate
    by folder names from the root each time.
    """
    
    def __init__(self, device_path: str):
        """
        Initialize navigator with device root path
        
        Args:
            device_path: The root GUID path of the MTP device
        """
        self.device_path = device_path
        self.current_breadcrumb = []  # List of folder names from root
    
    def navigate_to_root(self) -> List[Dict[str, str]]:
        """Navigate to device root (Internal storage level)"""
        self.current_breadcrumb = []
        return self.list_current_folder()
    
    def navigate_into(self, folder_name: str) -> List[Dict[str, str]]:
        """
        Navigate into a folder by name
        
        Args:
            folder_name: Name of the folder to enter
            
        Returns:
            List of items in that folder
        """
        self.current_breadcrumb.append(folder_name)
        return self.list_current_folder()
    
    def navigate_up(self) -> List[Dict[str, str]]:
        """Navigate up one level"""
        if len(self.current_breadcrumb) > 0:
            self.current_breadcrumb.pop()
        return self.list_current_folder()
    
    def navigate_to_path(self, folder_names: List[str]) -> List[Dict[str, str]]:
        """
        Navigate to a specific path using folder names
        
        Args:
            folder_names: List of folder names from root (e.g., ['DCIM', 'Camera'])
            
        Returns:
            List of items in that folder
        """
        self.current_breadcrumb = folder_names.copy()
        return self.list_current_folder()
    
    def get_current_path(self) -> str:
        """Get current path as string (for display)"""
        if not self.current_breadcrumb:
            return "Internal storage"
        return "Internal storage\\" + "\\".join(self.current_breadcrumb)
    
    def list_current_folder(self) -> List[Dict[str, str]]:
        """
        List contents of current folder by navigating from root
        
        Returns:
            List of items with name, is_folder, size, and breadcrumb
        """
        folders = []
        
        try:
            # Escape single quotes in path for PowerShell
            escaped_path = self.device_path.replace("'", "''")
            
            # Build breadcrumb string for PowerShell
            breadcrumb_str = "|".join(self.current_breadcrumb)
            
            ps_script = f"""
$ErrorActionPreference = 'SilentlyContinue'
$shell = New-Object -ComObject Shell.Application
$devicePath = '{escaped_path}'
$breadcrumb = '{breadcrumb_str}'

# Split breadcrumb into folder names
$folderNames = if ($breadcrumb -ne '') {{ $breadcrumb -split '\\|' }} else {{ @() }}

# Start from device root
$namespace = $shell.Namespace($devicePath)

if ($namespace -eq $null) {{
    Write-Error "Cannot access device"
    exit 1
}}

$items = $namespace.Items()
if ($items -eq $null) {{
    Write-Error "Cannot get items"
    exit 1
}}

# Navigate through the hierarchy
$currentFolder = $null
$currentLevel = 0

foreach ($item in $items) {{
    # Check if this is Internal storage or similar
    if ($item.IsFolder -and $item.Name -match "Internal|Storage|SD|Card") {{
        try {{
            $currentFolder = $item.GetFolder
            if ($currentFolder -ne $null) {{
                Write-Host "Found storage: $($item.Name)" -ForegroundColor Green
                break
            }}
        }} catch {{
            continue
        }}
    }}
}}

if ($currentFolder -eq $null) {{
    Write-Error "Cannot find storage"
    exit 1
}}

# Now navigate through breadcrumb
foreach ($targetName in $folderNames) {{
    Write-Host "Navigating to: $targetName" -ForegroundColor Cyan
    
    $found = $false
    $nextFolder = $null
    
    foreach ($item in $currentFolder.Items()) {{
        if ($item.Name -eq $targetName -and $item.IsFolder) {{
            try {{
                $nextFolder = $item.GetFolder
                if ($nextFolder -ne $null) {{
                    $currentFolder = $nextFolder
                    $found = $true
                    Write-Host "  Found!" -ForegroundColor Green
                    break
                }}
            }} catch {{
                Write-Host "  Error accessing folder" -ForegroundColor Red
                continue
            }}
        }}
    }}
    
    if (-not $found) {{
        Write-Error "Folder not found: $targetName"
        exit 1
    }}
}}

# Now list contents of current folder
Write-Host "Listing current folder contents..." -ForegroundColor Yellow

$itemCount = 0
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
        }} else {{
            # For folders, try to count items
            try {{
                $testFolder = $item.GetFolder
                if ($testFolder -ne $null) {{
                    $size = $testFolder.Items().Count
                }}
            }} catch {{
                $size = 0
            }}
        }}
        
        Write-Output "$name|$isFolder|$size"
        $itemCount++
    }} catch {{
        continue
    }}
}}

Write-Host "Found $itemCount items" -ForegroundColor Green
"""
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_script],
                capture_output=True,
                text=True,
                timeout=30  # Reduced timeout
            )
            
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Parse output lines (ignore debug messages)
                    if '|' in line and not line.startswith('Found') and not line.startswith('Navigating'):
                        parts = line.split('|')
                        if len(parts) >= 2:
                            name = parts[0].strip()
                            is_folder = parts[1].strip().lower() == 'true'
                            size = int(parts[2].strip()) if len(parts) >= 3 and parts[2].strip().isdigit() else 0
                            
                            # Build full breadcrumb for this item
                            item_breadcrumb = self.current_breadcrumb.copy()
                            if is_folder:
                                item_breadcrumb.append(name)
                            
                            folders.append({
                                'name': name,
                                'is_folder': is_folder,
                                'size': size,
                                'breadcrumb': item_breadcrumb,
                                'display_path': self.get_current_path() + "\\" + name if self.current_breadcrumb else "Internal storage\\" + name
                            })
                
                if len(folders) > 0:
                    print(f"✅ Successfully listed {len(folders)} items in {self.get_current_path()}")
                else:
                    print(f"⚠️ No items found in {self.get_current_path()}")
            else:
                print(f"❌ Failed to list folder: {self.get_current_path()}")
                if result.stderr:
                    print(f"Error: {result.stderr}")
                    
        except Exception as e:
            print(f"❌ Error in MTP navigation: {e}")
        
        return folders
    
    def get_full_path_for_copy(self) -> str:
        """
        Get a path that can be used for copying
        Returns a Computer\\Device\\Storage\\Path format
        """
        # This is for display/copy operations
        # The actual copy will use the breadcrumb navigation
        return "Computer\\MobileDevice\\Internal storage\\" + "\\".join(self.current_breadcrumb)


def test_navigator():
    """Test the MTP navigator"""
    import sys
    sys.path.insert(0, '.')
    
    from engine.device_manager import DeviceManager
    
    print("=" * 70)
    print("TESTING MTP NAVIGATOR")
    print("=" * 70)
    print()
    
    # Get device
    dm = DeviceManager()
    devices = dm.detect_all_devices()
    mtp_devices = [d for d in devices if d.device_type == 'mtp']
    
    if not mtp_devices:
        print("No MTP devices found")
        return
    
    device = mtp_devices[0]
    print(f"Device: {device.name}")
    print(f"Path: {device.path}")
    print()
    
    # Create navigator
    nav = MTPNavigator(device.path)
    
    # Test 1: List root
    print("TEST 1: List root (Internal storage)")
    print("-" * 70)
    items = nav.navigate_to_root()
    print(f"Current path: {nav.get_current_path()}")
    print(f"Items found: {len(items)}")
    print()
    
    # Show first 10 items
    for i, item in enumerate(items[:10]):
        icon = "📁" if item['is_folder'] else "📄"
        size_str = f" ({item['size']} items)" if item['is_folder'] else f" ({item['size']} bytes)"
        print(f"  {icon} {item['name']}{size_str}")
    
    if len(items) > 10:
        print(f"  ... and {len(items) - 10} more")
    
    print()
    
    # Test 2: Navigate into a folder
    dcim_folder = None
    pictures_folder = None
    for item in items:
        if item['name'] == 'DCIM':
            dcim_folder = item
        elif item['name'] == 'Pictures':
            pictures_folder = item
    
    test_folder = dcim_folder if dcim_folder else pictures_folder
    
    if test_folder:
        print(f"TEST 2: Navigate into '{test_folder['name']}'")
        print("-" * 70)
        
        sub_items = nav.navigate_into(test_folder['name'])
        print(f"Current path: {nav.get_current_path()}")
        print(f"Items found: {len(sub_items)}")
        print()
        
        if len(sub_items) > 0:
            print("✅ SUCCESS! Can navigate into folders!")
            print()
            print("Contents:")
            for item in sub_items[:10]:
                icon = "📁" if item['is_folder'] else "📄"
                print(f"  {icon} {item['name']}")
            
            if len(sub_items) > 10:
                print(f"  ... and {len(sub_items) - 10} more")
            
            # Test 3: Navigate deeper if possible
            if any(item['is_folder'] for item in sub_items):
                subfolder = next(item for item in sub_items if item['is_folder'])
                print()
                print(f"TEST 3: Navigate into '{subfolder['name']}'")
                print("-" * 70)
                
                deeper_items = nav.navigate_into(subfolder['name'])
                print(f"Current path: {nav.get_current_path()}")
                print(f"Items found: {len(deeper_items)}")
                
                if len(deeper_items) > 0:
                    print("✅ SUCCESS! Can navigate 2 levels deep!")
                    for item in deeper_items[:5]:
                        icon = "📁" if item['is_folder'] else "📄"
                        print(f"  {icon} {item['name']}")
        else:
            print("❌ No items found in subfolder")
    
    print()
    print("=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    test_navigator()
