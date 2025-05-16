# Homelab Kubernetes Cluster

This directory contains the Kubernetes manifests for deploying the homelab cluster. For detailed documentation, please refer to the MkDocs-based documentation:

- Online documentation: https://USERNAME.github.io/homelab/
- Local documentation: Run `cd docs-src && mkdocs serve`

## Directory Structure

- `apps/` - Application deployments
- `core/` - Core components (networking, storage, etc.)
  - `cubefs/` - CubeFS distributed storage 
  - `kube-vip/` - Kubernetes virtual IP
  - `zitadel/` - Zitadel identity provider
  - `netbird/` - NetBird secure gateway
- `config/` - Cluster-wide configurations
- `secrets/` - Encrypted secrets
