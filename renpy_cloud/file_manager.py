"""File management for Ren'Py save files and persistent data."""

import os
import json
import hashlib
from typing import Dict, List, Optional, Tuple
from datetime import datetime

from .exceptions import StorageError


class FileInfo:
    """Information about a synced file."""
    
    def __init__(
        self,
        path: str,
        size: int,
        modified_timestamp: float,
        checksum: Optional[str] = None
    ):
        self.path = path
        self.size = size
        self.modified_timestamp = modified_timestamp
        self.checksum = checksum or ""
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for API transmission."""
        return {
            'path': self.path,
            'size': self.size,
            'modified_timestamp': self.modified_timestamp,
            'checksum': self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'FileInfo':
        """Create FileInfo from dictionary."""
        return cls(
            path=data['path'],
            size=data['size'],
            modified_timestamp=data['modified_timestamp'],
            checksum=data.get('checksum', ''),
        )


class FileManager:
    """Manages local save files and persistent data."""
    
    def __init__(self, save_dir: str):
        """
        Initialize the file manager.
        
        Args:
            save_dir: Directory containing Ren'Py save files
        """
        self.save_dir = save_dir
        self._backup_dir = os.path.join(save_dir, '.renpy_cloud_backups')
    
    def _ensure_backup_dir(self) -> None:
        """Ensure backup directory exists."""
        if not os.path.exists(self._backup_dir):
            try:
                os.makedirs(self._backup_dir)
            except OSError as e:
                raise StorageError(f"Failed to create backup directory: {e}")
    
    def calculate_file_hash(self, filepath: str) -> str:
        """
        Calculate SHA256 hash of a file.
        
        Args:
            filepath: Path to the file
        
        Returns:
            Hex string of the SHA256 hash
        """
        sha256 = hashlib.sha256()
        try:
            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    sha256.update(chunk)
            return sha256.hexdigest()
        except IOError as e:
            raise StorageError(f"Failed to hash file {filepath}: {e}")
    
    def get_file_info(self, filepath: str) -> FileInfo:
        """
        Get metadata for a specific file.
        
        Args:
            filepath: Path to the file
        
        Returns:
            FileInfo object
        """
        try:
            stat = os.stat(filepath)
            checksum = self.calculate_file_hash(filepath)
            return FileInfo(
                path=os.path.basename(filepath),
                size=stat.st_size,
                modified_timestamp=stat.st_mtime,
                checksum=checksum,
            )
        except OSError as e:
            raise StorageError(f"Failed to get file info for {filepath}: {e}")
    
    def get_most_recent_save_slot(self) -> Optional[int]:
        """
        Find the most recently modified save slot.
        
        Returns:
            Slot number, or None if no saves found
        """
        save_files = []
        
        try:
            if not os.path.exists(self.save_dir):
                return None
            
            for filename in os.listdir(self.save_dir):
                # Ren'Py save files are typically named like: 1-1-LT1.save
                if filename.endswith('.save') and not filename.startswith('.'):
                    filepath = os.path.join(self.save_dir, filename)
                    try:
                        # Parse slot number from filename (format: slot-page-...)
                        slot_num = int(filename.split('-')[0])
                        mtime = os.path.getmtime(filepath)
                        save_files.append((slot_num, mtime))
                    except (ValueError, IndexError, OSError):
                        # Skip files that don't match expected format
                        continue
            
            if not save_files:
                return None
            
            # Return slot number with most recent modification time
            return max(save_files, key=lambda x: x[1])[0]
        
        except OSError as e:
            raise StorageError(f"Failed to scan save directory: {e}")
    
    def get_slot_files(self, slot: int) -> List[str]:
        """
        Get all files belonging to a specific save slot.
        
        Args:
            slot: Save slot number
        
        Returns:
            List of file paths
        """
        slot_files = []
        
        try:
            if not os.path.exists(self.save_dir):
                return []
            
            for filename in os.listdir(self.save_dir):
                # Match files for this slot: slot-*
                if filename.startswith(f"{slot}-") and not filename.startswith('.'):
                    slot_files.append(os.path.join(self.save_dir, filename))
            
            return slot_files
        
        except OSError as e:
            raise StorageError(f"Failed to get slot files: {e}")
    
    def get_persistent_file(self) -> Optional[str]:
        """
        Get the path to the persistent data file.
        
        Returns:
            Path to persistent file, or None if not found
        """
        persistent_path = os.path.join(self.save_dir, 'persistent')
        if os.path.exists(persistent_path):
            return persistent_path
        return None
    
    def build_local_manifest(self) -> Dict[str, FileInfo]:
        """
        Build a manifest of local files to sync.
        
        Returns:
            Dictionary mapping file paths to FileInfo objects
        """
        manifest = {}
        
        # Add persistent file
        persistent = self.get_persistent_file()
        if persistent:
            try:
                info = self.get_file_info(persistent)
                manifest[info.path] = info
            except StorageError:
                # Skip if can't read
                pass
        
        # Add most recent save slot files
        recent_slot = self.get_most_recent_save_slot()
        if recent_slot is not None:
            slot_files = self.get_slot_files(recent_slot)
            for filepath in slot_files:
                try:
                    info = self.get_file_info(filepath)
                    manifest[info.path] = info
                except StorageError:
                    # Skip files that can't be read
                    continue
        
        return manifest
    
    def backup_file(self, filepath: str) -> str:
        """
        Create a backup of a file before overwriting.
        
        Args:
            filepath: Path to file to backup
        
        Returns:
            Path to backup file
        """
        self._ensure_backup_dir()
        
        filename = os.path.basename(filepath)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{filename}.{timestamp}.backup"
        backup_path = os.path.join(self._backup_dir, backup_name)
        
        try:
            with open(filepath, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            return backup_path
        except IOError as e:
            raise StorageError(f"Failed to backup file {filepath}: {e}")
    
    def read_file(self, filepath: str) -> bytes:
        """
        Read file contents.
        
        Args:
            filepath: Path to file
        
        Returns:
            File contents as bytes
        """
        try:
            with open(filepath, 'rb') as f:
                return f.read()
        except IOError as e:
            raise StorageError(f"Failed to read file {filepath}: {e}")
    
    def write_file(self, filepath: str, content: bytes, backup: bool = True) -> None:
        """
        Write content to a file.
        
        Args:
            filepath: Path to file
            content: File content as bytes
            backup: Whether to backup existing file first
        """
        # Backup existing file if requested
        if backup and os.path.exists(filepath):
            try:
                self.backup_file(filepath)
            except StorageError:
                # Continue even if backup fails
                pass
        
        # Ensure directory exists
        dir_path = os.path.dirname(filepath)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path)
            except OSError as e:
                raise StorageError(f"Failed to create directory {dir_path}: {e}")
        
        # Write file
        try:
            with open(filepath, 'wb') as f:
                f.write(content)
        except IOError as e:
            raise StorageError(f"Failed to write file {filepath}: {e}")
    
    def get_full_path(self, filename: str) -> str:
        """
        Get full path for a filename in the save directory.
        
        Args:
            filename: Base filename
        
        Returns:
            Full path
        """
        return os.path.join(self.save_dir, filename)

