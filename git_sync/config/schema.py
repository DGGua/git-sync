"""Configuration schema and validation."""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class SourceConfig:
    """Source repository configuration."""

    url: str
    ssh_key: str


@dataclass
class TargetConfig:
    """Target repository configuration."""

    url: str
    ssh_key: str


@dataclass
class RepositoryConfig:
    """Repository configuration."""

    name: str
    source: SourceConfig
    target: TargetConfig
    enabled: bool = True
    sync_branches: List[str] = field(default_factory=list)
    sync_tags: bool = True


@dataclass
class SSHConfig:
    """SSH configuration."""

    key_storage: str = ".ssh"
    default_key_type: str = "ed25519"


@dataclass
class SyncSettings:
    """Sync settings."""

    temp_dir: str = "/tmp/git-sync"
    timeout: int = 300
    cleanup_after_sync: bool = True
    # Mirror cache settings for faster syncs
    enable_mirror_cache: bool = True
    mirror_cache_dir: str = ".mirror-cache"


@dataclass
class Config:
    """Main configuration."""

    version: str = "1.0"
    ssh: SSHConfig = field(default_factory=SSHConfig)
    sync: SyncSettings = field(default_factory=SyncSettings)
    repositories: List[RepositoryConfig] = field(default_factory=list)

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
            )
            repositories.append(repo)

        return cls(
            version=data.get("version", "1.0"),
            ssh=ssh,
            sync=sync,
            repositories=repositories,
        )
