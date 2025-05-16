---
title: Talos OS
description: Information about the Talos OS operating system implementation
---

# Talos OS

[Talos OS](https://www.talos.dev/) is an immutable, secure Linux distribution built specifically for Kubernetes. This document covers its implementation in the homelab cluster.

## Overview

Talos OS provides:

- A minimal, immutable operating system
- Built-in Kubernetes deployment
- Secure by default configuration
- API-driven management
- Simplified upgrades

## Architecture

Talos follows a unique architecture:

1. **Immutable System**: The operating system is read-only and follows secure design principles
2. **Control Plane Mode**: Configured to run both Kubernetes control plane and etcd
3. **Worker Mode**: Configured to run only Kubernetes worker components
4. **No Shell Access**: Management is exclusively through the Talos API

## Configuration

The homelab cluster uses a high-availability configuration with three Talos nodes:

- All three nodes run in both control plane and worker modes
- Each node has unique hardware characteristics (Ryzen, Intel, and M1 Mac)
- Configuration is managed via code in the `infrastructure/talos` directory

## Deployment Process

Deploying Talos OS involves:

1. Booting from the Talos ISO
2. Generating machine configurations
3. Applying configurations to each node
4. Bootstrapping the Kubernetes cluster
5. Retrieving the kubeconfig file

## Management

Talos is managed using the `talosctl` command-line tool:

```bash
# Check node health
talosctl --nodes 192.168.1.101,192.168.1.102,192.168.1.103 health

# Get cluster information
talosctl --nodes 192.168.1.101 kubeconfig

# Perform operating system upgrades
talosctl --nodes 192.168.1.101,192.168.1.102,192.168.1.103 upgrade
```

## Security Features

Talos provides several security advantages:

- No shell or SSH access
- Read-only filesystem
- Minimal attack surface
- Mutual TLS for all communications
- Secure boot support
- Automatic security patches

## Troubleshooting

Common troubleshooting commands:

```bash
# View system logs
talosctl --nodes 192.168.1.101 logs

# Get hardware information
talosctl --nodes 192.168.1.101 disks

# Check service status
talosctl --nodes 192.168.1.101 services

# Reset a node (caution!)
talosctl --nodes 192.168.1.101 reset
```

## Upgrading

Upgrading Talos OS is a straightforward process:

```bash
# Check current version
talosctl --nodes 192.168.1.101 version

# Perform upgrade to specific version
talosctl --nodes 192.168.1.101 upgrade --image ghcr.io/siderolabs/installer:v1.6.4
```

Always upgrade one node at a time to maintain cluster availability.
