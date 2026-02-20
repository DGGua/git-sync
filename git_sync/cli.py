"""Command-line interface for git-sync."""

import os
import sys
from pathlib import Path
from typing import Optional

import click

from git_sync import __version__
from git_sync.config.loader import ConfigManager
from git_sync.config.schema import SSHConfig
from git_sync.core.exceptions import GitSyncError
from git_sync.core.sync import SyncOrchestrator
from git_sync.ssh.key_manager import KeyManager
from git_sync.utils.logger import logger, setup_logger


def get_config_manager(config_path: Optional[str] = None) -> ConfigManager:
    """Get configuration manager.

    Args:
        config_path: Optional path to configuration file

    Returns:
        ConfigManager instance
    """
    return ConfigManager(config_path)


def get_key_manager(config_path: Optional[str] = None) -> KeyManager:
    """Get key manager from config.

    Args:
        config_path: Optional path to configuration file

    Returns:
        KeyManager instance
    """
    try:
        config_manager = get_config_manager(config_path)
        config = config_manager.config
        return KeyManager(config.ssh.key_storage)
    except GitSyncError:
        # If no config, use default storage
        return KeyManager(".ssh")


@click.group()
@click.version_option(version=__version__)
@click.option(
    "-c",
    "--config",
    "config_path",
    type=click.Path(exists=False),
    help="Path to configuration directory",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--log-level",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR"]),
    default="INFO",
    help="Log level",
)
@click.pass_context
def main(ctx, config_path: Optional[str], verbose: bool, log_level: str):
    """Git repository synchronization tool.

    Synchronize source Git repositories to target repositories with
    SSH key management and safety checks.
    """
    # Setup logging
    if verbose:
        log_level = "DEBUG"
    setup_logger(level=log_level)

    # Store context
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config_path


@main.command()
@click.pass_context
def init(ctx):
    """Initialize git-sync project.

    Creates configs directory with sample files and SSH directory if they don't exist.
    """
    config_path = ctx.obj.get("config_path")

    # Determine config directory location
    if config_path:
        config_dir = Path(config_path)
    else:
        config_dir = Path.cwd() / "configs"

    if config_dir.exists() and any(config_dir.glob("*.yaml")):
        click.echo(f"Configuration directory already exists with config files: {config_dir}")
        return

    # Create config directory
    config_dir.mkdir(exist_ok=True)

    # Create global settings file
    global_config = config_dir / "01-global.yaml"
    if not global_config.exists():
        global_config.write_text("""# Git Sync Global Configuration
# This file contains global settings that apply to all repositories.

version: "1.0"

ssh:
  key_storage: ".ssh"
  default_key_type: "ed25519"

sync:
  temp_dir: "/tmp/git-sync"
  timeout: 300
  cleanup_after_sync: true
  enable_mirror_cache: true
  mirror_cache_dir: ".mirror-cache"
""")
        click.echo(f"Created configuration file: {global_config}")

    # Create sample repositories file
    repos_config = config_dir / "02-repositories.yaml"
    if not repos_config.exists():
        repos_config.write_text("""# Repository Configurations
# Add your repository configurations below.

repositories:
  # Example repository configuration:
  # - name: "my-project"
  #   source:
  #     url: "git@github.com:source/project.git"
  #     ssh_key: "my-project_key"
  #   target:
  #     url: "git@gitlab.com:target/project.git"
  #     ssh_key: "my-project_key"
  #   enabled: true
  #   sync_branches: ["main", "develop"]
  #   sync_tags: true
""")
        click.echo(f"Created configuration file: {repos_config}")

    # Create SSH directory
    ssh_dir = Path.cwd() / ".ssh"
    ssh_dir.mkdir(exist_ok=True)
    ssh_dir.chmod(0o700)
    click.echo(f"Created SSH directory: {ssh_dir}")

    click.echo("\nNext steps:")
    click.echo("1. Generate SSH keys: git-sync key gen -n <name>")
    click.echo("2. Add repositories to configs/02-repositories.yaml")
    click.echo("3. Run sync: git-sync sync")


# Key management commands
@main.group(name="key")
def key_group():
    """SSH key management commands."""
    pass


