#!/bin/bash

# This script generates a TSIG key for BIND9/ExternalDNS integration
# Run this script from the root of the repository

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Generating TSIG key for BIND9/ExternalDNS integration...${NC}"

# Check if dnssec-keygen is installed
if ! command -v dnssec-keygen &> /dev/null; then
    echo -e "${RED}dnssec-keygen could not be found. Installing bind9utils...${NC}"
    sudo apt-get update
    sudo apt-get install -y bind9utils
fi

# Create temporary directory
TEMP_DIR=$(mktemp -d)
cd $TEMP_DIR

# Generate the key
KEY_NAME="externaldns-key"
echo -e "${BLUE}Generating key: ${KEY_NAME}${NC}"
dnssec-keygen -a HMAC-SHA256 -b 256 -n HOST -r /dev/urandom $KEY_NAME

# Extract the key
KEY_FILE=$(ls K${KEY_NAME}*.key)
KEY_VALUE=$(grep -v '^;' $KEY_FILE | cut -d ' ' -f 7)

echo -e "${GREEN}TSIG key generated successfully!${NC}"

# Create the Kubernetes secret
mkdir -p ../../cluster/core/bind9
cat > ../../cluster/core/bind9/tsig-key-secret.yaml << EOF
apiVersion: v1
kind: Secret
metadata:
  name: external-dns-tsig-key
  namespace: dns
type: Opaque
stringData:
  externaldns-key: "${KEY_VALUE}"
EOF

echo -e "${YELLOW}Secret created at: cluster/core/bind9/tsig-key-secret.yaml${NC}"
echo -e "${YELLOW}Remember to encrypt this file with SOPS:${NC}"
echo -e "${BLUE}sops --encrypt --in-place cluster/core/bind9/tsig-key-secret.yaml${NC}"

# Cleanup
cd - > /dev/null
rm -rf $TEMP_DIR

echo -e "${GREEN}TSIG key generation complete!${NC}"
