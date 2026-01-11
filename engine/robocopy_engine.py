"""
UltraSpeed Copy - Robocopy Engine Module
Handles all robocopy command construction and execution
"""

import subprocess
import threading
import re
import os
import time
from datetime import datetime
from typing import Callable, Optional, Dict, List


class RobocopyMode:
    """Copy mode constants"""
    FULL_COPY = "full"
    INCREMENTAL = "incremental"
    MIRROR = "mirror"


class RobocopyEngine:
    """
    High-performance file copy engine using Windows ROBOCOPY
    Supports multi-threaded operations, network optimization, and real-time monitoring
    """
    
    def __init__(self, log_callback: Optional[Callable] = None, 
                 progress_callback: Optional[Callable] = None):
        """
        Initialize the robocopy engine
        
        Args:
            log_callback: Function to call with log messages
            progress_callback: Function to call with progress updates (speed, files, etc.)
        """
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.process = None
        self.is_running = False
        self.is_cancelled = False
        self.thread = None
        
        # Statistics
        self.stats = {
            'files_copied': 0,
            'bytes_copied': 0,
            'speed_mbps': 0.0,
            'start_time': None,
            'end_time': None,
            'errors': 0,
            'current_file': ''
        }
    
    def build_command(self, source: str, destination: str, mode: str,
                     threads: int = 8, network_optimized: bool = False,
                     exclude_dirs: Optional[List[str]] = None,
                     exclude_files: Optional[List[str]] = None,
                     custom_options: Optional[List[str]] = None) -> List[str]:
        """
        Build robocopy command with specified parameters
        
        Args:
            source: Source directory path
            destination: Destination directory path
            mode: Copy mode (full, incremental, mirror)
            threads: Number of threads for multi-threaded copy
            network_optimized: Enable network optimization flags
            exclude_dirs: List of directory names to exclude
            exclude_files: List of file patterns to exclude
            custom_options: Additional custom robocopy options
            
        Returns:
            List of command arguments
        """
        cmd = ['robocopy', source, destination]
        
        # Base options - copy all subdirectories including empty ones
        cmd.extend(['/E'])  # Copy subdirectories including empty ones
        
        # Mode-specific options
        if mode == RobocopyMode.MIRROR:
            # Mirror mode - make destination identical to source
            cmd.append('/MIR')
            self._log("Mode: MIRROR - Destination will match source exactly")
        elif mode == RobocopyMode.INCREMENTAL:
            # Incremental - only copy newer/changed files
            cmd.extend(['/XO'])  # Exclude older files
            self._log("Mode: INCREMENTAL - Only newer/changed files")
        else:
            # Full copy mode
            self._log("Mode: FULL COPY - Copy all files")
        
        # Multi-threading
        if threads > 1:
            cmd.extend(['/MT:{}'.format(threads)])
            self._log(f"Multi-threading enabled: {threads} threads")
        
        # Network optimization
        if network_optimized:
            cmd.extend([
                '/Z',      # Restartable mode (for interrupted network transfers)
                '/ZB',     # Use restartable mode; if access denied, use backup mode
                '/R:3',    # Retry 3 times on failed copies
                '/W:5',    # Wait 5 seconds between retries
                '/NP',     # No progress - don't show percentage (cleaner output)
            ])
            self._log("Network optimization enabled")
        else:
            cmd.extend([
                '/R:1',    # Retry once
                '/W:3',    # Wait 3 seconds
                '/NP',     # No progress
            ])
        
        # Copy options
        cmd.extend([
            '/COPY:DAT',   # Copy Data, Attributes, Timestamps (no admin rights required)
            '/DCOPY:DAT',  # Copy directory timestamps and attributes
            '/V',          # Verbose output
            '/ETA',        # Show estimated time of completion
        ])
        
        # Logging and output
        cmd.extend([
            '/TEE',        # Output to console and log file
            '/BYTES',      # Print sizes in bytes
            '/TS',         # Include source file timestamps
            '/FP',         # Include full pathname in output
        ])
        
        # Exclude directories
        if exclude_dirs:
            for exdir in exclude_dirs:
                cmd.extend(['/XD', exdir])
        
        # Exclude files
        if exclude_files:
            for exfile in exclude_files:
                cmd.extend(['/XF', exfile])
        
        # Custom options
        if custom_options:
            cmd.extend(custom_options)
        
        self._log(f"Command built: {' '.join(cmd)}")
        return cmd
    
    def execute(self, command: List[str], log_file: Optional[str] = None) -> bool:
        """
        Execute robocopy command asynchronously
        
        Args:
            command: Robocopy command as list of arguments
            log_file: Optional log file path
            
        Returns:
            True if execution started successfully
        """
        if self.is_running:
            self._log("Error: Copy operation already in progress")
            return False
        
        # Add log file to command if specified
        if log_file:
            command.extend(['/LOG+:{}'.format(log_file)])
        
        self.is_running = True
        self.is_cancelled = False
        self.stats['start_time'] = datetime.now()
        self.stats['files_copied'] = 0
        self.stats['bytes_copied'] = 0
        self.stats['errors'] = 0
        
        # Start execution in separate thread
        self.thread = threading.Thread(target=self._execute_thread, args=(command,))
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def _execute_thread(self, command: List[str]):
        """
        Internal thread function to execute robocopy
        
        Args:
            command: Robocopy command as list of arguments
        """
        try:
            self._log("Starting robocopy operation...")
            self._log(f"Command: {' '.join(command)}")
            
            # Create subprocess with pipe for output
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            )
            
            # Read output line by line
            for line in self.process.stdout:
                if self.is_cancelled:
                    self._log("Cancellation requested, terminating process...")
                    self.process.terminate()
                    break
                
                line = line.strip()
                if line:
                    self._log(line)
                    self._parse_output(line)
            
            # Wait for process to complete
            return_code = self.process.wait()
            
            self.stats['end_time'] = datetime.now()
            
            # Interpret return code
            # Robocopy return codes: 0-7 are success, 8+ are errors
            if return_code < 8:
                self._log(f"Copy operation completed successfully (code: {return_code})")
                self._log(f"Files copied: {self.stats['files_copied']}")
                self._log(f"Bytes copied: {self._format_bytes(self.stats['bytes_copied'])}")
                if self.stats['start_time'] and self.stats['end_time']:
                    duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
                    self._log(f"Duration: {duration:.2f} seconds")
            else:
                self._log(f"Copy operation failed with code: {return_code}")
                self.stats['errors'] += 1
            
        except Exception as e:
            self._log(f"Error executing robocopy: {str(e)}")
            self.stats['errors'] += 1
        finally:
            self.is_running = False
            self.process = None
    
    def _parse_output(self, line: str):
        """
        Parse robocopy output to extract statistics
        
        Args:
            line: Output line from robocopy
        """
        # Parse copied file information
        # Example: "  New File       123456   C:\source\file.txt"
        if 'New File' in line or 'Newer' in line or 'Older' in line:
            # Extract file size (in bytes)
            size_match = re.search(r'\s+(\d+)\s+', line)
            if size_match:
                size = int(size_match.group(1))
                self.stats['bytes_copied'] += size
                self.stats['files_copied'] += 1
            
            # Extract filename
            file_match = re.search(r'\s+[A-Za-z\s]+\s+\d+\s+(.+)$', line)
            if file_match:
                self.stats['current_file'] = file_match.group(1)
        
        # Parse speed information
        # Example: "Speed : 12345678 Bytes/sec"
        speed_match = re.search(r'Speed\s*:\s*(\d+)\s*Bytes/sec', line)
        if speed_match:
            bytes_per_sec = int(speed_match.group(1))
            mb_per_sec = bytes_per_sec / (1024 * 1024)
            self.stats['speed_mbps'] = mb_per_sec
        
        # Parse total statistics
        # Example: "Files : 123 0 0 0 0 0"
        files_match = re.search(r'Files\s*:\s*(\d+)', line)
        if files_match and 'Total' not in line:
            self.stats['files_copied'] = int(files_match.group(1))
        
        # Parse bytes statistics
        # Example: "Bytes : 123456789 0 0 0 0 0"
        bytes_match = re.search(r'Bytes\s*:\s*(\d+)', line)
        if bytes_match and 'Total' not in line:
            self.stats['bytes_copied'] = int(bytes_match.group(1))
        
        # Error detection
        if 'ERROR' in line.upper():
            self.stats['errors'] += 1
        
        # Update progress callback
        if self.progress_callback:
            self.progress_callback(self.stats.copy())
    
    def cancel(self):
        """Cancel the running copy operation"""
        if self.is_running and self.process:
            self._log("Cancelling copy operation...")
            self.is_cancelled = True
            try:
                self.process.terminate()
            except:
                pass
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """
        Wait for copy operation to complete
        
        Args:
            timeout: Maximum time to wait in seconds (None = wait forever)
            
        Returns:
            True if completed, False if timeout
        """
        if self.thread:
            self.thread.join(timeout)
            return not self.thread.is_alive()
        return True
    
    def get_stats(self) -> Dict:
        """Get current statistics"""
        return self.stats.copy()
    
    def _log(self, message: str):
        """Internal logging function"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}"
        
        if self.log_callback:
            self.log_callback(log_message)
    
    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"


def test_robocopy_engine():
    """Test function for robocopy engine"""
    def log_handler(message):
        print(message)
    
    def progress_handler(stats):
        print(f"Progress: {stats['files_copied']} files, "
              f"{stats['bytes_copied']} bytes, "
              f"{stats['speed_mbps']:.2f} MB/s")
    
    engine = RobocopyEngine(log_callback=log_handler, progress_callback=progress_handler)
    
    # Example command build
    cmd = engine.build_command(
        source="C:\\Source",
        destination="D:\\Backup",
        mode=RobocopyMode.INCREMENTAL,
        threads=16,
        network_optimized=False
    )
    
    print("Built command:", ' '.join(cmd))


if __name__ == '__main__':
    test_robocopy_engine()
