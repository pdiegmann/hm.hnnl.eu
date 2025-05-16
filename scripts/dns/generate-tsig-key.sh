#!/bin/bash
# Script to generate TSIG key for BIND9 and external-dns integration

set -e

# Generate TSIG key
TSIG_KEY=$(head -c 32 /dev/urandom | base64)
CURRENT_DIR=$(pwd)
HOMELAB_ROOT=$(git rev-parse --show-toplevel || echo "$CURRENT_DIR")

if [ -z "$HOMELAB_ROOT" ]; then
  echo "Error: Could not determine homelab root directory."
  exit 1
fi

# Create SOPS secret for the TSIG key
cat > "$HOMELAB_ROOT/cluster/core/bind9/tsig-key-secret.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: bind9-tsig-key
  namespace: dns
stringData:
  tsig-key: "$TSIG_KEY"
EOF

# Update BIND9 ConfigMap to include TSIG key configuration
BIND_CONF="$HOMELAB_ROOT/cluster/core/bind9/configmap.yaml"

# Backup original ConfigMap
cp "$BIND_CONF" "$BIND_CONF.bak"

# Add TSIG key configuration to named.conf
sed -i '' '/listen-on-v6 { any; };/a\\n      // TSIG key for external-dns\n      key "externaldns-key" {\n        algorithm hmac-sha256;\n        secret "'$TSIG_KEY'";\n      };\n' "$BIND_CONF"

# Add zone update configuration for external-dns
sed -i '' '/allow-update { none; };/d' "$BIND_CONF"
sed -i '' '/type master;/a\\n      allow-update { key "externaldns-key"; };' "$BIND_CONF"

echo "TSIG key generated and configuration updated."
echo "Secret created at: $HOMELAB_ROOT/cluster/core/bind9/tsig-key-secret.yaml"
echo "Please encrypt this file with SOPS before committing."

# Add the new secret to the kustomization.yaml
sed -i '' '/configmap.yaml/a\\n  - tsig-key-secret.yaml' "$HOMELAB_ROOT/cluster/core/bind9/kustomization.yaml"

echo "Kustomization file updated to include the TSIG key secret."
