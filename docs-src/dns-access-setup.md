# Homelab DNS and Access Configuration

## Architecture Overview

![DNS and Access Architecture](images/dns-access-architecture.md)


This setup enables both local (LAN) and external (via NetBird) access to services in your homelab.

## Components

1. **Bind9 DNS Server**: Provides local DNS resolution for `local.hm.hnnl.eu`
2. **External-DNS (Cloudflare)**: Manages DNS records for external access via `ext.hm.hnnl.eu`
3. **External-DNS-Local (Bind9)**: Manages DNS records for local access via `local.hm.hnnl.eu`
4. **NetBird**: Provides secure external access without exposing services to the internet

## Setup Instructions

### 1. Initial Configuration

```bash
# Clone the repository (if you haven't already)
git clone <your-repo-url>
cd homelab

# Make scripts executable
bash scripts/make-scripts-executable.sh

# Update network configuration
bash scripts/dns/update-network-config.sh

# Generate TSIG key for BIND9/external-dns
bash scripts/dns/generate-tsig-key.sh

# Encrypt the TSIG key with SOPS
sops --encrypt --in-place cluster/core/bind9/tsig-key-secret.yaml
```

### 2. Update Core Components

Ensure these components are included in your core kustomization:

```yaml
# cluster/core/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - bind9
  - external-dns
  - external-dns-local
  - netbird
  # Other core components...
```

### 3. Deploy with Flux

The components will be deployed by Flux automatically once the changes are committed and pushed to your repository.

## Using the Dual Access System

### Service Configuration

To make a service accessible both locally and externally:

1. Create a service with annotations:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  namespace: my-namespace
  annotations:
    external-dns.alpha.kubernetes.io/hostname: myservice.ext.hm.hnnl.eu, myservice.local.hm.hnnl.eu
    external-dns.alpha.kubernetes.io/target-type: "both"
spec:
  type: LoadBalancer
  # ...
```

2. For services that should ONLY be accessible locally:

```yaml
metadata:
  annotations:
    external-dns.alpha.kubernetes.io/hostname: internal-service.local.hm.hnnl.eu
    external-dns.alpha.kubernetes.io/target-type: "internal"
```

3. For services that should ONLY be accessible externally:

```yaml
metadata:
  annotations:
    external-dns.alpha.kubernetes.io/hostname: external-service.ext.hm.hnnl.eu
    external-dns.alpha.kubernetes.io/target-type: "external"
```

### NetBird Configuration

1. Make sure devices connecting externally have the NetBird client installed.
2. Configure your NetBird setup to use `ext.hm.hnnl.eu` as the DNS domain.

## Maintenance

- To update network configurations: `bash scripts/dns/update-network-config.sh`
- To rotate the TSIG key: `bash scripts/dns/generate-tsig-key.sh`

## Troubleshooting

### Testing DNS Resolution

1. **Local DNS:**
   ```bash
   dig @<bind9-ip> myservice.local.hm.hnnl.eu
   ```

2. **External DNS:**
   ```bash
   dig @1.1.1.1 myservice.ext.hm.hnnl.eu
   ```

### Common Issues

- **Cannot resolve local DNS names**: 
  - Ensure your devices are using the Bind9 server as DNS
  - Check that external-dns-local pods are running
  
- **External access not working**:
  - Verify NetBird connectivity
  - Check that external-dns pods are running
  - Verify Cloudflare configuration
