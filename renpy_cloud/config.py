"""Configuration management for renpy-cloud."""

from typing import Optional
from .exceptions import ConfigurationError


class Config:
    """Global configuration singleton for renpy-cloud."""
    
    def __init__(self):
        self.api_base_url: Optional[str] = None
        self.game_id: Optional[str] = None
        self.aws_region: Optional[str] = None
        self.cognito_user_pool_id: Optional[str] = None
        self.cognito_app_client_id: Optional[str] = None
        self.sync_interval_seconds: int = 300  # 5 minutes
        self.max_retries: int = 3
        self.timeout_seconds: int = 30
        self._configured: bool = False
    
    def configure(
        self,
        api_base_url: str,
        game_id: str,
        aws_region: str,
        cognito_user_pool_id: str,
        cognito_app_client_id: str,
        sync_interval_seconds: int = 300,
        max_retries: int = 3,
        timeout_seconds: int = 30,
    ) -> None:
        """
        Configure the renpy-cloud client.
        
        Args:
            api_base_url: Base URL of the API Gateway endpoint
            game_id: Unique identifier for your game
            aws_region: AWS region (e.g., 'us-east-1')
            cognito_user_pool_id: Cognito User Pool ID
            cognito_app_client_id: Cognito App Client ID
            sync_interval_seconds: Minimum seconds between syncs (default: 300)
            max_retries: Maximum retry attempts for failed operations
            timeout_seconds: Timeout for network requests
        """
        self.api_base_url = api_base_url.rstrip('/')
        self.game_id = game_id
        self.aws_region = aws_region
        self.cognito_user_pool_id = cognito_user_pool_id
        self.cognito_app_client_id = cognito_app_client_id
        self.sync_interval_seconds = sync_interval_seconds
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._configured = True
    
    def validate(self) -> None:
        """Validate that all required configuration is set."""
        if not self._configured:
            raise ConfigurationError(
                "renpy-cloud not configured. Call renpy_cloud.configure() first."
            )
        
        required = {
            'api_base_url': self.api_base_url,
            'game_id': self.game_id,
            'aws_region': self.aws_region,
            'cognito_user_pool_id': self.cognito_user_pool_id,
            'cognito_app_client_id': self.cognito_app_client_id,
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ConfigurationError(
                f"Missing required configuration: {', '.join(missing)}"
            )
    
    def is_configured(self) -> bool:
        """Check if configuration is complete."""
        return self._configured and all([
            self.api_base_url,
            self.game_id,
            self.aws_region,
            self.cognito_user_pool_id,
            self.cognito_app_client_id,
        ])


# Global config instance
_config = Config()


def get_config() -> Config:
    """Get the global configuration instance."""
    return _config

