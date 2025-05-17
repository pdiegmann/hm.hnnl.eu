"""
Service management module for the hm-cli tool.
Handles service addition, listing, and removal.
"""

import os
import sys
import time
from typing import Dict, Any, List, Optional
from pathlib import Path

import yaml
import questionary
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from hm_cli.core import logger, console, ConfigManager, run_command, get_repo_path


class ServiceManager:
    """Manages Kubernetes service operations."""
    
    def __init__(self, repo_path: Optional[str] = None):
        """Initialize the service manager.
        
        Args:
            repo_path: Path to the repository. If None, uses the configured path.
        """
        self.config = ConfigManager()
        self.repo_path = repo_path or get_repo_path()
        
    def add(self) -> bool:
        """Add a new service to the cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Adding a new service to the cluster", title="Service Addition"))
        
        # Collect service information
        service_info = self._collect_service_info()
        if not service_info:
            return False
        
        # Create service directory structure
        if not self._create_service_structure(service_info):
            return False
        
        # Generate service manifests
        if not self._generate_service_manifests(service_info):
            return False
        
        console.print("[bold green]Service added successfully![/bold green]")
        console.print(f"[blue]Service files created at {os.path.join(self.repo_path, 'cluster', 'apps', service_info['name'])}[/blue]")
        console.print("[yellow]Remember to edit the generated files to add your specific service configuration.[/yellow]")
        
        # Ask if user wants to commit changes
        if questionary.confirm("Do you want to commit these changes to Git?").ask():
            from hm_cli.gitops import GitOpsManager
            gitops = GitOpsManager(self.repo_path)
            gitops.commit(f"Add service: {service_info['name']}")
        
        return True
    
    def list(self) -> bool:
        """List all services in the cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Listing all services in the cluster", title="Service List"))
        
        # Get services from the repository
        services = self._get_services()
        
        if not services:
            console.print("[yellow]No services found in the cluster.[/yellow]")
            return True
        
        # Create a table to display services
        table = Table(title="Cluster Services")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Namespace", style="blue")
        table.add_column("Path", style="dim")
        
        for service in services:
            table.add_row(
                service['name'],
                service['type'],
                service['namespace'],
                service['path']
            )
        
        console.print(table)
        return True
    
    def remove(self) -> bool:
        """Remove a service from the cluster.
        
        Returns:
            True if successful, False otherwise.
        """
        console.print(Panel.fit("Removing a service from the cluster", title="Service Removal"))
        
        # Get services from the repository
        services = self._get_services()
        
        if not services:
            console.print("[yellow]No services found in the cluster.[/yellow]")
            return False
        
        # Let user select a service to remove
        service_names = [service['name'] for service in services]
        service_name = questionary.select(
            "Select a service to remove:",
            choices=service_names
        ).ask()
        
        if not service_name:
            console.print("[yellow]Service removal cancelled.[/yellow]")
            return False
        
        # Find the selected service
        selected_service = next((s for s in services if s['name'] == service_name), None)
        if not selected_service:
            console.print(f"[bold red]Error: Service {service_name} not found.[/bold red]")
            return False
        
        # Confirm removal
        if not questionary.confirm(f"Are you sure you want to remove the service '{service_name}'?").ask():
            console.print("[yellow]Service removal cancelled.[/yellow]")
            return False
        
        # Remove the service
        if not self._remove_service(selected_service):
            return False
        
        console.print(f"[bold green]Service '{service_name}' removed successfully![/bold green]")
        
        # Ask if user wants to commit changes
        if questionary.confirm("Do you want to commit these changes to Git?").ask():
            from hm_cli.gitops import GitOpsManager
            gitops = GitOpsManager(self.repo_path)
            gitops.commit(f"Remove service: {service_name}")
        
        return True
    
    def _collect_service_info(self) -> Dict[str, Any]:
        """Collect information needed to add a service.
        
        Returns:
            Dict containing service information.
        """
        # Get service name
        service_name = questionary.text(
            "Service name:",
            validate=lambda text: len(text) > 0 and text.isalnum() or "-" in text
        ).ask()
        
        # Get service type
        service_type = questionary.select(
            "Service type:",
            choices=[
                "web-app",
                "database",
                "monitoring",
                "storage",
                "networking",
                "other"
            ]
        ).ask()
        
        # Get namespace
        namespace = questionary.text(
            "Namespace:",
            default=service_name
        ).ask()
        
        # Get service visibility
        visibility = questionary.select(
            "Service visibility:",
            choices=[
                "both (local and external)",
                "local-only",
                "external-only"
            ]
        ).ask()
        
        # Map visibility to target type
        if visibility == "both (local and external)":
            target_type = "both"
        elif visibility == "local-only":
            target_type = "internal"
        else:
            target_type = "external"
        
        # Get service port
        port = questionary.text(
            "Service port:",
            default="80",
            validate=lambda text: text.isdigit() and 1 <= int(text) <= 65535
        ).ask()
        
        # Get service description
        description = questionary.text(
            "Service description:",
            default=f"{service_name} service"
        ).ask()
        
        # Return collected information
        return {
            'name': service_name,
            'type': service_type,
            'namespace': namespace,
            'visibility': visibility,
            'target_type': target_type,
            'port': int(port),
            'description': description
        }
    
    def _create_service_structure(self, service_info: Dict[str, Any]) -> bool:
        """Create directory structure for a new service.
        
        Args:
            service_info: Service information.
            
        Returns:
            True if successful, False otherwise.
        """
        # Create service directories
        service_dir = os.path.join(self.repo_path, "cluster", "apps", service_info['name'])
        
        try:
            os.makedirs(service_dir, exist_ok=True)
            
            # Create subdirectories if needed
            os.makedirs(os.path.join(service_dir, "base"), exist_ok=True)
            os.makedirs(os.path.join(service_dir, "overlays"), exist_ok=True)
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error creating service directory structure: {e}[/bold red]")
            return False
    
    def _generate_service_manifests(self, service_info: Dict[str, Any]) -> bool:
        """Generate Kubernetes manifests for a new service.
        
        Args:
            service_info: Service information.
            
        Returns:
            True if successful, False otherwise.
        """
        service_dir = os.path.join(self.repo_path, "cluster", "apps", service_info['name'])
        
        try:
            # Create namespace.yaml
            namespace_yaml = f"""apiVersion: v1
kind: Namespace
metadata:
  name: {service_info['namespace']}
"""
            
            with open(os.path.join(service_dir, "namespace.yaml"), 'w') as f:
                f.write(namespace_yaml)
            
            # Create kustomization.yaml
            kustomization_yaml = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - base
