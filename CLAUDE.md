# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Git Sync is a command-line tool for synchronizing Git repositories between different hosting services (e.g., GitHub to GitLab). It supports SSH key management, selective branch/tag syncing, and includes safety features like fast-forward checks to prevent accidental overwrites.

## Development Commands

```bash
# Install the package in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run the CLI
git-sync --help
git-sync init
git-sync sync --dry-run

# Run tests
pytest

# Run tests with coverage
pytest --cov=git_sync

# Lint with ruff
ruff check .

# Format with black
black .
```

## Architecture

The codebase follows a layered architecture under the `git_sync/` package:

### CLI Layer (`cli.py`)
- Uses Click for command-line interface
- Main commands: `init`, `key` (gen/list/show/delete), `repo list`, `sync`
- Entry point: `git_sync.cli:main` (configured in pyproject.toml)

### Configuration Layer (`config/`)
- `schema.py`: Dataclasses defining configuration structure (Config, RepositoryConfig, SSHConfig, SyncSettings)
- `loader.py`: ConfigManager handles YAML loading and repository lookup

### SSH Layer (`ssh/`)
- `key_manager.py`: KeyManager class handles SSH key generation, storage, and manifest tracking
- `ssh_config.py`: SSHConfigGenerator builds SSH environment variables for git operations

### Core Layer (`core/`)
- `repository.py`: Repository class wraps git operations (clone, fetch, push, branch/tag queries)
- `sync.py`: SyncOrchestrator coordinates the sync workflow with SyncResult/SyncSummary dataclasses
- `exceptions.py`: Custom exception hierarchy (GitSyncError, ConfigurationError, SSHKeyError, etc.)

### Utilities (`utils/`)
- `logger.py`: Logging setup with configurable levels

## Key Design Decisions

1. **Mirror Cache**: Sync uses a local mirror cache (`.mirror-cache/`) for faster subsequent syncs. On first sync, a bare mirror is created; subsequent syncs fetch updates incrementally.

2. **Safety Checks**: Push operations only proceed if fast-forward is possible (checked via `merge-base --is-ancestor`). Branches with diverged history are skipped rather than force-pushed.

3. **SSH Key Management**: Keys are stored in `.ssh/` with a `keys_manifest.yaml` tracking metadata. The `GIT_SSH_COMMAND` environment variable is used to specify keys per-operation.

4. **Configuration Search**: ConfigManager searches for `config.yaml` or `config.yml` in the current directory and up to 5 parent directories.
