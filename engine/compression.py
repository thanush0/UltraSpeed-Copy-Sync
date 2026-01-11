"""
UltraSpeed Copy - Compression Module
Handles file compression before transfer (ZIP, TAR.GZ)
"""

import os
import zipfile
import tarfile
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional, List


class CompressionFormat:
    """Compression format constants"""
    ZIP = "zip"
    TAR_GZ = "tar.gz"
    TAR = "tar"


class CompressionEngine:
    """
    Handles compression and decompression of files and directories
    Optimized for large file transfers
    """
    
    def __init__(self, log_callback: Optional[Callable] = None,
                 progress_callback: Optional[Callable] = None):
        """
        Initialize compression engine
        
        Args:
            log_callback: Function to call with log messages
            progress_callback: Function to call with progress updates
        """
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.is_running = False
        self.is_cancelled = False
        self.thread = None
        
        # Statistics
        self.stats = {
            'total_files': 0,
            'processed_files': 0,
            'total_bytes': 0,
            'compressed_bytes': 0,
            'compression_ratio': 0.0,
            'start_time': None,
            'end_time': None
        }
    
    def compress_async(self, source_path: str, output_file: str,
                      format: str = CompressionFormat.ZIP,
                      compression_level: int = 6,
                      exclude_patterns: Optional[List[str]] = None) -> bool:
        """
        Compress directory or file asynchronously
        
        Args:
            source_path: Path to compress (file or directory)
            output_file: Output archive file path
            format: Compression format (zip, tar.gz, tar)
            compression_level: Compression level (0-9, higher = better compression)
            exclude_patterns: List of patterns to exclude
            
        Returns:
            True if compression started successfully
        """
        if self.is_running:
            self._log("Error: Compression already in progress")
            return False
        
        self.is_running = True
        self.is_cancelled = False
        
        # Start compression in separate thread
        self.thread = threading.Thread(
            target=self._compress_thread,
            args=(source_path, output_file, format, compression_level, exclude_patterns)
        )
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def _compress_thread(self, source_path: str, output_file: str,
                        format: str, compression_level: int,
                        exclude_patterns: Optional[List[str]]):
        """
        Internal thread function for compression
        
        Args:
            source_path: Path to compress
            output_file: Output archive file
            format: Compression format
            compression_level: Compression level
            exclude_patterns: Patterns to exclude
        """
        try:
            self.stats['start_time'] = datetime.now()
            self.stats['total_files'] = 0
            self.stats['processed_files'] = 0
            self.stats['total_bytes'] = 0
            self.stats['compressed_bytes'] = 0
            
            source_path = os.path.abspath(source_path)
            output_file = os.path.abspath(output_file)
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            
            self._log(f"Starting compression: {source_path}")
            self._log(f"Output file: {output_file}")
            self._log(f"Format: {format}")
            
            # Count total files first
            if os.path.isdir(source_path):
                self.stats['total_files'] = self._count_files(source_path, exclude_patterns)
                self._log(f"Total files to compress: {self.stats['total_files']}")
            else:
                self.stats['total_files'] = 1
            
            # Perform compression based on format
            if format == CompressionFormat.ZIP:
                self._compress_zip(source_path, output_file, compression_level, exclude_patterns)
            elif format == CompressionFormat.TAR_GZ:
                self._compress_tar(source_path, output_file, 'gz', compression_level, exclude_patterns)
            elif format == CompressionFormat.TAR:
                self._compress_tar(source_path, output_file, None, compression_level, exclude_patterns)
            else:
                raise ValueError(f"Unsupported compression format: {format}")
            
            self.stats['end_time'] = datetime.now()
            self.stats['compressed_bytes'] = os.path.getsize(output_file)
            
            if self.stats['total_bytes'] > 0:
                self.stats['compression_ratio'] = (
                    (1 - self.stats['compressed_bytes'] / self.stats['total_bytes']) * 100
                )
            
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            self._log(f"Compression completed successfully")
            self._log(f"Files compressed: {self.stats['processed_files']}")
            self._log(f"Original size: {self._format_bytes(self.stats['total_bytes'])}")
            self._log(f"Compressed size: {self._format_bytes(self.stats['compressed_bytes'])}")
            self._log(f"Compression ratio: {self.stats['compression_ratio']:.2f}%")
            self._log(f"Duration: {duration:.2f} seconds")
            
        except Exception as e:
            self._log(f"Error during compression: {str(e)}")
        finally:
            self.is_running = False
    
    def _compress_zip(self, source_path: str, output_file: str,
                     compression_level: int, exclude_patterns: Optional[List[str]]):
        """
        Compress using ZIP format
        
        Args:
            source_path: Path to compress
            output_file: Output ZIP file
            compression_level: Compression level (0-9)
            exclude_patterns: Patterns to exclude
        """
        # Map compression level to zipfile constants
        compression_type = zipfile.ZIP_DEFLATED
        
        with zipfile.ZipFile(output_file, 'w', compression_type, compresslevel=compression_level) as zipf:
            if os.path.isfile(source_path):
                # Single file
                self._add_file_to_zip(zipf, source_path, os.path.basename(source_path))
            else:
                # Directory
                base_path = Path(source_path)
                for root, dirs, files in os.walk(source_path):
                    if self.is_cancelled:
                        self._log("Compression cancelled")
                        break
                    
                    # Filter directories
                    if exclude_patterns:
                        dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
                    
                    for file in files:
                        if self.is_cancelled:
                            break
                        
                        if exclude_patterns and self._should_exclude(file, exclude_patterns):
                            continue
                        
                        file_path = os.path.join(root, file)
                        arcname = str(Path(file_path).relative_to(base_path.parent))
                        self._add_file_to_zip(zipf, file_path, arcname)
    
    def _add_file_to_zip(self, zipf: zipfile.ZipFile, file_path: str, arcname: str):
        """Add a single file to ZIP archive"""
        try:
            file_size = os.path.getsize(file_path)
            self.stats['total_bytes'] += file_size
            
            zipf.write(file_path, arcname)
            
            self.stats['processed_files'] += 1
            self._log(f"Compressed: {arcname}")
            
            if self.progress_callback:
                self.progress_callback(self.stats.copy())
                
        except Exception as e:
            self._log(f"Error compressing {file_path}: {str(e)}")
    
    def _compress_tar(self, source_path: str, output_file: str,
                     compression: Optional[str], compression_level: int,
                     exclude_patterns: Optional[List[str]]):
        """
        Compress using TAR format (with optional gzip)
        
        Args:
            source_path: Path to compress
            output_file: Output TAR file
            compression: Compression type ('gz' or None)
            compression_level: Compression level
            exclude_patterns: Patterns to exclude
        """
        mode = 'w:gz' if compression == 'gz' else 'w'
        
        with tarfile.open(output_file, mode) as tarf:
            if os.path.isfile(source_path):
                # Single file
                self._add_file_to_tar(tarf, source_path, os.path.basename(source_path))
            else:
                # Directory
                base_path = Path(source_path)
                for root, dirs, files in os.walk(source_path):
                    if self.is_cancelled:
                        self._log("Compression cancelled")
                        break
                    
                    # Filter directories
                    if exclude_patterns:
                        dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
                    
                    for file in files:
                        if self.is_cancelled:
                            break
                        
                        if exclude_patterns and self._should_exclude(file, exclude_patterns):
                            continue
                        
                        file_path = os.path.join(root, file)
                        arcname = str(Path(file_path).relative_to(base_path.parent))
                        self._add_file_to_tar(tarf, file_path, arcname)
    
    def _add_file_to_tar(self, tarf: tarfile.TarFile, file_path: str, arcname: str):
        """Add a single file to TAR archive"""
        try:
            file_size = os.path.getsize(file_path)
            self.stats['total_bytes'] += file_size
            
            tarf.add(file_path, arcname=arcname)
            
            self.stats['processed_files'] += 1
            self._log(f"Compressed: {arcname}")
            
            if self.progress_callback:
                self.progress_callback(self.stats.copy())
                
        except Exception as e:
            self._log(f"Error compressing {file_path}: {str(e)}")
    
    def decompress_async(self, archive_file: str, output_dir: str,
                        format: Optional[str] = None) -> bool:
        """
        Decompress archive asynchronously
        
        Args:
            archive_file: Archive file to decompress
            output_dir: Output directory
            format: Archive format (auto-detect if None)
            
        Returns:
            True if decompression started successfully
        """
        if self.is_running:
            self._log("Error: Decompression already in progress")
            return False
        
        self.is_running = True
        self.is_cancelled = False
        
        # Start decompression in separate thread
        self.thread = threading.Thread(
            target=self._decompress_thread,
            args=(archive_file, output_dir, format)
        )
        self.thread.daemon = True
        self.thread.start()
        
        return True
    
    def _decompress_thread(self, archive_file: str, output_dir: str,
                          format: Optional[str]):
        """
        Internal thread function for decompression
        
        Args:
            archive_file: Archive to decompress
            output_dir: Output directory
            format: Archive format
        """
        try:
            self.stats['start_time'] = datetime.now()
            
            archive_file = os.path.abspath(archive_file)
            output_dir = os.path.abspath(output_dir)
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            self._log(f"Starting decompression: {archive_file}")
            self._log(f"Output directory: {output_dir}")
            
            # Auto-detect format if not specified
            if format is None:
                if archive_file.endswith('.zip'):
                    format = CompressionFormat.ZIP
                elif archive_file.endswith('.tar.gz') or archive_file.endswith('.tgz'):
                    format = CompressionFormat.TAR_GZ
                elif archive_file.endswith('.tar'):
                    format = CompressionFormat.TAR
                else:
                    raise ValueError(f"Cannot determine format for: {archive_file}")
            
            self._log(f"Format: {format}")
            
            # Perform decompression
            if format == CompressionFormat.ZIP:
                self._decompress_zip(archive_file, output_dir)
            elif format in [CompressionFormat.TAR_GZ, CompressionFormat.TAR]:
                self._decompress_tar(archive_file, output_dir)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            self.stats['end_time'] = datetime.now()
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            self._log(f"Decompression completed successfully")
            self._log(f"Files extracted: {self.stats['processed_files']}")
            self._log(f"Duration: {duration:.2f} seconds")
            
        except Exception as e:
            self._log(f"Error during decompression: {str(e)}")
        finally:
            self.is_running = False
    
    def _decompress_zip(self, archive_file: str, output_dir: str):
        """Decompress ZIP archive"""
        with zipfile.ZipFile(archive_file, 'r') as zipf:
            members = zipf.namelist()
            self.stats['total_files'] = len(members)
            
            for member in members:
                if self.is_cancelled:
                    self._log("Decompression cancelled")
                    break
                
                zipf.extract(member, output_dir)
                self.stats['processed_files'] += 1
                self._log(f"Extracted: {member}")
                
                if self.progress_callback:
                    self.progress_callback(self.stats.copy())
    
    def _decompress_tar(self, archive_file: str, output_dir: str):
        """Decompress TAR archive"""
        with tarfile.open(archive_file, 'r:*') as tarf:
            members = tarf.getmembers()
            self.stats['total_files'] = len(members)
            
            for member in members:
                if self.is_cancelled:
                    self._log("Decompression cancelled")
                    break
                
                tarf.extract(member, output_dir)
                self.stats['processed_files'] += 1
                self._log(f"Extracted: {member.name}")
                
                if self.progress_callback:
                    self.progress_callback(self.stats.copy())
    
    def cancel(self):
        """Cancel running operation"""
        if self.is_running:
            self._log("Cancelling compression/decompression...")
            self.is_cancelled = True
    
    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """Wait for operation to complete"""
        if self.thread:
            self.thread.join(timeout)
            return not self.thread.is_alive()
        return True
    
    def get_stats(self):
        """Get current statistics"""
        return self.stats.copy()
    
    def _count_files(self, path: str, exclude_patterns: Optional[List[str]]) -> int:
        """Count total files in directory"""
        count = 0
        for root, dirs, files in os.walk(path):
            if exclude_patterns:
                dirs[:] = [d for d in dirs if not self._should_exclude(d, exclude_patterns)]
                files = [f for f in files if not self._should_exclude(f, exclude_patterns)]
            count += len(files)
        return count
    
    def _should_exclude(self, name: str, patterns: List[str]) -> bool:
        """Check if file/dir should be excluded"""
        import fnmatch
        for pattern in patterns:
            if fnmatch.fnmatch(name, pattern):
                return True
        return False
    
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


if __name__ == '__main__':
    # Test compression
    def log_handler(msg):
        print(msg)
    
    engine = CompressionEngine(log_callback=log_handler)
    print("Compression engine initialized")