"""
            
            with open(os.path.join(service_dir, "kustomization.yaml"), 'w') as f:
                f.write(kustomization_yaml)
            
            # Create base/kustomization.yaml
            base_kustomization_yaml = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - deployment.yaml
  - service.yaml
"""
            
            with open(os.path.join(service_dir, "base", "kustomization.yaml"), 'w') as f:
                f.write(base_kustomization_yaml)
            
            # Create base/deployment.yaml
            deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service_info['name']}
  namespace: {service_info['namespace']}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {service_info['name']}
  template:
    metadata:
      labels:
        app: {service_info['name']}
    spec:
      containers:
      - name: {service_info['name']}
        # TODO: Replace with your container image
        image: nginx:latest
        ports:
        - containerPort: {service_info['port']}
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 128Mi
"""
            
            with open(os.path.join(service_dir, "base", "deployment.yaml"), 'w') as f:
                f.write(deployment_yaml)
            
            # Create base/service.yaml
            service_yaml = f"""apiVersion: v1
kind: Service
metadata:
  name: {service_info['name']}
  namespace: {service_info['namespace']}
  annotations:
    external-dns.alpha.kubernetes.io/target-type: "{service_info['target_type']}"
"""
            
            # Add appropriate hostnames based on visibility
            if service_info['target_type'] == "both":
                service_yaml += f"""    external-dns.alpha.kubernetes.io/hostname: {service_info['name']}.ext.hm.hnnl.eu, {service_info['name']}.local.hm.hnnl.eu
