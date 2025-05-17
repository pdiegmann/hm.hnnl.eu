"""
Main CLI entry point for the hm-cli tool.
"""

import os
import sys
import click
from rich.console import Console

from hm_cli.core import logger, console, ConfigManager, get_repo_path
from hm_cli.cluster import ClusterManager
from hm_cli.service import ServiceManager
from hm_cli.gitops import GitOpsManager

@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Homelab Kubernetes Cluster Management CLI.
    
    This tool helps manage the lifecycle of a homelab Kubernetes cluster
    based on Talos OS, Flux CD, and GitOps principles.
    """
    pass

# Cluster commands
@cli.group()
def cluster():
    """Manage Kubernetes cluster lifecycle."""
    pass

@cluster.command("create")
def cluster_create():
    """Create a new Kubernetes cluster."""
    manager = ClusterManager()
    if not manager.create():
        sys.exit(1)

@cluster.command("upgrade")
def cluster_upgrade():
    """Upgrade an existing Kubernetes cluster."""
    manager = ClusterManager()
    if not manager.upgrade():
        sys.exit(1)

@cluster.command("delete")
def cluster_delete():
    """Delete an existing Kubernetes cluster."""
    manager = ClusterManager()
    if not manager.delete():
        sys.exit(1)

@cluster.command("status")
def cluster_status():
    """Show the status of the Kubernetes cluster."""
    manager = ClusterManager()
    if not manager.status():
        sys.exit(1)

# Service commands
@cli.group()
def service():
    """Manage cluster services."""
    pass

@service.command("add")
def service_add():
    """Add a new service to the cluster."""
    manager = ServiceManager()
    if not manager.add():
        sys.exit(1)

@service.command("list")
def service_list():
    """List all services in the cluster."""
    manager = ServiceManager()
    if not manager.list():
        sys.exit(1)

@service.command("remove")
def service_remove():
    """Remove a service from the cluster."""
    manager = ServiceManager()
    if not manager.remove():
        sys.exit(1)

# GitOps commands
@cli.group()
def gitops():
    """Manage GitOps operations."""
    pass

@gitops.command("commit")
@click.option("--message", "-m", help="Commit message")
def gitops_commit(message):
    """Commit changes to Git repository."""
    manager = GitOpsManager()
    if not manager.commit(message):
        sys.exit(1)

@gitops.command("push")
@click.option("--remote", help="Remote name")
@click.option("--branch", help="Branch name")
def gitops_push(remote, branch):
    """Push changes to remote repository."""
    manager = GitOpsManager()
    if not manager.push(remote, branch):
        sys.exit(1)

@gitops.command("sync")
def gitops_sync():
    """Trigger Flux synchronization."""
    manager = GitOpsManager()
    if not manager.sync():
        sys.exit(1)

# Config commands
@cli.group()
def config():
    """Manage CLI configuration."""
    pass

@config.command("show")
def config_show():
    """Show current configuration."""
    config_manager = ConfigManager()
    console.print(config_manager.config)

@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value."""
    config_manager = ConfigManager()
    config_manager.set(key, value)
    console.print(f"[green]Configuration updated: {key} = {value}[/green]")

def main():
    """Main entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
