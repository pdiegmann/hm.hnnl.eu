"""
GitOps management module for the hm-cli tool.
Handles Git operations and Flux synchronization.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional

import git
import questionary
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from hm_cli.core import logger, console, ConfigManager, run_command, get_repo_path


class GitOpsManager:
    """Manages GitOps operations."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize the GitOps manager.
        
        Args:
            repo_path: Path to the repository. If None, uses the configured path.
        """
        self.config = ConfigManager()
        self.repo_path = repo_path or get_repo_path()
        
        # Initialize Git repository
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            console.print(f"[bold yellow]Warning: {self.repo_path} is not a Git repository.[/bold yellow]")
            self.repo = None
        except Exception as e:
            console.print(f"[bold red]Error accessing Git repository: {e}[/bold red]")
            self.repo = None
    
    def commit(self, message: Optional[str] = None) -> bool:
        """Commit changes to the Git repository.
        
        Args:
            message: Commit message. If None, will prompt for one.
            
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Committing changes to Git repository", title="GitOps Commit"))
        
        if not self.repo:
            console.print(f"[bold red]Error: {self.repo_path} is not a Git repository.[/bold red]")
            return False
        
        # Check if there are changes to commit
        if not self.repo.is_dirty(untracked_files=True):
            console.print("[yellow]No changes to commit.[/yellow]")
            return True
        
        # Get commit message if not provided
        if not message:
            message = questionary.text(
                "Commit message:",
                default="Update cluster configuration"
            ).ask()
        
        # Configure Git user if not already configured
        if not self._ensure_git_config():
            return False
        
        try:
            # Add all changes
            self.repo.git.add(A=True)
            
            # Commit changes
            self.repo.git.commit(m=message)
            
            console.print(f"[green]Changes committed with message: {message}[/green]")
            return True
        except Exception as e:
            console.print(f"[bold red]Error committing changes: {e}[/bold red]")
            return False
    
    def push(self, remote: Optional[str] = None, branch: Optional[str] = None) -> bool:
        """Push changes to the remote repository.
        
        Args:
            remote: Remote name. If None, uses the configured remote.
            branch: Branch name. If None, uses the current branch.
            
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Pushing changes to remote repository", title="GitOps Push"))
        print(f"GITOPS_DEBUG: Entering push method. Remote: {remote}, Branch: {branch}") # DEBUG
        
        if not self.repo:
            console.print(f"[bold red]Error: {self.repo_path} is not a Git repository.[/bold red]")
            print("GITOPS_DEBUG: No repo found, returning False.") # DEBUG
            return False
        
        # Get remote and branch if not provided
        if not remote:
            remote = self.config.get('git.remote', 'origin')
            print(f"GITOPS_DEBUG: Remote not provided, using default: {remote}") # DEBUG
        
        if not branch:
            branch = self.repo.active_branch.name
            print(f"GITOPS_DEBUG: Branch not provided, using active: {branch}") # DEBUG
        
        print(f"GITOPS_DEBUG: Final remote: {remote}, branch: {branch}") # DEBUG
        try:
            # Check if remote exists
            print(f"GITOPS_DEBUG: Attempting to get remote '{remote}'") # DEBUG
            try:
                actual_remote_obj = self.repo.remote(remote)
                print(f"GITOPS_DEBUG: Successfully got remote '{remote}': {actual_remote_obj}") # DEBUG
            except ValueError:
                console.print(f"[bold red]Error: Remote '{remote}' not found.[/bold red]")
                print(f"GITOPS_DEBUG: Remote '{remote}' not found (ValueError).") # DEBUG
                
                # Ask if user wants to add the remote
                add_remote = questionary.confirm(f"Do you want to add remote '{remote}'?").ask()
                if add_remote:
                    remote_url = questionary.text("Remote URL:").ask()
                    self.repo.create_remote(remote, url=remote_url)
                    print(f"GITOPS_DEBUG: Created remote '{remote}' with URL '{remote_url}'.") # DEBUG
                else:
                    print(f"GITOPS_DEBUG: User declined to add remote, returning False.") # DEBUG
                    return False
            
            # Push changes
            print(f"GITOPS_DEBUG: Attempting to push to remote '{remote}', branch '{branch}'.") # DEBUG
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Pushing to {remote}/{branch}...", total=None)
                
                push_info_list = self.repo.remote(remote).push(branch) # Renamed to avoid conflict with git.PushInfo
                print(f"GITOPS_DEBUG: Push command executed. Result: {push_info_list}") # DEBUG
                
                progress.update(task, completed=True)
            
            # Check push results
            print(f"GITOPS_DEBUG: Checking push results: {push_info_list}") # DEBUG
            for info_item in push_info_list: # Renamed loop variable
                print(f"GITOPS_DEBUG: Processing push_info_item: flags={info_item.flags}, summary='{info_item.summary}'") # DEBUG
                # Assuming info.ERROR is an attribute like git.PushInfo.ERROR
                # We need to ensure 'info' here refers to the class git.PushInfo if that's where ERROR is defined
                # For now, let's assume info_item.ERROR would be the way if info_item was a PushInfo object
                # The mock provides a MagicMock as info_item, so info_item.ERROR would be another MagicMock
                # The original code uses 'info.flags & info.ERROR'. This implies info.ERROR is a flag bitmask.
                # Let's try to access git.PushInfo.ERROR directly if available.
                error_flag_value = getattr(git.PushInfo, 'ERROR', 128) # Default to 128 if not found
                print(f"GITOPS_DEBUG: Using error_flag_value: {error_flag_value}") # DEBUG

                if info_item.flags & error_flag_value:
                    console.print(f"[bold red]Error pushing to {remote}/{branch}: {info_item.summary}[/bold red]")
                    print(f"GITOPS_DEBUG: Push error detected by flags, returning False. Flags: {info_item.flags}, Summary: {info_item.summary}") # DEBUG
                    return False
            
            console.print(f"[green]Changes pushed to {remote}/{branch} successfully.[/green]")
            print("GITOPS_DEBUG: Push successful, returning True.") # DEBUG
            return True
        except Exception as e:
            console.print(f"[bold red]Error pushing changes: {e}[/bold red]")
            print(f"GITOPS_DEBUG: Exception during push: {e}, returning False.") # DEBUG
            import traceback # DEBUG
            print(traceback.format_exc()) # DEBUG
            return False
    
    def sync(self) -> bool:
        """Trigger Flux synchronization.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Triggering Flux synchronization", title="GitOps Sync"))
        
        # Check if kubeconfig exists
        kubeconfig_path = os.path.join(self.repo_path, "kubeconfig")
        if not os.path.exists(kubeconfig_path):
            console.print("[bold red]Error: Kubeconfig not found. Cluster may not be initialized.[/bold red]")
            return False
        
        # Set KUBECONFIG environment variable
        env = os.environ.copy()
        env["KUBECONFIG"] = kubeconfig_path
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Triggering Flux sync...", total=None)
            
            # Check if flux is installed
            returncode, stdout, stderr = run_command(
                "flux --version",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print("[bold red]Error: Flux CLI not installed or not in PATH.[/bold red]")
                return False
            
            # Trigger reconciliation
            returncode, stdout, stderr = run_command(
                "flux reconcile source git flux-system",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error triggering Flux reconciliation: {stderr}[/bold red]")
                return False
            
            # Wait for reconciliation to complete
            progress.update(task, description="Waiting for reconciliation to complete...")
            
            # Sleep for a moment to allow reconciliation to start
            time.sleep(2)
            
            # Check reconciliation status
            returncode, stdout, stderr = run_command(
                "flux get kustomizations --watch",
                cwd=self.repo_path
            )
            
            progress.update(task, completed=True)
        
        console.print("[green]Flux synchronization triggered successfully.[/green]")
        console.print("[blue]Check the status with: flux get all[/blue]")
        return True
    
    def _ensure_git_config(self) -> bool:
        """Ensure Git user configuration is set.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            # Check if user name and email are configured
            try:
                user_name = self.repo.git.config('user.name')
                user_email = self.repo.git.config('user.email')
            except git.GitCommandError:
                # Not configured, get from config or prompt
                user_name = self.config.get('git.user_name')
                user_email = self.config.get('git.user_email')
                
                if not user_name:
                    user_name = questionary.text("Git user name:").ask()
                    self.config.set('git.user_name', user_name)
                
                if not user_email:
                    user_email = questionary.text("Git user email:").ask()
                    self.config.set('git.user_email', user_email)
                
                # Set Git config
                self.repo.git.config('user.name', user_name)
                self.repo.git.config('user.email', user_email)
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error configuring Git: {e}[/bold red]")
            return False
