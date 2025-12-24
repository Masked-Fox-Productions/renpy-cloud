"""Tests for client interface module."""

import pytest
from unittest.mock import Mock, patch
from renpy_cloud.client import (
    configure,
    login,
    signup,
    logout,
    is_authenticated,
    sync_on_start,
    sync_on_quit,
    force_sync,
)


def test_configure():
    """Test configure sets up configuration."""
    with patch('renpy_cloud.client.get_config') as mock_get_config:
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        
        configure(
            api_base_url='https://api.example.com',
            game_id='test_game',
            aws_region='us-east-1',
            cognito_user_pool_id='us-east-1_TEST',
            cognito_app_client_id='test_client',
        )
        
        mock_config.configure.assert_called_once()


def test_login():
    """Test login calls auth manager."""
    with patch('renpy_cloud.client.get_config') as mock_get_config, \
         patch('renpy_cloud.client.get_auth_manager') as mock_get_auth:
        
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        
        mock_auth = Mock()
        mock_auth.login.return_value = True
        mock_get_auth.return_value = mock_auth
        
        result = login('testuser', 'testpass')
        
        assert result is True
        mock_auth.login.assert_called_once_with('testuser', 'testpass')


def test_signup():
    """Test signup calls auth manager."""
    with patch('renpy_cloud.client.get_config') as mock_get_config, \
         patch('renpy_cloud.client.get_auth_manager') as mock_get_auth:
        
        mock_config = Mock()
        mock_get_config.return_value = mock_config
        
        mock_auth = Mock()
        mock_get_auth.return_value = mock_auth
        
        signup('testuser', 'testpass', 'test@example.com')
        
        mock_auth.signup.assert_called_once_with('testuser', 'testpass', 'test@example.com')


def test_logout():
    """Test logout calls auth manager."""
    with patch('renpy_cloud.client.get_auth_manager') as mock_get_auth:
        mock_auth = Mock()
        mock_get_auth.return_value = mock_auth
        
        logout()
        
        mock_auth.logout.assert_called_once()


def test_is_authenticated():
    """Test is_authenticated returns auth status."""
    with patch('renpy_cloud.client.get_auth_manager') as mock_get_auth:
        mock_auth = Mock()
        mock_auth.is_authenticated.return_value = True
        mock_get_auth.return_value = mock_auth
        
        result = is_authenticated()
        
        assert result is True


def test_sync_on_start_not_authenticated():
    """Test sync_on_start skips when not authenticated."""
    with patch('renpy_cloud.client.is_authenticated', return_value=False):
        sync_on_start('/tmp/saves')  # Should not raise


def test_sync_on_start_authenticated(tmp_path):
    """Test sync_on_start performs sync when authenticated."""
    with patch('renpy_cloud.client.is_authenticated', return_value=True), \
         patch('renpy_cloud.client.get_sync_manager') as mock_get_sm:
        
        mock_sm = Mock()
        mock_get_sm.return_value = mock_sm
        
        sync_on_start(str(tmp_path))
        
        mock_sm.sync.assert_called_once_with(force=False)


def test_sync_on_quit_authenticated(tmp_path):
    """Test sync_on_quit forces sync when authenticated."""
    with patch('renpy_cloud.client.is_authenticated', return_value=True), \
         patch('renpy_cloud.client.get_sync_manager') as mock_get_sm:
        
        mock_sm = Mock()
        mock_get_sm.return_value = mock_sm
        
        sync_on_quit(str(tmp_path))
        
        mock_sm.sync.assert_called_once_with(force=True)


def test_force_sync_authenticated(tmp_path):
    """Test force_sync performs sync when authenticated."""
    with patch('renpy_cloud.client.is_authenticated', return_value=True), \
         patch('renpy_cloud.client.get_sync_manager') as mock_get_sm:
        
        mock_sm = Mock()
        mock_sm.sync.return_value = True
        mock_get_sm.return_value = mock_sm
        
        result = force_sync(str(tmp_path))
        
        assert result is True
        mock_sm.sync.assert_called_once_with(force=True)


def test_force_sync_not_authenticated():
    """Test force_sync returns False when not authenticated."""
    with patch('renpy_cloud.client.is_authenticated', return_value=False):
        result = force_sync('/tmp/saves')
        assert result is False

