# Home Kubernetes Cluster Implementation Overview

This document provides an overview of the Kubernetes cluster repository structure and the implemented components.

## Architecture

The cluster architecture consists of several key parts:

### 1. High Availability Infrastructure

This cluster implements high availability by:

1. **Multiple Control Plane Nodes**: All three machines serve as both control plane and worker nodes, ensuring high availability of the Kubernetes API and control plane components.

2. **Distributed etcd**: etcd runs across all three control plane nodes in a quorum configuration, where operations require a majority (at least 2 nodes) to succeed.

3. **Virtual IP with kube-vip**: kube-vip provides a virtual IP (192.168.1.100) that automatically floats between available control plane nodes, ensuring continuous access to the API server even if a node fails.

4. **Workload Distribution**: All nodes run both control plane components and regular workloads, maximizing resource utilization while maintaining redundancy.

### 2. Identity and Access Management

Zitadel serves as the identity provider for the cluster:

1. **Comprehensive IAM Solution**: Provides complete user management, authentication, and authorization.

2. **Multiple Protocol Support**: Implements OIDC, OAuth2.x, SAML2, and LDAP for versatile integration.

3. **Advanced Security Features**: Supports passkeys/FIDO2, OTP, and other modern authentication methods.

4. **Kubernetes Integration**: Integrates with Kubernetes for RBAC authorization.

5. **Multi-tenancy**: Supports organizational structures and team management.

See [docs/zitadel.md](zitadel.md) for detailed information.

### 3. Secure Network Access

NetBird provides secure access to cluster services:

1. **Zero-Trust Networking**: Implements a WireGuard-based secure overlay network.

2. **Identity Integration**: Authenticates users via Zitadel for consistent access control.

3. **Peer-to-Peer Connectivity**: Enables direct connections between clients and services.

4. **Granular Access Policies**: Provides fine-grained control over service access.

5. **Kubernetes Operator**: Manages network resources natively within Kubernetes.

See [docs/netbird.md](netbird.md) for detailed information.

### 4. Storage Infrastructure

CubeFS provides distributed storage for the cluster:

1. **Distributed File System**: Enables persistent storage across nodes.

2. **High Availability**: Replicates data across nodes for fault tolerance.

3. **Kubernetes Integration**: Integrates with Kubernetes via StorageClass.

### 5. Secret Management

SOPS with AGE encryption secures sensitive data:

1. **Git-Compatible Encryption**: Safely stores encrypted secrets in the repository.

2. **Flux Integration**: Automatic decryption when deploying to the cluster.

3. **Secure Key Management**: Keeps private keys separate from the repository.

For information on integrating these components, see [docs/integration.md](integration.md).

## Repository Structure

The repository follows a GitOps approach with the following structure:

```
homelab/
├── .github/                     # GitHub Actions workflows and Renovate bot configuration
├── .sops/                       # SOPS encryption keys (gitignored)
├── bootstrap/                   # Bootstrap scripts and tools
│   ├── talos/                   # Talos-specific bootstrap configurations
│   └── vm/                      # Mac Mini VM setup instructions
├── cluster/                     # Kubernetes resources
│   ├── apps/                    # Application deployments
│   │   └── demo/                # Sample demo application
│   ├── core/                    # Core components
│   │   ├── cubefs/              # CubeFS distributed storage
│   │   ├── kube-system/         # Kubernetes system components
│   │   ├── kube-vip/            # Kube-vip for virtual IP (high availability)
│   │   ├── zitadel/             # Zitadel identity provider
│   │   └── netbird/             # NetBird secure gateway
│   ├── config/                  # Cluster-wide configurations
│   ├── flux/                    # Flux CD configuration
│   └── secrets/                 # Encrypted secrets
│       ├── zitadel/             # Zitadel secrets
│       └── netbird/             # NetBird secrets
├── docs/                        # Documentation
│   ├── getting-started.md       # Getting started guide
│   ├── troubleshooting.md       # Troubleshooting guide
│   ├── zitadel.md               # Zitadel documentation
│   ├── netbird.md               # NetBird documentation
│   └── integration.md           # Integration guide
├── infrastructure/              # Infrastructure configurations
│   └── talos/                   # Talos OS configurations
│       └── controlplane/        # Control plane node configs
└── scripts/                     # Utility scripts
    └── sops/                    # SOPS secret management scripts
```

## Implemented Components

### 1. Bootstrap

The bootstrap directory contains scripts and tools to initialize the cluster:

- `bootstrap.sh`: Main script to bootstrap the entire cluster
- `talos/gen-config.sh`: Generates Talos OS configurations
- `vm/setup-mac-mini-vm.sh`: Helper script for Mac Mini VM setup

### 2. Core Components

The core infrastructure components include:

- **CubeFS**: Distributed file system for persistent storage
- **kube-vip**: Virtual IP manager for high availability
- **Kube-system**: Core Kubernetes system components
- **Zitadel**: Identity and access management
- **NetBird**: Secure gateway for service access

### 3. Flux CD

Flux CD is used for GitOps-style deployment and includes:

- Helm repository sources
- Kustomizations for deploying components
- Infrastructure components

### 4. Secret Management

Secrets are managed using SOPS with AGE encryption:

- Encrypted secrets stored in the repository
- Automatic decryption by Flux when deploying to the cluster
- Scripts for encrypting and decrypting secrets

### 5. Sample Application

A demo application is included as a reference:

- Simple NGINX deployment
- Service definition
- Namespace configuration

## Hardware Configuration

| Node | Role | Hardware | IP Address |
|------|------|----------|------------|
| talos-cp1 | Control Plane + Worker | Ryzen 5825u, 32GB RAM | 192.168.1.101 |
| talos-cp2 | Control Plane + Worker | Intel 4-core, 8GB RAM | 192.168.1.102 |
| talos-cp3 | Control Plane + Worker | Mac mini M1 (VM) | 192.168.1.103 |

## Virtual IP Addresses

| Service | IP Address | Description |
|---------|------------|-------------|
| Kubernetes API | 192.168.1.100 | Control plane access |
| Zitadel | 192.168.1.110 | Identity provider |

## Getting Started

To get started with the cluster:

1. Review the `docs/getting-started.md` file
2. Run the bootstrap script: `bootstrap/bootstrap.sh`
3. Follow the instructions to set up each node
4. Set up the VM on the Mac Mini using `bootstrap/vm/setup-mac-mini-vm.sh`
5. Configure SOPS for secret management
6. Deploy and configure Zitadel
7. Deploy and configure NetBird

## Automation

The repository includes GitHub Actions for:

- Validating Kubernetes manifests
- Linting YAML files
- Renovate bot for dependency updates

## Next Steps

After setting up the basic cluster, you can:

1. Add more applications in the `cluster/apps` directory
2. Configure persistent volumes using CubeFS
3. Use the virtual IP provided by kube-vip for high availability services
4. Set up Zitadel for user management
5. Configure NetBird for secure service access
6. Encrypt and manage secrets using SOPS
7. Customize the configuration to suit your specific needs

For troubleshooting, refer to `docs/troubleshooting.md`.
For secret management, refer to `docs/sops.md`.
For identity management, refer to `docs/zitadel.md`.
For secure access, refer to `docs/netbird.md`.
For integration details, refer to `docs/integration.md`.
