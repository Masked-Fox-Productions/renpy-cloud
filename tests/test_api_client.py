"""Tests for API client module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from renpy_cloud.api_client import APIClient, SyncPlan
from renpy_cloud.file_manager import FileInfo
from renpy_cloud.exceptions import SyncError, NetworkError


@pytest.fixture
def api_client():
    """Create an API client."""
    return APIClient()


@pytest.fixture
def mock_config():
    """Mock configuration."""
    with patch('renpy_cloud.api_client.get_config') as mock:
        config = Mock()
        config.api_base_url = 'https://api.example.com'
        config.game_id = 'test_game'
        config.timeout_seconds = 30
        config._configured = True
        config.aws_region = 'us-east-1'
        config.cognito_user_pool_id = 'test-pool'
        config.cognito_app_client_id = 'test-client'
        config.validate = Mock(return_value=None)  # Doesn't raise
        mock.return_value = config
        yield config


@pytest.fixture
def mock_auth():
    """Mock authentication."""
    with patch('renpy_cloud.api_client.get_auth_manager') as mock:
        auth = Mock()
        auth.get_access_token.return_value = 'test_token'
        mock.return_value = auth
        yield auth


def test_sync_plan_initialization():
    """Test SyncPlan initializes from data."""
    data = {
        'uploads': [{'filename': 'file1.save', 'upload_url': 'url1'}],
        'downloads': [{'filename': 'file2.save', 'download_url': 'url2'}],
        'conflicts': [],
        'deletes': []
    }
    
    plan = SyncPlan(data)
    assert len(plan.uploads) == 1
    assert len(plan.downloads) == 1
    assert len(plan.conflicts) == 0
    assert len(plan.deletes) == 0


def test_sync_plan_has_actions():
    """Test SyncPlan detects if actions exist."""
    plan_with_actions = SyncPlan({
        'uploads': [{'filename': 'test.save', 'upload_url': 'url'}],
        'downloads': [],
        'conflicts': [],
        'deletes': []
    })
    assert plan_with_actions.has_actions()
    
    plan_without_actions = SyncPlan({
        'uploads': [],
        'downloads': [],
        'conflicts': [],
        'deletes': []
    })
    assert not plan_without_actions.has_actions()


def test_request_sync_plan(api_client, mock_config, mock_auth):
    """Test requesting sync plan."""
    manifest = {
        'test.save': FileInfo('test.save', 1024, 1234567890.0, 'abc123')
    }
    
    mock_response = {
        'uploads': [],
        'downloads': [],
        'conflicts': [],
        'deletes': []
    }
    
    with patch.object(api_client, '_make_request', return_value=mock_response):
        plan = api_client.request_sync_plan(manifest)
    
    assert isinstance(plan, SyncPlan)


def test_make_request_authenticated(api_client, mock_config, mock_auth):
    """Test authenticated request includes token."""
    mock_response = {'status': 'ok'}
    # Directly replace the config and auth instances on the api_client
    api_client.config = mock_config
    api_client.auth = mock_auth
    
    with patch('renpy_cloud.api_client.urllib.request.urlopen') as mock_urlopen:
        mock_resp = Mock()
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_urlopen.return_value = mock_resp
        
        result = api_client._make_request('GET', '/test', authenticated=True)
    
    assert result == mock_response
    mock_auth.get_access_token.assert_called_once()


def test_make_request_unauthenticated(api_client, mock_config, mock_auth):
    """Test unauthenticated request."""
    mock_response = {'status': 'ok'}
    # Directly replace the config instance on the api_client
    api_client.config = mock_config
    
    with patch('renpy_cloud.api_client.urllib.request.urlopen') as mock_urlopen:
        mock_resp = Mock()
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_urlopen.return_value = mock_resp
        
        result = api_client._make_request('GET', '/test', authenticated=False)
    
    assert result == mock_response
    mock_auth.get_access_token.assert_not_called()


def test_upload_file_success(api_client, mock_config):
    """Test successful file upload."""
    with patch('renpy_cloud.api_client.urllib.request.urlopen') as mock_urlopen:
        api_client.upload_file('https://s3.example.com/upload', b'file data')
    
    mock_urlopen.assert_called_once()


def test_upload_file_failure(api_client, mock_config):
    """Test upload failure raises error."""
    import urllib.error
    
    with patch('renpy_cloud.api_client.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'url', 403, 'Forbidden', {}, None
        )
        
        with pytest.raises(SyncError, match="Upload failed"):
            api_client.upload_file('https://s3.example.com/upload', b'file data')


def test_download_file_success(api_client, mock_config):
    """Test successful file download."""
    with patch('renpy_cloud.api_client.urllib.request.urlopen') as mock_urlopen:
        mock_resp = Mock()
        mock_resp.read.return_value = b'downloaded data'
        mock_urlopen.return_value = mock_resp
        
        content = api_client.download_file('https://s3.example.com/download')
    
    assert content == b'downloaded data'


def test_download_file_failure(api_client, mock_config):
    """Test download failure raises error."""
    import urllib.error
    
    with patch('renpy_cloud.api_client.urllib.request.urlopen') as mock_urlopen:
        mock_urlopen.side_effect = urllib.error.HTTPError(
            'url', 404, 'Not Found', {}, None
        )
        
        with pytest.raises(SyncError, match="Download failed"):
            api_client.download_file('https://s3.example.com/download')


def test_complete_sync(api_client, mock_config, mock_auth):
    """Test sync completion notification."""
    with patch.object(api_client, '_make_request') as mock_request:
        api_client.complete_sync(success=True)
    
    mock_request.assert_called_once()
    call_args = mock_request.call_args
    assert call_args[0][1] == '/sync/complete'
    assert call_args[1]['data']['success'] is True


def test_complete_sync_ignores_errors(api_client, mock_config, mock_auth):
    """Test sync completion ignores errors."""
    with patch.object(api_client, '_make_request', side_effect=Exception("Error")):
        # Should not raise
        api_client.complete_sync(success=False, error="Test error")

