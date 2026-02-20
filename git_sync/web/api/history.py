"""Sync history API routes."""

from typing import List, Optional
from datetime import datetime
import uuid
from fastapi import APIRouter, HTTPException, Query

from git_sync.web.history import SyncHistoryManager, SyncHistoryRecord
from git_sync.web.schemas import MessageSchema
from git_sync.web.api.config import get_config_manager

router = APIRouter(prefix="/api/history", tags=["history"])


def get_history_manager() -> SyncHistoryManager:
    """Get the history manager instance."""
    config_manager = get_config_manager()
    config_dir = config_manager.find_config_dir() or "configs"
    return SyncHistoryManager(config_dir)


class HistoryRecordSchema(SyncHistoryRecord.__class__):
    """Schema for history record response."""
    pass


@router.get("", response_model=List[dict])
async def list_history(
    repository: Optional[str] = Query(None, description="Filter by repository name"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
):
    """Get sync history records."""
    try:
        manager = get_history_manager()
        records = manager.get_records(repository=repository, limit=limit, offset=offset)
        return [r.to_dict() for r in records]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_statistics():
    """Get sync statistics."""
    try:
        manager = get_history_manager()
        return manager.get_statistics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{record_id}", response_model=dict)
async def get_record(record_id: str):
    """Get a specific history record."""
    try:
        manager = get_history_manager()
        record = manager.get_record(record_id)
        if not record:
            raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")
        return record.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{record_id}", response_model=MessageSchema)
async def delete_record(record_id: str):
    """Delete a specific history record."""
    try:
        manager = get_history_manager()
        if not manager.delete_record(record_id):
            raise HTTPException(status_code=404, detail=f"Record '{record_id}' not found")
        return MessageSchema(message=f"Record '{record_id}' deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("", response_model=MessageSchema)
async def clear_history(repository: Optional[str] = Query(None, description="Only clear for this repository")):
    """Clear sync history."""
    try:
        manager = get_history_manager()
        cleared = manager.clear_history(repository=repository)
        return MessageSchema(message=f"Cleared {cleared} history records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def save_sync_record(
    repository: str,
    success: bool,
    message: str,
    branches_synced: List[str] = None,
    tags_synced: int = 0,
    duration: float = 0.0,
    error: str = None,
) -> SyncHistoryRecord:
    """Save a sync record to history.

    This is a helper function to be called from the sync API.

    Args:
        repository: Repository name
        success: Whether sync succeeded
        message: Result message
        branches_synced: List of synced branches
        tags_synced: Number of synced tags
        duration: Sync duration in seconds
        error: Error message if failed

    Returns:
        The created record
    """
    manager = get_history_manager()
    record = SyncHistoryRecord(
        id=str(uuid.uuid4())[:8],
        repository=repository,
        timestamp=datetime.now().isoformat(),
        success=success,
        message=message,
        branches_synced=branches_synced or [],
        tags_synced=tags_synced,
        duration=duration,
        error=error,
    )
    manager.add_record(record)
    return record
