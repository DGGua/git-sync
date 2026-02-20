"""Repository API routes."""

from typing import List
from fastapi import APIRouter, HTTPException

from git_sync.config.loader import ConfigManager
from git_sync.config.schema import RepositoryConfig, SourceConfig, TargetConfig
from git_sync.web.schemas import (
    RepositoryConfigSchema,
    RepositoryCreateSchema,
    RepositoryUpdateSchema,
    ReorderSchema,
    MessageSchema,
    SourceConfigSchema,
    TargetConfigSchema,
)
from git_sync.web.api.config import get_config_manager

router = APIRouter(prefix="/api/repositories", tags=["repositories"])


@router.get("", response_model=List[RepositoryConfigSchema])
async def list_repositories():
    """Get all repositories."""
    try:
        manager = get_config_manager()
        config = manager.config

        return [
            RepositoryConfigSchema(
                name=repo.name,
                source=SourceConfigSchema(
                    url=repo.source.url,
                    ssh_key=repo.source.ssh_key,
                ),
                target=TargetConfigSchema(
                    url=repo.target.url,
                    ssh_key=repo.target.ssh_key,
                ),
                enabled=repo.enabled,
                sync_branches=repo.sync_branches,
                sync_tags=repo.sync_tags,
                order=repo.order,
            )
            for repo in sorted(config.repositories, key=lambda r: r.order)
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=MessageSchema, status_code=201)
async def create_repository(repo_data: RepositoryCreateSchema):
    """Create a new repository."""
    try:
        manager = get_config_manager()

        # Check if repository already exists
        if manager.get_repository(repo_data.name):
            raise HTTPException(
                status_code=400,
                detail=f"Repository '{repo_data.name}' already exists"
            )

        # Create new repository config
        repo = RepositoryConfig(
            name=repo_data.name,
            source=SourceConfig(
                url=repo_data.source.url,
                ssh_key=repo_data.source.ssh_key,
            ),
            target=TargetConfig(
                url=repo_data.target.url,
                ssh_key=repo_data.target.ssh_key,
            ),
            enabled=repo_data.enabled,
            sync_branches=repo_data.sync_branches,
            sync_tags=repo_data.sync_tags,
        )

        manager.save_repository(repo)

        return MessageSchema(message=f"Repository '{repo_data.name}' created successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}", response_model=RepositoryConfigSchema)
async def get_repository(name: str):
    """Get a specific repository by name."""
    try:
        manager = get_config_manager()
        repo = manager.get_repository(name)

        if not repo:
            raise HTTPException(status_code=404, detail=f"Repository '{name}' not found")

        return RepositoryConfigSchema(
            name=repo.name,
            source=SourceConfigSchema(
                url=repo.source.url,
                ssh_key=repo.source.ssh_key,
            ),
            target=TargetConfigSchema(
                url=repo.target.url,
                ssh_key=repo.target.ssh_key,
            ),
            enabled=repo.enabled,
            sync_branches=repo.sync_branches,
            sync_tags=repo.sync_tags,
            order=repo.order,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{name}", response_model=MessageSchema)
async def update_repository(name: str, repo_data: RepositoryUpdateSchema):
    """Update an existing repository."""
    try:
        manager = get_config_manager()
        existing = manager.get_repository(name)

        if not existing:
            raise HTTPException(status_code=404, detail=f"Repository '{name}' not found")

        # Update only provided fields
        source_url = repo_data.source.url if repo_data.source else existing.source.url
        source_ssh_key = repo_data.source.ssh_key if repo_data.source else existing.source.ssh_key
        target_url = repo_data.target.url if repo_data.target else existing.target.url
        target_ssh_key = repo_data.target.ssh_key if repo_data.target else existing.target.ssh_key
        enabled = repo_data.enabled if repo_data.enabled is not None else existing.enabled
        sync_branches = repo_data.sync_branches if repo_data.sync_branches is not None else existing.sync_branches
        sync_tags = repo_data.sync_tags if repo_data.sync_tags is not None else existing.sync_tags

        updated_repo = RepositoryConfig(
            name=name,
            source=SourceConfig(url=source_url, ssh_key=source_ssh_key),
            target=TargetConfig(url=target_url, ssh_key=target_ssh_key),
            enabled=enabled,
            sync_branches=sync_branches,
            sync_tags=sync_tags,
            order=existing.order,
        )

        manager.save_repository(updated_repo)

        return MessageSchema(message=f"Repository '{name}' updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{name}", response_model=MessageSchema)
async def delete_repository(name: str):
    """Delete a repository."""
    try:
        manager = get_config_manager()

        if not manager.delete_repository(name):
            raise HTTPException(status_code=404, detail=f"Repository '{name}' not found")

        return MessageSchema(message=f"Repository '{name}' deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/order", response_model=MessageSchema)
async def reorder_repositories(order_data: ReorderSchema):
    """Update repository order (for drag-and-drop sorting)."""
    try:
        manager = get_config_manager()
        manager.reorder_repositories(order_data.ordered_names)

        return MessageSchema(message="Repository order updated successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
