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
from rich.table import Table
from rich.text import Text

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
        """Create a new Kubernetes cluster interactively, similar to bootstrap.sh."""
        console.print(Panel.fit("🚀 Starting Homelab Cluster Creation Process 🚀", title="[bold cyan]Cluster Creation[/bold cyan]", subtitle="Interactive Setup"))

        # 0. Collect cluster information
        console.print("\n[bold blue]Step 0: Collecting Cluster Information[/bold blue]")
        cluster_info = self._collect_cluster_info()
        if not cluster_info:
            console.print("[bold red]Cluster information collection cancelled or failed. Aborting.[/bold red]")
            return False
        console.print("[green]Cluster information collected successfully.[/green]")

        # 1. Generate Talos configurations
        console.print("\n[bold blue]Step 1: Talos Configurations[/bold blue]")
        generate_talos_configs = True
        if os.path.exists(os.path.join(self.repo_path, "infrastructure", "talos", "controlplane", f"{cluster_info['nodes'][0]['name']}.yaml")):
            if not questionary.confirm("Talos configurations might already exist. Do you want to re-generate them?", default=False).ask():
                generate_talos_configs = False
                console.print("[yellow]Skipping Talos configuration generation.[/yellow]")
        
        if generate_talos_configs:
            if not questionary.confirm("Proceed with generating Talos configurations?", default=True).ask():
                console.print("[yellow]Talos configuration generation skipped by user. Aborting.[/yellow]")
                return False
            if not self._generate_talos_configs(cluster_info):
                console.print("[bold red]Failed to generate Talos configurations. Aborting.[/bold red]")
                return False
            console.print("[green]Talos configurations generated successfully.[/green]")

        # 2. Apply Talos configurations to nodes
        console.print("\n[bold blue]Step 2: Applying Talos Configurations to Nodes[/bold blue]")
        if not questionary.confirm("Continue with applying Talos configurations to nodes?", default=True).ask():
            console.print("[yellow]Applying Talos configurations skipped by user. Aborting.[/yellow]")
            return False
        if not self._apply_talos_configs(cluster_info):
            console.print("[bold red]Failed to apply Talos configurations to nodes. Aborting.[/bold red]")
            return False
        console.print("[green]Talos configurations applied to nodes successfully.[/green]")

        # 3. Bootstrap the cluster
        console.print("\n[bold blue]Step 3: Bootstrapping the Cluster[/bold blue]")
        if not questionary.confirm("Continue with bootstrapping the cluster?", default=True).ask():
            console.print("[yellow]Cluster bootstrapping skipped by user. Aborting.[/yellow]")
            return False
        if not self._bootstrap_cluster(cluster_info):
            console.print("[bold red]Failed to bootstrap the cluster. Aborting.[/bold red]")
            return False
        console.print("[green]Cluster bootstrapped successfully.[/green]")
        
        console.print("\n[bold blue]Step 3a: Testing Kubernetes Connection[/bold blue]")
        if not self._test_kube_connection(cluster_info):
            console.print("[bold red]Failed to connect to the Kubernetes cluster after bootstrap. Please check manually.[/bold red]")
            # Not aborting here, as kubeconfig might be fine but nodes not ready yet.
        else:
            console.print("[green]Successfully connected to the Kubernetes cluster.[/green]")

        # 4. Setup Flux CD
        console.print("\n[bold blue]Step 4: Setting up Flux CD[/bold blue]")
        if not questionary.confirm("Continue with creating initial Flux directory structure and files?", default=True).ask():
            console.print("[yellow]Flux directory creation skipped by user.[/yellow]")
        elif not self._create_flux_directories_and_files(cluster_info):
            console.print("[bold red]Failed to create Flux directories/files. Flux setup might be incomplete.[/bold red]")
        else:
            console.print("[green]Flux directories and kustomization files created successfully.[/green]")

        if not questionary.confirm("Continue with bootstrapping Flux (running `flux bootstrap github`)?", default=True).ask():
            console.print("[yellow]Flux bootstrapping skipped by user.[/yellow]")
        elif not self._setup_flux(cluster_info): # _setup_flux already handles KUBECONFIG
            console.print("[bold red]Failed to set up Flux. Aborting further GitOps setup.[/bold red]")
            # Allow to continue to core components if user wants
        else:
            console.print("[green]Flux bootstrapped successfully.[/green]")
            
        # 5. Setup core components
        console.print("\n[bold blue]Step 5: Setting up Core Component Manifest Stubs[/bold blue]")
        if not questionary.confirm("Continue with creating directory structure for core components?", default=True).ask():
            console.print("[yellow]Core component directory creation skipped by user.[/yellow]")
        elif not self._create_core_component_directories_and_files(cluster_info):
            console.print("[bold red]Failed to create core component directories/files.[/bold red]")
        else:
            console.print("[green]Core component directory structure created successfully.[/green]")
            console.print("[yellow]You'll need to add actual manifests for each component in 'cluster/core/...'[/yellow]")

        console.print(Panel(
            Text.from_markup(
                "[bold green]🎉 Bootstrap process completed! 🎉[/bold green]\n\n"
                "[bold blue]Next steps:[/bold blue]\n"
                "1. Commit and push the changes in this repository to GitHub.\n"
                "2. Flux will start reconciling the repository and deploying components.\n"
                "3. Add your applications to the 'cluster/apps' directory and update kustomizations.\n\n"
                f"[yellow]See documentation (e.g., {os.path.join(self.repo_path, 'docs-src/docs/guide/getting-started.md')}) for detailed instructions.[/yellow]"
            ),
            title="[bold green]Completion Summary[/bold green]",
            expand=False
        ))
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
        console.print(Panel.fit("Kubernetes Cluster Status", title="[bold cyan]Cluster Status[/bold cyan]"))

        kubeconfig_path = os.path.join(self.repo_path, "kubeconfig")
        if not os.path.exists(kubeconfig_path):
            console.print("[bold red]Error: Kubeconfig not found. Cluster may not be initialized.[/bold red]")
            console.print(f"Expected kubeconfig at: {kubeconfig_path}")
            return False

        env = os.environ.copy()
        env["KUBECONFIG"] = kubeconfig_path

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True # Clears progress on exit
        ) as progress:
            # Total tasks: nodes, pods, flux (kustomizations+sources is one logical step for progress), storage, kube-vip, vip-ping, etcd
            num_tasks = 7
            task = progress.add_task("Fetching cluster status...", total=num_tasks)

            # 1. Node Status
            progress.update(task, description="Fetching node status...")
            self._check_node_status(env)
            progress.advance(task)

            # 2. Pod Status
            progress.update(task, description="Fetching pod status...")
            self._check_pod_status(env)
            progress.advance(task)

            # 3. Flux Status
            progress.update(task, description="Fetching Flux status...")
            self._check_flux_status(env)
            progress.advance(task)

            # 4. Storage Status (CubeFS & Generic)
            progress.update(task, description="Fetching storage status...")
            self._check_storage_status(env) # This will handle CubeFS and generic storage
            progress.advance(task)

            # 5. Kube-vip Status
            progress.update(task, description="Fetching kube-vip status...")
            self._check_kube_vip_status(env)
            progress.advance(task)
            
            # 6. Virtual IP Accessibility
            cluster_info = self._get_current_cluster_info()
            vip_to_check = "192.168.1.100" # Default from script
            if cluster_info and cluster_info.get('control_plane_vip'):
                vip_to_check = cluster_info['control_plane_vip']
            else:
                # Attempt to get VIP from kubeconfig if not in CLI config
                try:
                    with open(kubeconfig_path, 'r') as f_kc:
                        kc_data = yaml.safe_load(f_kc)
                        if kc_data and 'clusters' in kc_data and kc_data['clusters']:
                            server_url = kc_data['clusters'][0].get('cluster', {}).get('server', '')
                            if server_url:
                                # Extract IP from https://IP:PORT
                                vip_from_kc = server_url.split('//')[-1].split(':')[0]
                                # Validate if it's an IP before using
                                if all(c.isdigit() or c == '.' for c in vip_from_kc) and vip_from_kc.count('.') == 3: # Basic IP check
                                    vip_to_check = vip_from_kc
                                    console.print(f"[dim]Using VIP {vip_to_check} from kubeconfig for ping test.[/dim]")
                                else:
                                    console.print(f"[yellow]Could not parse valid IP from kubeconfig server URL ('{server_url}'). Using default {vip_to_check} for ping test.[/yellow]")
                except FileNotFoundError:
                     console.print(f"[yellow]Kubeconfig file not found at {kubeconfig_path} for VIP check. Using default {vip_to_check}.[/yellow]")
                except Exception as e:
                    console.print(f"[yellow]Could not read VIP from kubeconfig ({e}). Using default {vip_to_check} for ping test.[/yellow]")
                
                if vip_to_check == "192.168.1.100": # If still default after trying kubeconfig
                     console.print(f"[yellow]Control plane VIP not found in CLI config or kubeconfig. Using default {vip_to_check} for ping test.[/yellow]")


            progress.update(task, description=f"Checking Virtual IP ({vip_to_check}) accessibility...")
            self._check_vip_accessibility(vip_to_check)
            progress.advance(task)

            # 7. Etcd Health
            progress.update(task, description="Fetching etcd health...")
            self._check_etcd_health(env)
            progress.advance(task)

        console.print("\n[bold green]Cluster status check complete.[/bold green]")
        return True

    def _print_command_output_table(self, title: str, command_output: str, error_message: Optional[str] = None, success_message: Optional[str] = None):
        """Helper to print command output in a Rich table or as error/success message."""
        console.print(f"\n[bold blue]--- {title} ---[/bold blue]")

        if error_message:
            console.print(f"[yellow]{error_message}[/yellow]")
            return

        if success_message: # For simple success messages like ping
            console.print(f"[green]{success_message}[/green]")
            return

        if not command_output or not command_output.strip():
            console.print("[yellow]No resources found or command returned empty output.[/yellow]")
            return

        lines = command_output.strip().split('\n')
        if not lines: # Should be caught by previous check, but as a safeguard
            console.print("[yellow]No output to display.[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold magenta", show_lines=False, row_styles=["none", "dim"])
        
        headers = [header.strip() for header in lines[0].split(None)]
        
        processed_headers = []
        header_counts: Dict[str, int] = {}
        for header in headers:
            if header in header_counts:
                header_counts[header] += 1
                processed_headers.append(f"{header}({header_counts[header]})") # No space for uniqueness
            else:
                header_counts[header] = 0
                processed_headers.append(header)
        
        for header_text in processed_headers:
            table.add_column(header_text)

        for line_content in lines[1:]:
            # Split row by multiple spaces, up to number of headers minus one for the last column
            row_values = [val.strip() for val in line_content.split(None, len(processed_headers) - 1)]
            # Pad if necessary, ensuring we don't exceed the number of headers
            if len(row_values) < len(processed_headers):
                row_values.extend([""] * (len(processed_headers) - len(row_values)))
            elif len(row_values) > len(processed_headers): # Truncate if too many values (less likely with split(None, N-1))
                row_values = row_values[:len(processed_headers)]

            styled_row = []
            for val in row_values:
                val_lower = val.lower()
                # Prioritize critical failure states
                if "crashloopbackoff" in val_lower or "errimagepull" in val_lower or "imagepullbackoff" in val_lower or "failed" in val_lower or "error" in val_lower or "notready" in val_lower or val_lower == "false":
                    styled_row.append(f"[red]{val}[/red]")
                elif "running" in val_lower or "ready" in val_lower or "healthy" in val_lower or "bound" in val_lower or "available" in val_lower or val_lower == "true" or "active" in val_lower or "succeeded" in val_lower:
                    styled_row.append(f"[green]{val}[/green]")
                elif "pending" in val_lower or "unknown" in val_lower or "progressing" in val_lower or "terminating" in val_lower or "creating" in val_lower or "containercreating" in val_lower:
                    styled_row.append(f"[yellow]{val}[/yellow]")
                else:
                    styled_row.append(val)
            table.add_row(*styled_row)
        
        console.print(table)

    def _check_node_status(self, env: Dict[str, str]):
        returncode, stdout, stderr = run_command("kubectl get nodes -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode != 0:
            self._print_command_output_table("Node Status", "", error_message=f"Error: {stderr.strip()}")
        else:
            self._print_command_output_table("Node Status", stdout)

    def _check_pod_status(self, env: Dict[str, str]):
        returncode, stdout, stderr = run_command("kubectl get pods -A -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode != 0:
            self._print_command_output_table("Pod Status (All Namespaces)", "", error_message=f"Error: {stderr.strip()}")
        else:
            self._print_command_output_table("Pod Status (All Namespaces)", stdout)

    def _check_flux_status(self, env: Dict[str, str]):
        ret_ns, ns_check_out, err_ns = run_command("kubectl get ns flux-system --no-headers --output=name", cwd=self.repo_path, env=env, suppress_output=True)
        if ret_ns != 0 or not ns_check_out.strip():
            self._print_command_output_table("Flux Kustomizations", "", error_message="Flux (flux-system namespace) not found.")
            if err_ns and ret_ns !=0 : console.print(f"[dim red]Detail: {err_ns.strip()}[/dim red]")
            self._print_command_output_table("Flux Sources", "", error_message="Flux (flux-system namespace) not found, skipping sources.")
            return

        returncode_ks, stdout_ks, stderr_ks = run_command("kubectl get kustomizations -A -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode_ks != 0:
            self._print_command_output_table("Flux Kustomizations", "", error_message=f"Error: {stderr_ks.strip()}")
        else:
            self._print_command_output_table("Flux Kustomizations", stdout_ks)

        returncode_flux_sources, stdout_flux_sources, stderr_flux_sources = run_command("flux get sources all -A --server-side", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode_flux_sources != 0:
             self._print_command_output_table("Flux Sources (git, helm, etc.)", "", error_message=f"Error: {stderr_flux_sources.strip()}")
        else:
            self._print_command_output_table("Flux Sources (git, helm, etc.)", stdout_flux_sources)
            
    def _check_storage_status(self, env: Dict[str, str]):
        # Check for CubeFS first
        ret_ns_cubefs, ns_cubefs_out, err_ns_cubefs = run_command("kubectl get ns cubefs --no-headers --output=name", cwd=self.repo_path, env=env, suppress_output=True)
        if ret_ns_cubefs == 0 and ns_cubefs_out.strip():
            console.print(Text("\n--- CubeFS Specific Storage ---", style="bold blue")) # Changed from _print_command_output_table for section header
            returncode_pods, stdout_pods, stderr_pods = run_command("kubectl get pods -n cubefs -o wide", cwd=self.repo_path, env=env, suppress_output=True)
            if returncode_pods != 0:
                self._print_command_output_table("CubeFS Pods", "", error_message=f"Error: {stderr_pods.strip()}")
            else:
                self._print_command_output_table("CubeFS Pods", stdout_pods)
        else:
            # Use a simpler message if CubeFS namespace is not found, not an error table for "CubeFS Pods"
            console.print(f"\n[bold blue]--- CubeFS Pods ---[/bold blue]")
            console.print("[yellow]CubeFS (cubefs namespace) not found.[/yellow]")
            if err_ns_cubefs and ret_ns_cubefs !=0 : console.print(f"[dim red]Detail checking namespace: {err_ns_cubefs.strip()}[/dim red]")
        
        self._check_generic_storage(env)

    def _check_generic_storage(self, env: Dict[str, str]):
        console.print(Text("\n--- Generic Storage Components ---", style="bold blue")) # Changed from _print_command_output_table for section header
        returncode_sc, stdout_sc, stderr_sc = run_command("kubectl get sc -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode_sc != 0:
            self._print_command_output_table("Storage Classes", "", error_message=f"Error: {stderr_sc.strip()}")
        else:
            self._print_command_output_table("Storage Classes", stdout_sc)

        returncode_pv, stdout_pv, stderr_pv = run_command("kubectl get pv -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode_pv != 0:
            self._print_command_output_table("Persistent Volumes", "", error_message=f"Error: {stderr_pv.strip()}")
        else:
            self._print_command_output_table("Persistent Volumes", stdout_pv)
        
        returncode_pvc, stdout_pvc, stderr_pvc = run_command("kubectl get pvc -A -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode_pvc != 0:
            self._print_command_output_table("Persistent Volume Claims (All Namespaces)", "", error_message=f"Error: {stderr_pvc.strip()}")
        else:
            self._print_command_output_table("Persistent Volume Claims (All Namespaces)", stdout_pvc)

    def _check_kube_vip_status(self, env: Dict[str, str]):
        returncode, stdout, stderr = run_command("kubectl get pods -n kube-system -l name=kube-vip -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode != 0 or not stdout.strip() or (stdout.strip() and len(stdout.strip().split('\n')) <= 1):
            msg = f"Error: {stderr.strip()}" if returncode !=0 and stderr.strip() else "Kube-vip not installed or no pods found."
            self._print_command_output_table("Kube-vip Pods", "", error_message=msg)
        else:
            self._print_command_output_table("Kube-vip Pods", stdout)

    def _check_vip_accessibility(self, vip_address: str):
        title = f"Virtual IP ({vip_address}) Accessibility"
        if sys.platform == "win32":
            ping_command = f"ping -n 1 -w 1000 {vip_address}"
        else:
            ping_command = f"ping -c 1 -W 1 {vip_address}"

        returncode, stdout, stderr = run_command(ping_command, cwd=self.repo_path, suppress_output=True)
        
        if returncode == 0:
            self._print_command_output_table(title, "", success_message="Responded successfully.")
        else:
            err_detail = stderr.strip() or stdout.strip()
            self._print_command_output_table(title, "", error_message=f"NOT responding. Detail: {err_detail if err_detail else 'No output from ping command.'}")

    def _check_etcd_health(self, env: Dict[str, str]):
        returncode_pods, stdout_pods, stderr_pods = run_command("kubectl get pods -n kube-system -l component=etcd -o wide", cwd=self.repo_path, env=env, suppress_output=True)
        if returncode_pods != 0 or not stdout_pods.strip() or (stdout_pods.strip() and len(stdout_pods.strip().split('\n')) <=1 ):
            msg = f"Error: {stderr_pods.strip()}" if returncode_pods !=0 and stderr_pods.strip() else "No etcd pods found."
            self._print_command_output_table("etcd Pods", "", error_message=msg)
            self._print_command_output_table("etcd Cluster Health", "", error_message="Skipped: No etcd pods or error fetching them.")
            return
        
        self._print_command_output_table("etcd Pods", stdout_pods)
        
        jsonpath_expr = "\"{.items[?(@.status.phase=='Running')].metadata.name} {.items[?(@.status.phase!='Running')].metadata.name}\"" # Get running first, then others
        ret_etcd_name, out_etcd_name, err_etcd_name = run_command(
            f"kubectl get pods -n kube-system -l component=etcd -o jsonpath={jsonpath_expr} --ignore-not-found",
            cwd=self.repo_path, env=env, suppress_output=True
        )
        
        # Process output: it might be 'pod1 pod2' or just 'pod1' or empty. We want the first one.
        etcd_pod_names = out_etcd_name.strip().replace("'", "").split()
        etcd_pod_name = etcd_pod_names[0] if etcd_pod_names else None

        if ret_etcd_name == 0 and etcd_pod_name:
            health_title = "etcd Cluster Health" # Define title once
            console.print(f"\n[blue]Checking {health_title} via pod: {etcd_pod_name}...[/blue]")
            
            # Attempt with -w table first
            etcd_health_cmd_table = f"kubectl -n kube-system exec {etcd_pod_name} -- etcdctl endpoint health --cluster -w table"
            returncode_health, stdout_health, stderr_health = run_command(etcd_health_cmd_table, cwd=self.repo_path, env=env, suppress_output=True)
            
            if returncode_health == 0 and stdout_health.strip(): # Success with table
                console.print(f"\n[bold blue]--- {health_title} ---[/bold blue]")
                console.print(stdout_health)
                if stderr_health.strip(): console.print(f"[dim yellow]stderr (table): {stderr_health.strip()}[/dim yellow]")
            else: # Table failed or empty output, try raw
                if returncode_health != 0 : # Log why table might have failed before trying raw
                    console.print(f"[dim yellow]etcdctl table output failed (code {returncode_health}): {stderr_health.strip()}. Trying raw output...[/dim yellow]")
                else: # Table succeeded but empty output
                     console.print(f"[dim yellow]etcdctl table output was empty. Trying raw output...[/dim yellow]")

                etcd_health_cmd_raw = f"kubectl -n kube-system exec {etcd_pod_name} -- etcdctl endpoint health --cluster"
                returncode_health_raw, stdout_health_raw, stderr_health_raw = run_command(etcd_health_cmd_raw, cwd=self.repo_path, env=env, suppress_output=True)

                if returncode_health_raw == 0:
                    console.print(f"\n[bold blue]--- {health_title} (Raw Output) ---[/bold blue]")
                    if stdout_health_raw.strip(): console.print(stdout_health_raw)
                    else: console.print("[yellow]No health information returned (raw).[/yellow]")
                    if stderr_health_raw.strip(): console.print(f"[dim yellow]stderr (raw): {stderr_health_raw.strip()}[/dim yellow]")
                else: # Both failed
                    self._print_command_output_table(health_title, "", error_message=f"Error (raw): {stderr_health_raw.strip()}")

        elif err_etcd_name.strip() and ret_etcd_name != 0 :
            self._print_command_output_table("etcd Cluster Health", "", error_message=f"Could not query etcd pod names: {err_etcd_name.strip()}")
        else:
            self._print_command_output_table("etcd Cluster Health", "", error_message="No etcd pod name found to check cluster health.")

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
        default_talos_version = config.get('cluster.talos_version', 'v1.7.0') # Example default
        default_k8s_version = config.get('cluster.kubernetes_version', 'v1.29.0') # Example default
        
        console.print("Please provide the following details for your new cluster:")
        
        questions = [
            {
                'type': 'text',
                'name': 'cluster_name',
                'message': 'Cluster name:',
                'default': default_name,
                'qmark': "ℹ️"
            },
            {
                'type': 'text',
                'name': 'network_prefix',
                'message': 'Network prefix (e.g., 192.168.1):',
                'default': default_network_prefix,
                'validate': lambda text: len(text.split('.')) == 3 or "Must be three octets (e.g., 192.168.1)",
                'qmark': "ℹ️"
            },
            {
                'type': 'text',
                'name': 'control_plane_vip',
                'message': 'Control plane VIP:',
                'default': default_control_plane_vip,
                'validate': validate_ip_address,
                'qmark': "ℹ️"
            },
            {
                'type': 'text',
                'name': 'talos_version',
                'message': 'Talos version (e.g., v1.7.0):',
                'default': default_talos_version,
                'qmark': "ℹ️"
            },
            {
                'type': 'text',
                'name': 'kubernetes_version',
                'message': 'Kubernetes version (e.g., v1.29.0):',
                'default': default_k8s_version,
                'qmark': "ℹ️"
            },
        ]
        
        answers = questionary.unsafe_prompt(questions)
        if not answers: return {} # User cancelled

        cluster_name = answers["cluster_name"]
        network_prefix = answers["network_prefix"]
        control_plane_vip = answers["control_plane_vip"]
        talos_version = answers["talos_version"]
        kubernetes_version = answers["kubernetes_version"]

        console.print("\nDefine your control plane nodes (at least 3 recommended for HA):")
        nodes = []
        node_names_hw = [("talos-cp1", "ryzen"), ("talos-cp2", "intel"), ("talos-cp3", "mac-mini")] # Predefined for typical setup

        for i in range(3): # Assuming 3 control plane nodes as per bootstrap.sh
            node_name_default, hw_default = node_names_hw[i]
            console.print(f"\n--- Control Plane Node {i+1} ---")
            node_ip = questionary.text(
                f"IP address for {node_name_default} ({hw_default}):",
                validate=validate_ip_address,
                qmark="ℹ️"
            ).ask()
            if node_ip is None: return {} # User cancelled
            
            nodes.append({
                'name': node_name_default, # Using predefined names for consistency
                'ip': node_ip,
                'type': 'controlplane',
                'hardware': hw_default
            })
        
        # Save to config
        config.set('cluster.name', cluster_name)
        config.set('cluster.network_prefix', network_prefix)
        config.set('cluster.control_plane_vip', control_plane_vip)
        config.set('cluster.talos_version', talos_version)
        config.set('cluster.kubernetes_version', kubernetes_version)
        # Node IPs are not typically saved in general config this way, but rather used directly.
        # The bootstrap script also prompts for them each time.
        
        # Return collected information
        return {
            'name': cluster_name,
            'network_prefix': network_prefix,
            'control_plane_vip': control_plane_vip,
            'talos_version': talos_version,
            'kubernetes_version': kubernetes_version,
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
            
            # Determine the correct project root.
            # Assumes this file (cluster.py) is located at <project_root>/cli/hm_cli/cluster.py
            try:
                current_file_dir = os.path.dirname(os.path.abspath(__file__))
                project_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
            except NameError:
                logger.warning("__file__ not defined when trying to determine project root for Talos scripts. Falling back to self.repo_path.")
                project_root = self.repo_path # Fallback to original behavior if __file__ is not available

            logger.info(f"Using project root for Talos gen-config.sh: {project_root}. (Original self.repo_path: {self.repo_path})")

            # Define path to the gen-config.sh script and its working directory
            script_dir_relative_to_root = os.path.join("bootstrap", "talos")
            script_name = "gen-config.sh"
            
            script_path = os.path.join(project_root, script_dir_relative_to_root, script_name)
            script_execution_cwd = os.path.join(project_root, script_dir_relative_to_root)
            
            if not os.path.exists(script_path):
                progress.stop()
                console.print(f"[bold red]Error: gen-config.sh script not found at corrected path: {script_path}[/bold red]")
                return False
            
            # Make script executable
            try:
                os.chmod(script_path, 0o755)
            except OSError as e:
                progress.stop()
                console.print(f"[bold red]Error setting execute permission for {script_path}: {e}[/bold red]")
                return False
            
            # Run the script
            env_vars = os.environ.copy()
            env_vars['TALOS_VERSION'] = cluster_info.get('talos_version', 'v1.7.0') # Default if somehow not set
            env_vars['KUBERNETES_VERSION'] = cluster_info.get('kubernetes_version', 'v1.29.0') # Default
            env_vars['CLUSTER_NAME'] = cluster_info.get('name')
            env_vars['CONTROL_PLANE_VIP'] = cluster_info.get('control_plane_vip')
            # The gen-config.sh script will need to be aware of these IPs.
            # Assuming gen-config.sh might read these from env or specific files it generates based on env.
            # For now, passing main cluster params. Node IPs are usually embedded in generated files.
            # If gen-config.sh takes node IPs as env vars, they should be added here.
            # Example: env_vars['CP1_IP'] = cluster_info['nodes'][0]['ip'] etc.
            # This depends on gen-config.sh implementation.

            console.print(f"[dim]Running {script_path} in '{script_execution_cwd}' with TALOS_VERSION={env_vars['TALOS_VERSION']}, KUBERNETES_VERSION={env_vars['KUBERNETES_VERSION']}[/dim]")

            returncode, stdout, stderr = run_command(
                script_path, # script_path is now correctly determined
                cwd=script_execution_cwd, # Use the corrected CWD
                env=env_vars
            )
            
            if stdout:
                console.print(f"[dim]gen-config.sh stdout:\n{stdout}[/dim]")
            if stderr and returncode !=0: # only print stderr if it's an error
                 console.print(f"[yellow]gen-config.sh stderr:\n{stderr}[/yellow]")


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
        # Determine the correct project root, similar to _generate_talos_configs
        try:
            current_file_dir = os.path.dirname(os.path.abspath(__file__))
            # Assuming this file is at <project_root>/cli/hm_cli/cluster.py
            project_root = os.path.abspath(os.path.join(current_file_dir, "..", ".."))
        except NameError: # pragma: no cover
            logger.warning("__file__ not defined when trying to determine project root for applying Talos configs. Falling back to self.repo_path.")
            project_root = self.repo_path # Fallback

        logger.info(f"Using project root for applying Talos configs: {project_root}. (Original self.repo_path: {self.repo_path})")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Applying Talos configurations to nodes...", total=len(cluster_info['nodes']))
            
            for node in cluster_info['nodes']:
                progress.update(task, description=f"Applying configuration to {node['name']} ({node['ip']})...")
                
                # Get the configuration file path using the determined project_root
                config_file_relative_path = os.path.join(
                    "infrastructure",
                    "talos",
                    "controlplane",
                    f"{node['name']}.yaml"
                )
                config_file = os.path.join(project_root, config_file_relative_path)
                
                logger.debug(f"Attempting to apply Talos config from: {config_file}")

                if not os.path.exists(config_file):
                    progress.stop()
                    console.print(f"[bold red]Error: Configuration file not found at {config_file}[/bold red]")
                    # Log details about paths for debugging
                    console.print(f"[dim]Project root used: {project_root}[/dim]")
                    console.print(f"[dim]self.repo_path was: {self.repo_path}[/dim]")
                    console.print(f"[dim]Original path attempted (using self.repo_path): {os.path.join(self.repo_path, config_file_relative_path)}[/dim]")
                    return False
                
                # Apply the configuration
                # The cwd for talosctl should ideally be where talosctl can resolve any relative paths within the config file itself,
                # or if the config file uses absolute paths.
                # Using project_root as cwd seems safest if config files might have relative paths based on project root.
                # If talosctl apply-config --file expects the file path to be absolute or relative to its CWD,
                # and we provide an absolute path for config_file, CWD might be less critical for --file.
                # However, consistency with _generate_talos_configs (which uses script_execution_cwd) is good.
                # Let's use project_root as CWD.
                returncode, stdout, stderr = run_command(
                    f"talosctl apply-config --insecure --nodes {node['ip']} --file \"{config_file}\"", # Quote config_file for safety
                    cwd=project_root # Use determined project_root as CWD
                )
                
                if stdout: # Log stdout for apply-config
                    console.print(f"[dim]talosctl apply-config stdout for {node['name']}:\n{stdout}[/dim]")
                if stderr and returncode != 0: # Log stderr only on error
                     console.print(f"[yellow]talosctl apply-config stderr for {node['name']}:\n{stderr}[/yellow]")

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

    def _test_kube_connection(self, cluster_info: Dict[str, Any]) -> bool:
        """Test connection to the Kubernetes cluster using kubectl get nodes."""
        console.print("[dim]Attempting to connect to Kubernetes cluster...[/dim]")
        kubeconfig_path = os.path.join(self.repo_path, "kubeconfig")
        if not os.path.exists(kubeconfig_path):
            console.print(f"[bold red]Error: Kubeconfig not found at {kubeconfig_path}. Cannot test connection.[/bold red]")
            return False

        env = os.environ.copy()
        env["KUBECONFIG"] = kubeconfig_path

        returncode, stdout, stderr = run_command(
            "kubectl get nodes",
            cwd=self.repo_path,
            env=env,
            suppress_output=False # We want to see the output
        )

        if returncode != 0:
            console.print(f"[bold red]Error connecting to Kubernetes or getting nodes: {stderr}[/bold red]")
            if stdout:
                console.print(f"[yellow]Stdout from kubectl:\n{stdout}[/yellow]")
            return False
        
        # console.print(f"[green]Successfully fetched nodes:[/green]\n{stdout}")
        self._print_command_output_table("Node Status (Post-Bootstrap)", stdout)
        return True

    def _create_flux_directories_and_files(self, cluster_info: Dict[str, Any]) -> bool:
        """Create initial directory structure and kustomization files for Flux."""
        console.print("[dim]Creating Flux directory structure and kustomization files...[/dim]")
        base_flux_path = os.path.join(self.repo_path, "cluster", "flux")
        
        paths_to_create = [
            os.path.join(base_flux_path, "flux-system"),
            os.path.join(base_flux_path, "infrastructure", "sources"),
            os.path.join(base_flux_path, "apps") # As per bootstrap.sh implied structure
        ]
        
        for p in paths_to_create:
            try:
                os.makedirs(p, exist_ok=True)
                console.print(f"[dim]Created directory: {p}[/dim]")
            except OSError as e:
                console.print(f"[bold red]Error creating directory {p}: {e}[/bold red]")
                return False

        flux_kustomization_content = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - flux-system
  - infrastructure
  - apps
"""
        infra_kustomization_content = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - sources
# - controllers # This was in bootstrap.sh, but flux bootstrap handles controllers
"""
        infra_sources_kustomization_content = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
# - helm-repositories.yaml # Example, user adds these
""" # bootstrap.sh had helm-repositories.yaml, but it's better if user adds specifics
        infra_namespace_content = """apiVersion: v1
kind: Namespace
metadata:
  name: infrastructure
"""
        apps_kustomization_content = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
# Add your application namespaces and kustomizations here
# e.g.
# - demo
"""

        files_to_write = {
            os.path.join(base_flux_path, "kustomization.yaml"): flux_kustomization_content,
            os.path.join(base_flux_path, "infrastructure", "kustomization.yaml"): infra_kustomization_content,
            os.path.join(base_flux_path, "infrastructure", "sources", "kustomization.yaml"): infra_sources_kustomization_content,
            os.path.join(base_flux_path, "infrastructure", "namespace.yaml"): infra_namespace_content,
            os.path.join(base_flux_path, "apps", "kustomization.yaml"): apps_kustomization_content,
        }

        for file_path, content in files_to_write.items():
            try:
                with open(file_path, 'w') as f:
                    f.write(content)
                console.print(f"[dim]Created file: {file_path}[/dim]")
            except IOError as e:
                console.print(f"[bold red]Error writing file {file_path}: {e}[/bold red]")
                return False
        return True

    def _create_core_component_directories_and_files(self, cluster_info: Dict[str, Any]) -> bool:
        """Create initial directory structure for core components."""
        console.print("[dim]Creating core component directory structure...[/dim]")
        base_core_path = os.path.join(self.repo_path, "cluster", "core")
        
        core_components = ["kube-system", "cubefs", "kubevirt"] # As per bootstrap.sh
        
        try:
            os.makedirs(base_core_path, exist_ok=True) # Ensure base 'core' dir exists
            console.print(f"[dim]Ensured base directory: {base_core_path}[/dim]")
            for component in core_components:
                p = os.path.join(base_core_path, component)
                os.makedirs(p, exist_ok=True)
                console.print(f"[dim]Created directory: {p}[/dim]")
        except OSError as e:
            console.print(f"[bold red]Error creating core component directories: {e}[/bold red]")
            return False

        core_kustomization_content = """apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
"""
        for component in core_components:
            core_kustomization_content += f"  - {component}\n"
            # Create a placeholder kustomization.yaml in each component dir
            component_kustomization_path = os.path.join(base_core_path, component, "kustomization.yaml")
            placeholder_kustomization_content = f"""apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
# Add resources for {component} here
resources:
# - example.yaml
"""
            try:
                with open(component_kustomization_path, 'w') as f:
                    f.write(placeholder_kustomization_content)
                console.print(f"[dim]Created placeholder kustomization: {component_kustomization_path}[/dim]")
            except IOError as e:
                console.print(f"[bold red]Error writing file {component_kustomization_path}: {e}[/bold red]")
                # Continue, not critical for main structure

        core_kustomization_path = os.path.join(base_core_path, "kustomization.yaml")
        try:
            with open(core_kustomization_path, 'w') as f:
                f.write(core_kustomization_content)
            console.print(f"[dim]Created file: {core_kustomization_path}[/dim]")
        except IOError as e:
            console.print(f"[bold red]Error writing file {core_kustomization_path}: {e}[/bold red]")
            return False
            
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
