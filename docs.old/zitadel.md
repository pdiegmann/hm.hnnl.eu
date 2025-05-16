# Zitadel Identity Provider

[Zitadel](https://zitadel.com/) is deployed as the primary identity provider for the homelab Kubernetes cluster. This document outlines the configuration, usage, and integration points.

## Overview

Zitadel provides:
- Complete identity and access management (IAM) solution
- OIDC, OAuth2, and SAML2 authentication support
- Multi-tenancy capabilities
- Advanced security features (FIDO2, OTP)
- Role-based access control

## Architecture

The Zitadel deployment consists of:

1. **Zitadel Service** - The main application handling authentication and user management
2. **CockroachDB** - Embedded database for persistent storage
3. **Load Balancer Service** - Provides access via a dedicated virtual IP (192.168.1.110)

## Configuration

### Basic Configuration

- **URL**: https://id.homelab.local
- **Admin account**: Created during initial setup
- **Persistence**: Using CubeFS storage class

### Integration with Kubernetes

Zitadel can be configured as an OIDC provider for Kubernetes authentication by:

1. Creating a client in Zitadel for Kubernetes
2. Configuring the Kubernetes API server to use Zitadel as an OIDC provider
3. Setting up the appropriate RBAC roles and role bindings

Example API server configuration:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kube-apiserver
spec:
  containers:
  - command:
    - kube-apiserver
    - --oidc-issuer-url=https://id.homelab.local
    - --oidc-client-id=kubernetes
    - --oidc-username-claim=email
    - --oidc-groups-claim=groups
```

### Integration with NetBird

Zitadel is configured as the identity provider for NetBird, allowing:
- Single sign-on for NetBird access
- Role-based access to network resources
- Centralized user management
- Consistent authentication experience

## Initial Setup

After deployment, complete these steps:

1. Access the Zitadel UI at https://id.homelab.local
2. Log in with the admin credentials (stored in the `zitadel-secrets` secret)
3. Create organizations and users as needed
4. Set up OIDC clients for applications that need authentication
5. Configure roles and permissions

## Security Recommendations

- Regularly rotate all credentials
- Enable multi-factor authentication
- Use passkeys where possible
- Monitor login attempts and failures
- Implement strict password policies

## Troubleshooting

### Common Issues

- **Connection Problems**: Verify the Zitadel pods are running and the virtual IP is accessible
- **Database Errors**: Check CockroachDB logs for potential issues
- **Authentication Failures**: Verify client configurations and secret values
- **Certificate Issues**: Ensure TLS certificates are valid and properly configured

### Logs

Access logs with:

```bash
kubectl logs -n zitadel -l app.kubernetes.io/name=zitadel
```

For database logs:
```bash
kubectl logs -n zitadel -l app.kubernetes.io/name=cockroachdb
```
