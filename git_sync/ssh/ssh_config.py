"""SSH configuration generation."""

import os
from pathlib import Path
from typing import Optional


class SSHConfigGenerator:
    """Generates SSH configuration for key-based authentication."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize SSH config generator.

        Args:
            config_path: Path to SSH config file (default: ~/.ssh/config)
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            self.config_path = Path.home() / ".ssh" / "config"

    def get_git_ssh_command(self, key_path: str) -> str:
        """Get GIT_SSH_COMMAND for using a specific key.

        Args:
            key_path: Path to private key

        Returns:
            SSH command string
        """
        return f"ssh -i {key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new"

    def get_ssh_env(self, key_path: str) -> dict:
        """Get environment variables for SSH authentication.

        Args:
            key_path: Path to private key

        Returns:
            Dictionary with environment variables
        """
        return {
            "GIT_SSH_COMMAND": self.get_git_ssh_command(key_path),
        }

    @staticmethod
    def setup_ssh_env(key_path: str) -> dict:
        """Set up SSH environment variables for git operations.

        This is a convenience static method for quick setup.

        Args:
            key_path: Path to private key

        Returns:
            Environment variables dictionary
        """
        return {
            "GIT_SSH_COMMAND": f"ssh -i {key_path} -o IdentitiesOnly=yes -o StrictHostKeyChecking=no"
        }
