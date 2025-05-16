#!/bin/bash

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Mac Mini M1 VM Setup Helper${NC}"
echo -e "${YELLOW}This script will help you prepare for running Talos in a VM on the Mac Mini${NC}"

# Check for required tools
echo -e "${BLUE}Checking for required tools...${NC}"
if ! command -v wget &> /dev/null; then
  echo -e "${RED}wget is not installed. Please install it with brew install wget${NC}"
  exit 1
fi

# Create a directory for downloads
DOWNLOAD_DIR="$HOME/Downloads/talos-vm"
mkdir -p "$DOWNLOAD_DIR"
echo -e "${GREEN}Created download directory: $DOWNLOAD_DIR${NC}"

# Download the latest Talos ISO
echo -e "${BLUE}Downloading the latest Talos ISO...${NC}"
TALOS_VERSION="v1.6.4"
ISO_URL="https://github.com/siderolabs/talos/releases/download/${TALOS_VERSION}/metal-amd64.iso"
ISO_PATH="$DOWNLOAD_DIR/talos-${TALOS_VERSION}.iso"

wget -O "$ISO_PATH" "$ISO_URL"
echo -e "${GREEN}Downloaded Talos ISO to: $ISO_PATH${NC}"

# Display instructions
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Install UTM from https://mac.getutm.app/"
echo -e "2. Create a new VM with the following settings:"
echo -e "   - Type: Linux"
echo -e "   - Architecture: ARM64 (for M1)"
echo -e "   - Memory: 8-12GB"
echo -e "   - CPU Cores: 4-6"
echo -e "   - Disk: 40GB+"
echo -e "   - Network: Bridged"
echo -e "3. Mount the ISO at: $ISO_PATH"
echo -e "4. Start the VM and note the IP address"
echo -e "5. Apply the Talos configuration using:"
echo -e "   talosctl apply-config --insecure --nodes <VM_IP> --file infrastructure/talos/workers/talos-worker2.yaml"
echo -e ""
echo -e "${BLUE}See bootstrap/vm/mac-mini-utm-setup.md for more detailed instructions${NC}"
