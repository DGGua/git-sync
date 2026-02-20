"""Configuration loader."""

import os
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any

import yaml

from git_sync.config.schema import Config, RepositoryConfig, SSHConfig, SyncSettings
from git_sync.core.exceptions import ConfigurationError
from git_sync.utils.logger import logger

try:
    from ruamel.yaml import YAML
    HAS_RUAMEL = True
except ImportError:
    HAS_RUAMEL = False


class ConfigManager:
    """Manages configuration loading and access."""

    DEFAULT_CONFIG_DIR = "configs"

    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration directory or single file. If None, searches default locations.
        """
        self.config_path = config_path
        self._config: Optional[Config] = None

    def find_config_dir(self) -> Optional[str]:
        """Find configuration directory in default locations.

        Returns:
            Path to configuration directory or None if not found.
        """
        # If explicit path provided
        if self.config_path:
            if os.path.isdir(self.config_path):
                return self.config_path
            # If it's a file, return None (single file mode)
            if os.path.isfile(self.config_path):
                return None
            return None

        # Search in current directory and parent directories
        current = Path.cwd()
        for _ in range(5):
            config_dir = current / self.DEFAULT_CONFIG_DIR
            if config_dir.is_dir():
                return str(config_dir)
            parent = current.parent
            if parent == current:
                break
            current = parent

        return None

    def load_config_files(self) -> List[Tuple[str, dict]]:
        """Load all configuration files from directory.

        Returns:
            List of (filepath, data) tuples
        """
        config_dir = self.find_config_dir()
        if not config_dir:
            return []

        config_files = []
        dir_path = Path(config_dir)

        # Find all .yaml and .yml files, sort alphabetically
        yaml_files = sorted(
            list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml"))
        )

        for yaml_file in yaml_files:
            try:
                with open(yaml_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    config_files.append((str(yaml_file), data))
                    logger.info(f"Loaded config: {yaml_file.name}")
            except yaml.YAMLError as e:
                logger.warning(f"Skipping invalid YAML file {yaml_file}: {e}")
            except Exception as e:
                logger.warning(f"Error reading {yaml_file}: {e}")

        return config_files

    def merge_configs(self, configs: List[Tuple[str, dict]]) -> dict:
        """Merge multiple configuration dictionaries.

        Merge strategy:
        - Global settings (version, ssh, sync): First file defines
        - repositories: Merge all, later duplicates override earlier ones

        Args:
            configs: List of (filepath, data) tuples

        Returns:
            Merged configuration dictionary
        """
        if not configs:
            return {}

        merged = {
            "version": "1.0",
            "ssh": {},
            "sync": {},
            "repositories": []
        }

        repo_map = {}  # name -> config, for deduplication

        for filepath, data in configs:
            # Global settings: first wins
            if not merged["version"] and "version" in data:
                merged["version"] = data["version"]

            if not merged["ssh"] and "ssh" in data:
                merged["ssh"] = data["ssh"]

            if not merged["sync"] and "sync" in data:
                merged["sync"] = data["sync"]

            # Repositories: collect all, later duplicates override
            if "repositories" in data:
                for repo in data["repositories"]:
                    repo_name = repo.get("name")
                    if repo_name:
                        repo_map[repo_name] = repo

        merged["repositories"] = list(repo_map.values())
        logger.info(f"Merged {len(merged['repositories'])} repositories from {len(configs)} config files")
        return merged

    def load(self) -> Config:
        """Load configuration from configs directory.

        Returns:
            Config instance (returns default empty config if no config found)
        """
        config_files = self.load_config_files()
        if config_files:
            return self._load_multiple_files(config_files)

        # Return default empty config if no config files found
        logger.info("No configuration found, returning default empty config")
        self._config = Config()
        return self._config

    def _load_multiple_files(self, config_files: List[Tuple[str, dict]]) -> Config:
        """Load and merge multiple configuration files.

        Args:
            config_files: List of (filepath, data) tuples

        Returns:
            Config instance

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        merged_data = self.merge_configs(config_files)

        # Allow empty repositories for web UI use case
        if not merged_data:
            merged_data = {"version": "1.0", "repositories": []}

        try:
            self._config = Config.from_dict(merged_data)
            return self._config
        except KeyError as e:
            raise ConfigurationError(f"Missing required configuration key: {e}") from e
        except Exception as e:
            raise ConfigurationError(f"Error loading configuration: {e}") from e

    @property
    def config(self) -> Config:
        """Get loaded configuration.

        Returns:
            Config instance

        Raises:
            ConfigurationError: If configuration not loaded.
        """
        if self._config is None:
            self.load()
        return self._config

    def get_repository(self, name: str) -> Optional[Config]:
        """Get repository configuration by name.

        Args:
            name: Repository name

        Returns:
            Repository configuration or None if not found
        """
        for repo in self.config.repositories:
            if repo.name == name:
                return repo
        return None

    def get_enabled_repositories(self) -> list:
        """Get all enabled repositories.

        Returns:
            List of enabled repository configurations
        """
        return [repo for repo in self.config.repositories if repo.enabled]

    def _get_repositories_file(self) -> Path:
        """Get the path to repositories.yaml file."""
        config_dir = self.find_config_dir()
        if config_dir:
            return Path(config_dir) / "repositories.yaml"
        return Path(self.DEFAULT_CONFIG_DIR) / "repositories.yaml"

    def _get_global_config_file(self) -> Path:
        """Get the path to global config file (settings.yaml)."""
        config_dir = self.find_config_dir()
        if config_dir:
            return Path(config_dir) / "settings.yaml"
        return Path(self.DEFAULT_CONFIG_DIR) / "settings.yaml"

    def _ensure_config_dir(self) -> Path:
        """Ensure the config directory exists."""
        config_dir = self.find_config_dir()
        if config_dir:
            return Path(config_dir)

        # Create default config directory
        default_dir = Path(self.DEFAULT_CONFIG_DIR)
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir

    def save_repository(self, repo: RepositoryConfig) -> None:
        """Save or update a repository configuration.

        Args:
            repo: Repository configuration to save
        """
        config_dir = self._ensure_config_dir()
        repos_file = config_dir / "repositories.yaml"

        # Load existing repositories
        existing_repos = []
        if repos_file.exists():
            try:
                with open(repos_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    existing_repos = data.get("repositories", [])
            except Exception as e:
                logger.warning(f"Error loading existing repos: {e}")

        # Update or add the repository
        found = False
        for i, r in enumerate(existing_repos):
            if r.get("name") == repo.name:
                existing_repos[i] = repo.to_dict()
                found = True
                break

        if not found:
            # Set order for new repository
            repo.order = len(existing_repos)
            existing_repos.append(repo.to_dict())

        # Save back to file
        output_data = {"repositories": existing_repos}
        self._write_yaml(repos_file, output_data)

        # Reload config
        self._config = None
        logger.info(f"Saved repository: {repo.name}")

    def delete_repository(self, name: str) -> bool:
        """Delete a repository from configuration.

        Args:
            name: Repository name to delete

        Returns:
            True if deleted, False if not found
        """
        config_dir = self.find_config_dir()
        if not config_dir:
            return False

        repos_file = Path(config_dir) / "repositories.yaml"
        if not repos_file.exists():
            return False

        # Load existing repositories
        try:
            with open(repos_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                existing_repos = data.get("repositories", [])
        except Exception as e:
            logger.warning(f"Error loading existing repos: {e}")
            return False

        # Find and remove the repository
        original_len = len(existing_repos)
        existing_repos = [r for r in existing_repos if r.get("name") != name]

        if len(existing_repos) == original_len:
            return False

        # Save back to file
        output_data = {"repositories": existing_repos}
        self._write_yaml(repos_file, output_data)

        # Reload config
        self._config = None
        logger.info(f"Deleted repository: {name}")
        return True

    def reorder_repositories(self, ordered_names: List[str]) -> None:
        """Update repository order.

        Args:
            ordered_names: List of repository names in desired order
        """
        config_dir = self._ensure_config_dir()
        repos_file = config_dir / "repositories.yaml"

        # Load existing repositories
        existing_repos = []
        if repos_file.exists():
            try:
                with open(repos_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    existing_repos = data.get("repositories", [])
            except Exception as e:
                logger.warning(f"Error loading existing repos: {e}")

        # Create a map of name -> repo
        repo_map = {r.get("name"): r for r in existing_repos}

        # Reorder according to ordered_names
        reordered = []
        for i, name in enumerate(ordered_names):
            if name in repo_map:
                repo = repo_map[name]
                repo["order"] = i
                reordered.append(repo)

        # Add any repos not in the ordered list (at the end)
        for name, repo in repo_map.items():
            if name not in ordered_names:
                repo["order"] = len(reordered)
                reordered.append(repo)

        # Save back to file
        output_data = {"repositories": reordered}
        self._write_yaml(repos_file, output_data)

        # Reload config
        self._config = None
        logger.info(f"Reordered {len(ordered_names)} repositories")

    def save_global_config(self, ssh: Optional[SSHConfig] = None, sync: Optional[SyncSettings] = None) -> None:
        """Save global configuration (SSH and Sync settings).

        Args:
            ssh: SSH configuration to save (optional)
            sync: Sync settings to save (optional)
        """
        config_dir = self._ensure_config_dir()
        settings_file = config_dir / "settings.yaml"

        # Load existing settings
        existing_data = {}
        if settings_file.exists():
            try:
                with open(settings_file, "r", encoding="utf-8") as f:
                    existing_data = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Error loading existing settings: {e}")

        # Update with new values
        if ssh:
            existing_data["ssh"] = ssh.to_dict()
        if sync:
            existing_data["sync"] = sync.to_dict()

        # Ensure version is set
        if "version" not in existing_data:
            existing_data["version"] = "1.0"

        # Save back to file
        self._write_yaml(settings_file, existing_data)

        # Reload config
        self._config = None
        logger.info("Saved global configuration")

    def _write_yaml(self, filepath: Path, data: Dict[str, Any]) -> None:
        """Write data to YAML file, preserving formatting if ruamel.yaml is available.

        Args:
            filepath: Path to write to
            data: Data to write
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        if HAS_RUAMEL:
            yaml_handler = YAML()
            yaml_handler.preserve_quotes = True
            yaml_handler.default_flow_style = False
            with open(filepath, "w", encoding="utf-8") as f:
                yaml_handler.dump(data, f)
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
