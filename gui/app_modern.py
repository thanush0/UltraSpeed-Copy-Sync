"""
UltraSpeed Copy - Modern Animated GUI Application
Production-grade file transfer system with beautiful, animated interface
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import threading
from datetime import datetime
from pathlib import Path
import psutil  # For system resource detection

# Try to import ttkbootstrap for modern themes
try:
    import ttkbootstrap as ttk
    from ttkbootstrap.constants import *
    try:
        from ttkbootstrap.widgets import ToolTip
    except (ImportError, AttributeError):
        try:
            from ttkbootstrap.tooltip import ToolTip
        except:
            ToolTip = None
    MODERN_THEME = True
except ImportError:
    import tkinter.ttk as ttk
    MODERN_THEME = False
    ToolTip = None
    print("Warning: ttkbootstrap not installed. Using standard theme.")
    print("Install with: pip install ttkbootstrap")

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.robocopy_engine import RobocopyEngine, RobocopyMode
from engine.compression import CompressionEngine, CompressionFormat
from engine.network_optimizer import NetworkOptimizer
from engine.mtp_copy_handler import MTPCopyHandler
from benchmark.speed_monitor import SpeedMonitor, SpeedChart


class AnimatedProgressBar:
    """Animated progress bar with smooth transitions"""
    
    def __init__(self, parent, **kwargs):
        self.progress_var = tk.DoubleVar(value=0)
        self.target_value = 0
        self.current_value = 0
        self.animating = False
        
        if MODERN_THEME:
            self.bar = ttk.Progressbar(
                parent, 
                variable=self.progress_var,
                bootstyle="success-striped",
                **kwargs
            )
        else:
            self.bar = ttk.Progressbar(
                parent,
                variable=self.progress_var,
                mode='determinate',
                **kwargs
            )
    
    def set_value(self, value):
        """Set progress value with smooth animation"""
        self.target_value = max(0, min(100, value))
        if not self.animating:
            self._animate()
    
    def _animate(self):
        """Smooth animation to target value"""
        self.animating = True
        diff = self.target_value - self.current_value
        
        if abs(diff) < 0.5:
            self.current_value = self.target_value
            self.progress_var.set(self.current_value)
            self.animating = False
            return
        
        # Smooth easing
        step = diff * 0.15
        self.current_value += step
        self.progress_var.set(self.current_value)
        
        # Continue animation
        self.bar.after(30, self._animate)
    
    def grid(self, **kwargs):
        self.bar.grid(**kwargs)
    
    def pack(self, **kwargs):
        self.bar.pack(**kwargs)


class StatCard(ttk.Frame):
    """Modern statistic card with icon and animated value"""
    
    def __init__(self, parent, title, icon, color="primary", **kwargs):
        super().__init__(parent, **kwargs)
        
        if MODERN_THEME:
            self.configure(bootstyle=color)
        
        # Card styling
        self.configure(relief="raised", borderwidth=2)
        
        # Icon/Title row
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # Icon label
        self.icon_label = ttk.Label(
            header_frame, 
            text=icon, 
            font=("Segoe UI Emoji", 24)
        )
        self.icon_label.pack(side=tk.LEFT)
        
        # Title
        self.title_label = ttk.Label(
            header_frame,
            text=title,
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=10)
        
        # Value label (animated)
        self.value_var = tk.StringVar(value="0")
        self.value_label = ttk.Label(
            self,
            textvariable=self.value_var,
            font=("Segoe UI", 20, "bold")
        )
        self.value_label.pack(padx=10, pady=(0, 10))
        
        # Animation variables
        self.current_value = 0
        self.target_value = 0
        self.animating = False
    
    def set_value(self, value, suffix=""):
        """Set card value with animation"""
        if isinstance(value, (int, float)):
            self.target_value = value
            self.suffix = suffix
            if not self.animating:
                self._animate_value()
        else:
            self.value_var.set(str(value))
    
    def _animate_value(self):
        """Animate value change"""
        self.animating = True
        diff = self.target_value - self.current_value
        
        if abs(diff) < 0.1:
            self.current_value = self.target_value
            if isinstance(self.current_value, float):
                self.value_var.set(f"{self.current_value:.2f}{self.suffix}")
            else:
                self.value_var.set(f"{int(self.current_value)}{self.suffix}")
            self.animating = False
            return
        
        step = diff * 0.2
        self.current_value += step
        
        if isinstance(self.current_value, float):
            self.value_var.set(f"{self.current_value:.2f}{self.suffix}")
        else:
            self.value_var.set(f"{int(self.current_value)}{self.suffix}")
        
        self.after(50, self._animate_value)


class ModernScrolledText(ttk.Frame):
    """Modern scrolled text widget with syntax highlighting"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent)
        
        # Create text widget
        self.text = tk.Text(
            self,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e" if MODERN_THEME else "white",
            fg="#d4d4d4" if MODERN_THEME else "black",
            insertbackground="white",
            selectbackground="#264f78",
            relief="flat",
            **kwargs
        )
        
        # Scrollbar
        if MODERN_THEME:
            scrollbar = ttk.Scrollbar(
                self,
                command=self.text.yview,
                bootstyle="round"
            )
        else:
            scrollbar = ttk.Scrollbar(self, command=self.text.yview)
        
        self.text.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Configure tags for colored output
        self.text.tag_config("INFO", foreground="#4ec9b0")
        self.text.tag_config("ERROR", foreground="#f48771")
        self.text.tag_config("SUCCESS", foreground="#89d185")
        self.text.tag_config("WARNING", foreground="#dcdcaa")
        self.text.tag_config("TIMESTAMP", foreground="#858585")
    
    def insert_colored(self, text):
        """Insert text with automatic color coding"""
        self.text.insert(tk.END, text)
        
        # Auto-scroll
        self.text.see(tk.END)
    
    def clear(self):
        """Clear all text"""
        self.text.delete(1.0, tk.END)
    
    def get_content(self):
        """Get all text content"""
        return self.text.get(1.0, tk.END)


