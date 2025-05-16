# UTM Configuration for Talos on Mac Mini M1

This guide will help you set up a virtual machine on your Mac Mini M1 for running Talos OS.

## Requirements

- Mac Mini with Apple M1 chip
- UTM (https://mac.getutm.app/) installed
- Talos OS ISO downloaded (https://github.com/siderolabs/talos/releases)

## VM Configuration

### Basic Settings

1. Open UTM and click "Create a New Virtual Machine"
2. Select "Virtualize"
3. Select "Linux"
4. Select "Other" as the Linux system
5. Set the following specifications:
   - Memory: 8-12 GB
   - CPU Cores: 4-6 (leave at least 2 cores for the macOS host)
   - Storage: 40+ GB

### Network Configuration

1. In the VM settings, select "Network"
2. Change the network mode to "Bridged"
3. Select your main network interface (typically en0)
4. Make sure the VM gets its own IP address on your network

### Boot Settings

1. In the VM settings, select "CD/DVD"
2. Click "Browse" and select the Talos OS ISO
3. Make sure the VM is set to boot from CD/DVD first

## Running the VM

1. Start the VM and let Talos boot
2. From your workstation, apply the Talos configuration using:
   ```bash
   talosctl apply-config --insecure --nodes <VM_IP> --file infrastructure/talos/workers/talos-worker2.yaml
   ```

3. Verify the node is joining your cluster:
   ```bash
   kubectl get nodes
   ```

## Tips for Performance

- Ensure the VM has enough resources (memory and CPU) to run Kubernetes workloads
- Use persistent storage for volumes that require good performance
- Consider adding a second virtual network adapter if you need to separate networks

## Troubleshooting

- If the VM fails to start, check if virtualization is enabled and functioning properly
- If Talos fails to join the cluster, verify network connectivity and firewall settings
- Check Talos logs using `talosctl logs --nodes <VM_IP>`
