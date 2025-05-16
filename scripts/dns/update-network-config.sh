#!/bin/bash
# Script to update cluster with local network information

set -e

# Get the Node IP address
NODE_IP=$(hostname -I | awk '{print $1}')
# Set Bind9 IP - you can adjust this to your preferred fixed IP
BIND9_IP="$NODE_IP"  # You might want to make this a different IP in your MetalLB pool

CURRENT_DIR=$(pwd)
HOMELAB_ROOT=$(git rev-parse --show-toplevel || echo "$CURRENT_DIR")

if [ -z "$HOMELAB_ROOT" ]; then
  echo "Error: Could not determine homelab root directory."
  exit 1
fi

# Update Bind9 ConfigMap
CONFIG_MAP="$HOMELAB_ROOT/cluster/core/bind9/configmap.yaml"
sed -i '' "s/\${NODE_IP}/$NODE_IP/g" "$CONFIG_MAP"

# Create a ConfigMap with network information for Flux 
cat > "$HOMELAB_ROOT/cluster/config/network-config.yaml" << EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: network-config
  namespace: flux-system
data:
  NODE_IP: "$NODE_IP"
  BIND9_IP: "$BIND9_IP"
EOF

# Update External-DNS-Local with Bind9 IP
EXT_DNS_LOCAL="$HOMELAB_ROOT/cluster/core/external-dns-local/helmrelease.yaml"
sed -i '' "s/\${BIND9_IP}/$BIND9_IP/g" "$EXT_DNS_LOCAL"

# Update Bind9 HelmRelease with the IP
BIND9_HR="$HOMELAB_ROOT/cluster/core/bind9/helmrelease.yaml"
sed -i '' "s/\${BIND9_IP}/$BIND9_IP/g" "$BIND9_HR"

echo "Cluster configuration updated with:"
echo "Node IP: $NODE_IP"
echo "Bind9 IP: $BIND9_IP"
