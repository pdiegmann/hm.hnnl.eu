#!/bin/bash


set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for age-keygen
if ! command -v age-keygen &> /dev/null; then
    echo -e "${RED}age-keygen could not be found. Please install it first${NC}"
    echo -e "${BLUE}You can install it with:${NC}"
    echo -e "  - macOS: brew install age"
    echo -e "  - Linux: various package managers or download from https://github.com/FiloSottile/age${NC}"
    exit 1
fi

# Check for sops
if ! command -v sops &> /dev/null; then
    echo -e "${RED}sops could not be found. Please install it first${NC}"
    echo -e "${BLUE}You can install it with:${NC}"
    echo -e "  - macOS: brew install sops"
    echo -e "  - Linux: various package managers or download from https://github.com/getsops/sops${NC}"
    exit 1
fi

echo -e "${BLUE}Generating a new AGE key for SOPS encryption...${NC}"

# Create the sops directory if it doesn't exist
SOPS_DIR="./.sops"
mkdir -p $SOPS_DIR

# Generate a new age key
KEY_FILE="$SOPS_DIR/age.agekey"
if [ -f "$KEY_FILE" ]; then
    echo -e "${YELLOW}A key already exists at $KEY_FILE${NC}"
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Using existing key${NC}"
    else
        age-keygen -o $KEY_FILE
        echo -e "${GREEN}New AGE key generated at $KEY_FILE${NC}"
    fi
else
    age-keygen -o $KEY_FILE
    echo -e "${GREEN}New AGE key generated at $KEY_FILE${NC}"
fi

# Extract the public key
PUBLIC_KEY=$(grep "public key" $KEY_FILE | cut -d ":" -f 2 | tr -d ' ')

echo -e "${BLUE}Your AGE public key is:${NC} $PUBLIC_KEY"
echo -e "${YELLOW}Now update the .sops.yaml file with this public key${NC}"

# Update the .sops.yaml file
SOPS_CONFIG="./.sops.yaml"
if [ -f "$SOPS_CONFIG" ]; then
    echo -e "${BLUE}Updating $SOPS_CONFIG with your new public key...${NC}"
    sed -i'' -e "s|age: >-.*|age: >-\\n      $PUBLIC_KEY|" $SOPS_CONFIG
    echo -e "${GREEN}Updated $SOPS_CONFIG${NC}"
else
    echo -e "${YELLOW}$SOPS_CONFIG not found. Creating it...${NC}"
    cat > $SOPS_CONFIG << EOF
creation_rules:
  # Encrypt with AGE
  - path_regex: .*.ya?ml
    encrypted_regex: ^(data|stringData)$
    age: >-
      $PUBLIC_KEY
EOF
    echo -e "${GREEN}Created $SOPS_CONFIG${NC}"
fi

# Add to .gitignore to ensure the private key is not committed
GITIGNORE="./.gitignore"
if ! grep -q ".sops/age.agekey" $GITIGNORE 2>/dev/null; then
    echo -e "${BLUE}Adding .sops/age.agekey to .gitignore...${NC}"
    echo ".sops/age.agekey" >> $GITIGNORE
    echo -e "${GREEN}Updated .gitignore${NC}"
fi

echo -e "${GREEN}SOPS with AGE is now ready to use!${NC}"
echo -e "${YELLOW}Important: Keep your private key secure and back it up!${NC}"
echo -e "${BLUE}You can encrypt a file with:${NC}"
echo -e "  SOPS_AGE_KEY_FILE=$KEY_FILE sops --encrypt --in-place path/to/file.yaml"
echo -e "${BLUE}And decrypt with:${NC}"
echo -e "  SOPS_AGE_KEY_FILE=$KEY_FILE sops --decrypt path/to/file.yaml"
