"""
Enhanced Device Picker Dialog
Shows all available storage devices including MTP/portable devices
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.device_manager import DeviceManager, DeviceType

# Try to import ttkbootstrap for modern themes
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    MODERN_THEME = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_THEME = False


class DevicePickerDialog:
    """
    Custom dialog for selecting storage devices
    Shows local drives, network paths, USB drives, and MTP devices
    """
    
    def __init__(self, parent, title="Select Device", path_type="source", allow_files=False):
        self.parent = parent
        self.title = title
        self.path_type = path_type
        self.allow_files = allow_files  # Allow selecting files, not just folders
        self.selected_path = None
        self.device_manager = DeviceManager()
        self.devices = []
        self.current_path = None  # Track current browsing path
        self.path_history = []  # For navigation history
        self.current_device_path = None  # Track MTP device root path
        self.current_breadcrumb = []  # Track current MTP breadcrumb
        
        # Create dialog
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("900x650")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (650 // 2)
        self.dialog.geometry(f"900x650+{x}+{y}")
        
        self.create_ui()
        self.load_devices()
    
    def create_ui(self):
        """Create the dialog UI"""
        # Main container
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header with navigation
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(
            header_frame,
            text=f"📂 {self.title}",
            font=("Segoe UI", 14, "bold")
        )
        title_label.pack(side=tk.LEFT)
        
        # Navigation buttons
        nav_frame = ttk.Frame(header_frame)
        nav_frame.pack(side=tk.RIGHT)
        
        if MODERN_THEME:
            self.back_btn = ttk.Button(
                nav_frame,
                text="⬅ Back",
                command=self.go_back,
                bootstyle="secondary-outline",
                state='disabled'
            )
            refresh_btn = ttk.Button(
                nav_frame,
                text="🔄 Refresh",
                command=self.refresh_current,
                bootstyle="info-outline"
            )
            self.up_btn = ttk.Button(
                nav_frame,
                text="⬆ Up",
                command=self.go_up,
                bootstyle="secondary-outline",
                state='disabled'
            )
        else:
            self.back_btn = ttk.Button(
                nav_frame,
                text="⬅ Back",
                command=self.go_back,
                state='disabled'
            )
            refresh_btn = ttk.Button(
                nav_frame,
                text="🔄 Refresh",
                command=self.refresh_current
            )
            self.up_btn = ttk.Button(
                nav_frame,
                text="⬆ Up",
                command=self.go_up,
                state='disabled'
            )
        
        self.back_btn.pack(side=tk.LEFT, padx=2)
        self.up_btn.pack(side=tk.LEFT, padx=2)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        
        # Current path display
        path_display_frame = ttk.Frame(main_frame)
        path_display_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(path_display_frame, text="Location:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        self.current_path_label = ttk.Label(
            path_display_frame,
            text="Devices",
            font=("Consolas", 9),
            foreground="blue"
        )
        self.current_path_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Loading indicator
        self.loading_label = ttk.Label(
            path_display_frame,
            text="Scanning...",
            font=("Segoe UI", 9)
        )
        
        # Device list frame
        list_frame = ttk.LabelFrame(main_frame, text="Available Devices")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=10, ipady=10, ipadx=10)
        
        # Create container frame for treeview
        tree_container = ttk.Frame(list_frame)
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create Treeview for device list
        columns = ('Name', 'Type', 'Size', 'Path')
        self.device_tree = ttk.Treeview(
            tree_container,
            columns=columns,
            show='tree headings',
            selectmode='browse',
            height=15
        )
        
        # Configure columns
        self.device_tree.heading('#0', text='Icon')
        self.device_tree.heading('Name', text='Device Name')
        self.device_tree.heading('Type', text='Type')
        self.device_tree.heading('Size', text='Size / Status')
        self.device_tree.heading('Path', text='Path')
        
        self.device_tree.column('#0', width=50, stretch=False)
        self.device_tree.column('Name', width=250)
        self.device_tree.column('Type', width=120)
        self.device_tree.column('Size', width=150)
        self.device_tree.column('Path', width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=self.device_tree.yview)
        self.device_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack tree and scrollbar
        self.device_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click
        self.device_tree.bind('<Double-Button-1>', self.on_device_double_click)
        
        # Path preview frame with manual entry
        preview_frame = ttk.LabelFrame(main_frame, text="Selected Path")
        preview_frame.pack(fill=tk.X, pady=(0, 15), padx=10, ipady=10, ipadx=10)
        
        # Path display/entry
        path_entry_frame = ttk.Frame(preview_frame)
        path_entry_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.path_var = tk.StringVar(value="")
        self.path_entry = ttk.Entry(
            path_entry_frame,
            textvariable=self.path_var,
            font=("Consolas", 9)
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        # Use entered path button
        if MODERN_THEME:
            use_path_btn = ttk.Button(
                path_entry_frame,
                text="Use This Path",
                command=self.use_entered_path,
                bootstyle="success-outline",
                width=15
            )
        else:
            use_path_btn = ttk.Button(
                path_entry_frame,
                text="Use This Path",
                command=self.use_entered_path,
                width=15
            )
        use_path_btn.pack(side=tk.RIGHT)
        
        # Hint label
        hint_label = ttk.Label(
            preview_frame,
            text="💡 Tip: You can paste a path here from Windows Explorer and click 'Use This Path'",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        hint_label.pack(pady=(0, 5))
        
        # Buttons frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        if MODERN_THEME:
            select_btn = ttk.Button(
                button_frame,
                text="✓ Select",
                command=self.on_select,
                bootstyle="success",
                width=15
            )
            browse_btn = ttk.Button(
                button_frame,
                text="📁 Browse Folder...",
                command=self.browse_folder,
                bootstyle="primary-outline",
                width=20
            )
            cancel_btn = ttk.Button(
                button_frame,
                text="✗ Cancel",
                command=self.on_cancel,
                bootstyle="secondary",
                width=15
            )
        else:
            select_btn = ttk.Button(
                button_frame,
                text="✓ Select",
                command=self.on_select,
                width=15
            )
            browse_btn = ttk.Button(
                button_frame,
                text="📁 Browse Folder...",
                command=self.browse_folder,
                width=20
            )
            cancel_btn = ttk.Button(
                button_frame,
                text="✗ Cancel",
                command=self.on_cancel,
                width=15
            )
        
        select_btn.pack(side=tk.LEFT, padx=(0, 10))
        browse_btn.pack(side=tk.LEFT, padx=(0, 10))
        cancel_btn.pack(side=tk.RIGHT)
        
        # Info label
        info_label = ttk.Label(
            main_frame,
            text="💡 Tip: Double-click a device to select it, or select and click Browse Folder to navigate inside",
            font=("Segoe UI", 8),
            foreground="gray"
        )
        info_label.pack(pady=(10, 0))
    
    def load_devices(self):
        """Load all available devices"""
        # Show loading
        self.loading_label.pack(side=tk.RIGHT, padx=10)
        self.dialog.update()
        
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Load devices in background
        threading.Thread(target=self._load_devices_thread, daemon=True).start()
    
    def _load_devices_thread(self):
        """Load devices in background thread"""
        try:
            self.devices = self.device_manager.detect_all_devices()
            
            # Update UI in main thread
            self.dialog.after(0, self._populate_device_list)
        except Exception as e:
            self.dialog.after(0, lambda: messagebox.showerror(
                "Error",
                f"Failed to detect devices: {str(e)}"
            ))
        finally:
            self.dialog.after(0, lambda: self.loading_label.pack_forget())
    
    def _populate_device_list(self):
        """Populate device list (called in main thread)"""
        # Group devices by type
        local_devices = []
        usb_devices = []
        network_devices = []
        portable_devices = []
        
        for device in self.devices:
            if device.device_type == DeviceType.LOCAL_DRIVE:
                local_devices.append(device)
            elif device.device_type == DeviceType.USB_DRIVE:
                usb_devices.append(device)
            elif device.device_type == DeviceType.NETWORK_DRIVE:
                network_devices.append(device)
            elif device.device_type in [DeviceType.MTP_DEVICE, DeviceType.PORTABLE_DEVICE]:
                portable_devices.append(device)
        
        # Add grouped devices to tree
        if local_devices:
            local_parent = self.device_tree.insert(
                '', 'end', text='💻', 
                values=('Local Drives', '', '', ''),
                open=True
            )
            for device in local_devices:
                self.add_device_to_tree(device, local_parent)
        
        if usb_devices:
            usb_parent = self.device_tree.insert(
                '', 'end', text='💾',
                values=('USB / External Drives', '', '', ''),
                open=True
            )
            for device in usb_devices:
                self.add_device_to_tree(device, usb_parent)
        
        if portable_devices:
            portable_parent = self.device_tree.insert(
                '', 'end', text='📱',
                values=('Mobile Devices & Portable', '', '', ''),
                open=True
            )
            for device in portable_devices:
                self.add_device_to_tree(device, portable_parent)
        
        if network_devices:
            network_parent = self.device_tree.insert(
                '', 'end', text='🌐',
                values=('Network Drives', '', '', ''),
                open=True
            )
            for device in network_devices:
                self.add_device_to_tree(device, network_parent)
    
    def add_device_to_tree(self, device, parent=''):
        """Add a device to the tree"""
        # Determine icon based on type
        if device.device_type == DeviceType.LOCAL_DRIVE:
            icon = '🖥️'
        elif device.device_type == DeviceType.USB_DRIVE:
            icon = '💾'
        elif device.device_type == DeviceType.NETWORK_DRIVE:
            icon = '🌐'
        elif device.device_type in [DeviceType.MTP_DEVICE, DeviceType.PORTABLE_DEVICE]:
            icon = '📱'
        else:
            icon = '📂'
        
        # Format type
        type_str = device.device_type.upper()
        
        # Insert device - mark as browsable
        item_id = self.device_tree.insert(
            parent, 'end',
            text=icon,
            values=(
                device.name,
                type_str,
                device.description,
                device.path
            ),
            tags=('device', 'browsable')
        )
        
        # Note: text= already sets the icon, no need to set '#0' column
    
    def on_device_double_click(self, event):
        """Handle double-click on device/folder"""
        selection = self.device_tree.selection()
        if selection:
            item = selection[0]
            values = self.device_tree.item(item, 'values')
            tags = self.device_tree.item(item, 'tags')
            
            # Check if it's an MTP folder/content (uses breadcrumb navigation)
            if 'mtp_folder' in tags or 'mtp_content' in tags:
                # MTP item - use breadcrumb navigation
                breadcrumb_str = values[3] if len(values) > 3 else ""  # Path column contains breadcrumb
                
                # Debug logging
                print(f"DEBUG: MTP item double-clicked")
                print(f"DEBUG: Name: {values[0] if len(values) > 0 else 'N/A'}")
                print(f"DEBUG: Breadcrumb string: '{breadcrumb_str}'")
                print(f"DEBUG: Current device path: '{self.current_device_path}'")
                print(f"DEBUG: Tags: {tags}")
                
                if breadcrumb_str and self.current_device_path:
                    # Parse breadcrumb and navigate
                    breadcrumb = breadcrumb_str.split('|') if breadcrumb_str else []
                    
                    # Save to history
                    self.path_history.append(self.current_breadcrumb.copy())
                    self.current_breadcrumb = breadcrumb
                    
                    # Navigate into folder
                    self._browse_mtp_path(self.current_device_path, breadcrumb)
                    
                    # Update path display
                    path_display = "Internal storage"
                    if breadcrumb:
                        path_display += " > " + " > ".join(breadcrumb)
                    self.current_path_label.config(text=path_display)
                    self.back_btn.config(state='normal')
                    self.up_btn.config(state='normal')
                return
            
            # Check if it's a device or folder
            if len(values) >= 4 and values[3]:  # Has path
                path = values[3]
                
                # If it's marked as browsable (has 'browsable' tag), browse into it
                if 'browsable' in tags or 'folder' in tags:
                    self.browse_into_path(path, values[0])
                else:
                    # Select this item
                    self.selected_path = path
                    self.path_var.set(path)
                    
                    # Check if it's an MTP device
                    if self.device_manager.is_mtp_device(path):
                        # For MTP devices, try to browse or select
                        response = messagebox.askyesnocancel(
                            "Mobile Device Detected",
                            f"Selected: {values[0]}\n\n"
                            "MTP devices have browsing limitations in Windows.\n\n"
                            "Would you like to:\n"
                            "• YES - Open Windows Explorer (browse and copy path)\n"
                            "• NO - Copy entire device contents\n"
                            "• CANCEL - Go back\n",
                            icon='question'
                        )
                        if response is True:  # Yes - open Explorer
                            import subprocess
                            try:
                                subprocess.run(['explorer', path], check=False)
                                messagebox.showinfo(
                                    "Windows Explorer Opened",
                                    "Windows Explorer has been opened to your device.\n\n"
                                    "To copy a specific folder:\n"
                                    "1. Browse to the folder you want\n"
                                    "2. Click the address bar (or press Alt+D)\n"
                                    "3. Copy the path (Ctrl+C)\n"
                                    "4. Cancel this dialog\n"
                                    "5. Manually paste the path in the Source field\n\n"
                                    "Or select 'NO' to copy entire device."
                                )
                                self.go_back()
                            except Exception as e:
                                messagebox.showerror("Error", f"Could not open Explorer:\n{str(e)}")
                        elif response is False:  # No - select whole device
                            self.dialog.destroy()
                        # Cancel - do nothing
                    else:
                        # Regular device - browse into it
                        self.browse_into_path(path, values[0])
    
    def on_select(self):
        """Handle select button click"""
        selection = self.device_tree.selection()
        if selection:
            item = selection[0]
            values = self.device_tree.item(item, 'values')
            tags = self.device_tree.item(item, 'tags')
            
            if len(values) >= 4 and values[3]:
                # Check if it's a folder/device or a file
                if 'file' in tags and not self.allow_files:
                    messagebox.showwarning("Invalid Selection", "Please select a folder, not a file")
                    return
                
                self.selected_path = values[3]
                self.dialog.destroy()
            else:
                messagebox.showwarning("No Selection", "Please select a specific item, not a category")
        else:
            messagebox.showwarning("No Selection", "Please select an item first")
    
    def browse_folder(self):
        """Browse for a specific folder"""
        selection = self.device_tree.selection()
        
        if selection:
            item = selection[0]
            values = self.device_tree.item(item, 'values')
            
            if len(values) >= 4 and values[3]:
                device_path = values[3]
                
                # Check if MTP device
                if self.device_manager.is_mtp_device(device_path):
                    # For MTP devices, open Windows Explorer to let user browse and copy path
                    response = messagebox.askyesno(
                        "Mobile Device Browser",
                        "MTP device browsing has limitations in this dialog.\n\n"
                        "Would you like to:\n"
                        "• YES - Open Windows Explorer to browse your device\n"
                        "         (You can copy the path from Explorer's address bar)\n"
                        "• NO - Select this device/folder as-is\n",
                        icon='question'
                    )
                    if response:
                        # Open Windows Explorer to the device
                        import subprocess
                        try:
                            subprocess.run(['explorer', device_path], check=False)
                            messagebox.showinfo(
                                "Windows Explorer Opened",
                                "Windows Explorer has been opened to your device.\n\n"
                                "To use a specific folder:\n"
                                "1. Browse to the folder you want\n"
                                "2. Click the address bar in Explorer\n"
                                "3. Copy the path (Ctrl+C)\n"
                                "4. Paste it in the app's path field\n\n"
                                "Or just select this device here to copy all."
                            )
                        except Exception as e:
                            messagebox.showerror("Error", f"Could not open Explorer:\n{str(e)}")
                    return
                
                # Open folder dialog starting from device path
                try:
                    folder = filedialog.askdirectory(
                        title="Select Folder",
                        initialdir=device_path
                    )
                    if folder:
                        self.selected_path = folder
                        self.dialog.destroy()
                except:
                    # Fallback if initialdir doesn't work
                    folder = filedialog.askdirectory(title="Select Folder")
                    if folder:
                        self.selected_path = folder
                        self.dialog.destroy()
        else:
            # No device selected - open generic folder browser
            folder = filedialog.askdirectory(title="Select Folder")
            if folder:
                self.selected_path = folder
                self.dialog.destroy()
    
    def use_entered_path(self):
        """Use the manually entered path"""
        path = self.path_var.get().strip()
        if path:
            import os
            import re
            
            # Clean up the path
            original_path = path
            
            # Remove extra spaces around backslashes (e.g., "UNKNOWN \" becomes "UNKNOWN\")
            path = re.sub(r'\s*\\+\s*', '\\\\', path)
            path = re.sub(r'\s*/+\s*', '/', path)
            
            # Remove "This PC\" prefix if present
            if path.startswith("This PC\\"):
                path = path.replace("This PC\\", "Computer\\", 1)
            elif path.startswith("This PC/"):
                path = path.replace("This PC/", "Computer\\", 1)
            
            # If path doesn't start with Computer\ but looks like it should, add it
            if not path.startswith("Computer\\") and not path.startswith("Computer/"):
                # Check if it looks like a device path (not a regular drive letter path)
                if not (len(path) >= 2 and path[1] == ':'):
                    # Might be a device name without Computer\ prefix
                    computer_path = f"Computer\\{path}"
                    if self._try_path(computer_path):
                        self.selected_path = computer_path
                        self.dialog.destroy()
                        return
            
            # Try the path as-is
            if self._try_path(path):
                self.selected_path = path
                self.dialog.destroy()
            else:
                # Show helpful error with corrected path suggestion
                suggested_path = path
                if not path.startswith("Computer\\") and not (len(path) >= 2 and path[1] == ':'):
                    suggested_path = f"Computer\\{path}"
                
                messagebox.showerror(
                    "Path Not Found",
                    f"Cannot access this path:\n{original_path}\n\n"
                    "For mobile devices, the path should start with 'Computer\\':\n"
                    f"Try: {suggested_path}\n\n"
                    "How to get the correct path:\n"
                    "1. Open Windows Explorer (Win+E)\n"
                    "2. Navigate to your folder\n"
                    "3. Click the address bar (Alt+D)\n"
                    "4. Copy the FULL path (Ctrl+C)\n"
                    "5. Paste it here\n\n"
                    "Note: The path should look like:\n"
                    "  Computer\\DeviceName\\Internal storage\\folder\n"
                    "NOT like:\n"
                    "  This PC\\DeviceName\\Internal storage\\folder"
                )
        else:
            messagebox.showwarning("No Path", "Please enter a path first")
    
    def _try_path(self, path):
        """Try to validate if a path is accessible"""
        import os
        
        # Standard file system path
        if os.path.exists(path):
            return True
        
        # MTP device path
        if self.device_manager.is_mtp_device(path):
            # For MTP paths, we can't easily verify they exist
            # Just accept if it looks like an MTP path
            return True
        
        # Try to resolve via Shell.Application for MTP
        if path.startswith("Computer\\") or "::{" in path:
            try:
                import subprocess
                ps_script = f"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$path = '{path.replace("'", "''")}'
$folder = $shell.Namespace($path)
if ($folder -ne $null) {{
    Write-Output "EXISTS"
}} else {{
    Write-Output "NOT_FOUND"
}}
"""
                result = subprocess.run(
                    ['powershell', '-NoProfile', '-Command', ps_script],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if "EXISTS" in result.stdout:
                    return True
            except:
                pass
        
        return False
    
    def on_cancel(self):
        """Handle cancel button"""
        self.selected_path = None
        self.dialog.destroy()
    
    def browse_into_path(self, path, name):
        """Browse into a folder/device"""
        # Save current state to history
        self.path_history.append(self.current_path)
        self.current_path = path
        
        # Update UI
        self.current_path_label.config(text=path)
        self.back_btn.config(state='normal')
        self.up_btn.config(state='normal')
        
        # Clear tree
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Show loading
        self.loading_label.pack(side=tk.RIGHT, padx=10)
        self.dialog.update()
        
        # Load contents
        threading.Thread(target=self._browse_path_thread, args=(path, name), daemon=True).start()
    
    def _browse_path_thread(self, path, name):
        """Browse path in background thread"""
        try:
            import os
            
            # Check if it's an accessible path
            if os.path.exists(path) and os.path.isdir(path):
                # Standard file system path
                items = []
                try:
                    for entry in os.listdir(path):
                        entry_path = os.path.join(path, entry)
                        is_dir = os.path.isdir(entry_path)
                        
                        # Get size for files
                        size_str = ""
                        if not is_dir:
                            try:
                                size = os.path.getsize(entry_path)
                                size_str = self._format_size(size)
                            except:
                                size_str = "N/A"
                        else:
                            size_str = "<DIR>"
                        
                        items.append({
                            'name': entry,
                            'path': entry_path,
                            'is_dir': is_dir,
                            'size': size_str
                        })
                except Exception as e:
                    self.dialog.after(0, lambda: messagebox.showerror(
                        "Access Error",
                        f"Cannot access folder:\n{str(e)}"
                    ))
                    self.dialog.after(0, self.go_back)
                    return
                
                # Update UI in main thread
                self.dialog.after(0, lambda: self._populate_folder_contents(items))
            
            elif self.device_manager.is_mtp_device(path):
                # MTP device - store device path and browse from root
                self.current_device_path = path
                self.current_breadcrumb = []
                self.dialog.after(0, lambda: self._browse_mtp_path(path, []))
            else:
                # Unknown path type
                self.dialog.after(0, lambda: messagebox.showerror(
                    "Error",
                    f"Cannot browse this path:\n{path}"
                ))
                self.dialog.after(0, self.go_back)
                
        except Exception as e:
            self.dialog.after(0, lambda: messagebox.showerror(
                "Error",
                f"Error browsing path:\n{str(e)}"
            ))
            self.dialog.after(0, self.go_back)
        finally:
            self.dialog.after(0, lambda: self.loading_label.pack_forget())
    
    def _populate_folder_contents(self, items):
        """Populate tree with folder contents"""
        # Sort: directories first, then files
        items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
        
        # Add items to tree
        for item in items:
            icon = '📁' if item['is_dir'] else '📄'
            item_type = 'Folder' if item['is_dir'] else 'File'
            
            tags = ['folder', 'browsable'] if item['is_dir'] else ['file']
            if not self.allow_files and not item['is_dir']:
                tags.append('disabled')
            
            self.device_tree.insert(
                '', 'end',
                text=icon,
                values=(
                    item['name'],
                    item_type,
                    item['size'],
                    item['path']
                ),
                tags=tuple(tags)
            )
        
        # Update path display
        self.path_var.set(f"Current: {self.current_path}")
        self.loading_label.pack_forget()
    
    def go_back(self):
        """Go back in navigation history"""
        # Check if we're in MTP navigation mode
        if self.current_device_path and self.path_history:
            # MTP breadcrumb navigation
            if len(self.path_history) > 0:
                self.current_breadcrumb = self.path_history.pop()
                self._browse_mtp_path(self.current_device_path, self.current_breadcrumb)
                
                # Update display
                if self.current_breadcrumb:
                    path_display = "Internal storage > " + " > ".join(self.current_breadcrumb)
                else:
                    path_display = "Internal storage"
                self.current_path_label.config(text=path_display)
                
                if len(self.path_history) == 0:
                    self.back_btn.config(state='disabled')
            return
        
        if self.path_history:
            previous_path = self.path_history.pop()
            
            if previous_path is None:
                # Back to devices list
                self.current_path = None
                self.current_path_label.config(text="Devices")
                self.back_btn.config(state='disabled')
                self.up_btn.config(state='disabled')
                self.path_var.set("No device selected")
                self.load_devices()
            else:
                # Back to previous folder
                self.current_path = previous_path
                parent_path = os.path.dirname(previous_path) if previous_path else None
                self.browse_into_path(previous_path, os.path.basename(previous_path))
        else:
            # Already at root
            self.current_path = None
            self.current_path_label.config(text="Devices")
            self.back_btn.config(state='disabled')
            self.up_btn.config(state='disabled')
            self.path_var.set("No device selected")
            self.load_devices()
    
    def go_up(self):
        """Go up one level in directory hierarchy"""
        # Check if we're in MTP navigation mode
        if self.current_device_path and len(self.current_breadcrumb) > 0:
            # MTP navigation - go up one level
            self.path_history.append(self.current_breadcrumb.copy())
            self.current_breadcrumb.pop()
            self._browse_mtp_path(self.current_device_path, self.current_breadcrumb)
            
            # Update display
            if self.current_breadcrumb:
                path_display = "Internal storage > " + " > ".join(self.current_breadcrumb)
            else:
                path_display = "Internal storage"
            self.current_path_label.config(text=path_display)
            return
        
        if self.current_path:
            import os
            parent_path = os.path.dirname(self.current_path)
            
            if parent_path and parent_path != self.current_path:
                self.browse_into_path(parent_path, os.path.basename(parent_path))
            else:
                # Go back to devices list
                self.go_back()
    
    def refresh_current(self):
        """Refresh current view"""
        if self.current_path:
            # Refresh current folder
            self.browse_into_path(self.current_path, os.path.basename(self.current_path))
        else:
            # Refresh devices list
            self.load_devices()
    
    def _browse_mtp_path(self, mtp_path, breadcrumb=None):
        """Browse an MTP path and show its contents using breadcrumb navigation"""
        # Clear existing items first
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
        
        # Show loading
        self.loading_label.pack(side=tk.RIGHT, padx=10)
        self.dialog.update()
        
        # Initialize breadcrumb if not provided
        if breadcrumb is None:
            breadcrumb = []
        
        print(f"DEBUG: Navigating with breadcrumb: {breadcrumb}")
        
        # Get items from MTP path using breadcrumb navigation
        items = self.device_manager.get_mtp_device_folders(mtp_path, breadcrumb)
        
        if items:
            # Show folders and files from MTP device
            for item in items:
                is_folder = item.get('is_folder', True)
                size = item.get('size', 0)
                item_breadcrumb = item.get('breadcrumb', breadcrumb)
                
                if is_folder:
                    icon = '📁'
                    item_type = 'Folder'
                    size_str = '<DIR>'
                    tags = ('mtp_folder', 'browsable', 'mtp_content')
                else:
                    icon = '📄'
                    item_type = 'File'
                    size_str = self._format_size(size) if size > 0 else 'N/A'
                    tags = ('mtp_file', 'mtp_content')
                
                # Store breadcrumb as a string in the path column for navigation
                breadcrumb_str = '|'.join(item_breadcrumb) if item_breadcrumb else ''
                
                self.device_tree.insert(
                    '', 'end',
                    text=icon,
                    values=(
                        item['name'],
                        item_type,
                        size_str,
                        breadcrumb_str  # Store breadcrumb instead of path
                    ),
                    tags=tags
                )
            
            # Extract short name from path for display
            short_name = mtp_path.split('\\')[-1] if '\\' in mtp_path else 'Device'
            self.path_var.set(f"Current: {short_name} ({len(items)} items)")
            self.loading_label.pack_forget()
        else:
            # Empty folder or can't browse - offer solutions
            response = messagebox.askyesnocancel(
                "Cannot Browse Folder",
                "This folder appears to be empty or inaccessible.\n\n"
                "This is a common MTP limitation. Would you like to:\n\n"
                "• YES - Open Windows Explorer to browse this device\n"
                "• NO - Select this location anyway (copy all)\n"
                "• CANCEL - Go back\n",
                icon='warning'
            )
            
            if response is True:  # YES - Open Explorer
                import subprocess
                try:
                    subprocess.run(['explorer', mtp_path], check=False)
                    messagebox.showinfo(
                        "Explorer Opened",
                        "Windows Explorer opened.\n\n"
                        "Browse to your folder, then copy the path\n"
                        "from Explorer's address bar and paste it\n"
                        "in the app's source field."
                    )
                except:
                    pass
                self.go_back()
            elif response is False:  # NO - Select anyway
                self.selected_path = mtp_path
                self.path_var.set(f"Selected: {mtp_path}")
            else:  # CANCEL - Go back
                self.go_back()
            
            self.loading_label.pack_forget()
    
    def _show_mtp_folders(self, device_path):
        """Show storage folders from MTP device"""
        folders = self.device_manager.get_mtp_device_folders(device_path, [])
        
        if folders:
            # Show storage options (Internal Storage, SD Card, etc.)
            for folder in folders:
                icon = '💾'
                breadcrumb = folder.get('breadcrumb', [])
                breadcrumb_str = '|'.join(breadcrumb) if breadcrumb else folder['name']
                
                self.device_tree.insert(
                    '', 'end',
                    text=icon,
                    values=(
                        folder['name'],
                        'Storage',
                        '<Storage Volume>',
                        breadcrumb_str  # Store breadcrumb
                    ),
                    tags=('mtp_storage', 'browsable', 'mtp_folder')
                )
            
            self.path_var.set(f"Storage on device - Double-click to browse inside")
            self.loading_label.pack_forget()
        else:
            # No folders found, show option to select whole device
            messagebox.showinfo(
                "Mobile Device",
                "Could not browse device folders.\n\n"
                "You can:\n"
                "• Click 'Select' to copy entire device\n"
                "• Or use 'Back' and try Windows Explorer"
            )
            self.loading_label.pack_forget()
    
    def _format_size(self, size):
        """Format file size"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def show(self):
        """Show dialog and wait for result"""
        self.dialog.wait_window()
        return self.selected_path


def show_device_picker(parent, title="Select Device", path_type="source"):
    """
    Show device picker dialog
    
    Args:
        parent: Parent window
        title: Dialog title
        path_type: 'source' or 'destination'
        
    Returns:
        Selected path or None
    """
    dialog = DevicePickerDialog(parent, title, path_type)
    return dialog.show()


# Test function
def test_device_picker():
    """Test the device picker dialog"""
    root = tk.Tk()
    root.withdraw()
    
    path = show_device_picker(root, "Test Device Picker", "source")
    
    if path:
        print(f"Selected path: {path}")
    else:
        print("No device selected")
    
    root.destroy()


if __name__ == '__main__':
    test_device_picker()
