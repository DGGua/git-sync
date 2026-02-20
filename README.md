# Git Sync

A command-line tool for synchronizing Git repositories with SSH key management and safe sync operations.

[中文文档](README_CN.md)

## Features

- **Web Management UI**: Manage repository configs, SSH keys, and sync operations via web interface
- **SSH Key Management**: Generate, list, view, and delete SSH keys
- **Multi-Repository Support**: Configuration-driven batch sync for multiple repositories
- **Multiple Config Files**: Split configuration across multiple files in `configs/` directory
- **Safe Sync**: Fast-forward only pushes to prevent accidental overwrites
- **Branch and Tag Sync**: Selective sync of specific branches and tags
- **Dry Run Mode**: Preview sync operations without executing them

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd github-copy

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows

# Install dependencies
pip install -e .

# Install web interface dependencies (optional)
pip install -e ".[web]"

# Build frontend
cd frontend
npm install
npm run build
cd ..
```

## Getting Started

### CLI Mode

```bash
git-sync --help
git-sync init
git-sync sync --dry-run
```

### Web Interface Mode

```bash
# Start web service
uvicorn git_sync.web.app:app --reload

# Or specify host and port
uvicorn git_sync.web.app:app --host 0.0.0.0 --port 8000
```

Then visit http://localhost:8000 to access the web interface.

**Web Interface Features:**
- Dashboard overview
- Repository management (drag-and-drop sorting)
- SSH key management
- Global settings configuration
- One-click sync operations

### Docker Deployment

#### Quick Start

```bash
# Build and start (background)
docker compose up -d

# View logs
docker compose logs -f

# Stop service
docker compose down
```

Visit http://localhost:8000 to access the web interface.

#### Directory Structure

```
./
├── configs/          # Configuration files (YAML)
└── data/
    ├── ssh/          # SSH key storage
    └── mirror-cache/ # Mirror cache (faster syncs)
```

#### First-time Setup

1. **Start the service**
   ```bash
   docker compose up -d
   ```

2. **Access Web UI** - http://localhost:8000

3. **Add SSH Keys** - Generate or import keys in the Keys page

4. **Configure Public Keys** - Add public keys to your Git hosting service (GitHub/GitLab/Gitea etc.)

5. **Add Repositories** - Configure source and target repositories

6. **Enable Auto Sync** - Each repository can have its own sync interval

#### Configuration Files

**docker-compose.yml** - Development/Testing
- Uses bind mounts, data stored in `./data/` directory
- Easy to view and modify configurations

**docker-compose.prod.yml** - Production
- Uses Docker named volumes, managed by Docker
- Supports environment variables
- Automatic log rotation

```bash
# Use production config
docker compose -f docker-compose.prod.yml up -d

# Custom port and timezone
PORT=9000 TZ=America/New_York docker compose -f docker-compose.prod.yml up -d
```

#### Common Commands

```bash
# Rebuild image
docker compose build --no-cache

# View status
docker compose ps

# Debug in container
docker compose exec git-sync bash

# View resource usage
docker compose top

# Complete cleanup (including data)
docker compose down -v
```

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TZ` | `Asia/Shanghai` | Timezone |
| `PORT` | `8000` | Service port (prod config only) |

## Quick Start

### 1. Initialize Project

```bash
git-sync init
```

This creates `configs/` directory (with example config files) and `.ssh` directory.

### 2. Generate SSH Key

```bash
# Generate SSH key named my-key
git-sync key gen -n my-key

# View public key (add to Git hosting service)
git-sync key show my-key
```

### 3. Configure Repository

Edit `configs/02-repositories.yaml` to add your repository:

```yaml
repositories:
  - name: "my-project"
    source:
      url: "git@github.com:source/project.git"
      ssh_key: "my-key"
    target:
      url: "git@gitlab.com:target/project.git"
      ssh_key: "my-key"
    enabled: true
    sync_branches: ["main", "develop"]  # Empty list = all branches
    sync_tags: true
```

### 4. Add Public Key to Git Service

Add the public key to both source and target Git hosting services (GitHub, GitLab, Gitea, etc.).

### 5. Run Sync

```bash
# Dry run (preview)
git-sync sync --dry-run

# Actual sync
git-sync sync

# Sync specific repository
git-sync sync -r my-project
```

## CLI Commands

### Global Options

```
--version                       Show version
-c, --config PATH               Config directory path
-v, --verbose                   Verbose output
--log-level [DEBUG|INFO|WARNING|ERROR]  Log level
```

### Commands

#### `git-sync init`

Initialize git-sync project, creating necessary directories and files.

#### `git-sync key`

SSH key management commands.

```bash
# Generate key
git-sync key gen -n <name> [--type ed25519|rsa]

# List all keys
git-sync key list

# Show public key
git-sync key show <name>

# Delete key
git-sync key delete <name>
```

#### `git-sync repo`

