"""Custom exceptions for renpy-cloud."""


class RenpyCloudError(Exception):
    """Base exception for all renpy-cloud errors."""
    pass


class AuthenticationError(RenpyCloudError):
    """Raised when authentication fails."""
    pass


class ConfigurationError(RenpyCloudError):
    """Raised when configuration is invalid or missing."""
    pass


class SyncError(RenpyCloudError):
    """Raised when sync operation fails."""
    pass


class NetworkError(RenpyCloudError):
    """Raised when network operations fail."""
    pass


class StorageError(RenpyCloudError):
    """Raised when storage operations fail."""
    pass

