"""Git repository operations."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

from git_sync.core.exceptions import RepositoryError, AuthenticationError
from git_sync.ssh.ssh_config import SSHConfigGenerator
from git_sync.utils.logger import logger


class Repository:
    """Handles Git repository operations."""

    def __init__(
        self,
        url: str,
        ssh_key_path: Optional[str] = None,
        work_dir: Optional[str] = None,
    ):
        """Initialize repository handler.

        Args:
            url: Repository URL
            ssh_key_path: Path to SSH private key
            work_dir: Working directory for operations
        """
        self.url = url
        self.ssh_key_path = ssh_key_path
        self.work_dir = Path(work_dir) if work_dir else None
        self._env = self._build_env()

    def _build_env(self) -> dict:
        """Build environment variables for git operations.

        Returns:
            Environment dictionary
        """
        env = os.environ.copy()

        if self.ssh_key_path:
            env.update(SSHConfigGenerator.setup_ssh_env(self.ssh_key_path))

        return env

    def _run_git(
        self,
        args: List[str],
        cwd: Optional[str] = None,
        check: bool = True,
        capture: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run a git command.

        Args:
            args: Git command arguments
            cwd: Working directory
            check: Raise exception on non-zero exit
            capture: Capture stdout/stderr

        Returns:
            CompletedProcess instance
        """
        cmd = ["git"] + args
        working_dir = cwd or (str(self.work_dir) if self.work_dir else None)

        logger.debug(f"Running: {' '.join(cmd)}")

        return subprocess.run(
            cmd,
            cwd=working_dir,
            env=self._env,
            capture_output=capture,
            text=True,
            check=check,
        )

    def clone(
        self,
        target_dir: str,
        bare: bool = True,
        mirror: bool = False,
    ) -> Path:
        """Clone the repository.

        Args:
            target_dir: Target directory for clone
            bare: Create a bare repository
            mirror: Create a mirror clone

        Returns:
            Path to cloned repository

        Raises:
            RepositoryError: If clone fails
        """
        target_path = Path(target_dir)

        # Remove existing directory if exists
        if target_path.exists():
            logger.info(f"Removing existing directory: {target_path}")
            shutil.rmtree(target_path)

        args = ["clone"]
        if mirror:
            args.append("--mirror")
        elif bare:
            args.append("--bare")
        args.extend([self.url, str(target_path)])

        try:
            logger.info(f"Cloning repository: {self.url}")
            self._run_git(args)
            self.work_dir = target_path
            logger.info(f"Clone complete: {target_path}")
            return target_path

        except subprocess.CalledProcessError as e:
            if "Permission denied" in e.stderr or "Authentication failed" in e.stderr:
                raise AuthenticationError(
                    f"Authentication failed for {self.url}. Check SSH key."
                ) from e
            raise RepositoryError(f"Failed to clone repository: {e.stderr}") from e

    def get_branches(self, remote: str = "origin") -> List[str]:
        """Get list of branches.

        Args:
            remote: Remote name

        Returns:
            List of branch names
        """
        try:
            # 使用 for-each-ref 获取远程分支列表
            result = self._run_git(
                ["for-each-ref", "--format=%(refname:short)", f"refs/remotes/{remote}/"]
            )
            branches = [
                b.strip().replace(f"{remote}/", "")
                for b in result.stdout.strip().split("\n")
                if b.strip() and not b.strip().endswith("/HEAD") and b.strip() != f"{remote}/HEAD"
            ]
            return branches
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not get branches: {e.stderr}")
            return []

    def get_local_branches(self) -> List[str]:
        """Get list of local branches.

        Returns:
            List of branch names
        """
        try:
            result = self._run_git(["branch", "--format=%(refname:short)"])
            branches = [b.strip() for b in result.stdout.strip().split("\n") if b.strip()]
            return branches
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not get local branches: {e.stderr}")
            return []

    def get_tags(self) -> List[str]:
        """Get list of tags.

        Returns:
            List of tag names
        """
        try:
            result = self._run_git(["tag"])
            tags = [t.strip() for t in result.stdout.strip().split("\n") if t.strip()]
            return tags
        except subprocess.CalledProcessError as e:
            logger.warning(f"Could not get tags: {e.stderr}")
            return []

    def add_remote(self, name: str, url: str):
        """Add a remote repository.

        Args:
            name: Remote name
            url: Remote URL
        """
        try:
            # Check if remote exists
            result = self._run_git(["remote"], check=False)
            if name in result.stdout.strip().split("\n"):
                logger.info(f"Remote '{name}' exists, updating URL")
                self._run_git(["remote", "set-url", name, url])
            else:
                logger.info(f"Adding remote '{name}': {url}")
                self._run_git(["remote", "add", name, url])
        except subprocess.CalledProcessError as e:
            raise RepositoryError(f"Failed to add remote: {e.stderr}") from e

    def fetch(self, remote: str = "origin"):
        """Fetch from remote.

        Args:
            remote: Remote name
        """
        try:
            logger.info(f"Fetching from {remote}")
            self._run_git(["fetch", remote, "--prune"])
        except subprocess.CalledProcessError as e:
            raise RepositoryError(f"Failed to fetch: {e.stderr}") from e

    def get_ref_hash(self, ref: str) -> Optional[str]:
        """Get commit hash for a reference.

        Args:
            ref: Reference name (branch, tag, etc.)

        Returns:
            Commit hash or None if not found
        """
        try:
            result = self._run_git(["rev-parse", ref], check=False)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except Exception:
            return None

    def is_ancestor(self, ancestor: str, descendant: str) -> bool:
        """Check if one commit is ancestor of another.

        Args:
            ancestor: Potential ancestor commit
            descendant: Potential descendant commit

        Returns:
            True if ancestor is ancestor of descendant
        """
        try:
            result = self._run_git(
                ["merge-base", "--is-ancestor", ancestor, descendant],
                check=False,
            )
            return result.returncode == 0
        except Exception:
            return False

    def push(
        self,
        remote: str,
        refspec: str,
        force: bool = False,
        dry_run: bool = False,
    ) -> Tuple[bool, str]:
        """Push to remote.

        Args:
            remote: Remote name
            refspec: Refspec to push (e.g., 'refs/heads/main')
            force: Force push
            dry_run: Dry run mode

        Returns:
            Tuple of (success, message)
        """
        args = ["push", remote, refspec]

        if dry_run:
            args.insert(1, "--dry-run")

        if force:
            args.insert(1, "--force")

        try:
            logger.info(f"Pushing {refspec} to {remote}")
            result = self._run_git(args, check=False)

            if result.returncode == 0:
                return True, result.stdout
            else:
                return False, result.stderr

        except subprocess.CalledProcessError as e:
            return False, str(e.stderr)

    def push_all_branches(
        self,
        remote: str,
        branches: Optional[List[str]] = None,
        force: bool = False,
        dry_run: bool = False,
    ) -> List[Tuple[str, bool, str]]:
        """Push multiple branches to remote.

        Args:
            remote: Remote name
            branches: List of branches to push (None = all)
            force: Force push
            dry_run: Dry run mode

        Returns:
            List of (branch, success, message) tuples
        """
        if branches is None:
            branches = self.get_local_branches()

        results = []
        for branch in branches:
            refspec = f"refs/heads/{branch}:refs/heads/{branch}"
            success, message = self.push(remote, refspec, force=force, dry_run=dry_run)
            results.append((branch, success, message))

        return results

    def push_tags(
        self,
        remote: str,
        tags: Optional[List[str]] = None,
        dry_run: bool = False,
    ) -> List[Tuple[str, bool, str]]:
        """Push tags to remote.

        Args:
            remote: Remote name
            tags: List of tags to push (None = all)
            dry_run: Dry run mode

        Returns:
            List of (tag, success, message) tuples
        """
        if tags is None:
            tags = self.get_tags()

        results = []
        for tag in tags:
            refspec = f"refs/tags/{tag}:refs/tags/{tag}"
            success, message = self.push(remote, refspec, dry_run=dry_run)
            results.append((tag, success, message))

        return results
