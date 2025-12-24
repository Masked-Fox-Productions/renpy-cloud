"""
renpy-cloud: Cloud save synchronization for Ren'Py games.

A lightweight, serverless cloud sync solution for Ren'Py that synchronizes
persistent data and save files across devices using AWS infrastructure.
"""

from .client import (
    configure,
    sync_on_start,
    sync_on_quit,
    force_sync,
    login,
    signup,
    logout,
    is_authenticated,
)
from .exceptions import (
    RenpyCloudError,
    AuthenticationError,
    ConfigurationError,
    SyncError,
)

__version__ = "0.1.0"
__all__ = [
    "configure",
    "sync_on_start",
    "sync_on_quit",
    "force_sync",
    "login",
    "signup",
    "logout",
    "is_authenticated",
    "RenpyCloudError",
    "AuthenticationError",
    "ConfigurationError",
    "SyncError",
]

