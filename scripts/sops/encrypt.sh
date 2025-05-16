#!/bin/bash


set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for sops
if ! command -v sops &> /dev/null; then
    echo -e "${RED}sops could not be found. Please install it first${NC}"
    echo -e "${BLUE}You can install it with:${NC}"
    echo -e "  - macOS: brew install sops"
    echo -e "  - Linux: various package managers or download from https://github.com/getsops/sops${NC}"
    exit 1
fi

# Ensure the AGE key exists
KEY_FILE="./.sops/age.agekey"
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}AGE key not found at $KEY_FILE${NC}"
    echo -e "${YELLOW}Please generate a key first with scripts/sops/generate-key.sh${NC}"
    exit 1
fi

# Check if a file was provided
if [ -z "$1" ]; then
    echo -e "${RED}No file specified${NC}"
    echo -e "${BLUE}Usage: $0 <file.yaml>${NC}"
    exit 1
fi

# Check if file exists
if [ ! -f "$1" ]; then
    echo -e "${RED}File not found: $1${NC}"
    exit 1
fi

echo -e "${BLUE}Encrypting file: $1${NC}"
SOPS_AGE_KEY_FILE=$KEY_FILE sops --encrypt --in-place "$1"
echo -e "${GREEN}File encrypted: $1${NC}"
echo -e "${YELLOW}You can safely commit this to git now${NC}"
