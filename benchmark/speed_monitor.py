"""
UltraSpeed Copy - Speed Monitoring and Benchmarking Module
Tracks and stores performance metrics for file transfers
"""

import os
import json
import csv
import time
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path


class SpeedMonitor:
    """
    Monitors and records file transfer performance metrics
    """
    
    def __init__(self, stats_file: str = "benchmark/stats.csv"):
        """
        Initialize speed monitor
        
        Args:
            stats_file: Path to CSV file for storing statistics
        """
        self.stats_file = stats_file
        self.current_session = None
        self.history = []
        
        # Ensure stats directory exists
        os.makedirs(os.path.dirname(stats_file), exist_ok=True)
        
        # Load existing history
        self._load_history()
    
    def start_session(self, operation_type: str, source: str, destination: str,
                     additional_info: Optional[Dict] = None) -> str:
        """
        Start a new monitoring session
        
        Args:
            operation_type: Type of operation (copy, mirror, compress, etc.)
            source: Source path
            destination: Destination path
            additional_info: Additional metadata
            
        Returns:
            Session ID
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        
        self.current_session = {
            'session_id': session_id,
            'operation_type': operation_type,
            'source': source,
            'destination': destination,
            'start_time': datetime.now().isoformat(),
            'end_time': None,
            'duration_seconds': 0,
            'total_bytes': 0,
            'total_files': 0,
            'average_speed_mbps': 0.0,
            'peak_speed_mbps': 0.0,
            'min_speed_mbps': 0.0,
            'errors': 0,
            'success': False,
            'speed_samples': [],
            'additional_info': additional_info or {}
        }
        
        return session_id
    
    def update_progress(self, bytes_copied: int, files_copied: int,
                       current_speed_mbps: float, errors: int = 0):
        """
        Update current session with progress information
        
        Args:
            bytes_copied: Total bytes copied so far
            files_copied: Total files copied so far
            current_speed_mbps: Current transfer speed in MB/s
            errors: Number of errors encountered
        """
        if not self.current_session:
            return
        
        self.current_session['total_bytes'] = bytes_copied
        self.current_session['total_files'] = files_copied
        self.current_session['errors'] = errors
        
        # Track speed samples
        timestamp = time.time()
        self.current_session['speed_samples'].append({
            'timestamp': timestamp,
            'speed_mbps': current_speed_mbps,
            'bytes': bytes_copied
        })
        
        # Update peak speed
        if current_speed_mbps > self.current_session['peak_speed_mbps']:
            self.current_session['peak_speed_mbps'] = current_speed_mbps
        
        # Update min speed (ignore zero values)
        if current_speed_mbps > 0:
            if self.current_session['min_speed_mbps'] == 0:
                self.current_session['min_speed_mbps'] = current_speed_mbps
            elif current_speed_mbps < self.current_session['min_speed_mbps']:
                self.current_session['min_speed_mbps'] = current_speed_mbps
    
    def end_session(self, success: bool = True):
        """
        End current monitoring session
        
        Args:
            success: Whether operation completed successfully
        """
        if not self.current_session:
            return
        
        self.current_session['end_time'] = datetime.now().isoformat()
        self.current_session['success'] = success
        
        # Calculate duration
        start = datetime.fromisoformat(self.current_session['start_time'])
        end = datetime.fromisoformat(self.current_session['end_time'])
        duration = (end - start).total_seconds()
        self.current_session['duration_seconds'] = duration
        
        # Calculate average speed
        if duration > 0 and self.current_session['total_bytes'] > 0:
            bytes_per_second = self.current_session['total_bytes'] / duration
            self.current_session['average_speed_mbps'] = bytes_per_second / (1024 * 1024)
        
        # Save to history
        self.history.append(self.current_session.copy())
        self._save_to_csv()
        
        self.current_session = None
    
    def get_current_stats(self) -> Optional[Dict]:
        """Get current session statistics"""
        if self.current_session:
            stats = self.current_session.copy()
            
            # Calculate current average speed
            if self.current_session['speed_samples']:
                speeds = [s['speed_mbps'] for s in self.current_session['speed_samples']]
                stats['current_average_speed'] = sum(speeds) / len(speeds)
            
            return stats
        return None
    
    def get_history(self, limit: Optional[int] = None,
                   operation_type: Optional[str] = None) -> List[Dict]:
        """
        Get historical statistics
        
        Args:
            limit: Maximum number of records to return
            operation_type: Filter by operation type
            
        Returns:
            List of historical records
        """
        filtered = self.history
        
        if operation_type:
            filtered = [h for h in filtered if h['operation_type'] == operation_type]
        
        if limit:
            filtered = filtered[-limit:]
        
        return filtered
    
    def get_summary_stats(self) -> Dict:
        """
        Get summary statistics across all history
        
        Returns:
            Dictionary with summary statistics
        """
        if not self.history:
            return {
                'total_sessions': 0,
                'successful_sessions': 0,
                'total_bytes_transferred': 0,
                'total_files_transferred': 0,
                'average_speed_mbps': 0.0,
                'peak_speed_mbps': 0.0
            }
        
        total_sessions = len(self.history)
        successful = len([h for h in self.history if h['success']])
        total_bytes = sum(h['total_bytes'] for h in self.history)
        total_files = sum(h['total_files'] for h in self.history)
        
        speeds = [h['average_speed_mbps'] for h in self.history if h['average_speed_mbps'] > 0]
        avg_speed = sum(speeds) / len(speeds) if speeds else 0.0
        
        peak_speeds = [h['peak_speed_mbps'] for h in self.history]
        peak_speed = max(peak_speeds) if peak_speeds else 0.0
        
        return {
            'total_sessions': total_sessions,
            'successful_sessions': successful,
            'failed_sessions': total_sessions - successful,
            'total_bytes_transferred': total_bytes,
            'total_files_transferred': total_files,
            'average_speed_mbps': avg_speed,
            'peak_speed_mbps': peak_speed
        }
    
    def export_to_json(self, output_file: str):
        """
        Export history to JSON file
        
        Args:
            output_file: Output JSON file path
        """
        # Remove speed_samples to reduce file size
        export_data = []
        for session in self.history:
            session_copy = session.copy()
            session_copy.pop('speed_samples', None)
            export_data.append(session_copy)
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _save_to_csv(self):
        """Save current session to CSV file"""
        if not self.current_session and not self.history:
            return
        
        file_exists = os.path.exists(self.stats_file)
        
        with open(self.stats_file, 'a', newline='', encoding='utf-8') as f:
            fieldnames = [
                'session_id', 'operation_type', 'source', 'destination',
                'start_time', 'end_time', 'duration_seconds',
                'total_bytes', 'total_files', 'average_speed_mbps',
                'peak_speed_mbps', 'min_speed_mbps', 'errors', 'success'
            ]
            
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            
            # Write header if file is new
            if not file_exists:
                writer.writeheader()
            
            # Write last history entry
            if self.history:
                last_entry = self.history[-1].copy()
                last_entry.pop('speed_samples', None)
                last_entry.pop('additional_info', None)
                writer.writerow(last_entry)
    
    def _load_history(self):
        """Load history from CSV file"""
        if not os.path.exists(self.stats_file):
            return
        
        try:
            with open(self.stats_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert numeric fields
                    row['duration_seconds'] = float(row.get('duration_seconds', 0))
                    row['total_bytes'] = int(row.get('total_bytes', 0))
                    row['total_files'] = int(row.get('total_files', 0))
                    row['average_speed_mbps'] = float(row.get('average_speed_mbps', 0))
                    row['peak_speed_mbps'] = float(row.get('peak_speed_mbps', 0))
                    row['min_speed_mbps'] = float(row.get('min_speed_mbps', 0))
                    row['errors'] = int(row.get('errors', 0))
                    row['success'] = row.get('success', 'False') == 'True'
                    row['speed_samples'] = []
                    row['additional_info'] = {}
                    
                    self.history.append(row)
        except Exception as e:
            print(f"Error loading history: {e}")
    
    @staticmethod
    def format_bytes(bytes_val: int) -> str:
        """Format bytes to human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.2f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.2f} PB"
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration to human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


