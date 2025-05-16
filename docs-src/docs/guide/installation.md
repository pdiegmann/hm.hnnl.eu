---
title: Installation Guide
description: Complete installation instructions for the Homelab Kubernetes Cluster
---

# Installation Guide

This guide provides detailed instructions for installing and configuring the homelab Kubernetes cluster.

## 1. Hardware Preparation

### 1.1 Hardware Nodes (All Control Plane + Worker)

1. Download the latest Talos OS ISO from the [official website](https://github.com/siderolabs/talos/releases)
2. Flash the ISO to a USB drive using a tool like [Balena Etcher](https://www.balena.io/etcher/)
3. Boot the Ryzen and Intel machines from the USB drive
4. Note down the IP addresses assigned by DHCP

### 1.2 Mac Mini (VM Control Plane + Worker)

1. Install UTM for macOS via [https://mac.getutm.app/](https://mac.getutm.app/)
2. Create a new VM with the following specifications:
   - System: Linux
   - Architecture: ARM64 (for M1)
   - Memory: 8-12GB
   - CPU Cores: 4-6
   - Disk: 40GB+
3. Mount the Talos OS ISO in the VM
4. Start the VM and note the IP address

## 2. Configuring Talos

### 2.1 Generate Talos Configurations

From your workstation, run:

```bash
cd bootstrap/talos
./gen-config.sh
```

This script will generate the necessary configuration files for your Talos nodes.

### 2.2 Apply Configurations to Nodes

Apply the configuration to each node:

```bash
# Apply configuration to each node
talosctl apply-config --insecure --nodes 192.168.1.101 --file infrastructure/talos/controlplane/talos-cp1.yaml
talosctl apply-config --insecure --nodes 192.168.1.102 --file infrastructure/talos/controlplane/talos-cp2.yaml
talosctl apply-config --insecure --nodes 192.168.1.103 --file infrastructure/talos/controlplane/talos-cp3.yaml
```

### 2.3 Bootstrap the Cluster

Initialize the Kubernetes cluster on the first control plane node:

```bash
talosctl bootstrap --nodes 192.168.1.101
```

### 2.4 Get Kubeconfig

Retrieve the kubeconfig file to interact with your cluster:

```bash
talosctl kubeconfig --nodes 192.168.1.101 -f ./kubeconfig
export KUBECONFIG=$(pwd)/kubeconfig
```

### 2.5 Wait for the Cluster to Initialize

Wait for all control plane nodes to become ready and for etcd to form a healthy cluster:

```bash
talosctl health --nodes 192.168.1.101,192.168.1.102,192.168.1.103 --wait-timeout 15m
```

## 3. Setting Up Secret Management

### 3.1 Generate SOPS Keys

Generate a key for encrypting secrets:

```bash
./scripts/sops/generate-key.sh
```

This will create an AGE key pair in the `.sops/age.agekey` directory and update the `.sops.yaml` configuration.

### 3.2 Create Flux Secret

Create an encrypted secret containing your AGE key for Flux to use:

```bash
./scripts/sops/create-age-secret.sh
```

This creates and encrypts the `cluster/flux/flux-system/age-secret.yaml` file, which Flux will use to decrypt secrets.

### 3.3 Encrypt Your Secrets

Encrypt your Kubernetes secrets:

```bash
./scripts/sops/encrypt.sh path/to/your/secret.yaml
```

## 4. Setting Up Flux CD

### 4.1 Bootstrap Flux

From your workstation, run:

```bash
flux bootstrap github \
  --owner=<your-github-username> \
  --repository=homelab \
  --branch=main \
  --path=cluster/flux \
  --personal
```

This will:

1. Create a repository on GitHub if it doesn't exist
2. Add Flux components to your repository
3. Deploy Flux in your cluster

### 4.2 Deploy Core Components

Flux will automatically deploy all components defined in the repository. You can monitor the deployment with:

```bash
kubectl get kustomizations -A
```

## 5. Deploy Core Services

The following core services will be deployed by Flux based on the repository configuration:

### 5.1 CubeFS Storage

CubeFS will be deployed to provide distributed storage. Verify the deployment with:

```bash
kubectl get pods -n cubefs
```

### 5.2 kube-vip

kube-vip will be deployed to manage virtual IPs. Verify the deployment with:

```bash
kubectl get pods -n kube-system -l name=kube-vip
```

Check that the virtual IP is accessible:

```bash
ping -c 1 192.168.1.100
```

### 5.3 Zitadel Identity Provider

Zitadel will be deployed for identity management. Verify the deployment with:

```bash
kubectl get pods -n zitadel
```

Once deployed, you can access the Zitadel UI at `https://id.homelab.local` or via the virtual IP at `https://192.168.1.110`.

### 5.4 NetBird Secure Gateway

NetBird will be deployed for secure access. Verify the deployment with:

```bash
kubectl get pods -n netbird
```

## 6. Verifying the Installation

Check if all pods are running:

```bash
kubectl get pods -A
```

Check node status:

```bash
kubectl get nodes
```

Check etcd cluster health:

```bash
kubectl -n kube-system exec -it $(kubectl get pods -l component=etcd -n kube-system -o name | head -1) -- etcdctl endpoint health --cluster
```

## 7. Initial Configuration

### 7.1 Configure DNS

Add DNS entries for your services:

- `id.homelab.local` -> `192.168.1.110` (Zitadel)
- `netbird.homelab.local` -> IP of the NetBird dashboard service

### 7.2 Set Up Zitadel

1. Access the Zitadel UI at `https://id.homelab.local`
2. Log in with the initial admin credentials
3. Create organizations and users
4. Set up OIDC clients for applications

### 7.3 Set Up NetBird

1. Access the NetBird dashboard
2. Configure it to use Zitadel for authentication
3. Create network policies
4. Set up routes and access controls

## 8. Next Steps

After completing the installation:

- Set up custom applications in the `cluster/apps` directory
- Configure persistent volumes with CubeFS
- Set up monitoring and logging
- Implement backup and recovery solutions
- Configure additional security measures

For more information, see the [Configuration Guide](configuration.md).
