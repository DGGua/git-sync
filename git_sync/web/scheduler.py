"""Background scheduler for automatic sync."""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class SyncScheduler:
    """Background scheduler for automatic repository sync."""

    def __init__(self, config_manager):
        """Initialize the scheduler.

        Args:
            config_manager: ConfigManager instance for accessing configuration
        """
        self.scheduler = AsyncIOScheduler()
        self.config_manager = config_manager
        self._is_running = False

    @property
    def is_running(self) -> bool:
        """Check if the scheduler is running."""
        return self._is_running

    def start(self):
        """Start the scheduler and schedule jobs for enabled repositories."""
        self._schedule_jobs()
        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler stopped")

    def reload(self):
        """Reload configuration and reschedule all jobs."""
        self.stop()
        self.config_manager.reload()
        self.start()

    def _schedule_jobs(self):
        """Schedule sync jobs for each enabled repository."""
        # Remove all existing jobs
        for job in self.scheduler.get_jobs():
            if job.id.startswith("sync_"):
                self.scheduler.remove_job(job.id)

        # Schedule jobs for each repository with auto_sync_enabled
        repos = self.config_manager.get_enabled_repositories()
        scheduled_count = 0

        for repo in repos:
            if repo.auto_sync_enabled:
                job_id = f"sync_{repo.name}"
                interval = repo.auto_sync_interval
                interval_hours = interval / 3600

                self.scheduler.add_job(
                    self._create_sync_job(repo.name),
                    IntervalTrigger(seconds=interval),
                    id=job_id,
                    replace_existing=True,
                    misfire_grace_time=3600,  # Allow 1 hour grace period for missed jobs
                    coalesce=True,  # Combine multiple missed runs into one
                )
                scheduled_count += 1
                logger.info(
                    f"Scheduled sync for '{repo.name}' every {interval_hours:.1f} hours"
                )

        logger.info(f"Scheduled {scheduled_count} repository sync jobs")

    def _create_sync_job(self, repo_name: str):
        """Create a sync job function for a specific repository."""
        async def sync_job():
            await self._run_sync_for_repo(repo_name)
        return sync_job

    async def _run_sync_for_repo(self, repo_name: str):
        """Execute sync for a specific repository."""
        from git_sync.core.sync import SyncOrchestrator
        from git_sync.web.api.history import save_sync_record
        import time

        logger.info(f"Starting scheduled sync for '{repo_name}'")

        # Find the repository
        repo = self.config_manager.get_repository(repo_name)
        if not repo:
            logger.warning(f"Repository '{repo_name}' not found, skipping")
            return

        if not repo.enabled or not repo.auto_sync_enabled:
            logger.info(f"Repository '{repo_name}' is disabled, skipping")
            return

        orchestrator = SyncOrchestrator(self.config_manager)
        start = time.time()

        try:
            result = orchestrator.sync_repository(repo)
            save_sync_record(
                repository=repo.name,
                success=result.success,
                message=result.error or "Auto sync completed",
                branches_synced=result.branches_synced,
                tags_synced=len(result.tags_synced),
                duration=time.time() - start,
                error=result.error,
            )
            status = "succeeded" if result.success else "failed"
            logger.info(f"Scheduled sync for '{repo_name}' {status}")
        except Exception as e:
            logger.error(f"Error syncing '{repo_name}': {e}")
            save_sync_record(
                repository=repo.name,
                success=False,
                message=str(e),
                duration=time.time() - start,
                error=str(e),
            )

    def get_status(self) -> dict:
        """Get the current scheduler status."""
        jobs = []
        for job in self.scheduler.get_jobs():
            if job.id.startswith("sync_"):
                repo_name = job.id[5:]  # Remove "sync_" prefix
                jobs.append({
                    "repository": repo_name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                })

        return {
            "is_running": self._is_running,
            "scheduled_repositories": jobs,
        }

    async def run_sync_now(self, repo_name: str = None):
        """Trigger an immediate sync.

        Args:
            repo_name: Specific repository to sync, or None for all enabled repos
        """
        if repo_name:
            await self._run_sync_for_repo(repo_name)
        else:
            repos = self.config_manager.get_enabled_repositories()
            for repo in repos:
                if repo.auto_sync_enabled:
                    await self._run_sync_for_repo(repo.name)
