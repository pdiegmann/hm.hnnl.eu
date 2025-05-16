# external-dns for Automatic DNS Management

This directory contains the Kubernetes manifests for deploying [external-dns](https://github.com/kubernetes-sigs/external-dns) to the homelab cluster, which automatically manages DNS records in Cloudflare.

## Overview

external-dns creates and updates DNS records in Cloudflare based on Services and Ingresses in your Kubernetes cluster. This ensures your domain always points to the current public IP addresses of your cluster.

## Components

- **external-dns**: Core component that synchronizes Kubernetes resources with DNS records
- **Cloudflare API Token**: Secret for authentication with Cloudflare API
- **Public IP Service**: LoadBalancer service to expose and track the cluster's public IP addresses

## Configuration

The deployment includes:

- external-dns Helm release configured to use Cloudflare as the DNS provider
- A Service with annotations for external-dns to update the main domain record
- Support for both IPv4 and IPv6 addresses (dual-stack)

## Prerequisites

1. A Cloudflare API token with the following permissions:
   - Zone:Zone:Read
   - Zone:DNS:Edit

2. The domain `hm.hnnl.eu` must be managed by Cloudflare

## Secrets

The `cloudflare-token-secret.yaml` file contains a reference to the Cloudflare API token, which should be encrypted using SOPS.

## Usage

### Automatic Domain Updates

The `public-ip-service.yaml` file creates a Service of type LoadBalancer that has the annotation:

```yaml
external-dns.alpha.kubernetes.io/hostname: hm.hnnl.eu
```

This ensures that the domain `hm.hnnl.eu` always points to the public IP address of your cluster.

### Adding DNS Records for Services

To add DNS records for your services, add the following annotation to your Service or Ingress resources:

```yaml
annotations:
  external-dns.alpha.kubernetes.io/hostname: service.hm.hnnl.eu
```

## Troubleshooting

If DNS records aren't being updated:

1. Check the external-dns logs:
   ```bash
   kubectl logs -n external-dns -l app.kubernetes.io/name=external-dns
   ```

2. Check if the LoadBalancer service has an external IP assigned:
   ```bash
   kubectl get svc -n external-dns cluster-public-ip
   ```

3. Verify the DNS records in Cloudflare:
   ```bash
   dig +short hm.hnnl.eu
   dig +short AAAA hm.hnnl.eu  # For IPv6
   ```
