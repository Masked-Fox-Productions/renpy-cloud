"""Core sync logic and orchestration."""

import os
import time
from typing import Optional
from datetime import datetime, timedelta

from .config import get_config
from .auth import get_auth_manager
from .api_client import get_api_client
from .file_manager import FileManager
from .exceptions import SyncError, StorageError


class SyncManager:
    """Manages the sync process and throttling."""
    
    def __init__(self, save_dir: str):
        """
        Initialize the sync manager.
        
        Args:
            save_dir: Directory containing Ren'Py save files
        """
        self.save_dir = save_dir
        self.file_manager = FileManager(save_dir)
        self.api_client = get_api_client()
        self.last_sync_time: Optional[datetime] = None
        self._sync_in_progress = False
    
    def should_sync(self, force: bool = False) -> bool:
        """
        Check if enough time has passed since last sync.
        
        Args:
            force: Skip throttling check
        
        Returns:
            True if sync should proceed
        """
        if force:
            return True
        
        if self.last_sync_time is None:
            return True
        
        config = get_config()
        elapsed = datetime.now() - self.last_sync_time
        return elapsed.total_seconds() >= config.sync_interval_seconds
    
    def sync(self, force: bool = False) -> bool:
        """
        Perform a sync operation.
        
        Args:
            force: Force sync even if within throttle window
        
        Returns:
            True if sync was performed, False if skipped
        """
        # Check authentication
        auth = get_auth_manager()
        if not auth.is_authenticated():
            # Silently skip if not authenticated
            return False
        
        # Check throttling
        if not self.should_sync(force):
            return False
        
        # Prevent concurrent syncs
        if self._sync_in_progress:
            return False
        
        try:
            self._sync_in_progress = True
            self._perform_sync()
            self.last_sync_time = datetime.now()
            return True
        
        except Exception as e:
            # Log error but don't crash the game
            print(f"[renpy-cloud] Sync failed: {e}")
            return False
        
        finally:
            self._sync_in_progress = False
    
    def _perform_sync(self) -> None:
        """Execute the actual sync operation."""
        # Build local manifest
        local_manifest = self.file_manager.build_local_manifest()
        
        if not local_manifest:
            # No files to sync
            return
        
        # Request sync plan from backend
        sync_plan = self.api_client.request_sync_plan(local_manifest)
        
        if not sync_plan.has_actions():
            # Nothing to do
            return
        
        # Execute uploads
        for upload_item in sync_plan.uploads:
            filename = upload_item['filename']
            presigned_url = upload_item['upload_url']
            
            try:
                filepath = self.file_manager.get_full_path(filename)
                content = self.file_manager.read_file(filepath)
                self.api_client.upload_file(presigned_url, content)
            except (StorageError, SyncError) as e:
                print(f"[renpy-cloud] Failed to upload {filename}: {e}")
                # Continue with other files
                continue
        
        # Execute downloads
        for download_item in sync_plan.downloads:
            filename = download_item['filename']
            presigned_url = download_item['download_url']
            
            try:
                content = self.api_client.download_file(presigned_url)
                filepath = self.file_manager.get_full_path(filename)
                self.file_manager.write_file(filepath, content, backup=True)
            except (StorageError, SyncError) as e:
                print(f"[renpy-cloud] Failed to download {filename}: {e}")
                # Continue with other files
                continue
        
        # Handle conflicts (newer timestamp wins, backup created)
        for conflict in sync_plan.conflicts:
            filename = conflict['filename']
            action = conflict['action']  # 'upload' or 'download'
            
            if action == 'download':
                presigned_url = conflict['download_url']
                try:
                    content = self.api_client.download_file(presigned_url)
                    filepath = self.file_manager.get_full_path(filename)
                    self.file_manager.write_file(filepath, content, backup=True)
                except (StorageError, SyncError) as e:
                    print(f"[renpy-cloud] Failed to resolve conflict for {filename}: {e}")
            
            elif action == 'upload':
                presigned_url = conflict['upload_url']
                try:
                    filepath = self.file_manager.get_full_path(filename)
                    content = self.file_manager.read_file(filepath)
                    self.api_client.upload_file(presigned_url, content)
                except (StorageError, SyncError) as e:
                    print(f"[renpy-cloud] Failed to resolve conflict for {filename}: {e}")
        
        # Notify backend of completion
        self.api_client.complete_sync(success=True)


# Global sync manager instance
_sync_manager: Optional[SyncManager] = None


def get_sync_manager(save_dir: Optional[str] = None) -> SyncManager:
    """
    Get or create the global sync manager.
    
    Args:
        save_dir: Save directory (required on first call)
    
    Returns:
        SyncManager instance
    """
    global _sync_manager
    
    if _sync_manager is None:
        if save_dir is None:
            raise ValueError("save_dir required for first call to get_sync_manager")
        _sync_manager = SyncManager(save_dir)
    
    return _sync_manager

