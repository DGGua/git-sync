"""Sync orchestration for repository synchronization."""

import shutil
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from git_sync.config.loader import ConfigManager
from git_sync.config.schema import RepositoryConfig
from git_sync.core.exceptions import SyncError, ConfigurationError
from git_sync.core.repository import Repository
from git_sync.ssh.key_manager import KeyManager
from git_sync.utils.logger import logger


@dataclass
class SyncResult:
    """Result of a single repository sync."""

    repository: str
    success: bool
    branches_synced: List[str]
    branches_skipped: List[Tuple[str, str]]  # (branch, reason)
    tags_synced: List[str]
    tags_failed: List[Tuple[str, str]]  # (tag, reason)
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class SyncSummary:
    """Summary of all sync operations."""

    total: int
    successful: int
    failed: int
    results: List[SyncResult]
    start_time: datetime
    end_time: datetime

    @property
    def duration(self) -> float:
        """Total duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()


class SyncOrchestrator:
    """Orchestrates repository synchronization."""

    def __init__(
        self,
        config_manager: ConfigManager,
        key_manager: Optional[KeyManager] = None,
        dry_run: bool = False,
    ):
        """Initialize sync orchestrator.

        Args:
            config_manager: Configuration manager
            key_manager: SSH key manager
            dry_run: Dry run mode (no actual changes)
        """
        self.config_manager = config_manager
        self.dry_run = dry_run

        # Initialize key manager with storage path from config
        if key_manager:
            self.key_manager = key_manager
        else:
            config = config_manager.config
            self.key_manager = KeyManager(config.ssh.key_storage)

    def _get_key_path(self, key_name: str) -> str:
        """Get full path to SSH key.

        Args:
            key_name: Key name

        Returns:
            Full path to key file
        """
        return str(self.key_manager.get(key_name))

    def _create_temp_dir(self, base_dir: str, repo_name: str) -> Path:
        """Create temporary directory for sync operations.

        Args:
            base_dir: Base temporary directory
            repo_name: Repository name

        Returns:
            Path to temporary directory
        """
        base_path = Path(base_dir)
        base_path.mkdir(parents=True, exist_ok=True)

        # Create unique directory for this repo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        temp_dir = base_path / f"{repo_name}_{timestamp}"
        temp_dir.mkdir(parents=True, exist_ok=True)

        return temp_dir

    def _get_mirror_path(self, repo_name: str) -> Path:
        """Get the mirror cache path for a repository.

        Args:
            repo_name: Repository name

        Returns:
            Path to mirror cache directory
        """
        config = self.config_manager.config
        mirror_base = Path(config.sync.mirror_cache_dir)
        mirror_base.mkdir(parents=True, exist_ok=True)
        return mirror_base / f"{repo_name}.git"

    def _ensure_mirror(self, repo_url: str, repo_name: str, ssh_key_path: str) -> Path:
        """Ensure local mirror exists and is up-to-date.

        Args:
            repo_url: Source repository URL
            repo_name: Repository name
            ssh_key_path: Path to SSH key

        Returns:
            Path to mirror cache directory
        """
        mirror_path = self._get_mirror_path(repo_name)

        if mirror_path.exists():
            # Mirror exists, update incrementally
            logger.info(f"Updating mirror cache: {repo_name}")
            repo = Repository(
                url=repo_url, ssh_key_path=ssh_key_path, work_dir=str(mirror_path)
            )
            repo.fetch("origin")
        else:
            # First time, create mirror
            logger.info(f"Creating mirror cache: {repo_name}")
            repo = Repository(url=repo_url, ssh_key_path=ssh_key_path)
            repo.clone(str(mirror_path), mirror=True)

        return mirror_path

    def _cleanup_stale_mirrors(self, active_repos: List[str]):
        """Clean up mirrors for repos no longer in configuration.

        Args:
            active_repos: List of active repository names
        """
        config = self.config_manager.config
        mirror_base = Path(config.sync.mirror_cache_dir)

        if not mirror_base.exists():
            return

        # Get all existing mirrors
        existing_mirrors = set()
        for item in mirror_base.iterdir():
            if item.is_dir() and item.name.endswith(".git"):
                # Extract repo name (remove .git suffix)
                repo_name = item.name[:-4]
                existing_mirrors.add(repo_name)

        # Repos to keep
        active_repo_names = set(active_repos)

        # Find stale mirrors to delete
        stale_mirrors = existing_mirrors - active_repo_names

        for repo_name in stale_mirrors:
            mirror_path = mirror_base / f"{repo_name}.git"
            try:
                shutil.rmtree(mirror_path)
                logger.info(f"Removed stale mirror cache: {repo_name}")
            except Exception as e:
                logger.warning(f"Failed to remove stale mirror {repo_name}: {e}")

    def sync_repository(self, repo_config: RepositoryConfig) -> SyncResult:
        """Synchronize a single repository.

        Args:
            repo_config: Repository configuration

        Returns:
            SyncResult with sync details
        """
        start_time = datetime.now()
        logger.info(f"Starting sync for repository: {repo_config.name}")

        result = SyncResult(
            repository=repo_config.name,
            success=False,
            branches_synced=[],
            branches_skipped=[],
            tags_synced=[],
            tags_failed=[],
        )

        temp_dir = None

        try:
            # Get SSH key paths
            source_key = self._get_key_path(repo_config.source.ssh_key)
            target_key = self._get_key_path(repo_config.target.ssh_key)

            # Get temp directory from config
            config = self.config_manager.config
            temp_base = config.sync.temp_dir

            # Create temp directory
            temp_dir = self._create_temp_dir(temp_base, repo_config.name)

            if config.sync.enable_mirror_cache:
                # Use mirror cache for faster syncs
                mirror_path = self._ensure_mirror(
                    repo_config.source.url, repo_config.name, source_key
                )
                # Copy mirror to temp directory
                clone_dir = str(temp_dir / "source.git")
                shutil.copytree(mirror_path, clone_dir)
                source_repo = Repository(
                    url=repo_config.source.url,
                    ssh_key_path=source_key,
                    work_dir=clone_dir,
                )
            else:
                # Original logic: full clone
                clone_dir = str(temp_dir / "source.git")
                source_repo = Repository(
                    url=repo_config.source.url,
                    ssh_key_path=source_key,
                )
                source_repo.clone(clone_dir, bare=True)

            # Add target as remote
            target_repo = Repository(
                url=repo_config.target.url,
                ssh_key_path=target_key,
                work_dir=clone_dir,
            )
            target_repo.add_remote("target", repo_config.target.url)

            # Fetch target to compare
            logger.info("Fetching target repository state...")
            target_repo.fetch("target")

            # Determine branches to sync
            # 在裸仓库中，分支存储在 refs/heads/ 而不是 refs/remotes/origin/
            if repo_config.sync_branches:
                branches_to_sync = repo_config.sync_branches
            else:
                branches_to_sync = target_repo.get_local_branches()

            logger.info(f"Branches to sync: {branches_to_sync}")

            # Sync branches
            for branch in branches_to_sync:
                try:
                    # Get source branch hash (裸仓库中分支直接在 refs/heads/ 下)
                    source_hash = target_repo.get_ref_hash(f"refs/heads/{branch}")

                    if not source_hash:
                        logger.warning(f"Branch '{branch}' not found in source, skipping")
                        result.branches_skipped.append((branch, "not found in source"))
                        continue

                    # Check if branch exists in target
                    target_hash = target_repo.get_ref_hash(f"target/{branch}")

                    if target_hash:
                        # Check if safe to push (fast-forward possible)
                        if target_repo.is_ancestor(target_hash, source_hash):
                            # Safe to push
                            if not self.dry_run:
                                success, msg = target_repo.push(
                                    "target",
                                    f"refs/heads/{branch}:refs/heads/{branch}",
                                )
                                if success:
                                    result.branches_synced.append(branch)
                                    logger.info(f"Synced branch: {branch}")
                                else:
                                    result.branches_skipped.append((branch, msg))
                                    logger.warning(f"Failed to sync branch {branch}: {msg}")
                            else:
                                result.branches_synced.append(branch)
                                logger.info(f"[DRY RUN] Would sync branch: {branch}")
                        else:
                            # Would require force push - skip
                            reason = "diverged history (would require force push)"
                            result.branches_skipped.append((branch, reason))
                            logger.warning(
                                f"Branch '{branch}' has diverged, skipping (safety check)"
                            )
                    else:
                        # New branch - safe to push
                        if not self.dry_run:
                            success, msg = target_repo.push(
                                "target",
                                f"refs/heads/{branch}:refs/heads/{branch}",
                            )
                            if success:
                                result.branches_synced.append(branch)
                                logger.info(f"Synced new branch: {branch}")
                            else:
                                result.branches_skipped.append((branch, msg))
                                logger.warning(f"Failed to sync branch {branch}: {msg}")
                        else:
                            result.branches_synced.append(branch)
                            logger.info(f"[DRY RUN] Would sync new branch: {branch}")

                except Exception as e:
                    result.branches_skipped.append((branch, str(e)))
                    logger.error(f"Error syncing branch '{branch}': {e}")

            # Sync tags if enabled
            if repo_config.sync_tags:
                logger.info("Syncing tags...")
                tags = source_repo.get_tags()

                for tag in tags:
                    try:
                        if not self.dry_run:
                            success, msg = target_repo.push(
                                "target",
                                f"refs/tags/{tag}:refs/tags/{tag}",
                            )
                            if success:
                                result.tags_synced.append(tag)
                                logger.info(f"Synced tag: {tag}")
                            else:
                                result.tags_failed.append((tag, msg))
                                logger.warning(f"Failed to sync tag {tag}: {msg}")
                        else:
                            result.tags_synced.append(tag)
                            logger.info(f"[DRY RUN] Would sync tag: {tag}")
                    except Exception as e:
                        result.tags_failed.append((tag, str(e)))
                        logger.error(f"Error syncing tag '{tag}': {e}")

            result.success = True

        except Exception as e:
            result.error = str(e)
            logger.error(f"Sync failed for {repo_config.name}: {e}")

        finally:
            # Cleanup
            if temp_dir and self.config_manager.config.sync.cleanup_after_sync:
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temp directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Could not cleanup temp directory: {e}")

        result.duration = (datetime.now() - start_time).total_seconds()
        return result

    def sync_all(self, repositories: Optional[List[str]] = None) -> SyncSummary:
        """Synchronize all enabled repositories.

        Args:
            repositories: Optional list of specific repositories to sync

        Returns:
            SyncSummary with all results
        """
        start_time = datetime.now()

        # Get repositories to sync
        if repositories:
            repo_configs = []
            for name in repositories:
                repo = self.config_manager.get_repository(name)
                if repo:
                    repo_configs.append(repo)
                else:
                    logger.warning(f"Repository not found: {name}")
        else:
            repo_configs = self.config_manager.get_enabled_repositories()

        if not repo_configs:
            logger.warning("No repositories to sync")
            return SyncSummary(
                total=0,
                successful=0,
                failed=0,
                results=[],
                start_time=start_time,
                end_time=datetime.now(),
            )

        # Clean up stale mirrors (before syncing)
        if self.config_manager.config.sync.enable_mirror_cache:
            active_repo_names = [repo.name for repo in repo_configs]
            self._cleanup_stale_mirrors(active_repo_names)

        logger.info(f"Starting sync of {len(repo_configs)} repositories")

        results = []
        for repo_config in repo_configs:
            result = self.sync_repository(repo_config)
            results.append(result)

        end_time = datetime.now()

        summary = SyncSummary(
            total=len(results),
            successful=sum(1 for r in results if r.success),
            failed=sum(1 for r in results if not r.success),
            results=results,
            start_time=start_time,
            end_time=end_time,
        )

        # Log summary
        logger.info(f"Sync complete: {summary.successful}/{summary.total} successful")
        for result in results:
            status = "SUCCESS" if result.success else "FAILED"
            logger.info(
                f"  {result.repository}: {status} "
                f"({len(result.branches_synced)} branches, {len(result.tags_synced)} tags)"
            )

        return summary
