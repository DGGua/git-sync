"""Sync history management."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field, asdict

from git_sync.utils.logger import logger


@dataclass
class SyncHistoryRecord:
    """A single sync history record."""

    id: str
    repository: str
    timestamp: str
    success: bool
    message: str
    branches_synced: List[str] = field(default_factory=list)
    tags_synced: int = 0
    duration: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "repository": self.repository,
            "timestamp": self.timestamp,
            "success": self.success,
            "message": self.message,
            "branches_synced": self.branches_synced,
            "tags_synced": self.tags_synced,
            "duration": self.duration,
            "error": self.error,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SyncHistoryRecord":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            repository=data["repository"],
            timestamp=data["timestamp"],
            success=data["success"],
            message=data["message"],
            branches_synced=data.get("branches_synced", []),
            tags_synced=data.get("tags_synced", 0),
            duration=data.get("duration", 0.0),
            error=data.get("error"),
        )


class SyncHistoryManager:
    """Manages sync history storage."""

    HISTORY_FILE = "sync_history.json"
    MAX_RECORDS = 1000  # Keep last 1000 records

    def __init__(self, config_dir: str = "configs"):
        """Initialize history manager.

        Args:
            config_dir: Directory to store history file
        """
        self.config_dir = Path(config_dir)
        self.history_file = self.config_dir / self.HISTORY_FILE

    def _ensure_dir(self):
        """Ensure config directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load_history(self) -> List[Dict[str, Any]]:
        """Load history from file."""
        if not self.history_file.exists():
            return []

        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load sync history: {e}")
            return []

    def _save_history(self, records: List[Dict[str, Any]]):
        """Save history to file."""
        self._ensure_dir()
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save sync history: {e}")

    def add_record(self, record: SyncHistoryRecord) -> None:
        """Add a new sync history record.

        Args:
            record: The sync record to add
        """
        records = self._load_history()
        records.insert(0, record.to_dict())  # Add to beginning

        # Keep only last MAX_RECORDS
        if len(records) > self.MAX_RECORDS:
            records = records[:self.MAX_RECORDS]

        self._save_history(records)
        logger.info(f"Added sync history record for {record.repository}")

    def get_records(
        self,
        repository: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SyncHistoryRecord]:
        """Get sync history records.

        Args:
            repository: Filter by repository name (optional)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of sync history records
        """
        records = self._load_history()

        # Filter by repository if specified
        if repository:
            records = [r for r in records if r["repository"] == repository]

        # Apply pagination
        records = records[offset:offset + limit]

        return [SyncHistoryRecord.from_dict(r) for r in records]

    def get_record(self, record_id: str) -> Optional[SyncHistoryRecord]:
        """Get a specific record by ID.

        Args:
            record_id: The record ID

        Returns:
            The record or None if not found
        """
        records = self._load_history()
        for r in records:
            if r["id"] == record_id:
                return SyncHistoryRecord.from_dict(r)
        return None

    def delete_record(self, record_id: str) -> bool:
        """Delete a specific record.

        Args:
            record_id: The record ID to delete

        Returns:
            True if deleted, False if not found
        """
        records = self._load_history()
        original_len = len(records)
        records = [r for r in records if r["id"] != record_id]

        if len(records) < original_len:
            self._save_history(records)
            return True
        return False

    def clear_history(self, repository: Optional[str] = None) -> int:
        """Clear sync history.

        Args:
            repository: Only clear for this repository (optional)

        Returns:
            Number of records cleared
        """
        if repository:
            records = self._load_history()
            original_len = len(records)
            records = [r for r in records if r["repository"] != repository]
            self._save_history(records)
            return original_len - len(records)
        else:
            self._save_history([])
            return len(self._load_history())

    def get_statistics(self) -> Dict[str, Any]:
        """Get sync statistics.

        Returns:
            Dictionary with statistics
        """
        records = self._load_history()

        total = len(records)
        successful = sum(1 for r in records if r["success"])
        failed = total - successful

        # Get per-repository stats
        repo_stats = {}
        for r in records:
            repo = r["repository"]
            if repo not in repo_stats:
                repo_stats[repo] = {"total": 0, "successful": 0, "failed": 0}
            repo_stats[repo]["total"] += 1
            if r["success"]:
                repo_stats[repo]["successful"] += 1
            else:
                repo_stats[repo]["failed"] += 1

        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "repositories": repo_stats,
        }
