"""SSH key management."""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from git_sync.core.exceptions import SSHKeyError
from git_sync.utils.logger import logger


class KeyManager:
    """Manages SSH keys for repository authentication."""

    MANIFEST_FILE = "keys_manifest.yaml"

    def __init__(self, storage_path: str = ".ssh"):
        """Initialize key manager.

        Args:
            storage_path: Directory to store SSH keys
        """
        self.storage_path = Path(storage_path)
        self._ensure_storage_exists()
        self._manifest: Optional[Dict] = None

    def _ensure_storage_exists(self):
        """Ensure storage directory exists with proper permissions."""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        # Set permissions to 700 for SSH directory
        os.chmod(self.storage_path, 0o700)

    def _load_manifest(self) -> Dict:
        """Load keys manifest file.

        Returns:
            Manifest dictionary
        """
        manifest_path = self.storage_path / self.MANIFEST_FILE

        if not manifest_path.exists():
            return {"version": "1.0", "keys": {}}

        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {"version": "1.0", "keys": {}}
        except Exception as e:
            logger.warning(f"Could not load manifest: {e}")
            return {"version": "1.0", "keys": {}}

    def _save_manifest(self, manifest: Dict):
        """Save keys manifest file.

        Args:
            manifest: Manifest dictionary to save
        """
        manifest_path = self.storage_path / self.MANIFEST_FILE

        with open(manifest_path, "w", encoding="utf-8") as f:
            yaml.dump(manifest, f, default_flow_style=False, sort_keys=False)

    def generate(
        self,
        name: str,
        key_type: str = "ed25519",
        comment: Optional[str] = None,
        overwrite: bool = False,
    ) -> Path:
        """Generate a new SSH key pair.

        Args:
            name: Name for the key
            key_type: Key type (ed25519, rsa, ecdsa)
            comment: Optional comment for the key
            overwrite: Whether to overwrite existing key

        Returns:
            Path to the private key

        Raises:
            SSHKeyError: If key generation fails
        """
        key_path = self.storage_path / name

        # Check if key exists
        if key_path.exists() and not overwrite:
            raise SSHKeyError(
                f"Key '{name}' already exists. Use --overwrite to replace it."
            )

        # Build ssh-keygen command
        cmd = ["ssh-keygen", "-t", key_type, "-f", str(key_path), "-N", ""]

        if comment:
            cmd.extend(["-C", comment])
        else:
            cmd.extend(["-C", f"git-sync-{name}"])

        # For RSA keys, specify bits
        if key_type == "rsa":
            cmd.extend(["-b", "4096"])

        try:
            logger.info(f"Generating {key_type} key: {name}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Set proper permissions
            os.chmod(key_path, 0o600)
            os.chmod(f"{key_path}.pub", 0o644)

            # Update manifest
            manifest = self._load_manifest()
            manifest["keys"][name] = {
                "type": key_type,
                "created_at": datetime.now().isoformat(),
                "bound_to": [],
            }
            self._save_manifest(manifest)

            logger.info(f"Key generated successfully: {key_path}")
            return key_path

        except subprocess.CalledProcessError as e:
            raise SSHKeyError(f"Failed to generate key: {e.stderr}") from e
        except Exception as e:
            raise SSHKeyError(f"Error generating key: {e}") from e

    def get(self, name: str) -> Path:
        """Get path to a key by name.

        Args:
            name: Key name

        Returns:
            Path to the private key

        Raises:
            SSHKeyError: If key not found
        """
        key_path = self.storage_path / name

        if not key_path.exists():
            raise SSHKeyError(f"Key '{name}' not found at {key_path}")

        return key_path

    def get_public_key(self, name: str) -> str:
        """Get public key content.

        Args:
            name: Key name

        Returns:
            Public key content

        Raises:
            SSHKeyError: If key not found
        """
        pub_path = self.storage_path / f"{name}.pub"

        if not pub_path.exists():
            raise SSHKeyError(f"Public key '{name}' not found")

        try:
            with open(pub_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception as e:
            raise SSHKeyError(f"Error reading public key: {e}") from e

    def list(self) -> List[Dict]:
        """List all managed keys.

        Returns:
            List of key information dictionaries
        """
        manifest = self._load_manifest()
        result = []

        for name, info in manifest.get("keys", {}).items():
            key_path = self.storage_path / name
            pub_path = self.storage_path / f"{name}.pub"

            result.append(
                {
                    "name": name,
                    "type": info.get("type", "unknown"),
                    "created_at": info.get("created_at", "unknown"),
                    "exists": key_path.exists(),
                    "public_exists": pub_path.exists(),
                    "bound_to": info.get("bound_to", []),
                }
            )

        return result

    def bind_to_repository(self, key_name: str, repo_name: str):
        """Bind a key to a repository.

        Args:
            key_name: Key name
            repo_name: Repository name
        """
        manifest = self._load_manifest()

        if key_name not in manifest.get("keys", {}):
            raise SSHKeyError(f"Key '{key_name}' not found in manifest")

        bound_to = manifest["keys"][key_name].setdefault("bound_to", [])
        if repo_name not in bound_to:
            bound_to.append(repo_name)

        self._save_manifest(manifest)
        logger.info(f"Bound key '{key_name}' to repository '{repo_name}'")

    def unbind_from_repository(self, key_name: str, repo_name: str):
        """Unbind a key from a repository.

        Args:
            key_name: Key name
            repo_name: Repository name
        """
        manifest = self._load_manifest()

        if key_name not in manifest.get("keys", {}):
            return

        bound_to = manifest["keys"][key_name].get("bound_to", [])
        if repo_name in bound_to:
            bound_to.remove(repo_name)

        self._save_manifest(manifest)
        logger.info(f"Unbound key '{key_name}' from repository '{repo_name}'")

    def delete(self, name: str) -> bool:
        """Delete a key pair.

        Args:
            name: Key name

        Returns:
            True if deleted, False if not found
        """
        key_path = self.storage_path / name
        pub_path = self.storage_path / f"{name}.pub"

        deleted = False

        if key_path.exists():
            key_path.unlink()
            deleted = True

        if pub_path.exists():
            pub_path.unlink()
            deleted = True

        # Update manifest
        manifest = self._load_manifest()
        if name in manifest.get("keys", {}):
            del manifest["keys"][name]
            self._save_manifest(manifest)
            deleted = True

        if deleted:
            logger.info(f"Deleted key: {name}")

        return deleted
