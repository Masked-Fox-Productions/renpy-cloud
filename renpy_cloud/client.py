"""Main client interface for Ren'Py integration."""

import os
from typing import Optional

from .config import get_config
from .auth import get_auth_manager
from .sync_manager import get_sync_manager
from .exceptions import ConfigurationError, AuthenticationError


def configure(
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
    
    This should be called once during game initialization, typically in an
    `init python` block.
    
    Args:
        api_base_url: Base URL of the API Gateway endpoint
        game_id: Unique identifier for your game
        aws_region: AWS region (e.g., 'us-east-1')
        cognito_user_pool_id: Cognito User Pool ID
        cognito_app_client_id: Cognito App Client ID
        sync_interval_seconds: Minimum seconds between syncs (default: 300)
        max_retries: Maximum retry attempts for failed operations
        timeout_seconds: Timeout for network requests
    
    Example:
        ```python
        init python:
            import renpy_cloud
            
            renpy_cloud.configure(
                api_base_url="https://your-api-id.execute-api.us-east-1.amazonaws.com",
                game_id="my_game_id",
                aws_region="us-east-1",
                cognito_user_pool_id="us-east-1_XXXXXXX",
                cognito_app_client_id="YYYYYYYYYYYY",
            )
        ```
    """
    config = get_config()
    config.configure(
        api_base_url=api_base_url,
        game_id=game_id,
        aws_region=aws_region,
        cognito_user_pool_id=cognito_user_pool_id,
        cognito_app_client_id=cognito_app_client_id,
        sync_interval_seconds=sync_interval_seconds,
        max_retries=max_retries,
        timeout_seconds=timeout_seconds,
    )


def login(username: str, password: str) -> bool:
    """
    Log in a user.
    
    Args:
        username: Username
        password: Password
    
    Returns:
        True if login successful
    
    Raises:
        AuthenticationError: If login fails
        ConfigurationError: If not configured
    
    Example:
        ```python
        try:
            if renpy_cloud.login(username, password):
                renpy.notify("Logged in successfully!")
        except renpy_cloud.AuthenticationError as e:
            renpy.notify(f"Login failed: {e}")
        ```
    """
    config = get_config()
    config.validate()
    
    auth = get_auth_manager()
    return auth.login(username, password)


def signup(username: str, password: str, email: str) -> None:
    """
    Sign up a new user.
    
    Args:
        username: Username for the new account
        password: Password (must meet Cognito requirements)
        email: Email address for verification
    
    Raises:
        AuthenticationError: If signup fails
        ConfigurationError: If not configured
    
    Example:
        ```python
        try:
            renpy_cloud.signup(username, password, email)
            renpy.notify("Account created! Please check your email.")
        except renpy_cloud.AuthenticationError as e:
            renpy.notify(f"Signup failed: {e}")
        ```
    """
    config = get_config()
    config.validate()
    
    auth = get_auth_manager()
    auth.signup(username, password, email)


def logout() -> None:
    """
    Log out the current user.
    
    Example:
        ```python
        renpy_cloud.logout()
        renpy.notify("Logged out")
        ```
    """
    auth = get_auth_manager()
    auth.logout()


def is_authenticated() -> bool:
    """
    Check if a user is currently authenticated.
    
    Returns:
        True if authenticated
    
    Example:
        ```python
        if renpy_cloud.is_authenticated():
            textbutton "Sync Now" action Function(renpy_cloud.force_sync)
        else:
            textbutton "Log In" action Jump("login_screen")
        ```
    """
    auth = get_auth_manager()
    return auth.is_authenticated()


def sync_on_start(save_dir: Optional[str] = None) -> None:
    """
    Perform sync when the game starts.
    
    This respects the sync interval throttling, so it won't sync if a sync
    was recently performed.
    
    Args:
        save_dir: Directory containing save files (auto-detected if None)
    
    Example:
        ```python
        label start:
            $ renpy_cloud.sync_on_start()
            # Rest of your game...
        ```
    """
    if not is_authenticated():
        return
    
    # Auto-detect save directory if not provided
    if save_dir is None:
        try:
            import renpy
            save_dir = os.path.join(renpy.config.savedir)
        except:
            # Fallback if renpy not available (e.g., testing)
            save_dir = os.path.expanduser('~/.renpy/saves')
    
    try:
        sync_manager = get_sync_manager(save_dir)
        sync_manager.sync(force=False)
    except Exception as e:
        # Never block game startup due to sync failures
        print(f"[renpy-cloud] Sync on start failed: {e}")


def sync_on_quit(save_dir: Optional[str] = None) -> None:
    """
    Perform sync when the game quits.
    
    This forces a sync regardless of the throttle interval.
    
    Args:
        save_dir: Directory containing save files (auto-detected if None)
    
    Example:
        ```python
        init python:
            config.quit_action = renpy_cloud.sync_on_quit
        ```
    """
    if not is_authenticated():
        return
    
    # Auto-detect save directory if not provided
    if save_dir is None:
        try:
            import renpy
            save_dir = os.path.join(renpy.config.savedir)
        except:
            save_dir = os.path.expanduser('~/.renpy/saves')
    
    try:
        sync_manager = get_sync_manager(save_dir)
        sync_manager.sync(force=True)
    except Exception as e:
        # Never block game quit due to sync failures
        print(f"[renpy-cloud] Sync on quit failed: {e}")


def force_sync(save_dir: Optional[str] = None) -> bool:
    """
    Force an immediate sync, bypassing throttling.
    
    Args:
        save_dir: Directory containing save files (auto-detected if None)
    
    Returns:
        True if sync was performed
    
    Example:
        ```python
        textbutton "Sync Now" action Function(renpy_cloud.force_sync)
        ```
    """
    if not is_authenticated():
        return False
    
    # Auto-detect save directory if not provided
    if save_dir is None:
        try:
            import renpy
            save_dir = os.path.join(renpy.config.savedir)
        except:
            save_dir = os.path.expanduser('~/.renpy/saves')
    
    try:
        sync_manager = get_sync_manager(save_dir)
        return sync_manager.sync(force=True)
    except Exception as e:
        print(f"[renpy-cloud] Force sync failed: {e}")
        return False

