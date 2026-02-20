"""Custom exceptions for git-sync."""


class GitSyncError(Exception):
    """Base exception for git-sync errors."""

    pass


class ConfigurationError(GitSyncError):
    """Error in configuration file."""

    pass


class SSHKeyError(GitSyncError):
    """Error related to SSH key operations."""

    pass


class RepositoryError(GitSyncError):
    """Error related to repository operations."""

    pass


class SyncError(GitSyncError):
    """Error during synchronization."""

    pass


class AuthenticationError(GitSyncError):
    """Error related to authentication."""

    pass
