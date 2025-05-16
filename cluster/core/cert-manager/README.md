# cert-manager for SSL Certificates

This directory contains the Kubernetes manifests for deploying [cert-manager](https://cert-manager.io/) to the homelab cluster, which manages TLS certificates using Let's Encrypt.

## Overview

cert-manager automates the management and issuance of TLS certificates from Let's Encrypt. We're using the DNS01 challenge with Cloudflare for domain validation.

## Components

- **cert-manager**: Core component that handles certificate issuance and renewal
- **ClusterIssuer**: Configures Let's Encrypt as the certificate authority
- **Certificate**: Defines the wildcard certificate for the domain
- **Cloudflare API Token**: Secret for DNS validation

## Configuration

The deployment includes:

- A staging and production Let's Encrypt ClusterIssuer
- Wildcard certificate for `*.hm.hnnl.eu`
- DNS01 challenge with Cloudflare for domain validation

## Prerequisites

1. A Cloudflare API token with the following permissions:
   - Zone:Zone:Read
   - Zone:DNS:Edit

2. The domain `hm.hnnl.eu` must be managed by Cloudflare

## Secrets

The `cloudflare-token-secret.yaml` file contains a reference to the Cloudflare API token, which should be encrypted using SOPS.

## Usage

To use the certificates in your services, reference the TLS secret in your Ingress resources:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: example-ingress
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - service.hm.hnnl.eu
    secretName: service-tls
  rules:
  - host: service.hm.hnnl.eu
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: example-service
            port:
              number: 80
```

## Troubleshooting

If certificates aren't being issued or renewed:

1. Check the cert-manager logs:
   ```bash
   kubectl logs -n cert-manager -l app=cert-manager
   ```

2. Check the certificate status:
   ```bash
   kubectl get certificates -A
   kubectl describe certificate hm-hnnl-eu-tls -n cert-manager
   ```

3. Check for challenges:
   ```bash
   kubectl get challenges -A
   ```
