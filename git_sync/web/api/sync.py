"""Sync operation API routes."""

import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks

from git_sync.config.loader import ConfigManager
from git_sync.core.sync import SyncOrchestrator
from git_sync.core.repository import Repository
from git_sync.web.schemas import (
    SyncRequestSchema,
    SyncResponseSchema,
    SyncResultSchema,
    MessageSchema,
)
from git_sync.web.api.config import get_config_manager
from git_sync.web.api.history import save_sync_record

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncResponseSchema)
async def sync_repositories(sync_request: SyncRequestSchema):
    """Execute sync operation.

    If repository is specified, sync only that repository.
    Otherwise, sync all enabled repositories.
    """
    try:
        manager = get_config_manager()

        # Determine which repositories to sync
        if sync_request.repository:
            repo_config = manager.get_repository(sync_request.repository)
            if not repo_config:
                raise HTTPException(
                    status_code=404,
                    detail=f"Repository '{sync_request.repository}' not found"
                )
            repos_to_sync = [repo_config]
        else:
            repos_to_sync = manager.get_enabled_repositories()

        if not repos_to_sync:
            return SyncResponseSchema(
                results=[],
                total_synced=0,
                total_failed=0,
            )

        # Execute sync for each repository
        results = []
        orchestrator = SyncOrchestrator(manager)

        for repo_config in repos_to_sync:
            try:
                if sync_request.dry_run:
                    # For dry run, just report what would be done
                    results.append(SyncResultSchema(
                        repository=repo_config.name,
                        success=True,
                        message="Dry run - no changes made",
                        branches_synced=repo_config.sync_branches or ["all"],
                        tags_synced=0,
                    ))
                else:
                    # Execute actual sync
                    sync_result = orchestrator.sync_repository(repo_config)
                    results.append(SyncResultSchema(
                        repository=repo_config.name,
                        success=sync_result.success,
                        message=sync_result.error or "Sync completed",
                        branches_synced=sync_result.branches_synced,
                        tags_synced=len(sync_result.tags_synced),
                    ))
            except Exception as e:
                results.append(SyncResultSchema(
                    repository=repo_config.name,
                    success=False,
                    message=str(e),
                    branches_synced=[],
                    tags_synced=0,
                ))

        # Calculate totals
        total_synced = sum(1 for r in results if r.success)
        total_failed = len(results) - total_synced

        return SyncResponseSchema(
            results=results,
            total_synced=total_synced,
            total_failed=total_failed,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{name}", response_model=SyncResultSchema)
async def sync_single_repository(name: str, dry_run: bool = False):
    """Sync a single repository by name."""
    start_time = time.time()
    try:
        manager = get_config_manager()

        repo_config = manager.get_repository(name)
        if not repo_config:
            raise HTTPException(status_code=404, detail=f"Repository '{name}' not found")

        if dry_run:
            return SyncResultSchema(
                repository=name,
                success=True,
                message="Dry run - no changes made",
                branches_synced=repo_config.sync_branches or ["all"],
                tags_synced=0,
            )

        orchestrator = SyncOrchestrator(manager)
        sync_result = orchestrator.sync_repository(repo_config)

        duration = time.time() - start_time
        message = sync_result.error or "Sync completed"

        # Save to history
        save_sync_record(
            repository=name,
            success=sync_result.success,
            message=message,
            branches_synced=sync_result.branches_synced,
            tags_synced=len(sync_result.tags_synced),
            duration=duration,
            error=sync_result.error,
        )

        return SyncResultSchema(
            repository=name,
            success=sync_result.success,
            message=message,
            branches_synced=sync_result.branches_synced,
            tags_synced=len(sync_result.tags_synced),
        )
    except HTTPException:
        raise
    except Exception as e:
        duration = time.time() - start_time
        # Save failed sync to history
        save_sync_record(
            repository=name,
            success=False,
            message=str(e),
            branches_synced=[],
            tags_synced=0,
            duration=duration,
            error=str(e),
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=MessageSchema)
async def get_sync_status():
    """Get current sync status (placeholder for future implementation)."""
    return MessageSchema(
        message="No active sync operations",
        success=True,
    )