@key_group.command("gen")
@click.option("-n", "--name", required=True, help="Key name")
@click.option(
    "-t",
    "--type",
    "key_type",
    default="ed25519",
    type=click.Choice(["ed25519", "rsa", "ecdsa"]),
    help="Key type",
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing key")
@click.option("-c", "--comment", help="Key comment")
@click.pass_context
def key_gen(ctx, name: str, key_type: str, overwrite: bool, comment: Optional[str]):
    """Generate a new SSH key pair."""
    key_manager = get_key_manager(ctx.obj.get("config_path"))

    try:
        key_path = key_manager.generate(
            name=name,
            key_type=key_type,
            comment=comment,
            overwrite=overwrite,
        )
        click.echo(f"Generated SSH key: {key_path}")
        click.echo(f"\nPublic key:")
        click.echo(key_manager.get_public_key(name))
        click.echo("\nAdd this public key to your Git hosting service.")
    except GitSyncError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@key_group.command("list")
@click.pass_context
def key_list(ctx):
    """List all managed SSH keys."""
    key_manager = get_key_manager(ctx.obj.get("config_path"))

    keys = key_manager.list()

    if not keys:
        click.echo("No SSH keys found.")
        return

    click.echo("Managed SSH keys:")
    click.echo("-" * 60)

    for key in keys:
        status = "OK" if key["exists"] and key["public_exists"] else "MISSING"
        click.echo(f"\nName: {key['name']}")
        click.echo(f"  Type: {key['type']}")
        click.echo(f"  Created: {key['created_at']}")
        click.echo(f"  Status: {status}")
        if key["bound_to"]:
            click.echo(f"  Bound to: {', '.join(key['bound_to'])}")


@key_group.command("show")
@click.argument("name")
@click.pass_context
def key_show(ctx, name: str):
    """Display public key for a managed key."""
    key_manager = get_key_manager(ctx.obj.get("config_path"))

    try:
        public_key = key_manager.get_public_key(name)
        click.echo(public_key)
    except GitSyncError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@key_group.command("delete")
@click.argument("name")
@click.option("--yes", is_flag=True, help="Skip confirmation")
@click.pass_context
def key_delete(ctx, name: str, yes: bool):
    """Delete an SSH key pair."""
    key_manager = get_key_manager(ctx.obj.get("config_path"))

    if not yes:
        if not click.confirm(f"Delete key '{name}'?"):
            click.echo("Aborted.")
            return

    try:
        if key_manager.delete(name):
            click.echo(f"Deleted key: {name}")
        else:
            click.echo(f"Key not found: {name}")
    except GitSyncError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# Repository commands
@main.group(name="repo")
def repo_group():
    """Repository management commands."""
    pass


@repo_group.command("list")
@click.pass_context
def repo_list(ctx):
    """List configured repositories."""
    config_manager = get_config_manager(ctx.obj.get("config_path"))

    try:
        config = config_manager.config
    except GitSyncError as e:
        click.echo(f"Error loading config: {e}", err=True)
        sys.exit(1)

    if not config.repositories:
        click.echo("No repositories configured.")
        return

    click.echo("Configured repositories:")
    click.echo("-" * 60)

    for repo in config.repositories:
        status = "enabled" if repo.enabled else "disabled"
        click.echo(f"\nName: {repo.name}")
        click.echo(f"  Status: {status}")
        click.echo(f"  Source: {repo.source.url}")
        click.echo(f"  Target: {repo.target.url}")
        if repo.sync_branches:
            click.echo(f"  Branches: {', '.join(repo.sync_branches)}")
        else:
            click.echo("  Branches: all")
        click.echo(f"  Sync tags: {repo.sync_tags}")


# Sync commands
@main.command()
@click.option("-r", "--repository", "repositories", multiple=True, help="Specific repository to sync")
@click.option("--dry-run", is_flag=True, help="Show what would be done without making changes")
@click.pass_context
def sync(ctx, repositories: tuple, dry_run: bool):
    """Synchronize repositories.

    By default, syncs all enabled repositories. Use -r to sync specific repositories.
    """
    config_manager = get_config_manager(ctx.obj.get("config_path"))

    try:
        orchestrator = SyncOrchestrator(
            config_manager=config_manager,
            dry_run=dry_run,
        )

        repo_list = list(repositories) if repositories else None
        summary = orchestrator.sync_all(repo_list)

        # Print summary
        click.echo("\n" + "=" * 60)
        click.echo("Sync Summary")
        click.echo("=" * 60)
        click.echo(f"Total: {summary.total}")
        click.echo(f"Successful: {summary.successful}")
        click.echo(f"Failed: {summary.failed}")
        click.echo(f"Duration: {summary.duration:.2f}s")

        # Show details for each repo
        for result in summary.results:
            click.echo(f"\n{result.repository}:")
            click.echo(f"  Status: {'SUCCESS' if result.success else 'FAILED'}")
            if result.branches_synced:
                click.echo(f"  Branches synced: {', '.join(result.branches_synced)}")
            if result.branches_skipped:
                for branch, reason in result.branches_skipped:
                    click.echo(f"  Branch skipped: {branch} ({reason})")
            if result.tags_synced:
                click.echo(f"  Tags synced: {', '.join(result.tags_synced)}")
            if result.tags_failed:
                for tag, reason in result.tags_failed:
                    click.echo(f"  Tag failed: {tag} ({reason})")
            if result.error:
                click.echo(f"  Error: {result.error}")

        # Exit with error if any failed
        if summary.failed > 0:
            sys.exit(1)

    except GitSyncError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
