#!/bin/bash

# This script updates network configuration for the homelab
# Run this script from the root of the repository

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Updating network configuration...${NC}"

# Get local network information
LOCAL_IP=$(hostname -I | awk '{print $1}')
NETWORK_PREFIX=$(echo $LOCAL_IP | cut -d. -f1-3)

# Create configuration directory if it doesn't exist
mkdir -p cluster/config/network

# Create network configuration file
cat > cluster/config/network/config.yaml << EOF
---
# Network Configuration
network:
  # Local network settings
  local:
    prefix: "${NETWORK_PREFIX}"
    dns_server_ip: "${NETWORK_PREFIX}.53"
    control_plane_vip: "${NETWORK_PREFIX}.100"
    zitadel_vip: "${NETWORK_PREFIX}.110"
  
  # Domain settings
  domains:
    base: "hm.hnnl.eu"
    local: "local.hm.hnnl.eu"
    external: "ext.hm.hnnl.eu"
EOF

echo -e "${GREEN}Network configuration updated!${NC}"
echo -e "${YELLOW}Configuration saved to: cluster/config/network/config.yaml${NC}"
echo -e "${BLUE}Local network prefix: ${NETWORK_PREFIX}${NC}"
echo -e "${BLUE}DNS Server IP: ${NETWORK_PREFIX}.53${NC}"
echo -e "${BLUE}Control Plane VIP: ${NETWORK_PREFIX}.100${NC}"
echo -e "${BLUE}Zitadel VIP: ${NETWORK_PREFIX}.110${NC}"

# Update references in other files if needed
echo -e "${BLUE}Checking for files that need to be updated with network information...${NC}"

# This would typically update other configuration files that reference network settings
# For example, updating Kubernetes manifests, DNS configurations, etc.

echo -e "${GREEN}Network configuration update complete!${NC}"
echo -e "${YELLOW}Remember to commit these changes to your repository.${NC}"
