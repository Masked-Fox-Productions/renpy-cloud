"""API client for communicating with the backend."""

import json
from typing import Dict, List, Optional, Any
try:
    import urllib.request
    import urllib.parse
    import urllib.error
except ImportError:
    import urllib2 as urllib

from .config import get_config
from .auth import get_auth_manager
from .exceptions import NetworkError, SyncError
from .file_manager import FileInfo


class SyncPlan:
    """Represents a sync plan returned by the API."""
    
    def __init__(self, data: Dict[str, Any]):
        self.uploads: List[Dict[str, str]] = data.get('uploads', [])
        self.downloads: List[Dict[str, str]] = data.get('downloads', [])
        self.deletes: List[str] = data.get('deletes', [])
        self.conflicts: List[Dict[str, Any]] = data.get('conflicts', [])
    
    def has_actions(self) -> bool:
        """Check if plan has any actions to perform."""
        return bool(self.uploads or self.downloads or self.deletes)


class APIClient:
    """Client for the renpy-cloud backend API."""
    
    def __init__(self):
        self.config = get_config()
        self.auth = get_auth_manager()
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        authenticated: bool = True
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Optional request body
            authenticated: Whether to include auth token
        
        Returns:
            Response data as dictionary
        """
        self.config.validate()
        
        url = f"{self.config.api_base_url}{endpoint}"
        headers = {
            'Content-Type': 'application/json',
        }
        
        if authenticated:
            try:
                token = self.auth.get_access_token()
                headers['Authorization'] = f'Bearer {token}'
            except Exception as e:
                raise SyncError(f"Authentication failed: {e}")
        
        request_data = None
        if data is not None:
            request_data = json.dumps(data).encode('utf-8')
        
        try:
            req = urllib.request.Request(
                url,
                data=request_data,
                headers=headers,
                method=method
            )
            response = urllib.request.urlopen(req, timeout=self.config.timeout_seconds)
            result = json.loads(response.read().decode('utf-8'))
            return result
        
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            try:
                error_data = json.loads(error_body)
                error_msg = error_data.get('message', str(e))
            except:
                error_msg = error_body or str(e)
            raise SyncError(f"API request failed ({e.code}): {error_msg}")
        
        except urllib.error.URLError as e:
            raise NetworkError(f"Network error: {str(e)}")
        
        except Exception as e:
            raise SyncError(f"Request failed: {str(e)}")
    
    def request_sync_plan(
        self,
        local_manifest: Dict[str, FileInfo]
    ) -> SyncPlan:
        """
        Request a sync plan from the backend.
        
        Args:
            local_manifest: Dictionary of local file info
        
        Returns:
            SyncPlan object
        """
        # Convert FileInfo objects to dicts
        manifest_data = {
            path: info.to_dict()
            for path, info in local_manifest.items()
        }
        
        payload = {
            'game_id': self.config.game_id,
            'manifest': manifest_data,
        }
        
        response = self._make_request(
            'POST',
            '/sync/plan',
            data=payload,
            authenticated=True
        )
        
        return SyncPlan(response)
    
    def upload_file(self, presigned_url: str, file_content: bytes) -> None:
        """
        Upload a file to S3 using a pre-signed URL.
        
        Args:
            presigned_url: Pre-signed S3 URL
            file_content: File content as bytes
        """
        try:
            req = urllib.request.Request(
                presigned_url,
                data=file_content,
                method='PUT',
                headers={'Content-Type': 'application/octet-stream'}
            )
            urllib.request.urlopen(req, timeout=self.config.timeout_seconds)
        
        except urllib.error.HTTPError as e:
            raise SyncError(f"Upload failed ({e.code}): {e.reason}")
        
        except urllib.error.URLError as e:
            raise NetworkError(f"Upload network error: {str(e)}")
        
        except Exception as e:
            raise SyncError(f"Upload failed: {str(e)}")
    
    def download_file(self, presigned_url: str) -> bytes:
        """
        Download a file from S3 using a pre-signed URL.
        
        Args:
            presigned_url: Pre-signed S3 URL
        
        Returns:
            File content as bytes
        """
        try:
            req = urllib.request.Request(presigned_url, method='GET')
            response = urllib.request.urlopen(req, timeout=self.config.timeout_seconds)
            return response.read()
        
        except urllib.error.HTTPError as e:
            raise SyncError(f"Download failed ({e.code}): {e.reason}")
        
        except urllib.error.URLError as e:
            raise NetworkError(f"Download network error: {str(e)}")
        
        except Exception as e:
            raise SyncError(f"Download failed: {str(e)}")
    
    def complete_sync(self, success: bool, error: Optional[str] = None) -> None:
        """
        Notify the backend that sync is complete.
        
        Args:
            success: Whether sync was successful
            error: Optional error message if failed
        """
        payload = {
            'game_id': self.config.game_id,
            'success': success,
            'error': error,
        }
        
        try:
            self._make_request(
                'POST',
                '/sync/complete',
                data=payload,
                authenticated=True
            )
        except Exception:
            # Don't fail the overall sync if completion notification fails
            pass


def get_api_client() -> APIClient:
    """Get an API client instance."""
    return APIClient()