class UltraSpeedModernGUI:
    """
    Modern Animated GUI Application for UltraSpeed Copy System
    Features: Smooth animations, modern theme, beautiful design
    """
    
    def __init__(self, root):
        """Initialize the modern GUI application"""
        self.root = root
        self.root.title("UltraSpeed Copy - Modern Edition")
        
        # Set window size and center
        window_width = 1400
        window_height = 900
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(1200, 800)
        
        # Apply modern theme
        if MODERN_THEME:
            self.style = ttk.Style("darkly")  # Modern dark theme
        
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
        
        # Auto-detect optimal thread count
        self.optimal_threads = self.calculate_optimal_threads()
        self.thread_count = tk.IntVar(value=self.optimal_threads)
        self.auto_thread_adjust = tk.BooleanVar(value=True)
        
        self.network_optimized = tk.BooleanVar(value=False)
        self.compression_enabled = tk.BooleanVar(value=False)
        self.compression_format = tk.StringVar(value=CompressionFormat.ZIP)
        
        # Status variables
        self.is_running = tk.BooleanVar(value=False)
        self.current_speed = tk.StringVar(value="0.00")
        self.files_copied = tk.IntVar(value=0)
        self.bytes_copied = tk.IntVar(value=0)
        self.progress_percent = tk.DoubleVar(value=0)
        
        # Animation state
        self.pulse_state = 0
        
        # Create modern UI
        self.create_modern_ui()
        
        # Load last session
        self.load_last_session()
        
        # Start animations
        self.start_animations()
        
        self.log_message("🚀 UltraSpeed Copy Modern Edition initialized")
        self.log_message(f"🔧 Auto-detected optimal threads: {self.optimal_threads}")
        self.log_message("💡 Ready for high-speed file operations")
    
    def calculate_optimal_threads(self):
        """
        Calculate optimal thread count based on system resources
        
        Returns:
            int: Recommended thread count
        """
        try:
            # Get CPU count
            cpu_count = psutil.cpu_count(logical=True)
            physical_cores = psutil.cpu_count(logical=False)
            
            # Get available memory (in GB)
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024**3)
            
            # Get disk type (SSD vs HDD) - simplified detection
            # For Windows, check if C: drive
            try:
                disk_usage = psutil.disk_io_counters(perdisk=True)
                # Assume SSD if we can't determine (modern systems)
                is_ssd = True
            except:
                is_ssd = True
            
            # Calculate based on hardware
            if is_ssd:
                # SSD: Can handle more threads
                if cpu_count >= 16 and available_gb >= 16:
                    optimal = 32
                elif cpu_count >= 8 and available_gb >= 8:
                    optimal = 16
                elif cpu_count >= 4:
                    optimal = 8
                else:
                    optimal = 4
            else:
                # HDD: Fewer threads recommended
                if cpu_count >= 8:
                    optimal = 8
                elif cpu_count >= 4:
                    optimal = 4
                else:
                    optimal = 2
            
            # Ensure within bounds
            optimal = max(1, min(128, optimal))
            
            return optimal
            
        except Exception as e:
            # Fallback to safe default
            return 8
    
    def create_modern_ui(self):
        """Create the modern animated user interface"""
        # Main container with padding
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create header
        self.create_header(main_container)
        
        # Create main content area (2 columns)
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Left column - Configuration
        left_column = ttk.Frame(content_frame)
        left_column.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.create_path_section(left_column)
        self.create_options_section(left_column)
        self.create_control_section(left_column)
        
        # Right column - Status and Logs
        right_column = ttk.Frame(content_frame)
        right_column.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        self.create_dashboard(right_column)
        self.create_log_section(right_column)
    
    def create_header(self, parent):
        """Create animated header with logo and title"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        if MODERN_THEME:
            header_frame.configure(bootstyle="dark")
        
        # Logo and title
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        # Logo (emoji or custom)
        logo_label = ttk.Label(
            title_frame,
            text="⚡",
            font=("Segoe UI Emoji", 36)
        )
        logo_label.pack(side=tk.LEFT, padx=(0, 15))
        
        # Title and subtitle
        text_frame = ttk.Frame(title_frame)
        text_frame.pack(side=tk.LEFT)
        
        title_label = ttk.Label(
            text_frame,
            text="UltraSpeed Copy",
            font=("Segoe UI", 24, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(
            text_frame,
            text="Smart Copy & Sync System - Modern Edition",
            font=("Segoe UI", 10)
        )
        subtitle_label.pack(anchor=tk.W)
        
        # Status indicator (animated pulse)
        self.status_indicator = ttk.Label(
            header_frame,
            text="● Ready",
            font=("Segoe UI", 12, "bold")
        )
        self.status_indicator.pack(side=tk.RIGHT, padx=20)
        
        if MODERN_THEME:
            self.status_indicator.configure(bootstyle="success")
    
    def create_path_section(self, parent):
        """Create modern path selection section"""
        path_frame = ttk.LabelFrame(parent, text="📁 Paths")
        path_frame.pack(fill=tk.X, pady=(0, 15), padx=5, ipadx=10, ipady=10)
        
        # Source path
        source_container = ttk.Frame(path_frame)
        source_container.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(
            source_container,
            text="Source Directory:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        source_entry_frame = ttk.Frame(source_container)
        source_entry_frame.pack(fill=tk.X)
        
        self.source_entry = ttk.Entry(
            source_entry_frame,
            textvariable=self.source_path,
            font=("Segoe UI", 10)
        )
        self.source_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        if MODERN_THEME:
            source_btn = ttk.Button(
                source_entry_frame,
                text="Browse",
                command=self.browse_source,
                bootstyle="primary-outline",
                width=12
            )
        else:
            source_btn = ttk.Button(
                source_entry_frame,
                text="Browse",
                command=self.browse_source,
                width=12
            )
        source_btn.pack(side=tk.RIGHT)
        
        # Destination path
        dest_container = ttk.Frame(path_frame)
        dest_container.pack(fill=tk.X)
        
        ttk.Label(
            dest_container,
            text="Destination Directory:",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        dest_entry_frame = ttk.Frame(dest_container)
        dest_entry_frame.pack(fill=tk.X)
        
        self.dest_entry = ttk.Entry(
            dest_entry_frame,
            textvariable=self.dest_path,
            font=("Segoe UI", 10)
        )
        self.dest_entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        if MODERN_THEME:
            dest_btn = ttk.Button(
                dest_entry_frame,
                text="Browse",
                command=self.browse_destination,
                bootstyle="primary-outline",
                width=12
            )
        else:
            dest_btn = ttk.Button(
                dest_entry_frame,
                text="Browse",
                command=self.browse_destination,
                width=12
            )
        dest_btn.pack(side=tk.RIGHT)
    
    def create_options_section(self, parent):
        """Create modern options section with cards"""
        options_frame = ttk.LabelFrame(parent, text="⚙️ Options")
        options_frame.pack(fill=tk.X, pady=(0, 15), padx=5, ipadx=10, ipady=10)
        
        # Copy mode with modern radio buttons
        mode_label = ttk.Label(
            options_frame,
            text="Copy Mode:",
            font=("Segoe UI", 10, "bold")
        )
        mode_label.pack(anchor=tk.W, pady=(0, 8))
        
        mode_frame = ttk.Frame(options_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 15))
        
        modes = [
            ("🔄 Full Copy", RobocopyMode.FULL_COPY, "Copy all files"),
            ("⚡ Incremental", RobocopyMode.INCREMENTAL, "Only new/changed files"),
            ("🔁 Mirror Sync", RobocopyMode.MIRROR, "Exact replica (deletes extra)")
        ]
        
        for text, value, tooltip in modes:
            if MODERN_THEME:
                rb = ttk.Radiobutton(
                    mode_frame,
                    text=text,
                    variable=self.copy_mode,
                    value=value,
                    bootstyle="primary-toolbutton"
                )
            else:
                rb = ttk.Radiobutton(
                    mode_frame,
                    text=text,
                    variable=self.copy_mode,
                    value=value
                )
            rb.pack(side=tk.LEFT, padx=(0, 15))
            
            if MODERN_THEME and ToolTip:
                ToolTip(rb, text=tooltip)
        
        # Thread count with modern slider and auto-adjust
        thread_header_frame = ttk.Frame(options_frame)
        thread_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        thread_label = ttk.Label(
            thread_header_frame,
            text="Thread Count:",
            font=("Segoe UI", 10, "bold")
        )
        thread_label.pack(side=tk.LEFT)
        
        # Auto-adjust toggle
        if MODERN_THEME:
            auto_check = ttk.Checkbutton(
                thread_header_frame,
                text="Auto-adjust",
                variable=self.auto_thread_adjust,
                command=self.on_auto_thread_toggle,
                bootstyle="success-round-toggle"
            )
        else:
            auto_check = ttk.Checkbutton(
                thread_header_frame,
                text="Auto-adjust",
                variable=self.auto_thread_adjust,
                command=self.on_auto_thread_toggle
            )
        auto_check.pack(side=tk.RIGHT)
        
        thread_frame = ttk.Frame(options_frame)
        thread_frame.pack(fill=tk.X, pady=(0, 15))
        
        if MODERN_THEME:
            self.thread_scale = ttk.Scale(
                thread_frame,
                from_=1,
                to=128,
                variable=self.thread_count,
                orient=tk.HORIZONTAL,
                command=self.update_thread_label,
                bootstyle="success"
            )
        else:
            self.thread_scale = ttk.Scale(
                thread_frame,
                from_=1,
                to=128,
                variable=self.thread_count,
                orient=tk.HORIZONTAL,
                command=self.update_thread_label
            )
        self.thread_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 15))
        
        self.thread_label = ttk.Label(
            thread_frame,
            text=f"{self.optimal_threads} threads (optimal)",
            font=("Segoe UI", 10, "bold"),
            width=18
        )
        self.thread_label.pack(side=tk.RIGHT)
        
        # Checkboxes with modern styling
        check_frame = ttk.Frame(options_frame)
        check_frame.pack(fill=tk.X)
        
        if MODERN_THEME:
            self.network_check = ttk.Checkbutton(
                check_frame,
                text="🌐 Network Optimization",
                variable=self.network_optimized,
                command=self.on_network_toggle,
                bootstyle="success-round-toggle"
            )
        else:
            self.network_check = ttk.Checkbutton(
                check_frame,
                text="🌐 Network Optimization",
                variable=self.network_optimized,
                command=self.on_network_toggle
            )
        self.network_check.pack(anchor=tk.W, pady=5)
        
        if MODERN_THEME:
            self.compression_check = ttk.Checkbutton(
                check_frame,
                text="📦 Compression",
                variable=self.compression_enabled,
                command=self.on_compression_toggle,
                bootstyle="info-round-toggle"
            )
        else:
            self.compression_check = ttk.Checkbutton(
                check_frame,
                text="📦 Compression",
                variable=self.compression_enabled,
                command=self.on_compression_toggle
            )
        self.compression_check.pack(anchor=tk.W, pady=5)
        
        # Compression format selector
        format_frame = ttk.Frame(check_frame)
        format_frame.pack(anchor=tk.W, padx=30, pady=5)
        
        ttk.Label(format_frame, text="Format:").pack(side=tk.LEFT, padx=(0, 5))
        
        if MODERN_THEME:
            self.format_combo = ttk.Combobox(
                format_frame,
                textvariable=self.compression_format,
                values=[CompressionFormat.ZIP, CompressionFormat.TAR_GZ],
                state='disabled',
                width=10,
                bootstyle="info"
            )
        else:
            self.format_combo = ttk.Combobox(
                format_frame,
                textvariable=self.compression_format,
                values=[CompressionFormat.ZIP, CompressionFormat.TAR_GZ],
                state='disabled',
                width=10
            )
        self.format_combo.pack(side=tk.LEFT)
    
    def create_control_section(self, parent):
        """Create control buttons with modern styling"""
        if MODERN_THEME:
            control_frame = ttk.Frame(parent, bootstyle="dark")
        else:
            control_frame = ttk.Frame(parent)
        
        control_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Large action buttons
        button_container = ttk.Frame(control_frame)
        button_container.pack(fill=tk.X)
        
        if MODERN_THEME:
            self.start_button = ttk.Button(
                button_container,
                text="▶ Start Copy",
                command=self.start_copy,
                bootstyle="success",
                width=20
            )
        else:
            self.start_button = ttk.Button(
                button_container,
                text="▶ Start Copy",
                command=self.start_copy,
                width=20
            )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10), ipady=10)
        
        if MODERN_THEME:
            self.stop_button = ttk.Button(
                button_container,
                text="⏹ Stop",
                command=self.stop_copy,
                bootstyle="danger",
                width=15,
                state='disabled'
            )
        else:
            self.stop_button = ttk.Button(
                button_container,
                text="⏹ Stop",
                command=self.stop_copy,
                width=15,
                state='disabled'
            )
        self.stop_button.pack(side=tk.LEFT, ipady=10)
        
        # Secondary buttons
        secondary_frame = ttk.Frame(control_frame)
        secondary_frame.pack(fill=tk.X, pady=(10, 0))
        
        if MODERN_THEME:
            ttk.Button(
                secondary_frame,
                text="📊 Statistics",
                command=self.show_statistics,
                bootstyle="info-outline",
                width=15
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(
                secondary_frame,
                text="💾 Save Config",
                command=self.save_config_dialog,
                bootstyle="secondary-outline",
                width=15
            ).pack(side=tk.LEFT)
        else:
            ttk.Button(
                secondary_frame,
                text="📊 Statistics",
                command=self.show_statistics,
                width=15
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(
                secondary_frame,
                text="💾 Save Config",
                command=self.save_config_dialog,
                width=15
            ).pack(side=tk.LEFT)
    
    def create_dashboard(self, parent):
        """Create modern animated dashboard with stat cards"""
        dashboard_frame = ttk.LabelFrame(parent, text="📊 Live Dashboard")
        dashboard_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15), padx=5, ipadx=10, ipady=10)
        
        # Stat cards grid
        cards_container = ttk.Frame(dashboard_frame)
        cards_container.pack(fill=tk.BOTH, expand=True)
        
        # Top row - Speed and Files
        top_row = ttk.Frame(cards_container)
        top_row.pack(fill=tk.X, pady=(0, 10))
        
        self.speed_card = StatCard(
            top_row,
            title="Speed",
            icon="⚡",
            color="success"
        )
        self.speed_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.files_card = StatCard(
            top_row,
            title="Files",
            icon="📄",
            color="info"
        )
        self.files_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Bottom row - Data Copied and Progress
        bottom_row = ttk.Frame(cards_container)
        bottom_row.pack(fill=tk.X)
        
        self.data_card = StatCard(
            bottom_row,
            title="Data Copied",
            icon="💾",
            color="primary"
        )
        self.data_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.progress_card = StatCard(
            bottom_row,
            title="Progress",
            icon="📈",
            color="warning"
        )
        self.progress_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Animated progress bar
        progress_container = ttk.Frame(dashboard_frame)
        progress_container.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(
            progress_container,
            text="Overall Progress:",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.animated_progress = AnimatedProgressBar(progress_container)
        self.animated_progress.pack(fill=tk.X)
    
    def create_log_section(self, parent):
        """Create modern log viewer section"""
        log_frame = ttk.LabelFrame(parent, text="📋 Activity Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, ipadx=10, ipady=10)
        
        # Log control buttons at TOP
        log_button_frame = ttk.Frame(log_frame)
        log_button_frame.pack(fill=tk.X, pady=(0, 10))
        
        if MODERN_THEME:
            ttk.Button(
                log_button_frame,
                text="🗑️ Clear",
                command=self.clear_log,
                bootstyle="warning-outline",
                width=12
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(
                log_button_frame,
                text="💾 Export",
                command=self.save_log,
                bootstyle="info-outline",
                width=12
            ).pack(side=tk.LEFT)
        else:
            ttk.Button(
                log_button_frame,
                text="🗑️ Clear",
                command=self.clear_log,
                width=12
            ).pack(side=tk.LEFT, padx=(0, 10))
            
            ttk.Button(
                log_button_frame,
                text="💾 Export",
                command=self.save_log,
                width=12
            ).pack(side=tk.LEFT)
        
        # Log viewer with modern styling (now below buttons)
        self.log_viewer = ModernScrolledText(log_frame, height=15)
        self.log_viewer.pack(fill=tk.BOTH, expand=True)
    
    # Animation Methods
    
    def start_animations(self):
        """Start all UI animations"""
        self.animate_status_indicator()
    
    def animate_status_indicator(self):
        """Animate the status indicator (pulsing effect)"""
        if not self.is_running.get():
            # Ready state - green pulse
            colors = ["#28a745", "#20c997", "#28a745"]
            self.pulse_state = (self.pulse_state + 1) % len(colors)
            
            if MODERN_THEME and hasattr(self, 'status_indicator'):
                # Subtle pulse animation
                pass  # ttkbootstrap handles this
        else:
            # Running state - animated
            pass
        
        # Schedule next animation frame
        self.root.after(1000, self.animate_status_indicator)
    
    # Event Handlers
    
    def browse_source(self):
        """Browse for source directory with animation"""
        # Use enhanced device picker
        from gui.device_picker import show_device_picker
        path = show_device_picker(self.root, "Select Source Device", "source")
        if path:
            self.source_path.set(path)
            self.log_message(f"✅ Source selected: {path}")
            self.check_network_path()
        return
        
        # OLD CODE - Fallback if device picker fails
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Source")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create tabs for local and network
        if MODERN_THEME:
            notebook = ttk.Notebook(dialog, bootstyle="primary")
        else:
            notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Local tab
        local_frame = ttk.Frame(notebook)
        notebook.add(local_frame, text="📁 Local Drives")
        
        ttk.Label(local_frame, text="Select from local drives:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        if MODERN_THEME:
            browse_btn = ttk.Button(local_frame, text="Browse Local Folders", 
                                   command=lambda: self._select_local_path(dialog, "source"),
                                   bootstyle="primary", width=30)
        else:
            browse_btn = ttk.Button(local_frame, text="Browse Local Folders",
                                   command=lambda: self._select_local_path(dialog, "source"),
                                   width=30)
        browse_btn.pack(pady=10)
        
        # Network tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="🌐 Network Devices")
        
        ttk.Label(network_frame, text="Enter network path:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # UNC path entry
        unc_frame = ttk.Frame(network_frame)
        unc_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(unc_frame, text="UNC Path:").pack(anchor=tk.W)
        unc_entry = ttk.Entry(unc_frame, width=50)
        unc_entry.pack(fill=tk.X, pady=5)
        unc_entry.insert(0, "\\\\")
        
        ttk.Label(network_frame, text="Examples:", font=("Segoe UI", 9)).pack(pady=(10, 5))
        examples_text = (
            "• \\\\192.168.1.100\\SharedFolder\n"
            "• \\\\DESKTOP-PC\\Users\\Public\n"
            "• \\\\NAS-Device\\Backup\n"
            "• \\\\server\\share$"
        )
        ttk.Label(network_frame, text=examples_text, justify=tk.LEFT).pack()
        
        if MODERN_THEME:
            connect_btn = ttk.Button(network_frame, text="Connect to Network Path",
                                    command=lambda: self._select_network_path(dialog, unc_entry.get(), "source"),
                                    bootstyle="success", width=30)
        else:
            connect_btn = ttk.Button(network_frame, text="Connect to Network Path",
                                    command=lambda: self._select_network_path(dialog, unc_entry.get(), "source"),
                                    width=30)
        connect_btn.pack(pady=20)
        
        # USB/External devices
        usb_frame = ttk.Frame(notebook)
        notebook.add(usb_frame, text="💾 USB/External")
        
        ttk.Label(usb_frame, text="Available drives:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # List available drives
        drives = self._get_available_drives()
        for drive in drives:
            drive_btn = ttk.Button(usb_frame, text=f"{drive['letter']} - {drive['label']} ({drive['size']})",
                                  command=lambda d=drive['letter']: self._select_drive(dialog, d, "source"),
                                  width=40)
            drive_btn.pack(pady=5)
    
    def _select_local_path(self, dialog, path_type):
        """Select local path via file dialog"""
        path = filedialog.askdirectory(title="Select Directory")
        if path:
            dialog.destroy()
            if path_type == "source":
                self.source_path.set(path)
                self.log_message(f"✅ Source selected: {path}")
            else:
                self.dest_path.set(path)
                self.log_message(f"✅ Destination selected: {path}")
            self.check_network_path()
    
    def _select_network_path(self, dialog, unc_path, path_type):
        """Select network UNC path"""
        if not unc_path or unc_path == "\\\\":
            messagebox.showwarning("Invalid Path", "Please enter a valid UNC path")
            return
        
        # Validate UNC path format
        if not (unc_path.startswith("\\\\") or unc_path.startswith("//")):
            messagebox.showwarning("Invalid Format", "Network path must start with \\\\ or //")
            return
        
        dialog.destroy()
        if path_type == "source":
            self.source_path.set(unc_path)
            self.log_message(f"✅ Source selected: {unc_path}")
        else:
            self.dest_path.set(unc_path)
            self.log_message(f"✅ Destination selected: {unc_path}")
        self.check_network_path()
    
    def _select_drive(self, dialog, drive_letter, path_type):
        """Select a specific drive"""
        path = f"{drive_letter}:\\"
        dialog.destroy()
        if path_type == "source":
            self.source_path.set(path)
            self.log_message(f"✅ Source selected: {path}")
        else:
            self.dest_path.set(path)
            self.log_message(f"✅ Destination selected: {path}")
        self.check_network_path()
    
    def _get_available_drives(self):
        """Get list of available drives with info"""
        drives = []
        try:
            import string
            for letter in string.ascii_uppercase:
                drive_path = f"{letter}:\\"
                if os.path.exists(drive_path):
                    try:
                        usage = psutil.disk_usage(drive_path)
                        partitions = psutil.disk_partitions()
                        label = "Local Disk"
                        for partition in partitions:
                            if partition.device.startswith(letter):
                                label = partition.opts if partition.opts else "Local Disk"
                                break
                        
                        size = self.format_bytes(usage.total)
                        free = self.format_bytes(usage.free)
                        
                        drives.append({
                            'letter': letter,
                            'label': label[:20],
                            'size': f"{size} total, {free} free"
                        })
                    except:
                        pass
        except:
            pass
        return drives
    
    def browse_destination(self):
        """Browse for destination directory"""
        # Use enhanced device picker
        from gui.device_picker import show_device_picker
        path = show_device_picker(self.root, "Select Destination Device", "destination")
        if path:
            self.dest_path.set(path)
            self.log_message(f"✅ Destination selected: {path}")
            self.check_network_path()
        return
        
        # OLD CODE - Fallback if device picker fails
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Destination")
        dialog.geometry("600x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Create tabs for local and network
        if MODERN_THEME:
            notebook = ttk.Notebook(dialog, bootstyle="primary")
        else:
            notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Local tab
        local_frame = ttk.Frame(notebook)
        notebook.add(local_frame, text="📁 Local Drives")
        
        ttk.Label(local_frame, text="Select from local drives:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        if MODERN_THEME:
            browse_btn = ttk.Button(local_frame, text="Browse Local Folders",
                                   command=lambda: self._select_local_path(dialog, "dest"),
                                   bootstyle="primary", width=30)
        else:
            browse_btn = ttk.Button(local_frame, text="Browse Local Folders",
                                   command=lambda: self._select_local_path(dialog, "dest"),
                                   width=30)
        browse_btn.pack(pady=10)
        
        # Network tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="🌐 Network Devices")
        
        ttk.Label(network_frame, text="Enter network path:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # UNC path entry
        unc_frame = ttk.Frame(network_frame)
        unc_frame.pack(pady=10, padx=20, fill=tk.X)
        
        ttk.Label(unc_frame, text="UNC Path:").pack(anchor=tk.W)
        unc_entry = ttk.Entry(unc_frame, width=50)
        unc_entry.pack(fill=tk.X, pady=5)
        unc_entry.insert(0, "\\\\")
        
        ttk.Label(network_frame, text="Examples:", font=("Segoe UI", 9)).pack(pady=(10, 5))
        examples_text = (
            "• \\\\192.168.1.100\\SharedFolder\n"
            "• \\\\PHONE-NAME\\Internal Storage\n"
            "• \\\\TABLET-PC\\SDCard\n"
            "• \\\\NAS\\Backup"
        )
        ttk.Label(network_frame, text=examples_text, justify=tk.LEFT).pack()
        
        if MODERN_THEME:
            connect_btn = ttk.Button(network_frame, text="Connect to Network Path",
                                    command=lambda: self._select_network_path(dialog, unc_entry.get(), "dest"),
                                    bootstyle="success", width=30)
        else:
            connect_btn = ttk.Button(network_frame, text="Connect to Network Path",
                                    command=lambda: self._select_network_path(dialog, unc_entry.get(), "dest"),
                                    width=30)
        connect_btn.pack(pady=20)
        
        # USB/External devices
        usb_frame = ttk.Frame(notebook)
        notebook.add(usb_frame, text="💾 USB/External")
        
        ttk.Label(usb_frame, text="Available drives:", font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        # List available drives
        drives = self._get_available_drives()
        for drive in drives:
            drive_btn = ttk.Button(usb_frame, text=f"{drive['letter']} - {drive['label']} ({drive['size']})",
                                  command=lambda d=drive['letter']: self._select_drive(dialog, d, "dest"),
                                  width=40)
            drive_btn.pack(pady=5)
    
    def check_network_path(self):
        """Auto-detect network paths and suggest optimization"""
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            return
        
        optimizer = NetworkOptimizer()
        params = optimizer.get_optimized_parameters(source, dest)
        
        if params['network_optimized']:
            self.network_optimized.set(True)
            
            # Only adjust threads if auto mode is enabled
            if self.auto_thread_adjust.get():
                self.auto_adjust_threads()
            
            reasons = ', '.join(params['optimization_reason'])
            self.log_message(f"🌐 Network path detected: {reasons}")
            self.log_message(f"⚙️ Auto-enabled network optimization")
    
    def update_thread_label(self, value):
        """Update thread count label"""
        count = int(float(value))
        
        # Show if it's optimal or manual
        if self.auto_thread_adjust.get():
            if count == self.optimal_threads:
                self.thread_label.config(text=f"{count} threads (optimal)")
            else:
                self.thread_label.config(text=f"{count} threads (manual)")
        else:
            self.thread_label.config(text=f"{count} threads (manual)")
    
    def on_auto_thread_toggle(self):
        """Handle auto thread adjustment toggle"""
        if self.auto_thread_adjust.get():
            # Auto mode - adjust based on paths
            self.log_message("🔧 Auto thread adjustment enabled")
            self.auto_adjust_threads()
        else:
            # Manual mode
            self.log_message("🔧 Manual thread adjustment mode")
            self.update_thread_label(self.thread_count.get())
    
    def auto_adjust_threads(self):
        """Automatically adjust thread count based on operation type"""
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            # Default to optimal
            self.thread_count.set(self.optimal_threads)
            self.update_thread_label(self.optimal_threads)
            return
        
        try:
            # Check if network paths
            optimizer = NetworkOptimizer()
            source_is_network = optimizer.is_network_path(source)
            dest_is_network = optimizer.is_network_path(dest)
            
            # Get base optimal threads
            optimal = self.optimal_threads
            
            # Adjust based on scenario
            if source_is_network or dest_is_network:
                # Network transfer - moderate threads
                if source_is_network and dest_is_network:
                    # Network to network - lower threads
                    recommended = max(8, optimal // 2)
                    reason = "Network-to-network transfer"
                else:
                    # One network - balanced
                    recommended = min(16, optimal)
                    reason = "Network transfer"
            else:
                # Local to local - use full optimal
                recommended = optimal
                reason = "Local transfer"
            
            # Set the thread count
            self.thread_count.set(recommended)
            self.update_thread_label(recommended)
            
            self.log_message(f"🔧 Auto-adjusted threads to {recommended} ({reason})")
            
        except Exception as e:
            # Fallback to optimal
            self.thread_count.set(self.optimal_threads)
            self.update_thread_label(self.optimal_threads)
    
    def on_network_toggle(self):
        """Handle network optimization toggle"""
        if self.network_optimized.get():
            self.log_message("🌐 Network optimization enabled")
        else:
            self.log_message("🌐 Network optimization disabled")
    
    def on_compression_toggle(self):
        """Handle compression toggle"""
        if self.compression_enabled.get():
            self.format_combo.config(state='readonly')
            self.log_message("📦 Compression enabled")
        else:
            self.format_combo.config(state='disabled')
            self.log_message("📦 Compression disabled")
    
    def start_copy(self):
        """Start the copy operation with animations"""
        # Validate inputs
        source = self.source_path.get()
        dest = self.dest_path.get()
        
        if not source or not dest:
            messagebox.showerror("Error", "Please select both source and destination paths")
            return
        
        # Validate source path (with MTP support)
        if not self._validate_path(source):
            messagebox.showerror("Error", f"Source path does not exist:\n{source}")
            return
        
        # Confirm mirror mode
        if self.copy_mode.get() == RobocopyMode.MIRROR:
            response = messagebox.askyesno(
                "⚠️ Confirm Mirror Mode",
                "Mirror mode will DELETE files in destination that don't exist in source.\n\n"
                "This operation cannot be undone!\n\n"
                "Are you sure you want to continue?",
                icon='warning'
            )
            if not response:
                return
        
        # Update UI state
        self.is_running.set(True)
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        if hasattr(self, 'status_indicator'):
            self.status_indicator.config(text="● Running")
            if MODERN_THEME:
                self.status_indicator.configure(bootstyle="warning")
        
        # Reset progress
        self.animated_progress.set_value(0)
        self.speed_card.set_value(0, " MB/s")
        self.files_card.set_value(0, "")
        self.data_card.set_value("0 B")
        self.progress_card.set_value(0, "%")
        
        self.log_message("🚀 Starting copy operation...")
        self.log_message(f"📂 Source: {source}")
        self.log_message(f"📂 Destination: {dest}")
        self.log_message(f"⚙️ Mode: {self.copy_mode.get()}")
        self.log_message(f"🔧 Threads: {self.thread_count.get()}")
        
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
    
    def stop_copy(self):
        """Stop the running copy operation"""
        response = messagebox.askyesno(
            "Confirm Stop",
            "Are you sure you want to stop the operation?\n\n"
            "Progress may be lost."
        )
        if response:
            self.log_message("⏸️ Stopping operation...")
            self.robocopy_engine.cancel()
            self.compression_engine.cancel()
    
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
                self.log_message("📦 Starting compression phase...")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = f"backup_{timestamp}.{self.compression_format.get()}"
                archive_path = os.path.join(os.path.dirname(dest), archive_name)
                
                self.compression_engine.compress_async(
                    source_path=source,
                    output_file=archive_path,
                    format=self.compression_format.get(),
                    compression_level=6
                )
                
                self.compression_engine.wait_for_completion()
                
                if not os.path.exists(archive_path):
                    raise Exception("Compression failed")
                
                self.log_message("✅ Compression completed successfully")
                
                source = archive_path
                dest = os.path.join(dest, archive_name)
                self.log_message(f"📦 Copying compressed archive...")
            
            # Build robocopy command
            os.makedirs(dest, exist_ok=True)
            
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
            
            self.log_message("✅ Operation completed successfully")
            
        except Exception as e:
            self.log_message(f"❌ Error: {str(e)}")
            self.speed_monitor.end_session(success=False)
        finally:
            self.root.after(0, self._operation_completed)
    
    def _operation_completed(self):
        """Called when operation completes (runs in main thread)"""
        self.is_running.set(False)
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        
        if hasattr(self, 'status_indicator'):
            self.status_indicator.config(text="● Ready")
            if MODERN_THEME:
                self.status_indicator.configure(bootstyle="success")
        
        self.animated_progress.set_value(100)
    
    def update_progress(self, stats):
        """Update progress display with smooth animations"""
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
        # Animate stat cards
        self.speed_card.set_value(stats['speed_mbps'], " MB/s")
        self.files_card.set_value(stats['files_copied'], "")
        self.data_card.set_value(self.format_bytes(stats['bytes_copied']))
        
        # Update progress bar with animation
        if stats['files_copied'] > 0:
            current_progress = min(95, self.animated_progress.current_value + 0.5)
            self.animated_progress.set_value(current_progress)
            self.progress_card.set_value(int(current_progress), "%")
    
    def update_compression_progress(self, stats):
        """Update progress from compression engine"""
        self.root.after(0, self._update_compression_ui, stats)
    
    def _update_compression_ui(self, stats):
        """Update UI with compression progress"""
        if stats['total_files'] > 0:
            percent = (stats['processed_files'] / stats['total_files']) * 100
            self.animated_progress.set_value(percent)
            self.progress_card.set_value(int(percent), "%")
        
        self.files_card.set_value(stats['processed_files'], f" / {stats['total_files']}")
        self.data_card.set_value(self.format_bytes(stats['total_bytes']))
    
    def show_statistics(self):
        """Show statistics window with modern design"""
        stats_window = tk.Toplevel(self.root)
        stats_window.title("📊 Transfer Statistics")
        stats_window.geometry("900x700")
        
        if MODERN_THEME:
            # Apply same theme to popup
            pass
        
        # Create notebook for tabs
        if MODERN_THEME:
            notebook = ttk.Notebook(stats_window, bootstyle="info")
        else:
            notebook = ttk.Notebook(stats_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Summary tab
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="📈 Summary")
        summary_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        summary = self.speed_monitor.get_summary_stats()
        
        # Create summary cards
        summary_cards = ttk.Frame(summary_frame)
        summary_cards.pack(fill=tk.X, pady=(0, 20))
        
        # Sessions card
        sessions_card = StatCard(summary_cards, "Total Sessions", "📊", "primary")
        sessions_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        sessions_card.set_value(summary['total_sessions'], "")
        
        # Success rate card
        if summary['total_sessions'] > 0:
            success_rate = (summary['successful_sessions'] / summary['total_sessions']) * 100
        else:
            success_rate = 0
        
        rate_card = StatCard(summary_cards, "Success Rate", "✅", "success")
        rate_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        rate_card.set_value(success_rate, "%")
        
        # Data transferred card
        data_card = StatCard(summary_cards, "Total Data", "💾", "info")
        data_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        data_card.set_value(self.format_bytes(summary['total_bytes_transferred']))
        
        # Detailed info
        info_text = ModernScrolledText(summary_frame, height=15)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        info_text.insert_colored("=== Transfer Statistics Summary ===\n\n")
        info_text.insert_colored(f"Total Sessions: {summary['total_sessions']}\n")
        info_text.insert_colored(f"Successful: {summary['successful_sessions']}\n")
        info_text.insert_colored(f"Failed: {summary['failed_sessions']}\n\n")
        info_text.insert_colored(f"Total Data Transferred: {self.format_bytes(summary['total_bytes_transferred'])}\n")
        info_text.insert_colored(f"Total Files Transferred: {summary['total_files_transferred']:,}\n\n")
        info_text.insert_colored(f"Average Speed: {summary['average_speed_mbps']:.2f} MB/s\n")
        info_text.insert_colored(f"Peak Speed: {summary['peak_speed_mbps']:.2f} MB/s\n")
        
        # History tab
        history_frame = ttk.Frame(notebook)
        notebook.add(history_frame, text="📜 History")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Create treeview for history
        columns = ('Session', 'Type', 'Files', 'Size', 'Speed', 'Status')
        
        if MODERN_THEME:
            tree = ttk.Treeview(
                history_frame,
                columns=columns,
                show='headings',
                height=15,
                bootstyle="info"
            )
        else:
            tree = ttk.Treeview(
                history_frame,
                columns=columns,
                show='headings',
                height=15
            )
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140)
        
        history = self.speed_monitor.get_history(limit=50)
        for entry in reversed(history):
            status_icon = '✅' if entry['success'] else '❌'
            tree.insert('', tk.END, values=(
                entry['session_id'][-12:],
                entry['operation_type'],
                f"{entry['total_files']:,}",
                self.format_bytes(entry['total_bytes']),
                f"{entry['average_speed_mbps']:.2f} MB/s",
                f"{status_icon} {'Success' if entry['success'] else 'Failed'}"
            ))
        
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        if MODERN_THEME:
            scrollbar = ttk.Scrollbar(
                history_frame,
                orient=tk.VERTICAL,
                command=tree.yview,
                bootstyle="round"
            )
        else:
            scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=tree.yview)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)
    
    # Logging
    
    def log_message(self, message):
        """Log a message with emoji and color coding"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # Update UI in main thread
        self.root.after(0, self._append_log, log_entry)
        
        # Write to file
        self._write_to_log_file(log_entry)
    
    def _append_log(self, message):
        """Append message to log viewer (main thread only)"""
        if hasattr(self, 'log_viewer'):
            self.log_viewer.insert_colored(message)
    
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
        if hasattr(self, 'log_viewer'):
            self.log_viewer.clear()
            self.log_message("🗑️ Log cleared")
    
    def save_log(self):
        """Save log to file"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=f"ultraspeed_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        if filename:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.log_viewer.get_content())
            self.log_message(f"💾 Log exported to: {filename}")
    
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
            'default_threads': 16,
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
            self.log_message("💾 Configuration saved")
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration:\n{str(e)}")
    
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
        if isinstance(bytes_val, str):
            return bytes_val
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


def main():
    """Main entry point for modern GUI"""
    if MODERN_THEME:
        root = ttk.Window(themename="darkly")
    else:
        root = tk.Tk()
        print("\n" + "="*60)
        print("NOTICE: Running in standard mode")
        print("For the best experience, install ttkbootstrap:")
        print("  pip install ttkbootstrap")
        print("="*60 + "\n")
    
    app = UltraSpeedModernGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