class SpeedChart:
    """
    Generate speed charts using matplotlib
    """
    
    def __init__(self, monitor: SpeedMonitor):
        """
        Initialize chart generator
        
        Args:
            monitor: SpeedMonitor instance
        """
        self.monitor = monitor
    
    def plot_current_session(self, output_file: Optional[str] = None):
        """
        Plot current session speed over time
        
        Args:
            output_file: Optional file to save plot
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            from datetime import datetime
            
            stats = self.monitor.get_current_stats()
            if not stats or not stats['speed_samples']:
                print("No data to plot")
                return None
            
            # Extract data
            samples = stats['speed_samples']
            start_timestamp = samples[0]['timestamp']
            times = [(s['timestamp'] - start_timestamp) for s in samples]
            speeds = [s['speed_mbps'] for s in samples]
            
            # Create plot
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(times, speeds, linewidth=2, color='#2196F3')
            ax.fill_between(times, speeds, alpha=0.3, color='#2196F3')
            
            ax.set_xlabel('Time (seconds)', fontsize=12)
            ax.set_ylabel('Speed (MB/s)', fontsize=12)
            ax.set_title('Transfer Speed Over Time', fontsize=14, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            # Add average line
            avg_speed = stats.get('current_average_speed', 0)
            if avg_speed > 0:
                ax.axhline(y=avg_speed, color='#FF9800', linestyle='--', 
                          label=f'Average: {avg_speed:.2f} MB/s')
                ax.legend()
            
            plt.tight_layout()
            
            if output_file:
                plt.savefig(output_file, dpi=150)
            
            return fig
            
        except ImportError:
            print("Matplotlib not installed. Install with: pip install matplotlib")
            return None
    
    def plot_history_comparison(self, limit: int = 10, output_file: Optional[str] = None):
        """
        Plot comparison of historical sessions
        
        Args:
            limit: Number of recent sessions to plot
            output_file: Optional file to save plot
        """
        try:
            import matplotlib.pyplot as plt
            
            history = self.monitor.get_history(limit=limit)
            if not history:
                print("No history to plot")
                return None
            
            # Extract data
            session_ids = [h['session_id'][-8:] for h in history]  # Last 8 chars
            avg_speeds = [h['average_speed_mbps'] for h in history]
            peak_speeds = [h['peak_speed_mbps'] for h in history]
            
            # Create plot
            fig, ax = plt.subplots(figsize=(12, 6))
            
            x = range(len(session_ids))
            width = 0.35
            
            ax.bar([i - width/2 for i in x], avg_speeds, width, 
                  label='Average Speed', color='#2196F3')
            ax.bar([i + width/2 for i in x], peak_speeds, width,
                  label='Peak Speed', color='#4CAF50')
            
            ax.set_xlabel('Session', fontsize=12)
            ax.set_ylabel('Speed (MB/s)', fontsize=12)
            ax.set_title('Transfer Speed Comparison', fontsize=14, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels(session_ids, rotation=45, ha='right')
            ax.legend()
            ax.grid(True, alpha=0.3, axis='y')
            
            plt.tight_layout()
            
            if output_file:
                plt.savefig(output_file, dpi=150)
            
            return fig
            
        except ImportError:
            print("Matplotlib not installed. Install with: pip install matplotlib")
            return None


if __name__ == '__main__':
    # Test speed monitor
    monitor = SpeedMonitor("test_stats.csv")
    
    session_id = monitor.start_session("test_copy", "C:\\Source", "D:\\Dest")
    print(f"Started session: {session_id}")
    
    # Simulate progress updates
    import time
    for i in range(5):
        time.sleep(0.5)
        monitor.update_progress(
            bytes_copied=(i + 1) * 1024 * 1024 * 100,
            files_copied=(i + 1) * 10,
            current_speed_mbps=50 + i * 10
        )
    
    monitor.end_session(success=True)
    
    # Print summary
    summary = monitor.get_summary_stats()
    print("\nSummary:")
    print(json.dumps(summary, indent=2))
