# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Git Sync is a tool for synchronizing Git repositories between different hosting services (e.g., GitHub to GitLab). It provides both a CLI and a Web UI, with SSH key management, selective branch/tag syncing, and safety features like fast-forward checks.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Install with dev dependencies (testing, linting)
pip install -e ".[dev]"

# Install with web dependencies (FastAPI, scheduler)
pip install -e ".[web]"

# CLI usage
git-sync --help
git-sync init
git-sync sync --dry-run

# Run web server
uvicorn git_sync.web.app:app --reload

# Run tests
pytest
pytest --cov=git_sync

# Linting and formatting
ruff check .
black .
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev      # Development server
npm run build    # Build for production
```

### Docker

```bash
docker compose up -d              # Development (bind mounts)
docker compose -f docker-compose.prod.yml up -d  # Production (named volumes)
```

## Architecture

The codebase follows a layered architecture under `git_sync/`:

### CLI Layer (`cli.py`)
- Uses Click for command-line interface
- Main commands: `init`, `key` (gen/list/show/delete), `repo list`, `sync`

### Configuration Layer (`config/`)
- `schema.py`: Dataclasses for Config, RepositoryConfig, SSHConfig, SyncSettings
- `loader.py`: ConfigManager handles YAML loading from `configs/` directory

### SSH Layer (`ssh/`)
- `key_manager.py`: KeyManager handles SSH key generation, storage, and manifest tracking
- `ssh_config.py`: SSHConfigGenerator builds `GIT_SSH_COMMAND` environment variable

### Core Layer (`core/`)
- `repository.py`: Repository class wraps git operations (clone, fetch, push, branch/tag queries)
- `sync.py`: SyncOrchestrator coordinates the sync workflow
- `exceptions.py`: Custom exception hierarchy

### Web Layer (`web/`)
- `app.py`: FastAPI application with lifespan management, serves Vue.js frontend
- `scheduler.py`: SyncScheduler uses APScheduler for automatic sync jobs per repository
- `api/`: REST API endpoints (config, keys, repositories, sync, history, scheduler)
- `history.py`: Sync history tracking stored in `data/sync_history.json`

### Frontend (`frontend/`)
- Vue 3 + Vue Router + Pinia + Vite
- Single-page app served by FastAPI at non-API routes

## Key Design Decisions

1. **Mirror Cache**: Uses `.mirror-cache/` for faster subsequent syncs. First sync creates a bare mirror; subsequent syncs fetch incrementally.

2. **Safety Checks**: Push only proceeds if fast-forward is possible (via `merge-base --is-ancestor`). Diverged branches are skipped, never force-pushed.

3. **SSH Key Management**: Keys stored in `.ssh/` with `keys_manifest.yaml` tracking. Uses `GIT_SSH_COMMAND` env var to specify keys per-operation.

4. **Multi-File Configuration**: `configs/` directory supports multiple YAML files merged at load time. Global settings from first file, repositories merged with later files overriding duplicates.

5. **Auto-Sync Scheduler**: Each repository can have `auto_sync_enabled` and `auto_sync_interval`. SyncScheduler schedules APScheduler jobs per repo on web server startup.
