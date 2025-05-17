"""
Cluster management module for the hm-cli tool.
Handles cluster creation, upgrade, deletion, and status.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional

import yaml
import questionary
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from hm_cli.core import logger, console, ConfigManager, run_command, validate_ip_address, get_repo_path


class ClusterManager:
    """Manages Kubernetes cluster operations."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize the cluster manager.
        
        Args:
            repo_path: Path to the repository. If None, uses the configured path.
        """
        self.config = ConfigManager()
        self.repo_path = repo_path or get_repo_path()
        
    def create(self) -> bool:
        """Create a new Kubernetes cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Creating a new Kubernetes cluster", title="Cluster Creation"))
        
        # Collect cluster information
        cluster_info = self._collect_cluster_info()
        if not cluster_info:
            return False
        
        # Generate Talos configurations
        if not self._generate_talos_configs(cluster_info):
            return False
        
        # Apply configurations to nodes
        if not self._apply_talos_configs(cluster_info):
            return False
        
        # Bootstrap the cluster
        if not self._bootstrap_cluster(cluster_info):
            return False
        
        # Set up Flux
        if not self._setup_flux(cluster_info):
            return False
        
        console.print("[bold green]Cluster created successfully![/bold green]")
        return True
    
    def upgrade(self) -> bool:
        """Upgrade an existing Kubernetes cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Upgrading Kubernetes cluster", title="Cluster Upgrade"))
        
        # Get cluster information
        cluster_info = self._get_current_cluster_info()
        if not cluster_info:
            return False
        
        # Confirm upgrade
        if not questionary.confirm("Are you sure you want to upgrade the cluster?").ask():
            console.print("[yellow]Upgrade cancelled.[/yellow]")
            return False
        
        # Get upgrade targets
        k8s_version = questionary.text(
            "Kubernetes version to upgrade to (leave empty for latest):",
            default=""
        ).ask()
        
        talos_version = questionary.text(
            "Talos version to upgrade to (leave empty for latest):",
            default=""
        ).ask()
        
        # Perform upgrade
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Upgrading cluster...", total=None)
            
            # Update Talos configurations
            if not self._update_talos_configs(cluster_info, k8s_version, talos_version):
                progress.stop()
                return False
            
            # Apply updated configurations
            if not self._apply_talos_configs(cluster_info, is_upgrade=True):
                progress.stop()
                return False
            
            # Wait for upgrade to complete
            if not self._wait_for_upgrade(cluster_info):
                progress.stop()
                return False
            
            progress.update(task, completed=True)
        
        console.print("[bold green]Cluster upgraded successfully![/bold green]")
        return True
    
    def delete(self) -> bool:
        """Delete an existing Kubernetes cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Deleting Kubernetes cluster", title="Cluster Deletion"))
        
        # Get cluster information
        cluster_info = self._get_current_cluster_info()
        if not cluster_info:
            return False
        
        # Confirm deletion
        confirmation = questionary.text(
            "Type the cluster name to confirm deletion:",
        ).ask()
        
        if confirmation != cluster_info.get('name'):
            console.print("[bold red]Deletion cancelled: Cluster name does not match.[/bold red]")
            return False
        
        # Perform deletion
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Deleting cluster...", total=None)
            
            # Reset nodes
            if not self._reset_nodes(cluster_info):
                progress.stop()
                return False
            
            # Clean up local files
            if not self._cleanup_local_files(cluster_info):
                progress.stop()
                return False
            
            progress.update(task, completed=True)
        
        console.print("[bold green]Cluster deleted successfully![/bold green]")
        return True
    
    def status(self) -> bool:
        """Show the status of the Kubernetes cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Kubernetes Cluster Status", title="Cluster Status"))
        
        # Get cluster information
        cluster_info = self._get_current_cluster_info()
        if not cluster_info:
            return False
        
        # Check if kubeconfig exists
        kubeconfig_path = os.path.join(self.repo_path, "kubeconfig")
        if not os.path.exists(kubeconfig_path):
            console.print("[bold red]Error: Kubeconfig not found. Cluster may not be initialized.[/bold red]")
            return False
        
        # Get node status
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Fetching cluster status...", total=None)
            
            # Run kubectl to get nodes
            env = os.environ.copy()
            env["KUBECONFIG"] = kubeconfig_path
            
            returncode, stdout, stderr = run_command(
                "kubectl get nodes -o wide",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error getting node status: {stderr}[/bold red]")
                return False
            
            # Get pod status
            returncode, pods_stdout, pods_stderr = run_command(
                "kubectl get pods --all-namespaces",
                cwd=self.repo_path
            )
            
            progress.update(task, completed=True)
        
        # Display results
        console.print("\n[bold]Node Status:[/bold]")
        console.print(stdout)
        
        if returncode == 0:
            console.print("\n[bold]Pod Status:[/bold]")
            console.print(pods_stdout)
        
        return True
    
    def _collect_cluster_info(self) -> Dict[str, Any]:
        """Collect information needed to create a cluster.
        
        Returns:
            Dict containing cluster information.
        """
        # Get default values from config
        config = self.config
        default_name = config.get('cluster.name', 'homelab')
        default_network_prefix = config.get('cluster.network_prefix', '192.168.1')
        default_control_plane_vip = config.get('cluster.control_plane_vip', f"{default_network_prefix}.100")
        
        # Collect information
        cluster_name = questionary.text(
            "Cluster name:",
            default=default_name
        ).ask()
        
        network_prefix = questionary.text(
            "Network prefix (e.g., 192.168.1):",
            default=default_network_prefix,
            validate=lambda text: len(text.split('.')) == 3
        ).ask()
        
        control_plane_vip = questionary.text(
            "Control plane VIP:",
            default=default_control_plane_vip,
            validate=validate_ip_address
        ).ask()
        
        # Collect node information
        nodes = []
        
        # First control plane node (required)
        cp1_ip = questionary.text(
            "First control plane IP:",
            validate=validate_ip_address
        ).ask()
        
        nodes.append({
            'name': 'talos-cp1',
            'ip': cp1_ip,
            'type': 'controlplane',
            'hardware': 'ryzen'
        })
        
        # Second control plane node (required)
        cp2_ip = questionary.text(
            "Second control plane IP:",
            validate=validate_ip_address
        ).ask()
        
        nodes.append({
            'name': 'talos-cp2',
            'ip': cp2_ip,
            'type': 'controlplane',
            'hardware': 'intel'
        })
        
        # Third control plane node (required)
        cp3_ip = questionary.text(
            "Third control plane IP:",
            validate=validate_ip_address
        ).ask()
        
        nodes.append({
            'name': 'talos-cp3',
            'ip': cp3_ip,
            'type': 'controlplane',
            'hardware': 'mac-mini'
        })
        
        # Save to config
        config.set('cluster.name', cluster_name)
        config.set('cluster.network_prefix', network_prefix)
        config.set('cluster.control_plane_vip', control_plane_vip)
        
        # Return collected information
        return {
            'name': cluster_name,
            'network_prefix': network_prefix,
            'control_plane_vip': control_plane_vip,
            'nodes': nodes
        }
    
    def _generate_talos_configs(self, cluster_info: Dict[str, Any]) -> bool:
        """Generate Talos configurations for the cluster.
        
        Args:
            cluster_info: Cluster information.
            
        Returns:
            True if successful, False otherwise.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Generating Talos configurations...", total=None)
            
            # Run the gen-config.sh script
            script_path = os.path.join(self.repo_path, "bootstrap", "talos", "gen-config.sh")
            
            if not os.path.exists(script_path):
                progress.stop()
                console.print(f"[bold red]Error: gen-config.sh script not found at {script_path}[/bold red]")
                return False
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            # Run the script
            returncode, stdout, stderr = run_command(
                script_path,
                cwd=os.path.join(self.repo_path, "bootstrap", "talos")
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error generating Talos configurations: {stderr}[/bold red]")
                return False
            
            progress.update(task, completed=True)
        
        console.print("[green]Talos configurations generated successfully.[/green]")
        return True
    
    def _apply_talos_configs(self, cluster_info: Dict[str, Any], is_upgrade: bool = False) -> bool:
        """Apply Talos configurations to nodes.
        
        Args:
            cluster_info: Cluster information.
            is_upgrade: Whether this is an upgrade operation.
            
        Returns:
            True if successful, False otherwise.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Applying Talos configurations to nodes...", total=len(cluster_info['nodes']))
            
            for node in cluster_info['nodes']:
                progress.update(task, description=f"Applying configuration to {node['name']} ({node['ip']})...")
                
                # Get the configuration file path
                config_file = os.path.join(
                    self.repo_path,
                    "infrastructure",
                    "talos",
                    "controlplane",
                    f"{node['name']}.yaml"
                )
                
                if not os.path.exists(config_file):
                    progress.stop()
                    console.print(f"[bold red]Error: Configuration file not found at {config_file}[/bold red]")
                    return False
                
                # Apply the configuration
                returncode, stdout, stderr = run_command(
                    f"talosctl apply-config --insecure --nodes {node['ip']} --file {config_file}",
                    cwd=self.repo_path
                )
                
                if returncode != 0:
                    progress.stop()
                    console.print(f"[bold red]Error applying configuration to {node['name']}: {stderr}[/bold red]")
                    return False
                
                progress.advance(task)
            
            progress.update(task, completed=True)
        
        console.print("[green]Talos configurations applied successfully.[/green]")
        return True
    
    def _bootstrap_cluster(self, cluster_info: Dict[str, Any]) -> bool:
        """Bootstrap the Kubernetes cluster.
        
        Args:
            cluster_info: Cluster information.
            
        Returns:
            True if successful, False otherwise.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Bootstrapping cluster...", total=None)
            
            # Bootstrap the first control plane node
            first_node = cluster_info['nodes'][0]
            
            returncode, stdout, stderr = run_command(
                f"talosctl bootstrap --nodes {first_node['ip']}",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error bootstrapping cluster: {stderr}[/bold red]")
                return False
            
            # Wait for the Kubernetes API to be available
            progress.update(task, description="Waiting for Kubernetes API...")
            
            node_ips = ",".join([node['ip'] for node in cluster_info['nodes']])
            
            returncode, stdout, stderr = run_command(
                f"talosctl health --nodes {node_ips} --wait-timeout 15m",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error waiting for Kubernetes API: {stderr}[/bold red]")
                return False
            
            # Get kubeconfig
            progress.update(task, description="Retrieving kubeconfig...")
            
            returncode, stdout, stderr = run_command(
                f"talosctl kubeconfig --nodes {first_node['ip']} -f ./kubeconfig",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error retrieving kubeconfig: {stderr}[/bold red]")
                return False
            
            progress.update(task, completed=True)
        
        console.print("[green]Cluster bootstrapped successfully.[/green]")
        console.print(f"[blue]Kubeconfig saved to {os.path.join(self.repo_path, 'kubeconfig')}[/blue]")
        return True
    
    def _setup_flux(self, cluster_info: Dict[str, Any]) -> bool:
        """Set up Flux CD for GitOps.
        
        Args:
            cluster_info: Cluster information.
            
        Returns:
            True if successful, False otherwise.
        """
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Setting up Flux CD...", total=None)
            
            # Get Git information
            git_user = self.config.get('git.user_name')
            if not git_user:
                git_user = questionary.text("GitHub username:").ask()
                self.config.set('git.user_name', git_user)
            
            git_repo = questionary.text(
                "GitHub repository name:",
                default="homelab"
            ).ask()
            
            git_branch = self.config.get('git.branch', 'main')
            
            # Set KUBECONFIG environment variable
            env = os.environ.copy()
            env["KUBECONFIG"] = os.path.join(self.repo_path, "kubeconfig")
            
            # Run bootstrap command
            returncode, stdout, stderr = run_command(
                f"flux bootstrap github --owner={git_user} --repository={git_repo} --branch={git_branch} --path=cluster/flux --personal",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                progress.stop()
                console.print(f"[bold red]Error setting up Flux: {stderr}[/bold red]")
                return False
            
            progress.update(task, completed=True)
        
        console.print("[green]Flux CD set up successfully.[/green]")
        return True
    
    def _get_current_cluster_info(self) -> Dict[str, Any]:
        """Get information about the current cluster.
        
        Returns:
            Dict containing cluster information, or None if not found.
        """
        # Check if repository exists
        if not os.path.exists(self.repo_path):
            console.print(f"[bold red]Error: Repository not found at {self.repo_path}[/bold red]")
            return None
        
        # Get cluster information from config
        config = self.config
        cluster_name = config.get('cluster.name')
        network_prefix = config.get('cluster.network_prefix')
        control_plane_vip = config.get('cluster.control_plane_vip')
        
        if not all([cluster_name, network_prefix, control_plane_vip]):
            console.print("[bold yellow]Warning: Incomplete cluster information in config.[/bold yellow]")
            
            # Try to get information from infrastructure files
            try:
                # Check for talos configurations
                talos_dir = os.path.join(self.repo_path, "infrastructure", "talos", "controlplane")
                if os.path.exists(talos_dir):
                    # Get node information from file names
                    nodes = []
                    for file_name in os.listdir(talos_dir):
                        if file_name.endswith(".yaml"):
                            node_name = file_name.replace(".yaml", "")
                            
                            # Try to extract IP from file
                            with open(os.path.join(talos_dir, file_name), 'r') as f:
                                content = f.read()
                                # This is a simplistic approach, would need more robust parsing
                                ip_match = re.search(r'# Node: \w+ \((\d+\.\d+\.\d+\.\d+)\)', content)
                                ip = ip_match.group(1) if ip_match else "unknown"
                            
                            # Determine type and hardware
                            if "cp" in node_name:
                                node_type = "controlplane"
                            else:
                                node_type = "worker"
                            
                            if "cp1" in node_name:
                                hardware = "ryzen"
                            elif "cp2" in node_name:
                                hardware = "intel"
                            elif "cp3" in node_name:
                                hardware = "mac-mini"
                            else:
                                hardware = "unknown"
                            
                            nodes.append({
                                'name': node_name,
                                'ip': ip,
                                'type': node_type,
                                'hardware': hardware
                            })
                    
                    if nodes:
                        # Extract network prefix from first IP
                        if nodes[0]['ip'] != "unknown":
                            network_prefix = '.'.join(nodes[0]['ip'].split('.')[:3])
                        
                        # Use default VIP if not found
                        if not control_plane_vip:
                            control_plane_vip = f"{network_prefix}.100"
                        
                        # Use default name if not found
                        if not cluster_name:
                            cluster_name = "homelab"
                        
                        return {
                            'name': cluster_name,
                            'network_prefix': network_prefix,
                            'control_plane_vip': control_plane_vip,
                            'nodes': nodes
                        }
            except Exception as e:
                console.print(f"[bold red]Error extracting cluster information: {e}[/bold red]")
            
            console.print("[bold red]Error: Could not determine cluster information.[/bold red]")
            return None
        
        # Try to get node information
        nodes = []
        
        # Check if we can get node information from talosctl
        returncode, stdout, stderr = run_command(
            "talosctl get nodes -o yaml",
            cwd=self.repo_path
        )
        
        if returncode == 0:
            try:
                nodes_data = yaml.safe_load(stdout)
                for node in nodes_data:
                    nodes.append({
                        'name': node['metadata']['hostname'],
                        'ip': node['spec']['addresses'][0]['address'],
                        'type': 'controlplane' if 'controlplane' in node['metadata']['labels'] else 'worker',
                        'hardware': node['metadata']['labels'].get('hardware', 'unknown')
                    })
            except Exception:
                # Fall back to default node structure
                nodes = [
                    {
                        'name': 'talos-cp1',
                        'ip': f"{network_prefix}.101",
                        'type': 'controlplane',
                        'hardware': 'ryzen'
                    },
                    {
                        'name': 'talos-cp2',
                        'ip': f"{network_prefix}.102",
                        'type': 'controlplane',
                        'hardware': 'intel'
                    },
                    {
                        'name': 'talos-cp3',
                        'ip': f"{network_prefix}.103",
                        'type': 'controlplane',
                        'hardware': 'mac-mini'
                    }
                ]
        else:
            # Fall back to default node structure
            nodes = [
                {
                    'name': 'talos-cp1',
                    'ip': f"{network_prefix}.101",
                    'type': 'controlplane',
                    'hardware': 'ryzen'
                },
                {
                    'name': 'talos-cp2',
                    'ip': f"{network_prefix}.102",
                    'type': 'controlplane',
                    'hardware': 'intel'
                },
                {
                    'name': 'talos-cp3',
                    'ip': f"{network_prefix}.103",
                    'type': 'controlplane',
                    'hardware': 'mac-mini'
                }
            ]
        
        return {
            'name': cluster_name,
            'network_prefix': network_prefix,
            'control_plane_vip': control_plane_vip,
            'nodes': nodes
        }
    
    def _update_talos_configs(self, cluster_info: Dict[str, Any], k8s_version: str, talos_version: str) -> bool:
        """Update Talos configurations for upgrade.
        
        Args:
            cluster_info: Cluster information.
            k8s_version: Kubernetes version to upgrade to.
            talos_version: Talos version to upgrade to.
            
        Returns:
            True if successful, False otherwise.
        """
        # Build command with versions if provided
        cmd = os.path.join(self.repo_path, "bootstrap", "talos", "gen-config.sh")
        
        if k8s_version:
            cmd += f" --kubernetes-version {k8s_version}"
        
        if talos_version:
            cmd += f" --talos-version {talos_version}"
        
        # Run the command
        returncode, stdout, stderr = run_command(
            cmd,
            cwd=os.path.join(self.repo_path, "bootstrap", "talos")
        )
        
        if returncode != 0:
            console.print(f"[bold red]Error updating Talos configurations: {stderr}[/bold red]")
            return False
        
        return True
    
    def _wait_for_upgrade(self, cluster_info: Dict[str, Any]) -> bool:
        """Wait for cluster upgrade to complete.
        
        Args:
            cluster_info: Cluster information.
            
        Returns:
            True if successful, False otherwise.
        """
        node_ips = ",".join([node['ip'] for node in cluster_info['nodes']])
        
        returncode, stdout, stderr = run_command(
            f"talosctl health --nodes {node_ips} --wait-timeout 30m",
            cwd=self.repo_path
        )
        
        if returncode != 0:
            console.print(f"[bold red]Error waiting for upgrade to complete: {stderr}[/bold red]")
            return False
        
        return True
    
    def _reset_nodes(self, cluster_info: Dict[str, Any]) -> bool:
        """Reset Talos nodes.
        
        Args:
            cluster_info: Cluster information.
            
        Returns:
            True if successful, False otherwise.
        """
        for node in cluster_info['nodes']:
            console.print(f"Resetting node {node['name']} ({node['ip']})...")
            
            returncode, stdout, stderr = run_command(
                f"talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --system-labels-to-wipe EPHEMERAL --nodes {node['ip']}",
                cwd=self.repo_path
            )
            
            if returncode != 0:
                console.print(f"[bold yellow]Warning: Error resetting node {node['name']}: {stderr}[/bold yellow]")
                
                # Continue with other nodes even if one fails
                continue
        
        return True
    
    def _cleanup_local_files(self, cluster_info: Dict[str, Any]) -> bool:
        """Clean up local files after cluster deletion.
        
        Args:
            cluster_info: Cluster information.
            
        Returns:
            True if successful, False otherwise.
        """
        # Remove kubeconfig
        kubeconfig_path = os.path.join(self.repo_path, "kubeconfig")
        if os.path.exists(kubeconfig_path):
            try:
                os.remove(kubeconfig_path)
            except Exception as e:
                console.print(f"[bold yellow]Warning: Error removing kubeconfig: {e}[/bold yellow]")
        
        return True
