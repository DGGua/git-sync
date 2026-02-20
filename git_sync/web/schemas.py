"""Pydantic schemas for API request/response models."""

from typing import List, Optional
from pydantic import BaseModel, Field


class SourceConfigSchema(BaseModel):
    """Source repository configuration schema."""

    url: str
    ssh_key: str


class TargetConfigSchema(BaseModel):
    """Target repository configuration schema."""

    url: str
    ssh_key: str


class RepositoryConfigSchema(BaseModel):
    """Repository configuration schema."""

    name: str
    source: SourceConfigSchema
    target: TargetConfigSchema
    enabled: bool = True
    sync_branches: List[str] = Field(default_factory=list)
    sync_tags: bool = True
    order: int = 0


class RepositoryCreateSchema(BaseModel):
    """Schema for creating a new repository."""

    name: str
    source: SourceConfigSchema
    target: TargetConfigSchema
    enabled: bool = True
    sync_branches: List[str] = Field(default_factory=list)
    sync_tags: bool = True


class RepositoryUpdateSchema(BaseModel):
    """Schema for updating an existing repository."""

    source: Optional[SourceConfigSchema] = None
    target: Optional[TargetConfigSchema] = None
    enabled: Optional[bool] = None
    sync_branches: Optional[List[str]] = None
    sync_tags: Optional[bool] = None


class ReorderSchema(BaseModel):
    """Schema for reordering repositories."""

    ordered_names: List[str] = Field(..., alias="orderedNames")

    class Config:
        populate_by_name = True


class SSHConfigSchema(BaseModel):
    """SSH configuration schema."""

    key_storage: str = Field(default=".ssh", alias="keyStorage")
    default_key_type: str = Field(default="ed25519", alias="defaultKeyType")

    class Config:
        populate_by_name = True


class SyncSettingsSchema(BaseModel):
    """Sync settings schema."""

    temp_dir: str = Field(default="/tmp/git-sync", alias="tempDir")
    timeout: int = 300
    cleanup_after_sync: bool = Field(default=True, alias="cleanupAfterSync")
    enable_mirror_cache: bool = Field(default=True, alias="enableMirrorCache")
    mirror_cache_dir: str = Field(default=".mirror-cache", alias="mirrorCacheDir")

    class Config:
        populate_by_name = True


class GlobalConfigUpdateSchema(BaseModel):
    """Schema for updating global configuration."""

    ssh: Optional[SSHConfigSchema] = None
    sync: Optional[SyncSettingsSchema] = None


class ConfigSchema(BaseModel):
    """Full configuration schema."""

    version: str = "1.0"
    ssh: SSHConfigSchema
    sync: SyncSettingsSchema
    repositories: List[RepositoryConfigSchema]


class KeyInfoSchema(BaseModel):
    """SSH key information schema."""

    name: str
    type: str
    created_at: Optional[str] = Field(None, alias="createdAt")
    comment: Optional[str] = None

    class Config:
        populate_by_name = True


class KeyCreateSchema(BaseModel):
    """Schema for creating a new SSH key."""

    name: str
    key_type: str = Field(default="ed25519", alias="keyType")
    comment: Optional[str] = None

    class Config:
        populate_by_name = True


class SyncRequestSchema(BaseModel):
    """Schema for sync request."""

    repository: Optional[str] = None  # If None, sync all enabled repos
    dry_run: bool = Field(default=False, alias="dryRun")

    class Config:
        populate_by_name = True


class SyncResultSchema(BaseModel):
    """Schema for sync result."""

    repository: str
    success: bool
    message: str
    branches_synced: List[str] = Field(default_factory=list, alias="branchesSynced")
    tags_synced: int = Field(default=0, alias="tagsSynced")
    background: bool = Field(default=False, alias="background")

    class Config:
        populate_by_name = True


class SyncResponseSchema(BaseModel):
    """Schema for sync response."""

    results: List[SyncResultSchema]
    total_synced: int = Field(..., alias="totalSynced")
    total_failed: int = Field(..., alias="totalFailed")

    class Config:
        populate_by_name = True


class MessageSchema(BaseModel):
    """Generic message response."""

    message: str
    success: bool = True
