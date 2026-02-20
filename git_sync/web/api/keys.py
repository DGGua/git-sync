"""SSH Key management API routes."""

from typing import List
from fastapi import APIRouter, HTTPException

from git_sync.ssh.key_manager import KeyManager
from git_sync.web.schemas import KeyInfoSchema, KeyCreateSchema, MessageSchema
from git_sync.web.api.config import get_config_manager

router = APIRouter(prefix="/api/keys", tags=["keys"])


def get_key_manager() -> KeyManager:
    """Get the key manager instance."""
    config_manager = get_config_manager()
    config = config_manager.config
    return KeyManager(config.ssh.key_storage)


@router.get("", response_model=List[KeyInfoSchema])
async def list_keys():
    """List all SSH keys."""
    try:
        key_manager = get_key_manager()
        keys_list = key_manager.list()

        keys = []
        for key_info in keys_list:
            keys.append(KeyInfoSchema(
                name=key_info["name"],
                type=key_info["type"],
                created_at=key_info.get("created_at"),
                comment=key_info.get("comment"),
            ))

        return keys
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=MessageSchema, status_code=201)
async def create_key(key_data: KeyCreateSchema):
    """Generate a new SSH key."""
    try:
        key_manager = get_key_manager()

        # Generate the key
        key_path = key_manager.generate(
            name=key_data.name,
            key_type=key_data.key_type,
            comment=key_data.comment,
        )

        return MessageSchema(
            message=f"SSH key '{key_data.name}' generated successfully at {key_path}"
        )
    except Exception as e:
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(status_code=400, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.delete("/{name}", response_model=MessageSchema)
async def delete_key(name: str):
    """Delete an SSH key."""
    try:
        key_manager = get_key_manager()

        # Delete the key
        deleted = key_manager.delete(name)

        if not deleted:
            raise HTTPException(status_code=404, detail=f"Key '{name}' not found")

        return MessageSchema(message=f"SSH key '{name}' deleted successfully")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{name}/public", response_model=MessageSchema)
async def get_public_key(name: str):
    """Get the public key content."""
    try:
        key_manager = get_key_manager()
        public_key = key_manager.get_public_key(name)

        return MessageSchema(message=public_key)
    except Exception as e:
        error_msg = str(e)
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