"""
            elif service_info['target_type'] == "internal":
                service_yaml += f"""    external-dns.alpha.kubernetes.io/hostname: {service_info['name']}.local.hm.hnnl.eu
"""
            else:  # external
                service_yaml += f"""    external-dns.alpha.kubernetes.io/hostname: {service_info['name']}.ext.hm.hnnl.eu
"""
            
            service_yaml += f"""spec:
  type: LoadBalancer
  ports:
  - port: {service_info['port']}
    targetPort: {service_info['port']}
    protocol: TCP
  selector:
    app: {service_info['name']}
"""
            
            with open(os.path.join(service_dir, "base", "service.yaml"), 'w') as f:
                f.write(service_yaml)
            
            # Create README.md
            readme_md = f"""# {service_info['name']}

{service_info['description']}

## Overview

This is a {service_info['type']} service running in the {service_info['namespace']} namespace.

## Access

"""
            
            if service_info['target_type'] == "both" or service_info['target_type'] == "internal":
                readme_md += f"- Local access: http://{service_info['name']}.local.hm.hnnl.eu:{service_info['port']}\n"
            
            if service_info['target_type'] == "both" or service_info['target_type'] == "external":
                readme_md += f"- External access: http://{service_info['name']}.ext.hm.hnnl.eu:{service_info['port']}\n"
            
            readme_md += """
## Configuration

Edit the files in the `base` directory to configure the service.

## Customization

Add environment-specific customizations in the `overlays` directory.
"""
            
            with open(os.path.join(service_dir, "README.md"), 'w') as f:
                f.write(readme_md)
            
            return True
        except Exception as e:
            console.print(f"[bold red]Error generating service manifests: {e}[/bold red]")
            return False
    
    def _get_services(self) -> List[Dict[str, Any]]:
        """Get all services from the repository.
        
        Returns:
            List of dictionaries containing service information.
        """
        services = []
        apps_dir = os.path.join(self.repo_path, "cluster", "apps")
        
        if not os.path.exists(apps_dir):
            return services
        
        for item in os.listdir(apps_dir):
            item_path = os.path.join(apps_dir, item)
            
            # Skip non-directories and hidden directories
            if not os.path.isdir(item_path) or item.startswith('.'):
                continue
            
            # Check if this looks like a service directory
            if os.path.exists(os.path.join(item_path, "kustomization.yaml")):
                # Try to determine service type
                service_type = "unknown"
                readme_path = os.path.join(item_path, "README.md")
                
                if os.path.exists(readme_path):
                    try:
                        with open(readme_path, 'r') as f:
                            content = f.read()
                            if "web-app" in content.lower():
                                service_type = "web-app"
                            elif "database" in content.lower():
                                service_type = "database"
                            elif "monitoring" in content.lower():
                                service_type = "monitoring"
                            elif "storage" in content.lower():
                                service_type = "storage"
                            elif "networking" in content.lower():
                                service_type = "networking"
                    except Exception:
                        pass
                
                # Try to determine namespace
                namespace = item  # Default to service name
                namespace_path = os.path.join(item_path, "namespace.yaml")
                
                if os.path.exists(namespace_path):
                    try:
                        with open(namespace_path, 'r') as f:
                            namespace_yaml = yaml.safe_load(f)
                            if namespace_yaml and 'metadata' in namespace_yaml and 'name' in namespace_yaml['metadata']:
                                namespace = namespace_yaml['metadata']['name']
                    except Exception:
                        pass
                
                services.append({
                    'name': item,
                    'type': service_type,
                    'namespace': namespace,
                    'path': os.path.relpath(item_path, self.repo_path)
                })
        
        return services
    
    def _remove_service(self, service: Dict[str, Any]) -> bool:
        """Remove a service from the repository.
        
        Args:
            service: Service information.
            
        Returns:
            True if successful, False otherwise.
        """
        service_path = os.path.join(self.repo_path, service['path'])
        
        try:
            import shutil
            shutil.rmtree(service_path)
            return True
        except Exception as e:
            console.print(f"[bold red]Error removing service: {e}[/bold red]")
            return False
