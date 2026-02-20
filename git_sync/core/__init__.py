"""Core modules for git-sync."""

from git_sync.core.exceptions import (
    GitSyncError,
    ConfigurationError,
    SSHKeyError,
    RepositoryError,
    SyncError,
    AuthenticationError,
)

# Lazy imports to avoid circular dependencies
__all__ = [
    "GitSyncError",
    "ConfigurationError",
    "SSHKeyError",
    "RepositoryError",
    "SyncError",
    "AuthenticationError",
    "Repository",
    "SyncOrchestrator",
    "SyncResult",
    "SyncSummary",
]


def __getattr__(name):
    """Lazy import to avoid circular dependencies."""
    if name == "Repository":
        from git_sync.core.repository import Repository
        return Repository
    elif name == "SyncOrchestrator":
        from git_sync.core.sync import SyncOrchestrator
        return SyncOrchestrator
    elif name == "SyncResult":
        from git_sync.core.sync import SyncResult
        return SyncResult
    elif name == "SyncSummary":
        from git_sync.core.sync import SyncSummary
        return SyncSummary
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
