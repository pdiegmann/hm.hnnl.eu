---
title: Configuration Guide
description: Advanced configuration options for the Homelab Kubernetes Cluster
---

# Configuration Guide

This guide provides detailed information on configuring various aspects of the homelab Kubernetes cluster after initial installation.

## Repository Structure

The GitOps approach means configurations are managed in the repository with the following structure:

```
homelab/
├── cluster/
│   ├── apps/                    # Application deployments
│   ├── core/                    # Core components
│   ├── config/                  # Cluster-wide configurations
│   ├── flux/                    # Flux CD configuration
│   └── secrets/                 # Encrypted secrets
└── infrastructure/
    └── talos/                   # Talos OS configurations
```

## Talos Configuration

### Updating Node Configurations

To update a Talos node configuration:

1. Edit the configuration file in `infrastructure/talos/controlplane/`
2. Apply the updated configuration:

```bash
talosctl apply-config --nodes 192.168.1.101 --file infrastructure/talos/controlplane/talos-cp1.yaml
```

### Common Configuration Changes

#### Changing Network Settings

To modify network settings, update the `machine.network` section:

```yaml
machine:
  network:
    hostname: talos-cp1
    interfaces:
      - interface: eth0
        dhcp: false
        addresses:
          - 192.168.1.101/24
        routes:
          - network: 0.0.0.0/0
            gateway: 192.168.1.1
```

#### Modifying Kernel Parameters

To add or change kernel parameters:

```yaml
machine:
  sysctls:
    net.ipv4.ip_forward: "1"
    net.ipv6.conf.all.forwarding: "1"
```

## Kubernetes Configuration

### Adding or Modifying Node Labels

To add or change node labels:

```bash
kubectl label nodes talos-cp1 node-role.kubernetes.io/storage=true
```

### Configuring Resource Quotas

Create or modify namespace resource quotas:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: compute-quota
  namespace: my-namespace
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
```

## Core Component Configuration

### CubeFS Storage

To modify CubeFS configuration, update the HelmRelease in `cluster/core/cubefs/helmrelease.yaml`:

```yaml
spec:
  values:
    master:
      replicas: 3
      resources:
        requests:
          cpu: 200m
          memory: 256Mi
```

### kube-vip

To configure kube-vip, update the ConfigMap in `cluster/core/kube-vip/configmap.yaml`:

```yaml
data:
  config.yaml: |
    vip_interface: "eth0"
    vip_address: "192.168.1.100"
    vip_leaderelection: true
    enable_loadbalancer: true
```

### Zitadel Identity Provider

To modify Zitadel configuration, update the HelmRelease in `cluster/core/zitadel/helmrelease.yaml`:

```yaml
spec:
  values:
    zitadel:
      configmapConfig:
        ExternalDomain: "id.homelab.local"
        ExternalPort: 443
```

### NetBird Secure Gateway

To modify NetBird configuration, update the HelmRelease in `cluster/core/netbird/management.yaml`:

```yaml
spec:
  values:
    env:
      AUTH_OIDC_ENABLED: "true"
      AUTH_OIDC_ISSUER: "https://id.homelab.local"
```

## Flux CD Configuration

### Adding New Repositories

To add a new Helm repository:

```yaml
apiVersion: source.toolkit.fluxcd.io/v1beta2
kind: HelmRepository
metadata:
  name: new-repo
  namespace: flux-system
spec:
  interval: 1h
  url: https://charts.example.com
```

### Adding New Kustomizations

To add a new Kustomization:

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: new-component
  namespace: flux-system
spec:
  interval: 10m
  path: ./cluster/apps/new-component
  prune: true
  sourceRef:
    kind: GitRepository
    name: flux-system
```

## Secret Management

### Creating a New Secret

1. Create a plaintext secret:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
  namespace: default
type: Opaque
stringData:
  username: admin
  password: change-me
```

2. Encrypt it with SOPS:

```bash
./scripts/sops/encrypt.sh path/to/my-secret.yaml
```

### Updating an Existing Secret

1. Decrypt the secret:

```bash
./scripts/sops/decrypt.sh path/to/encrypted-secret.yaml --stdout > /tmp/decrypted-secret.yaml
```

2. Edit the decrypted file
3. Re-encrypt it:

```bash
./scripts/sops/encrypt.sh /tmp/decrypted-secret.yaml
```

4. Replace the original encrypted file:

```bash
mv /tmp/decrypted-secret.yaml.enc path/to/encrypted-secret.yaml
```

## Network Configuration

### Adding a New Virtual IP

To add a new virtual IP for a service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: my-service
  namespace: default
  annotations:
    kube-vip.io/loadbalancerIPs: "192.168.1.120"
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 8080
  selector:
    app: my-app
```

### Configuring DNS

Update your local DNS or `/etc/hosts` to include:

```
192.168.1.100 k8s.homelab.local
192.168.1.110 id.homelab.local
```

## Application Deployment

### Creating a New Application

1. Create a directory in `cluster/apps/my-app`
2. Create the necessary Kubernetes resources
3. Create a kustomization.yaml file:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - deployment.yaml
  - service.yaml
```

4. Add the application to the main apps kustomization:

```yaml
# In cluster/apps/kustomization.yaml
resources:
  - existing-app
  - my-app
```

## Backup and Recovery

### Creating Backup Configurations

Use a backup solution like Velero with CubeFS:

```yaml
apiVersion: velero.io/v1
kind: Schedule
metadata:
  name: daily-backup
spec:
  schedule: "0 0 * * *"
  template:
    includedNamespaces:
      - default
      - kube-system
    includedResources:
      - persistentvolumes
      - persistentvolumeclaims
    storageLocation: default
    volumeSnapshotLocations:
      - default
```

## Security Configurations

### Implementing Network Policies

Create a network policy to restrict pod communication:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: default
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
```

### Adding RBAC Roles

Create a role and role binding:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: app-reader
  namespace: default
rules:
- apiGroups: [""]
  resources: ["pods", "services"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: app-reader-binding
  namespace: default
subjects:
- kind: Group
  name: readers@homelab.local
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: Role
  name: app-reader
  apiGroup: rbac.authorization.k8s.io
```

## System Monitoring

### Adding Prometheus Monitoring

Deploy Prometheus for monitoring:

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: prometheus
  namespace: monitoring
spec:
  chart:
    spec:
      chart: prometheus
      version: 15.x.x
      sourceRef:
        kind: HelmRepository
        name: prometheus-community
        namespace: flux-system
```

### Configuring Alerts

Add alert rules to Prometheus:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: node-alerts
  namespace: monitoring
spec:
  groups:
  - name: node-alerts
    rules:
    - alert: NodeMemoryHigh
      expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes > 0.9
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: Node memory usage is high
        description: Node {{ $labels.instance }} memory usage is above 90%
```

## Advanced Topics

### Scaling the Cluster

To add a new node to the cluster:

1. Prepare the hardware with Talos OS
2. Generate a new configuration file
3. Apply the configuration
4. Update the kustomization files as needed

### Upgrading Kubernetes

To upgrade Kubernetes version:

1. Update the `KUBERNETES_VERSION` in `bootstrap/talos/gen-config.sh`
2. Regenerate configurations
3. Apply the new configurations one node at a time
4. Monitor node health during the upgrade process
