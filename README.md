# Homelab Kubernetes Cluster

This repository contains the infrastructure code and configurations for a home Kubernetes cluster running on three mini servers:
- Apple M1 Mac mini
- Intel 4-core, 8GB RAM mini PC
- Ryzen 5825u, 32GB RAM mini PC

## Features

- [Talos OS](https://www.talos.dev/v1.10/) as the operating system and Kubernetes distribution
- GitOps deployment using [Flux CD](https://fluxcd.io/)
- High availability control plane with 3 nodes
- Virtual IP management via [kube-vip](https://kube-vip.io/)
- Identity management with [Zitadel](https://zitadel.com/)
- Secure service access via [NetBird](https://netbird.io/)
- Distributed storage with [CubeFS](https://www.cubefs.io)
- Secret management with [SOPS](https://github.com/getsops/sops) and [Age](https://github.com/FiloSottile/age)
- Infrastructure as Code (IaC) approach
- **Dual-access DNS system** for both local and external access to services
- **Automated DNS management** with ExternalDNS integration

## Repository Structure

```
homelab/
├── .github/                     # GitHub Actions workflows
├── bootstrap/                   # Bootstrap scripts and tools
│   └── talos/                   # Talos-specific bootstrap configurations
├── .sops/                       # SOPS encryption keys (gitignored)
├── cluster/                     # Kubernetes resources
│   ├── apps/                    # Application deployments
│   │   ├── demo/                # Demo applications
│   │   └── dual-access-demo/    # Demo showing local/external access
│   ├── core/                    # Core components (networking, storage, etc.)
│   │   ├── bind9/               # Local DNS server
│   │   ├── cubefs/              # CubeFS distributed storage 
│   │   ├── external-dns/        # External DNS management (Cloudflare)
│   │   ├── external-dns-local/  # Local DNS management (Bind9)
│   │   ├── kube-vip/            # Kubernetes virtual IP
│   │   ├── zitadel/             # Zitadel identity provider
│   │   └── netbird/             # NetBird secure gateway
│   ├── config/                  # Cluster-wide configurations
│   ├── secrets/                 # Encrypted secrets
│   │   ├── zitadel/             # Zitadel secrets
│   │   └── netbird/             # NetBird secrets
├── infrastructure/              # Infrastructure configurations
│   └── talos/                   # Talos OS configurations
│       └── controlplane/        # Control plane node configs
├── docs-src/                    # Documentation source
│   ├── dns-access-setup.md      # DNS and Access Configuration
├── scripts/                     # Utility scripts
│   ├── dns/                     # DNS configuration scripts
│   │   ├── generate-tsig-key.sh # Generate TSIG key for Bind9/ExternalDNS
│   │   └── update-network-config.sh # Update network configuration
```

## Prerequisites

- [kubectl](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- [flux](https://fluxcd.io/docs/installation/)
- [talosctl](https://www.talos.dev/v1.10/introduction/getting-started/)
- [Docker](https://docs.docker.com/get-docker/) (for the Mac mini VM)
- [Virtualbox](https://www.virtualbox.org/) or [UTM](https://mac.getutm.app/) (for Mac mini)
- [sops](https://github.com/getsops/sops)
- [age](https://github.com/FiloSottile/age)

## Getting Started

See [docs/getting-started.md](docs/getting-started.md) for detailed installation instructions.

For DNS and dual-access setup, see [docs-src/dns-access-setup.md](docs-src/dns-access-setup.md).

## DNS and Access System

This homelab features a dual-access system that allows:

- **Local Access**: Services are accessible from the local network using `local.hm.hnnl.eu` subdomains
- **External Access**: Services can be securely accessed over the internet via NetBird using `ext.hm.hnnl.eu` subdomains
- **Automated Management**: DNS records are automatically created and updated via ExternalDNS integration

### Key Components

- **Bind9**: Local DNS server for `local.hm.hnnl.eu` domain
- **External-DNS**: Integration with Cloudflare for external DNS and Bind9 for local DNS
- **NetBird**: Secure, zero-trust overlay network for external access

## Hardware Setup

| Node | Role | Hardware | IP Address | Notes |
|------|------|----------|------------|-------|
| talos-cp1 | Control Plane + Worker | Ryzen 5825u, 32GB RAM | 192.168.1.101 | First control plane node |
| talos-cp2 | Control Plane + Worker | Intel 4-core, 8GB RAM | 192.168.1.102 | Second control plane node |
| talos-cp3 | Control Plane + Worker | Mac mini M1 (VM) | 192.168.1.103 | Third control plane node |

## Virtual IP Addresses

| Service | Virtual IP | Description |
|---------|------------|-------------|
| Kubernetes API | 192.168.1.100 | Kubernetes control plane access |
| Zitadel | 192.168.1.110 | Identity provider interface |
| Bind9 DNS | (Dynamic) | Local DNS server |

## Documentation

Documentation is available in two formats:

1. **Online Documentation**: Visit our [GitHub Pages site](https://USERNAME.github.io/homelab/) for the latest documentation.

2. **Local Documentation**: Run the documentation locally by following these steps:

```bash
cd docs-src
pip install -r requirements.txt
mkdocs serve
```

Then open your browser to http://localhost:8000

See the [docs-src/README.md](docs-src/README.md) file for more information about the documentation system.

## License

MIT
