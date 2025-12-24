"""Tests for authentication module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from renpy_cloud.auth import AuthManager, get_auth_manager
from renpy_cloud.exceptions import AuthenticationError, NetworkError


@pytest.fixture
def auth_manager():
    """Create a fresh AuthManager for each test."""
    return AuthManager()


@pytest.fixture
def configured_config():
    """Mock a configured config."""
    with patch('renpy_cloud.auth.get_config') as mock_config:
        config = Mock()
        config.aws_region = 'us-east-1'
        config.cognito_app_client_id = 'test_client_id'
        config.timeout_seconds = 30
        mock_config.return_value = config
        yield config


def test_auth_manager_initialization(auth_manager):
    """Test AuthManager initializes with no tokens."""
    assert auth_manager.access_token is None
    assert auth_manager.refresh_token is None
    assert auth_manager.id_token is None
    assert not auth_manager.is_authenticated()


def test_login_success(auth_manager, configured_config):
    """Test successful login."""
    mock_response = {
        'AuthenticationResult': {
            'AccessToken': 'test_access_token',
            'RefreshToken': 'test_refresh_token',
            'IdToken': 'test_id_token',
            'ExpiresIn': 3600,
        }
    }
    
    with patch.object(auth_manager, '_make_cognito_request', return_value=mock_response):
        result = auth_manager.login('testuser', 'testpass')
    
    assert result is True
    assert auth_manager.access_token == 'test_access_token'
    assert auth_manager.refresh_token == 'test_refresh_token'
    assert auth_manager.id_token == 'test_id_token'
    assert auth_manager.username == 'testuser'
    assert auth_manager.is_authenticated()


def test_login_failure(auth_manager, configured_config):
    """Test login failure."""
    with patch.object(
        auth_manager,
        '_make_cognito_request',
        side_effect=AuthenticationError("Invalid credentials")
    ):
        with pytest.raises(AuthenticationError, match="Invalid credentials"):
            auth_manager.login('testuser', 'wrongpass')


def test_signup_success(auth_manager, configured_config):
    """Test successful signup."""
    mock_response = {
        'UserConfirmed': False,
        'UserSub': 'test-user-id',
    }
    
    with patch.object(auth_manager, '_make_cognito_request', return_value=mock_response):
        # Should not raise
        auth_manager.signup('testuser', 'TestPass123', 'test@example.com')


def test_refresh_tokens_success(auth_manager, configured_config):
    """Test successful token refresh."""
    # Set initial tokens
    auth_manager.refresh_token = 'old_refresh_token'
    auth_manager.access_token = 'old_access_token'
    
    mock_response = {
        'AuthenticationResult': {
            'AccessToken': 'new_access_token',
            'IdToken': 'new_id_token',
            'ExpiresIn': 3600,
        }
    }
    
    with patch.object(auth_manager, '_make_cognito_request', return_value=mock_response):
        result = auth_manager.refresh_tokens()
    
    assert result is True
    assert auth_manager.access_token == 'new_access_token'
    assert auth_manager.id_token == 'new_id_token'
    assert auth_manager.refresh_token == 'old_refresh_token'  # Unchanged


def test_refresh_tokens_no_refresh_token(auth_manager):
    """Test refresh fails without refresh token."""
    with pytest.raises(AuthenticationError, match="No refresh token"):
        auth_manager.refresh_tokens()


def test_logout(auth_manager):
    """Test logout clears all tokens."""
    auth_manager.access_token = 'test_token'
    auth_manager.refresh_token = 'test_refresh'
    auth_manager.id_token = 'test_id'
    auth_manager.username = 'testuser'
    
    auth_manager.logout()
    
    assert auth_manager.access_token is None
    assert auth_manager.refresh_token is None
    assert auth_manager.id_token is None
    assert auth_manager.username is None
    assert not auth_manager.is_authenticated()


def test_get_access_token_not_authenticated(auth_manager):
    """Test getting access token when not authenticated."""
    with pytest.raises(AuthenticationError, match="Not authenticated"):
        auth_manager.get_access_token()


def test_get_access_token_valid(auth_manager):
    """Test getting access token when valid."""
    auth_manager.access_token = 'valid_token'
    auth_manager.token_expiry = datetime.now() + timedelta(hours=1)
    
    token = auth_manager.get_access_token()
    assert token == 'valid_token'


def test_get_access_token_expired_refreshes(auth_manager, configured_config):
    """Test getting access token refreshes when about to expire."""
    auth_manager.access_token = 'old_token'
    auth_manager.refresh_token = 'refresh_token'
    auth_manager.token_expiry = datetime.now() + timedelta(minutes=2)  # Expires soon
    
    mock_response = {
        'AuthenticationResult': {
            'AccessToken': 'new_token',
            'IdToken': 'new_id_token',
            'ExpiresIn': 3600,
        }
    }
    
    with patch.object(auth_manager, '_make_cognito_request', return_value=mock_response):
        token = auth_manager.get_access_token()
    
    assert token == 'new_token'


def test_get_auth_manager_singleton():
    """Test get_auth_manager returns same instance."""
    manager1 = get_auth_manager()
    manager2 = get_auth_manager()
    assert manager1 is manager2

