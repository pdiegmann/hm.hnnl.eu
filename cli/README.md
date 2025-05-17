# hm-cli: Homelab Kubernetes Cluster Management CLI

A comprehensive command-line tool for managing the entire lifecycle of a homelab Kubernetes cluster based on Talos OS, Flux CD, and GitOps principles.

## Overview

The `hm-cli` tool simplifies the management of your homelab Kubernetes cluster by providing commands for:

- Cluster lifecycle management (create, upgrade, delete)
- Service management (add, list, remove)
- GitOps operations (commit, push, sync)
- Configuration management

## Understanding the Core Technologies

This section provides a brief overview of the key technologies used by `hm-cli` and in the homelab setup.

-   **Kubernetes:** An open-source system for automating deployment, scaling, and management of containerized applications. It groups containers that make up an application into logical units for easy management and discovery. For more details, see the official [Kubernetes documentation](https://kubernetes.io/docs/home/) or project documentation like [`docs-src/docs/components/kubernetes.md`](docs-src/docs/components/kubernetes.md:1).
-   **Talos OS:** A modern, minimalist, and secure Linux distribution specifically designed for running Kubernetes. It's API-managed and immutable, enhancing cluster security and manageability. Learn more from the [official Talos OS documentation](https://www.talos.dev/v1.7/introduction/what-is-talos/) or project documentation like [`docs-src/docs/components/talos.md`](docs-src/docs/components/talos.md:1).
-   **Flux CD:** A GitOps toolkit for Kubernetes that enables declarative application delivery and cluster management. It keeps your cluster state synchronized with configurations defined in a Git repository. Explore the [Flux CD documentation](https://fluxcd.io/docs/) for comprehensive information.
-   **GitOps:** A way of implementing Continuous Delivery for cloud native applications. It focuses on using Git as the single source of truth for declarative infrastructure and applications, automating updates when changes are pushed to Git.

## Installation

### Prerequisites

-   **Python 3.8 or higher:** A versatile programming language. `hm-cli` is written in Python. Installation instructions can be found on the [official Python website](https://www.python.org/downloads/).
-   **pip (Python package manager):** The package installer for Python. It's used to install `hm-cli` and its dependencies. Usually installed automatically with Python.
-   **Git:** A distributed version control system used for tracking changes in source code during software development. It's essential for GitOps workflows. Download from the [official Git website](https://git-scm.com/downloads).
-   **Talos CLI (`talosctl`):** The command-line tool for interacting with Talos OS clusters. It's used for bootstrapping and managing Talos nodes. Follow the [official Talos OS documentation for `talosctl` installation](https://www.talos.dev/v1.7/introduction/getting-started/#install-talosctl).
-   **Flux CLI (`flux`):** The command-line tool for bootstrapping and interacting with Flux CD. It's used to manage GitOps synchronization. Installation instructions are on the [Flux CD website](https://fluxcd.io/flux/installation/).
-   **kubectl:** The Kubernetes command-line tool, which allows you to run commands against Kubernetes clusters. It's used for interacting with and managing cluster resources. Install it by following the [official Kubernetes documentation](https://kubernetes.io/docs/tasks/tools/install-kubectl/).

### Install from Source

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hm-cli.git
   cd hm-cli
   ```

2. Install the package:
   ```bash
   pip install -e .
   ```
   This installs the package in 'editable' mode, meaning changes to the source code in the `hm_cli` directory will be immediately effective without needing to reinstall.

## Configuration

The CLI tool stores its configuration in `~/.config/hm-cli/config.yaml`. You can view and modify the configuration using the `config` commands:

```bash
# Show current configuration
hm-cli config show

# Set a configuration value
hm-cli config set repo_path /path/to/your/repo
```

Important configuration options:

- `repo_path`: Path to your homelab repository (default: `~/hm.hnnl.eu`). This defaults to `~/hm.hnnl.eu`, assuming you have cloned the main `hm.hnnl.eu` project repository to your home directory. Adjust this path if your clone is located elsewhere.
- `git.user_name`: Git username for commits
- `git.user_email`: Git email for commits
- `git.remote`: Git remote name (default: `origin`)
- `git.branch`: Git branch name (default: `main`)
- `cluster.name`: Cluster name (default: `homelab`)
- `cluster.network_prefix`: Network prefix (default: `192.168.1`)
- `cluster.control_plane_vip`: Control plane VIP (default: `192.168.1.100`)

## Usage

### Cluster Management

#### Create a New Cluster

```bash
hm-cli cluster create
```

This highly interactive command guides you through the complete cluster creation process:
1.  **Collect Cluster Information**: Prompts for cluster name, network settings (prefix, VIP), Talos version, Kubernetes version, and control plane node IPs.
2.  **Generate Talos Configurations**: Optionally generates new Talos configurations (control plane and machine configs) using the provided versions. You can skip if they already exist.
3.  **Apply Talos Configurations**: Applies the generated configurations to each specified control plane node.
4.  **Bootstrap Cluster**: Initializes the Talos cluster on the first control plane node and waits for the Kubernetes API to become available.
5.  **Retrieve Kubeconfig**: Fetches the `kubeconfig` file for accessing the new cluster.
6.  **Test Kubernetes Connection**: Verifies connectivity to the newly bootstrapped cluster by attempting to list nodes.
7.  **Create Flux Directories**: Sets up the initial directory structure (`cluster/flux/`, `cluster/flux/infrastructure/`, `cluster/flux/apps/`) and kustomization files for Flux.
8.  **Bootstrap Flux**: Runs `flux bootstrap github` to set up GitOps, prompting for GitHub username and repository details.
9.  **Create Core Component Stubs**: Creates a basic directory structure (`cluster/core/kube-system/`, etc.) and placeholder kustomization files for essential core components.

Each major step requires user confirmation before proceeding, allowing for a controlled and observable setup.

#### Upgrade a Cluster

```bash
hm-cli cluster upgrade
```

This command will:
1. Collect information about the current cluster
2. Prompt for Kubernetes and Talos versions to upgrade to
3. Update and apply Talos configurations
4. Wait for the upgrade to complete

#### Delete a Cluster

```bash
hm-cli cluster delete
```

This command will:
1. Confirm deletion by asking for the cluster name
2. Reset all Talos nodes
3. Clean up local files

#### Check Cluster Status

```bash
hm-cli cluster status
```

This command provides a comprehensive overview of the cluster's health and status, including:
1.  **Node Status**: Displays the status, roles, age, version, internal/external IPs, OS image, kernel, and container runtime for each node.
2.  **Pod Status (All Namespaces)**: Shows all pods across all namespaces, their status, restarts, age, IP, node, and nominated node.
3.  **Flux Status**:
    *   **Kustomizations**: Lists all Flux kustomizations, their readiness, and status.
    *   **Sources**: Details all Flux sources (GitRepositories, HelmRepositories, etc.), their readiness, and status.
4.  **Storage Status**:
    *   **CubeFS Pods**: If CubeFS is installed, shows the status of its pods.
    *   **Storage Classes (SCs)**: Lists available storage classes.
    *   **Persistent Volumes (PVs)**: Displays all persistent volumes and their status.
    *   **Persistent Volume Claims (PVCs)**: Shows all PVCs across namespaces, their status, volume, capacity, access modes, and age.
5.  **Kube-vip Status**: If kube-vip is used, shows the status of its pods.
6.  **Virtual IP Accessibility**: Pings the configured control-plane VIP to check its responsiveness.
7.  **etcd Health**:
    *   **etcd Pods**: Displays the status of etcd pods in the `kube-system` namespace.
    *   **etcd Cluster Health**: Executes `etcdctl endpoint health --cluster` on an etcd pod to check member health.

The output is formatted using tables for readability, with color-coding for different statuses (e.g., green for 'Running'/'Ready', red for 'Failed'/'Error').

### Service Management

#### Add a New Service

```bash
hm-cli service add
```

This interactive command will:
1. Collect service information (name, type, namespace, visibility, port)
2. Create service directory structure
3. Generate Kubernetes manifests (deployment, service, etc.)
4. Optionally commit changes to Git

#### List Services

```bash
hm-cli service list
```

This command will display a table of all services in the cluster, including:
- Name
- Type
- Namespace
- Path

#### Remove a Service

```bash
hm-cli service remove
```

This command will:
1. Display a list of services to choose from
2. Confirm removal
3. Remove the service directory
4. Optionally commit changes to Git

### GitOps Operations

#### Commit Changes

```bash
# With interactive prompt for commit message
hm-cli gitops commit

# With specified commit message
hm-cli gitops commit -m "Add new service"
```

This command will:
1. Check for changes in the repository
2. Prompt for Git user configuration if not set
3. Commit all changes with the specified message

#### Push Changes

```bash
# Push to default remote and branch
hm-cli gitops push

# Push to specific remote and branch
hm-cli gitops push --remote origin --branch main
```

This command will push committed changes to the remote repository.

#### Sync with Flux

```bash
hm-cli gitops sync
```

This command will:
1. Trigger Flux to reconcile the repository
2. Wait for reconciliation to complete
3. Display the status

## Examples

### Complete Cluster Setup Workflow

```bash
# 1. Create a new cluster
hm-cli cluster create

# 2. Add a web application service
hm-cli service add

# 3. Commit and push changes
hm-cli gitops commit -m "Initial cluster setup with web app"
hm-cli gitops push

# 4. Trigger Flux synchronization
hm-cli gitops sync

# 5. Check cluster status
hm-cli cluster status
```

### Adding Multiple Services

```bash
# Add a database service
hm-cli service add
# (Follow prompts to create a database service)

# Add a monitoring service
hm-cli service add
# (Follow prompts to create a monitoring service)

# Commit all changes at once
hm-cli gitops commit -m "Add database and monitoring services"
hm-cli gitops push
hm-cli gitops sync
```

### Upgrading the Cluster

```bash
# Check current status
hm-cli cluster status

# Perform upgrade
hm-cli cluster upgrade

# Verify upgrade
hm-cli cluster status
```

## Troubleshooting

### Common Issues

1. **Git Authentication Errors**
   - Ensure your Git credentials are properly configured
   - Check that you have access to the remote repository

2. **Talos Configuration Errors**
   - Verify that node IPs are correct
   - Ensure Talos is properly installed on all nodes

3. **Flux Synchronization Issues**
   - Check that Flux is installed in the cluster
   - Verify that the repository URL and credentials are correct

### Logs

The CLI tool logs to the console with detailed information about operations. For more verbose output from `hm-cli` itself, you can set the `LOG_LEVEL` environment variable:

```bash
export LOG_LEVEL=DEBUG
hm-cli cluster status
```
For issues during cluster operations or GitOps sync, you may also need to consult the logs from the underlying tools like `talosctl` (e.g., `talosctl -n <node-ip> logs controller`), `kubectl get events -A -w`, or `flux logs --all-namespaces`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
