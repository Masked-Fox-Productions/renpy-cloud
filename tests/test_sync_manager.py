"""Tests for sync manager module."""

import os
import tempfile
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from renpy_cloud.sync_manager import SyncManager, get_sync_manager
from renpy_cloud.file_manager import FileInfo


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sync_manager(temp_dir):
    """Create a SyncManager with temporary directory."""
    return SyncManager(temp_dir)


@pytest.fixture
def mock_auth():
    """Mock authenticated auth manager."""
    with patch('renpy_cloud.sync_manager.get_auth_manager') as mock:
        auth = Mock()
        auth.is_authenticated.return_value = True
        mock.return_value = auth
        yield auth


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch('renpy_cloud.sync_manager.get_config') as mock:
        config = Mock()
        config.sync_interval_seconds = 300
        mock.return_value = config
        yield config


def test_sync_manager_initialization(sync_manager, temp_dir):
    """Test SyncManager initializes correctly."""
    assert sync_manager.save_dir == temp_dir
    assert sync_manager.last_sync_time is None
    assert not sync_manager._sync_in_progress


def test_should_sync_no_previous_sync(sync_manager):
    """Test should sync when no previous sync."""
    assert sync_manager.should_sync(force=False)


def test_should_sync_with_force(sync_manager):
    """Test should sync with force flag."""
    sync_manager.last_sync_time = datetime.now()
    assert sync_manager.should_sync(force=True)


def test_should_sync_within_interval(sync_manager, mock_config):
    """Test should not sync within interval."""
    sync_manager.last_sync_time = datetime.now()
    assert not sync_manager.should_sync(force=False)


def test_should_sync_after_interval(sync_manager, mock_config):
    """Test should sync after interval."""
    sync_manager.last_sync_time = datetime.now() - timedelta(seconds=400)
    assert sync_manager.should_sync(force=False)


def test_sync_not_authenticated(sync_manager):
    """Test sync skips when not authenticated."""
    with patch('renpy_cloud.sync_manager.get_auth_manager') as mock_auth:
        auth = Mock()
        auth.is_authenticated.return_value = False
        mock_auth.return_value = auth
        
        result = sync_manager.sync()
        assert result is False


def test_sync_skips_if_in_progress(sync_manager, mock_auth):
    """Test sync skips if already in progress."""
    sync_manager._sync_in_progress = True
    result = sync_manager.sync(force=True)
    assert result is False


def test_sync_performs_sync(sync_manager, mock_auth, mock_config, temp_dir):
    """Test sync performs full sync operation."""
    # Create a test file
    persistent = os.path.join(temp_dir, 'persistent')
    with open(persistent, 'wb') as f:
        f.write(b'test data')
    
    # Mock API client
    with patch.object(sync_manager, 'api_client') as mock_api:
        mock_plan = Mock()
        mock_plan.has_actions.return_value = False
        mock_api.request_sync_plan.return_value = mock_plan
        
        result = sync_manager.sync(force=True)
    
    assert result is True
    assert sync_manager.last_sync_time is not None


def test_sync_handles_uploads(sync_manager, mock_auth, mock_config, temp_dir):
    """Test sync handles file uploads."""
    # Create a test file
    test_file = os.path.join(temp_dir, 'test.save')
    with open(test_file, 'wb') as f:
        f.write(b'save data')
    
    # Mock API client with upload plan
    with patch.object(sync_manager, 'api_client') as mock_api:
        mock_plan = Mock()
        mock_plan.has_actions.return_value = True
        mock_plan.uploads = [{
            'filename': 'test.save',
            'upload_url': 'https://s3.example.com/upload'
        }]
        mock_plan.downloads = []
        mock_plan.conflicts = []
        mock_api.request_sync_plan.return_value = mock_plan
        
        with patch.object(sync_manager.file_manager, 'build_local_manifest') as mock_manifest:
            mock_manifest.return_value = {
                'test.save': FileInfo('test.save', 9, 1234567890.0, 'abc123')
            }
            
            result = sync_manager.sync(force=True)
    
    assert result is True
    mock_api.upload_file.assert_called_once()


def test_sync_handles_downloads(sync_manager, mock_auth, mock_config, temp_dir):
    """Test sync handles file downloads."""
    # Create a test file to trigger manifest building
    test_file = os.path.join(temp_dir, 'persistent')
    with open(test_file, 'wb') as f:
        f.write(b'local data')
    
    # Mock API client with download plan
    with patch.object(sync_manager, 'api_client') as mock_api:
        mock_plan = Mock()
        mock_plan.has_actions.return_value = True
        mock_plan.uploads = []
        mock_plan.downloads = [{
            'filename': 'remote.save',
            'download_url': 'https://s3.example.com/download'
        }]
        mock_plan.conflicts = []
        mock_api.request_sync_plan.return_value = mock_plan
        mock_api.download_file.return_value = b'remote data'
        
        with patch.object(sync_manager.file_manager, 'write_file'):
            result = sync_manager.sync(force=True)
    
    assert result is True
    assert mock_api.download_file.called


def test_sync_error_handling(sync_manager, mock_auth, mock_config):
    """Test sync handles errors gracefully."""
    with patch.object(sync_manager.file_manager, 'build_local_manifest') as mock_manifest:
        # Cause an error during manifest building
        mock_manifest.side_effect = Exception("Network error")
        
        result = sync_manager.sync(force=True)
    
    assert result is False  # Sync failed but didn't crash


def test_get_sync_manager_singleton(temp_dir):
    """Test get_sync_manager with singleton pattern."""
    manager1 = get_sync_manager(temp_dir)
    manager2 = get_sync_manager()  # No save_dir needed on second call
    assert manager1 is manager2


def test_get_sync_manager_requires_save_dir():
    """Test get_sync_manager requires save_dir on first call."""
    # Reset global
    import renpy_cloud.sync_manager as sm
    sm._sync_manager = None
    
    with pytest.raises(ValueError, match="save_dir required"):
        get_sync_manager()

