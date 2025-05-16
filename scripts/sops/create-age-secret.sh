#!/bin/bash


set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for required files
KEY_FILE="./.sops/age.agekey"
if [ ! -f "$KEY_FILE" ]; then
    echo -e "${RED}AGE key not found at $KEY_FILE${NC}"
    echo -e "${YELLOW}Please generate a key first with scripts/sops/generate-key.sh${NC}"
    exit 1
fi

# Check for sops
if ! command -v sops &> /dev/null; then
    echo -e "${RED}sops could not be found. Please install it first${NC}"
    exit 1
fi

echo -e "${BLUE}Generating SOPS AGE secret for Flux...${NC}"

# Create the flux-system directory if it doesn't exist
FLUX_DIR="./cluster/flux/flux-system"
mkdir -p $FLUX_DIR

# Create the age secret file
AGE_SECRET="$FLUX_DIR/age-secret.yaml"

cat > $AGE_SECRET << EOF
apiVersion: v1
kind: Secret
metadata:
    name: sops-age
    namespace: flux-system
stringData:
    age.agekey: $(cat $KEY_FILE)
EOF

echo -e "${GREEN}Created $AGE_SECRET${NC}"
echo -e "${YELLOW}Warning: This file contains your private key and should be encrypted!${NC}"
echo -e "${BLUE}Encrypting the age secret...${NC}"

# Encrypt the file
./scripts/sops/encrypt.sh "$AGE_SECRET"

echo -e "${GREEN}Age secret is now encrypted and ready for Flux!${NC}"
echo -e "${BLUE}You can now commit this to your repository.${NC}"