Repository management commands.

```bash
# List configured repositories
git-sync repo list
```

#### `git-sync sync`

Synchronize repositories.

```bash
# Sync all enabled repositories
git-sync sync

# Sync specific repository
git-sync sync -r <name>

# Dry run mode
git-sync sync --dry-run
```

## Configuration

### Multiple Config Files

Git Sync supports splitting configuration across multiple YAML files in `configs/` directory:

```
configs/
├── 01-global.yaml      # Global settings (SSH, sync config)
├── 02-team-a.yaml      # Team A repositories
└── 03-team-b.yaml      # Team B repositories
```

**Merge Strategy:**

| Config Item | Merge Strategy |
|-------------|----------------|
| `version` | Value from first file |
| `ssh` | Value from first file |
| `sync` | Value from first file |
| `repositories` | Merge all, later files override same-name repos |

**Naming Convention:**

- Use numeric prefix to control load order (e.g., `01-`, `02-`)
- Global settings file should be first
- Config files are loaded in alphabetical order

**Example:**

`configs/01-global.yaml`:
```yaml
version: "1.0"

ssh:
  key_storage: ".ssh"
  default_key_type: "ed25519"

sync:
  temp_dir: "/tmp/git-sync"
  timeout: 300
  cleanup_after_sync: true
```

`configs/02-repositories.yaml`:
```yaml
repositories:
  - name: "project-alpha"
    source:
      url: "git@github.com:source/project.git"
      ssh_key: "project-key"
    target:
      url: "git@gitlab.com:target/project.git"
      ssh_key: "project-key"
    enabled: true
```

### SSH Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `key_storage` | string | `.ssh` | SSH key storage directory |
| `default_key_type` | string | `ed25519` | Default key type (ed25519/rsa) |

### Sync Configuration

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `temp_dir` | string | `/tmp/git-sync` | Temporary working directory |
| `timeout` | int | `300` | Operation timeout (seconds) |
| `cleanup_after_sync` | bool | `true` | Clean up temp files after sync |

### Repository Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Repository name (unique identifier) |
| `source.url` | string | Yes | Source repository URL |
| `source.ssh_key` | string | Yes | SSH key name for source |
| `target.url` | string | Yes | Target repository URL |
| `target.ssh_key` | string | Yes | SSH key name for target |
| `enabled` | bool | No | Enable sync (default: true) |
| `sync_branches` | list | No | Branches to sync, empty = all |
| `sync_tags` | bool | No | Sync tags (default: false) |
| `auto_sync_enabled` | bool | No | Enable auto sync (default: true) |
| `auto_sync_interval` | int | No | Auto sync interval in seconds (default: 86400) |

## Security Features

### Fast-Forward Check

Before pushing, the tool checks if the target branch can be fast-forward merged. If source and target branches have diverged, the branch is skipped to prevent accidental overwrites.

### No Force Push

For safety, the tool does not support force push. If you need to force update, please do it manually.

## Example Scenarios

### Scenario 1: GitHub to GitLab Mirror

```yaml
repositories:
  - name: "mirror-project"
    source:
      url: "git@github.com:myorg/project.git"
      ssh_key: "github-key"
    target:
      url: "git@gitlab.com:myorg/project.git"
      ssh_key: "gitlab-key"
    enabled: true
    sync_branches: ["main"]
    sync_tags: true
```

### Scenario 2: Multi-Repository Batch Sync

```yaml
repositories:
  - name: "frontend"
    source:
      url: "git@github.com:company/frontend.git"
      ssh_key: "company-key"
    target:
      url: "git@gitlab.com:company/frontend.git"
      ssh_key: "company-key"
    enabled: true

  - name: "backend"
    source:
      url: "git@github.com:company/backend.git"
      ssh_key: "company-key"
    target:
      url: "git@gitlab.com:company/backend.git"
      ssh_key: "company-key"
    enabled: true
```

### Scenario 3: Self-hosted Gitea Sync

```yaml
repositories:
  - name: "internal-sync"
    source:
      url: "ssh://git@gitea.example.com:2222/team/project.git"
      ssh_key: "gitea-key"
    target:
      url: "ssh://git@gitea-backup.example.com:2222/team/project.git"
      ssh_key: "gitea-key"
    enabled: true
    sync_branches: []
    sync_tags: true
```

## Troubleshooting

### SSH Authentication Failed

1. Verify public key is correctly added to Git hosting service
2. Check key permissions: `chmod 600 .ssh/<key-name>`
3. Test connection manually: `ssh -i .ssh/<key-name> -T git@<host>`

### Host Key Verification Failed

```bash
# Scan and add host key
ssh-keyscan <host> >> ~/.ssh/known_hosts
```

### Branch Skipped

If a branch is skipped due to "diverged history", it means the target branch has commits that the source doesn't. You need to decide how to handle this conflict manually.

## License

MIT License
