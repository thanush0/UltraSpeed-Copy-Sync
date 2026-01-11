"""
UltraSpeed Copy - Network Optimizer Module
Detects network paths and optimizes robocopy parameters for network transfers
"""

import os
import re
from typing import Tuple, Optional


class NetworkOptimizer:
    """
    Analyzes paths and provides optimized settings for network transfers
    """
    
    @staticmethod
    def is_network_path(path: str) -> bool:
        """
        Detect if a path is a network path (UNC path or mapped drive)
        
        Args:
            path: Path to check
            
        Returns:
            True if network path, False otherwise
        """
        # Check for UNC path (\\server\share)
        if path.startswith('\\\\') or path.startswith('//'):
            return True
        
        # Check if it's a mapped network drive on Windows
        if os.name == 'nt' and len(path) >= 2 and path[1] == ':':
            drive_letter = path[0].upper()
            try:
                import subprocess
                result = subprocess.run(
                    ['net', 'use', f'{drive_letter}:'],
                    capture_output=True,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                # If 'net use' shows remote path, it's a network drive
                if 'Remote name' in result.stdout or '\\\\' in result.stdout:
                    return True
            except:
                pass
        
        return False
    
    @staticmethod
    def get_network_info(path: str) -> Optional[dict]:
        """
        Get information about network path
        
        Args:
            path: Network path
            
        Returns:
            Dictionary with network info or None
        """
        if not NetworkOptimizer.is_network_path(path):
            return None
        
        info = {
            'is_network': True,
            'type': 'unknown',
            'server': None,
            'share': None
        }
        
        # Parse UNC path
        if path.startswith('\\\\') or path.startswith('//'):
            info['type'] = 'unc'
            # Extract server and share from \\server\share\path
            parts = path.replace('//', '\\\\').split('\\')
            if len(parts) >= 4:
                info['server'] = parts[2]
                info['share'] = parts[3]
        else:
            info['type'] = 'mapped_drive'
            info['drive'] = path[0].upper()
        
        return info
    
    @staticmethod
    def get_optimized_parameters(source: str, destination: str) -> dict:
        """
        Get optimized robocopy parameters based on source and destination
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            Dictionary with optimized parameters
        """
        source_is_network = NetworkOptimizer.is_network_path(source)
        dest_is_network = NetworkOptimizer.is_network_path(destination)
        
        params = {
            'network_optimized': source_is_network or dest_is_network,
            'recommended_threads': 8,
            'retry_count': 3,
            'retry_wait': 5,
            'use_restartable': False,
            'use_backup_mode': False,
            'optimization_reason': []
        }
        
        # If either source or destination is network, enable optimizations
        if source_is_network or dest_is_network:
            params['use_restartable'] = True
            params['use_backup_mode'] = True
            params['retry_count'] = 5
            params['retry_wait'] = 10
            params['recommended_threads'] = 16
            
            if source_is_network:
                params['optimization_reason'].append('Source is network path')
            if dest_is_network:
                params['optimization_reason'].append('Destination is network path')
        else:
            # Local to local - optimize for speed
            params['recommended_threads'] = 32
            params['retry_count'] = 1
            params['retry_wait'] = 3
            params['optimization_reason'].append('Local to local transfer')
        
        return params
    
    @staticmethod
    def estimate_speed(source: str, destination: str) -> dict:
        """
        Estimate expected transfer speed based on path types
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            Dictionary with speed estimates
        """
        source_is_network = NetworkOptimizer.is_network_path(source)
        dest_is_network = NetworkOptimizer.is_network_path(destination)
        
        estimates = {
            'expected_mbps': 0,
            'scenario': '',
            'bottleneck': ''
        }
        
        if not source_is_network and not dest_is_network:
            # Local to local - limited by disk speed
            estimates['expected_mbps'] = 500  # Typical SSD speed
            estimates['scenario'] = 'Local to Local'
            estimates['bottleneck'] = 'Disk I/O speed'
        elif source_is_network and dest_is_network:
            # Network to network - limited by network speed
            estimates['expected_mbps'] = 100  # Typical gigabit ethernet
            estimates['scenario'] = 'Network to Network'
            estimates['bottleneck'] = 'Network bandwidth'
        else:
            # One network, one local - limited by network
            estimates['expected_mbps'] = 100
            estimates['scenario'] = 'Network to Local' if source_is_network else 'Local to Network'
            estimates['bottleneck'] = 'Network bandwidth'
        
        return estimates
    
    @staticmethod
    def validate_path_access(path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a path is accessible
        
        Args:
            path: Path to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if not os.path.exists(path):
                return False, f"Path does not exist: {path}"
            
            if not os.access(path, os.R_OK):
                return False, f"Path is not readable: {path}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error accessing path: {str(e)}"


if __name__ == '__main__':
    # Test network detection
    optimizer = NetworkOptimizer()
    
    test_paths = [
        r"C:\Users\Test",
        r"\\server\share\folder",
        r"//192.168.1.100/backup",
        r"D:\Backup"
    ]
    
    for path in test_paths:
        is_net = optimizer.is_network_path(path)
        info = optimizer.get_network_info(path)
        print(f"Path: {path}")
        print(f"  Is Network: {is_net}")
        print(f"  Info: {info}")
        print()
