"""Configuration API routes."""

from fastapi import APIRouter, HTTPException

from git_sync.config.loader import ConfigManager
from git_sync.config.schema import SSHConfig, SyncSettings
from git_sync.web.schemas import (
    ConfigSchema,
    GlobalConfigUpdateSchema,
    SSHConfigSchema,
    SyncSettingsSchema,
    MessageSchema,
)

router = APIRouter(prefix="/api/config", tags=["config"])

# Global config manager instance
_config_manager: ConfigManager = None


def get_config_manager() -> ConfigManager:
    """Get or create the config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def set_config_manager(manager: ConfigManager) -> None:
    """Set the config manager instance."""
    global _config_manager
    _config_manager = manager


@router.get("", response_model=ConfigSchema)
async def get_config():
    """Get the full configuration."""
    try:
        manager = get_config_manager()
        config = manager.config

        return ConfigSchema(
            version=config.version,
            ssh=SSHConfigSchema(
                key_storage=config.ssh.key_storage,
                default_key_type=config.ssh.default_key_type,
            ),
            sync=SyncSettingsSchema(
                temp_dir=config.sync.temp_dir,
                timeout=config.sync.timeout,
                cleanup_after_sync=config.sync.cleanup_after_sync,
                enable_mirror_cache=config.sync.enable_mirror_cache,
                mirror_cache_dir=config.sync.mirror_cache_dir,
            ),
            repositories=[
                {
                    "name": repo.name,
                    "source": {
                        "url": repo.source.url,
                        "ssh_key": repo.source.ssh_key,
                    },
                    "target": {
                        "url": repo.target.url,
                        "ssh_key": repo.target.ssh_key,
                    },
                    "enabled": repo.enabled,
                    "sync_branches": repo.sync_branches,
                    "sync_tags": repo.sync_tags,
                    "order": repo.order,
                }
                for repo in config.repositories
            ],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("", response_model=MessageSchema)
async def update_config(config_update: GlobalConfigUpdateSchema):
    """Update global configuration (SSH and Sync settings)."""
    try:
        manager = get_config_manager()

        ssh_config = None
        sync_settings = None

        if config_update.ssh:
            ssh_config = SSHConfig(
                key_storage=config_update.ssh.key_storage,
                default_key_type=config_update.ssh.default_key_type,
            )

        if config_update.sync:
            sync_settings = SyncSettings(
                temp_dir=config_update.sync.temp_dir,
                timeout=config_update.sync.timeout,
                cleanup_after_sync=config_update.sync.cleanup_after_sync,
                enable_mirror_cache=config_update.sync.enable_mirror_cache,
                mirror_cache_dir=config_update.sync.mirror_cache_dir,
            )

        manager.save_global_config(ssh=ssh_config, sync=sync_settings)

        return MessageSchema(message="Configuration updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
