# Troubleshooting

This document provides solutions for common issues you might encounter with your Talos Kubernetes cluster.

## Talos OS Issues

### Cannot Connect to Node

If you can't connect to a Talos node:

1. Verify the node is powered on and has network connectivity
2. Check if the IP address is correct
3. Try pinging the node
4. If using the Mac Mini VM, ensure the VM is running and has proper network configuration

```bash
# Test basic connectivity
ping 192.168.1.101

# Check if Talos API is responding
talosctl --nodes 192.168.1.101 healthcheck
```

### Reset a Talos Node

If you need to completely reset a node:

```bash
talosctl reset --graceful=false --reboot --system-labels-to-wipe STATE --nodes 192.168.1.101
```

## Kubernetes Issues

### Pods Stuck in Pending State

If pods are stuck in pending state, check for resource constraints:

```bash
kubectl describe pod <pod-name> -n <namespace>
```

Common reasons:
- Insufficient memory or CPU
- PersistentVolumeClaim not bound
- Node affinity/taints preventing scheduling

### Node Not Ready

If a node is showing as NotReady:

```bash
kubectl describe node <node-name>
```

Check Talos node status:

```bash
talosctl dmesg --nodes 192.168.1.101
```

## Networking Issues

### Services Not Accessible

If you can't access services:

1. Check if the service is running:
   ```bash
   kubectl get svc -A
   ```

2. Verify the pod is running:
   ```bash
   kubectl get pods -A | grep <service-name>
   ```

3. Check Cilium network connectivity:
   ```bash
   kubectl -n kube-system exec -it <cilium-pod-name> -- cilium status
   ```

## Storage Issues

### CubeFS Problems

If experiencing CubeFS issues:

1. Check the status of CubeFS pods:
   ```bash
   kubectl get pods -n cubefs
   ```

2. Verify the volumes are created properly:
   ```bash
   kubectl get pv
   kubectl get pvc -A
   ```

3. Check CubeFS logs:
   ```bash
   kubectl logs -n cubefs <cubefs-pod-name>
   ```

## Flux CD Issues

### Flux Not Reconciling

If Flux is not applying your changes:

1. Check Flux status:
   ```bash
   flux get kustomizations
   ```

2. Check for reconciliation errors:
   ```bash
   flux get kustomizations --all-namespaces
   ```

3. Check the Flux logs:
   ```bash
   kubectl logs -n flux-system deployment/source-controller
   kubectl logs -n flux-system deployment/kustomize-controller
   ```

## Kube-vip Issues

### Virtual IP Not Working

If the kube-vip virtual IP is not functioning correctly:

1. Check if kube-vip pods are running on the control plane:
   ```bash
   kubectl get pods -n kube-system | grep kube-vip
   ```

2. Check kube-vip logs:
   ```bash
   kubectl logs -n kube-system <kube-vip-pod-name>
   ```

3. Verify ARP configuration on the control plane node:
   ```bash
   talosctl --nodes 192.168.1.101 netstat -rn
   ```

4. Test if the VIP responds to ping:
   ```bash
   ping 192.168.1.100
   ```

5. Verify connectivity to the Kubernetes API through the VIP:
   ```bash
   curl -k https://192.168.1.100:6443/version
   ```

## Hardware-Specific Issues

### Mac Mini VM Problems

If experiencing issues with the Mac Mini VM:

1. Ensure the VM has enough resources allocated
2. Check if virtualization extensions are enabled
3. Consider reinstalling the Talos ISO to the VM
4. Verify network connectivity between the VM and other nodes

### Recovering from Power Failure

After a power outage:

1. Start all nodes, beginning with the control plane (Ryzen)
2. Wait for the control plane to be fully booted before starting worker nodes
3. Check the cluster status:
   ```bash
   kubectl get nodes
   talosctl --nodes 192.168.1.101 health
   ```
