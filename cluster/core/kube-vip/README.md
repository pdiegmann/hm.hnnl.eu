# kube-vip

[kube-vip](https://kube-vip.io/) provides Kubernetes clusters with a virtual IP and load balancer for both the control plane and Kubernetes services. 

## Features

- ARP-based Layer 2 virtual IP for the Kubernetes control plane
- High availability for the Kubernetes API endpoint
- Load balancing for Kubernetes services
- Leader election ensures only one node handles the virtual IP

## Configuration

The deployment consists of:

- **configmap.yaml**: Configuration for kube-vip including the virtual IP address and settings
- **daemonset.yaml**: Deploys kube-vip as a DaemonSet on control plane nodes
- **rbac.yaml**: Required RBAC permissions for kube-vip to function

## Virtual IP

The virtual IP is configured to be: `192.168.1.100`

This IP will be used to access the Kubernetes API server (`https://192.168.1.100:6443`) and will float between available control plane nodes automatically.

## Deployment

kube-vip is deployed as a DaemonSet that runs only on control plane nodes (nodes with the label `node.kubernetes.io/controller=true`).

## Troubleshooting

If the virtual IP is not working:

1. Check if the kube-vip pods are running:
   ```bash
   kubectl get pods -n kube-system -l name=kube-vip
   ```

2. Check the logs:
   ```bash
   kubectl logs -n kube-system -l name=kube-vip
   ```

3. Ensure the virtual IP is accessible:
   ```bash
   ping 192.168.1.100
   ```

For more detailed troubleshooting, see the [kube-vip documentation](https://kube-vip.io/docs/troubleshooting/).
