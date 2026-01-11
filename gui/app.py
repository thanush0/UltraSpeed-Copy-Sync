"""
UltraSpeed Copy - Main GUI Application
Production-grade file transfer system with GUI interface
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import json
import threading
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.robocopy_engine import RobocopyEngine, RobocopyMode
from engine.compression import CompressionEngine, CompressionFormat
from engine.network_optimizer import NetworkOptimizer
from engine.mtp_copy_handler import MTPCopyHandler
from benchmark.speed_monitor import SpeedMonitor, SpeedChart


class UltraSpeedCopyGUI:
    """
    Main GUI Application for UltraSpeed Copy System
    """
    
    def __init__(self, root):
        """Initialize the GUI application"""
        self.root = root
        self.root.title("UltraSpeed Smart Copy & Sync System")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Initialize engines
        self.robocopy_engine = RobocopyEngine(
            log_callback=self.log_message,
            progress_callback=self.update_progress
        )
        self.compression_engine = CompressionEngine(
            log_callback=self.log_message,
            progress_callback=self.update_compression_progress
        )
        self.mtp_handler = MTPCopyHandler(
            log_callback=self.log_message,
            progress_callback=self.update_progress
        )
        self.speed_monitor = SpeedMonitor()
        
        # Configuration
        self.config_file = "config/config.json"
        self.log_file = "logs/copy.log"
        self.config = self.load_config()
        
        # UI Variables
        self.source_path = tk.StringVar()
        self.dest_path = tk.StringVar()
        self.copy_mode = tk.StringVar(value=RobocopyMode.FULL_COPY)
        self.thread_count = tk.IntVar(value=8)
        self.network_optimized = tk.BooleanVar(value=False)
        self.compression_enabled = tk.BooleanVar(value=False)
        self.compression_format = tk.StringVar(value=CompressionFormat.ZIP)
        
        # Status variables
        self.is_running = tk.BooleanVar(value=False)
        self.current_speed = tk.StringVar(value="0.00 MB/s")
        self.files_copied = tk.StringVar(value="0")
        self.bytes_copied = tk.StringVar(value="0 B")
        self.progress_percent = tk.DoubleVar(value=0)
        
        # Create UI
        self.create_ui()
        
        # Load last session
        self.load_last_session()
        
        self.log_message("UltraSpeed Copy System initialized")
    
    def create_ui(self):
        """Create the main user interface"""
        # Create main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Create sections
        self.create_path_section(main_frame)
        self.create_options_section(main_frame)
        self.create_control_section(main_frame)
        self.create_status_section(main_frame)
        self.create_log_section(main_frame)
    
    def create_path_section(self, parent):
        """Create path selection section"""
        path_frame = ttk.LabelFrame(parent, text="Paths", padding="10")
        path_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        path_frame.columnconfigure(1, weight=1)
        
        # Source path
        ttk.Label(path_frame, text="Source:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.source_path, width=60).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(path_frame, text="Browse...", command=self.browse_source).grid(
            row=0, column=2, pady=5
        )
        
        # Destination path
        ttk.Label(path_frame, text="Destination:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(path_frame, textvariable=self.dest_path, width=60).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        ttk.Button(path_frame, text="Browse...", command=self.browse_destination).grid(
            row=1, column=2, pady=5
        )
    
    def create_options_section(self, parent):
        """Create options section"""
        options_frame = ttk.LabelFrame(parent, text="Options", padding="10")
        options_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        options_frame.columnconfigure(1, weight=1)
        
        # Copy mode
        ttk.Label(options_frame, text="Copy Mode:").grid(row=0, column=0, sticky=tk.W, pady=5)
        mode_frame = ttk.Frame(options_frame)
        mode_frame.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(mode_frame, text="Full Copy", variable=self.copy_mode,
                       value=RobocopyMode.FULL_COPY).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Incremental Copy", variable=self.copy_mode,
                       value=RobocopyMode.INCREMENTAL).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_frame, text="Mirror Sync", variable=self.copy_mode,
                       value=RobocopyMode.MIRROR).pack(side=tk.LEFT, padx=5)
        
        # Thread count
        ttk.Label(options_frame, text="Threads:").grid(row=1, column=0, sticky=tk.W, pady=5)
        thread_frame = ttk.Frame(options_frame)
        thread_frame.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Scale(thread_frame, from_=1, to=128, variable=self.thread_count,
                 orient=tk.HORIZONTAL, length=200, command=self.update_thread_label).pack(side=tk.LEFT)
        self.thread_label = ttk.Label(thread_frame, text="8 threads")
        self.thread_label.pack(side=tk.LEFT, padx=10)
        
        # Network optimization
        ttk.Checkbutton(options_frame, text="Network Optimization (for UNC/NAS paths)",
                       variable=self.network_optimized,
                       command=self.on_network_toggle).grid(row=2, column=0, columnspan=2,
                                                            sticky=tk.W, pady=5)
        
        # Compression
        compression_frame = ttk.Frame(options_frame)
        compression_frame.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Checkbutton(compression_frame, text="Enable Compression",
                       variable=self.compression_enabled,
                       command=self.on_compression_toggle).pack(side=tk.LEFT)
        
        ttk.Label(compression_frame, text="Format:").pack(side=tk.LEFT, padx=(20, 5))
        self.compression_combo = ttk.Combobox(compression_frame, textvariable=self.compression_format,
                                             values=[CompressionFormat.ZIP, CompressionFormat.TAR_GZ],
                                             state='disabled', width=10)
        self.compression_combo.pack(side=tk.LEFT)
    
    def create_control_section(self, parent):
        """Create control buttons section"""
        control_frame = ttk.Frame(parent, padding="10")
        control_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_button = ttk.Button(control_frame, text="Start Copy", 
                                       command=self.start_copy, width=15)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(control_frame, text="Stop", 
                                      command=self.stop_copy, width=15, state='disabled')
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="View Statistics", 
                  command=self.show_statistics, width=15).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(control_frame, text="Save Config", 
                  command=self.save_config_dialog, width=15).pack(side=tk.LEFT, padx=5)
    
    def create_status_section(self, parent):
        """Create status display section"""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Progress bar
        ttk.Label(status_frame, text="Progress:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_percent,
                                           maximum=100, mode='determinate')
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Speed
        ttk.Label(status_frame, text="Speed:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_frame, textvariable=self.current_speed, 
                 font=('Arial', 12, 'bold')).grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Files copied
        ttk.Label(status_frame, text="Files Copied:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_frame, textvariable=self.files_copied).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=5
        )
        
        # Bytes copied
        ttk.Label(status_frame, text="Data Copied:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Label(status_frame, textvariable=self.bytes_copied).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=5
        )
    
    def create_log_section(self, parent):
        """Create log viewer section"""
        log_frame = ttk.LabelFrame(parent, text="Log", padding="10")
        log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD,
                                                  font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Log control buttons
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        ttk.Button(log_button_frame, text="Clear Log", 
                  command=self.clear_log).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_button_frame, text="Save Log", 
                  command=self.save_log).pack(side=tk.LEFT, padx=5)
    
    # Event Handlers
    
    def browse_source(self):
        """Browse for source directory"""
        # Use enhanced device picker to show mobile devices
        try:
            from gui.device_picker import show_device_picker
            path = show_device_picker(self.root, "Select Source Device", "source")
        except Exception as e:
            # Fallback to standard dialog
            print(f"Device picker failed: {e}")
            path = filedialog.askdirectory(title="Select Source Directory")
        
        if path:
            self.source_path.set(path)
            self.check_network_path()
    
    def browse_destination(self):
        """Browse for destination directory"""
        # Use enhanced device picker to show mobile devices
        try:
            from gui.device_picker import show_device_picker
            path = show_device_picker(self.root, "Select Destination Device", "destination")
        except Exception as e:
            # Fallback to standard dialog
            print(f"Device picker failed: {e}")
            path = filedialog.askdirectory(title="Select Destination Directory")
        
        if path:
            self.dest_path.set(path)
            self.check_network_path()
    
    def check_network_path(self):
        """Auto-detect network paths and suggest optimization"""
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            return
        
        optimizer = NetworkOptimizer()
        params = optimizer.get_optimized_parameters(source, dest)
        
        if params['network_optimized']:
            # Auto-enable network optimization
            self.network_optimized.set(True)
            self.thread_count.set(params['recommended_threads'])
            
            reasons = ', '.join(params['optimization_reason'])
            self.log_message(f"Network path detected: {reasons}")
            self.log_message(f"Network optimization enabled automatically")
            self.log_message(f"Recommended threads: {params['recommended_threads']}")
    
    def update_thread_label(self, value):
        """Update thread count label"""
        count = int(float(value))
        self.thread_label.config(text=f"{count} threads")
    
    def on_network_toggle(self):
        """Handle network optimization toggle"""
        if self.network_optimized.get():
            self.log_message("Network optimization enabled")
        else:
            self.log_message("Network optimization disabled")
    
    def on_compression_toggle(self):
        """Handle compression toggle"""
        if self.compression_enabled.get():
            self.compression_combo.config(state='readonly')
            self.log_message("Compression enabled")
        else:
            self.compression_combo.config(state='disabled')
            self.log_message("Compression disabled")
    
    def start_copy(self):
        """Start the copy operation"""
        # Validate inputs
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            messagebox.showerror("Error", "Please select both source and destination paths")
            return
        
        # Validate source path (with MTP support)
        if not self._validate_path(source):
            messagebox.showerror("Error", f"Source path does not exist: {source}")
            return
        
        # Confirm mirror mode
        if self.copy_mode.get() == RobocopyMode.MIRROR:
            response = messagebox.askyesno(
                "Confirm Mirror Mode",
                "Mirror mode will DELETE files in destination that don't exist in source.\n\n"
                "Are you sure you want to continue?"
            )
            if not response:
                return
        
        # Disable UI
        self.is_running.set(True)
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Reset progress
        self.progress_percent.set(0)
        self.current_speed.set("0.00 MB/s")
        self.files_copied.set("0")
        self.bytes_copied.set("0 B")
        
        # Start monitoring session
        self.speed_monitor.start_session(
            operation_type=self.copy_mode.get(),
            source=source,
            destination=dest,
            additional_info={
                'threads': self.thread_count.get(),
                'network_optimized': self.network_optimized.get(),
                'compression': self.compression_enabled.get()
            }
        )
        
        # Start operation in thread
        thread = threading.Thread(target=self._execute_copy_operation)
        thread.daemon = True
        thread.start()
    
    def _execute_copy_operation(self):
        """Execute the copy operation (runs in separate thread)"""
        try:
            source = self.source_path.get()
            dest = self.dest_path.get()
            
            # Check if source is an MTP device
            is_mtp_source = self._is_mtp_path(source)
            is_mtp_dest = self._is_mtp_path(dest)
            
            if is_mtp_dest:
                self.log_message("📱 Mobile device detected as DESTINATION")
                self.log_message("Using MTP handler to copy TO mobile device...")
                
                # Copy TO MTP device
                success = self.mtp_handler.copy_to_mtp(source, dest)
                
                if not success:
                    raise Exception("Failed to copy to mobile device")
                
                self.log_message("✅ Successfully copied to mobile device!")
                return
            
            if is_mtp_source:
                self.log_message("📱 Mobile device detected as source")
                self.log_message("Using MTP handler for two-stage copy process...")
                
                # Stage 1: Copy from MTP to temp folder
                success, temp_or_error = self.mtp_handler.copy_from_mtp(source, dest)
                
                if not success:
                    raise Exception(f"MTP copy failed: {temp_or_error}")
                
                # Stage 2: Copy from temp to final destination using Robocopy
                temp_source = temp_or_error
                self.log_message(f"⏳ Stage 2: Fast copy from staging to destination using Robocopy...")
                source = temp_source  # Update source to temp folder
            
            # Check if compression is enabled
            if self.compression_enabled.get():
                self.log_message("Starting compression phase...")
                
                # Create compressed archive
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"backup_{timestamp}.{self.compression_format.get()}"
                archive_path = os.path.join(os.path.dirname(dest), archive_name)
                
                self.compression_engine.compress_async(
                    source_path=source,
                    output_file=archive_path,
                    format=self.compression_format.get(),
                    compression_level=6
                )
                
                # Wait for compression to complete
                self.compression_engine.wait_for_completion()
                
                if not os.path.exists(archive_path):
                    raise Exception("Compression failed")
                
                self.log_message("Compression completed successfully")
                
                # Now copy the archive
                source = archive_path
                dest = os.path.join(dest, archive_name)
                self.log_message(f"Copying compressed archive to destination...")
            
            # Build robocopy command
            ensure_dir_exists(dest)
            
            command = self.robocopy_engine.build_command(
                source=source,
                destination=dest,
                mode=self.copy_mode.get(),
                threads=self.thread_count.get(),
                network_optimized=self.network_optimized.get()
            )
            
            # Execute robocopy
            log_file = self.get_log_file_path()
            self.robocopy_engine.execute(command, log_file=log_file)
            
            # Wait for completion
            self.robocopy_engine.wait_for_completion()
            
            # End monitoring session
            self.speed_monitor.end_session(success=True)
            
            self.log_message("✅ Operation completed successfully!")
            
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
            self.speed_monitor.end_session(success=False)
        finally:
            # Re-enable UI
            self.root.after(0, self._operation_completed)
    
    def _operation_completed(self):
        """Called when operation completes (runs in main thread)"""
        self.is_running.set(False)
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
    
    def stop_copy(self):
        """Stop the running copy operation"""
        response = messagebox.askyesno(
            "Confirm Stop",
            "Are you sure you want to stop the operation?"
        )
        if response:
            self.log_message("Stopping operation...")
            self.robocopy_engine.cancel()
            self.compression_engine.cancel()
    
    def update_progress(self, stats):
        """Update progress display from robocopy engine"""
        # Update UI in main thread
        self.root.after(0, self._update_progress_ui, stats)
        
        # Update speed monitor
        self.speed_monitor.update_progress(
            bytes_copied=stats['bytes_copied'],
            files_copied=stats['files_copied'],
            current_speed_mbps=stats['speed_mbps'],
            errors=stats['errors']
        )
    
    def _update_progress_ui(self, stats):
        """Update UI with progress (runs in main thread)"""
        self.files_copied.set(str(stats['files_copied']))
        self.bytes_copied.set(self.format_bytes(stats['bytes_copied']))
        self.current_speed.set(f"{stats['speed_mbps']:.2f} MB/s")
        
        # Update progress bar (estimate)
        # Note: actual progress is hard to calculate without knowing total
        # This is a simple estimation based on activity
        if stats['files_copied'] > 0:
            self.progress_percent.set(min(90, self.progress_percent.get() + 1))
    
    def update_compression_progress(self, stats):
        """Update progress from compression engine"""
        self.root.after(0, self._update_compression_ui, stats)
    
    def _update_compression_ui(self, stats):
        """Update UI with compression progress"""
        if stats['total_files'] > 0:
            percent = (stats['processed_files'] / stats['total_files']) * 100
            self.progress_percent.set(percent)
        
        self.files_copied.set(f"{stats['processed_files']} / {stats['total_files']}")
        self.bytes_copied.set(self.format_bytes(stats['total_bytes']))
    
    def show_statistics(self):
        """Show statistics window"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Transfer Statistics")
        stats_window.geometry("800x600")
        
        # Create notebook for tabs
        notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Summary tab
        summary_frame = ttk.Frame(notebook, padding="10")
        notebook.add(summary_frame, text="Summary")
        
        summary = self.speed_monitor.get_summary_stats()
        
        info_text = scrolledtext.ScrolledText(summary_frame, height=20, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        info_text.insert(tk.END, "=== Transfer Statistics Summary ===\n\n")
        info_text.insert(tk.END, f"Total Sessions: {summary['total_sessions']}\n")
        info_text.insert(tk.END, f"Successful: {summary['successful_sessions']}\n")
        info_text.insert(tk.END, f"Failed: {summary['failed_sessions']}\n\n")
        info_text.insert(tk.END, f"Total Data Transferred: {self.format_bytes(summary['total_bytes_transferred'])}\n")
        info_text.insert(tk.END, f"Total Files Transferred: {summary['total_files_transferred']}\n\n")
        info_text.insert(tk.END, f"Average Speed: {summary['average_speed_mbps']:.2f} MB/s\n")
        info_text.insert(tk.END, f"Peak Speed: {summary['peak_speed_mbps']:.2f} MB/s\n")
        
        info_text.config(state='disabled')
        
        # History tab
        history_frame = ttk.Frame(notebook, padding="10")
        notebook.add(history_frame, text="History")
        
        # Create treeview for history
        columns = ('Session', 'Type', 'Files', 'Size', 'Speed', 'Status')
        tree = ttk.Treeview(history_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        history = self.speed_monitor.get_history(limit=50)
        for entry in reversed(history):
            tree.insert('', tk.END, values=(
                entry['session_id'][-12:],
                entry['operation_type'],
                entry['total_files'],
                self.format_bytes(entry['total_bytes']),
                f"{entry['average_speed_mbps']:.2f} MB/s",
                'Success' if entry['success'] else 'Failed'
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
    
    # Logging
    
    def log_message(self, message):
        """Log a message to the log viewer"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update UI in main thread
        self.root.after(0, self._append_log, log_entry)
        
        # Write to file
        self._write_to_log_file(log_entry)
    
    def _append_log(self, message):
        """Append message to log text widget (main thread only)"""
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
    
    def _write_to_log_file(self, message):
        """Write to log file"""
        try:
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(message)
        except:
            pass
    
    def clear_log(self):
        """Clear the log viewer"""
        self.log_text.delete(1.0, tk.END)
    
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"Log saved to: {filename}")
    
    def get_log_file_path(self):
        """Get timestamped log file path"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"logs/robocopy_{timestamp}.log"
    
    # Configuration
    
    def load_config(self):
        """Load configuration from file"""
        default_config = {
            'last_source': '',
            'last_destination': '',
            'default_threads': 8,
            'default_mode': RobocopyMode.INCREMENTAL
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        
        return default_config
    
    def save_config_dialog(self):
        """Save current configuration"""
        config = {
            'last_source': self.source_path.get(),
            'last_destination': self.dest_path.get(),
            'default_threads': self.thread_count.get(),
            'default_mode': self.copy_mode.get()
        }
        
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            self.log_message("Configuration saved")
            messagebox.showinfo("Success", "Configuration saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_last_session(self):
        """Load last session from config"""
        if self.config.get('last_source'):
            self.source_path.set(self.config['last_source'])
        if self.config.get('last_destination'):
            self.dest_path.set(self.config['last_destination'])
        if self.config.get('default_threads'):
            self.thread_count.set(self.config['default_threads'])
        if self.config.get('default_mode'):
            self.copy_mode.set(self.config['default_mode'])
    
    # Utilities
    
    def _is_mtp_path(self, path):
        """Check if path is an MTP device path"""
        path = path.strip()
        return (path.startswith("Computer\\") or 
                path.startswith("Computer/") or 
                "::{" in path or
                path.startswith("wpd://"))
    
    def _validate_path(self, path):
        """Validate that a path exists (handles both regular paths and MTP devices)"""
        import subprocess
        
        # Clean up the path - remove extra spaces
        path = path.strip()
        
        # Standard file system path
        if os.path.exists(path):
            return True
        
        # Check if it's an MTP device path
        # MTP paths are difficult to validate due to Windows limitations
        # Allow any path that looks like an MTP device path
        if self._is_mtp_path(path):
            self.log_message(f"📱 Detected MTP device path: {path}")
            self.log_message("Note: MTP path validation is limited. Operation will proceed.")
            # For MTP devices, we can't reliably validate the full path
            # Just accept it and let the copy operation handle errors
            return True
        
        return False
    
    @staticmethod
    def format_bytes(bytes_val):
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


def ensure_dir_exists(path):
    """Ensure directory exists"""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def main():
    """Main entry point"""
    root = tk.Tk()
    app = UltraSpeedCopyGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
