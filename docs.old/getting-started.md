# Getting Started

This guide will walk you through the process of setting up your homelab Kubernetes cluster using Talos OS.

## 1. Hardware Preparation

### 1.1 Hardware Nodes (All Control Plane + Worker)

1. Download the latest Talos ISO from the [official website](https://github.com/siderolabs/talos/releases)
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
3. Mount the Talos ISO in the VM
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
talosctl kubeconfig --nodes 192.168.1.101 -f .
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

See [docs/sops.md](sops.md) for detailed instructions on secret management.

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

## 5. Verifying the Installation

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

## 6. Accessing Services

Once everything is set up, you can access the services through their respective endpoints.

For example, to get the URL for the Kubernetes dashboard:

```bash
kubectl get -n kubernetes-dashboard svc kubernetes-dashboard -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
```

You can also access services via the virtual IP provided by kube-vip (192.168.1.100).

## 7. Next Steps

- Set up custom applications in the `cluster/apps` directory
- Configure storage volumes with CubeFS
- Access services using the virtual IP provided by kube-vip
- Manage and encrypt your secrets using SOPS (see [docs/sops.md](sops.md))

## Troubleshooting

See [troubleshooting.md](troubleshooting.md) for common issues and solutions.
