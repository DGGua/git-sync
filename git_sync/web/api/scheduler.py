"""Scheduler API routes."""

from fastapi import APIRouter, HTTPException, Query

from git_sync.web.schemas import MessageSchema

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])

# Global scheduler instance (set from app.py)
_scheduler = None


def set_scheduler(scheduler):
    """Set the global scheduler instance."""
    global _scheduler
    _scheduler = scheduler


def get_scheduler():
    """Get the global scheduler instance."""
    if _scheduler is None:
        raise HTTPException(status_code=503, detail="Scheduler not initialized")
    return _scheduler


@router.get("")
async def get_scheduler_status():
    """Get the current scheduler status."""
    scheduler = get_scheduler()
    return scheduler.get_status()


@router.post("/reload", response_model=MessageSchema)
async def reload_scheduler():
    """Reload configuration and restart the scheduler."""
    scheduler = get_scheduler()
    try:
        scheduler.reload()
        return MessageSchema(message="Scheduler reloaded successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start", response_model=MessageSchema)
async def start_scheduler():
    """Manually start the scheduler."""
    scheduler = get_scheduler()
    try:
        if scheduler.is_running:
            return MessageSchema(message="Scheduler is already running")
        scheduler.start()
        return MessageSchema(message="Scheduler started successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=MessageSchema)
async def stop_scheduler():
    """Stop the scheduler."""
    scheduler = get_scheduler()
    try:
        if not scheduler.is_running:
            return MessageSchema(message="Scheduler is not running")
        scheduler.stop()
        return MessageSchema(message="Scheduler stopped successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run", response_model=MessageSchema)
async def run_sync_now(
    repository: str = Query(None, description="Specific repository to sync, or all if not specified")
):
    """Trigger an immediate sync."""
    scheduler = get_scheduler()
    try:
        await scheduler.run_sync_now(repository)
        if repository:
            return MessageSchema(message=f"Sync triggered for '{repository}'")
        return MessageSchema(message="Sync triggered for all enabled repositories")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
