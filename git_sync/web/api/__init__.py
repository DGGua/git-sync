"""API routes for git-sync web frontend."""

from git_sync.web.api.config import router as config_router
from git_sync.web.api.repositories import router as repositories_router
from git_sync.web.api.keys import router as keys_router
from git_sync.web.api.sync import router as sync_router
from git_sync.web.api.history import router as history_router
from git_sync.web.api.scheduler import router as scheduler_router

__all__ = [
    "config_router",
    "repositories_router",
    "keys_router",
    "sync_router",
    "history_router",
    "scheduler_router",
]
