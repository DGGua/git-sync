"""Configuration loader."""

import os
from pathlib import Path
from typing import Optional, List, Tuple

import yaml

from git_sync.config.schema import Config
from git_sync.core.exceptions import ConfigurationError
from git_sync.utils.logger import logger


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
            Config instance

        Raises:
            ConfigurationError: If no configuration found.
        """
        config_files = self.load_config_files()
        if config_files:
            return self._load_multiple_files(config_files)

        raise ConfigurationError(
            "Configuration not found. Create a configs/ directory with .yaml files, "
            "or specify path with --config"
        )

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
        if not merged_data or not merged_data.get("repositories"):
            raise ConfigurationError("No valid configuration found in configs/")

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
