"""Configuration schema and validation."""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from pathlib import Path


@dataclass
class SourceConfig:
    """Source repository configuration."""

    url: str
    ssh_key: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "ssh_key": self.ssh_key,
        }


@dataclass
class TargetConfig:
    """Target repository configuration."""

    url: str
    ssh_key: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "url": self.url,
            "ssh_key": self.ssh_key,
        }


@dataclass
class RepositoryConfig:
    """Repository configuration."""

    name: str
    source: SourceConfig
    target: TargetConfig
    enabled: bool = True
    sync_branches: List[str] = field(default_factory=list)
    sync_tags: bool = True
    order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "source": self.source.to_dict(),
            "target": self.target.to_dict(),
            "enabled": self.enabled,
            "sync_branches": self.sync_branches,
            "sync_tags": self.sync_tags,
            "order": self.order,
        }


@dataclass
class SSHConfig:
    """SSH configuration."""

    key_storage: str = ".ssh"
    default_key_type: str = "ed25519"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "key_storage": self.key_storage,
            "default_key_type": self.default_key_type,
        }


@dataclass
class SyncSettings:
    """Sync settings."""

    temp_dir: str = "/tmp/git-sync"
    timeout: int = 300
    cleanup_after_sync: bool = True
    # Mirror cache settings for faster syncs
    enable_mirror_cache: bool = True
    mirror_cache_dir: str = ".mirror-cache"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "temp_dir": self.temp_dir,
            "timeout": self.timeout,
            "cleanup_after_sync": self.cleanup_after_sync,
            "enable_mirror_cache": self.enable_mirror_cache,
            "mirror_cache_dir": self.mirror_cache_dir,
        }


@dataclass
class Config:
    """Main configuration."""

    version: str = "1.0"
    ssh: SSHConfig = field(default_factory=SSHConfig)
    sync: SyncSettings = field(default_factory=SyncSettings)
    repositories: List[RepositoryConfig] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "version": self.version,
            "ssh": self.ssh.to_dict(),
            "sync": self.sync.to_dict(),
            "repositories": [repo.to_dict() for repo in self.repositories],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """Create Config from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            Config instance
        """
        # Parse SSH config
        ssh_data = data.get("ssh", {})
        ssh = SSHConfig(
            key_storage=ssh_data.get("key_storage", ".ssh"),
            default_key_type=ssh_data.get("default_key_type", "ed25519"),
        )

        # Parse sync settings
        sync_data = data.get("sync", {})
        sync = SyncSettings(
            temp_dir=sync_data.get("temp_dir", "/tmp/git-sync"),
            timeout=sync_data.get("timeout", 300),
            cleanup_after_sync=sync_data.get("cleanup_after_sync", True),
            enable_mirror_cache=sync_data.get("enable_mirror_cache", True),
            mirror_cache_dir=sync_data.get("mirror_cache_dir", ".mirror-cache"),
        )

        # Parse repositories
        repositories = []
        for repo_data in data.get("repositories", []):
            source = SourceConfig(
                url=repo_data["source"]["url"],
                ssh_key=repo_data["source"]["ssh_key"],
            )
            target = TargetConfig(
                url=repo_data["target"]["url"],
                ssh_key=repo_data["target"]["ssh_key"],
            )
            repo = RepositoryConfig(
                name=repo_data["name"],
                source=source,
                target=target,
                enabled=repo_data.get("enabled", True),
                sync_branches=repo_data.get("sync_branches", []),
                sync_tags=repo_data.get("sync_tags", True),
                order=repo_data.get("order", 0),
            )
            repositories.append(repo)

        return cls(
            version=data.get("version", "1.0"),
            ssh=ssh,
            sync=sync,
            repositories=repositories,
        )
