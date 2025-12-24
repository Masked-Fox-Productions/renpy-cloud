"""Tests for configuration module."""

import pytest
from renpy_cloud.config import Config, get_config
from renpy_cloud.exceptions import ConfigurationError


def test_config_initialization():
    """Test Config initializes with defaults."""
    config = Config()
    assert config.api_base_url is None
    assert config.game_id is None
    assert config.sync_interval_seconds == 300
    assert not config.is_configured()


def test_config_configure():
    """Test configuration sets all values."""
    config = Config()
    config.configure(
        api_base_url="https://api.example.com",
        game_id="test_game",
        aws_region="us-east-1",
        cognito_user_pool_id="us-east-1_TEST",
        cognito_app_client_id="test_client_id",
        sync_interval_seconds=600,
    )
    
    assert config.api_base_url == "https://api.example.com"
    assert config.game_id == "test_game"
    assert config.aws_region == "us-east-1"
    assert config.cognito_user_pool_id == "us-east-1_TEST"
    assert config.cognito_app_client_id == "test_client_id"
    assert config.sync_interval_seconds == 600
    assert config.is_configured()


def test_config_strips_trailing_slash():
    """Test that trailing slash is removed from API URL."""
    config = Config()
    config.configure(
        api_base_url="https://api.example.com/",
        game_id="test_game",
        aws_region="us-east-1",
        cognito_user_pool_id="us-east-1_TEST",
        cognito_app_client_id="test_client_id",
    )
    
    assert config.api_base_url == "https://api.example.com"


def test_config_validate_not_configured():
    """Test validation fails when not configured."""
    config = Config()
    with pytest.raises(ConfigurationError, match="not configured"):
        config.validate()


def test_config_validate_missing_fields():
    """Test validation fails with missing required fields."""
    config = Config()
    config._configured = True
    config.api_base_url = "https://api.example.com"
    # Missing other required fields
    
    with pytest.raises(ConfigurationError, match="Missing required configuration"):
        config.validate()


def test_config_validate_success():
    """Test validation succeeds with all fields."""
    config = Config()
    config.configure(
        api_base_url="https://api.example.com",
        game_id="test_game",
        aws_region="us-east-1",
        cognito_user_pool_id="us-east-1_TEST",
        cognito_app_client_id="test_client_id",
    )
    
    # Should not raise
    config.validate()


def test_get_config_singleton():
    """Test get_config returns same instance."""
    config1 = get_config()
    config2 = get_config()
    assert config1 is config2

