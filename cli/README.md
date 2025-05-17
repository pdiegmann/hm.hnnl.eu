# hm-cli: Homelab Kubernetes Cluster Management CLI

A comprehensive command-line tool for managing the entire lifecycle of a homelab Kubernetes cluster based on Talos OS, Flux CD, and GitOps principles.

## Overview

The `hm-cli` tool simplifies the management of your homelab Kubernetes cluster by providing commands for:

- Cluster lifecycle management (create, upgrade, delete)
- Service management (add, list, remove)
- GitOps operations (commit, push, sync)
- Configuration management

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Talos CLI (`talosctl`)
- Flux CLI (`flux`)
- kubectl

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

## Configuration

The CLI tool stores its configuration in `~/.config/hm-cli/config.yaml`. You can view and modify the configuration using the `config` commands:

```bash
# Show current configuration
hm-cli config show

# Set a configuration value
hm-cli config set repo_path /path/to/your/repo
```

Important configuration options:

- `repo_path`: Path to your homelab repository (default: `~/hm.hnnl.eu`)
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

This interactive command will:
1. Collect cluster information (name, network settings, node IPs)
2. Generate Talos configurations
3. Apply configurations to nodes
4. Bootstrap the cluster
5. Set up Flux for GitOps

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

This command will display:
1. Node status
2. Pod status

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

The CLI tool logs to the console with detailed information about operations. For more verbose output, you can set the log level:

```bash
export LOG_LEVEL=DEBUG
hm-cli cluster status
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
