#!/bin/bash

# This script generates secure random values for secrets
# and updates template files with these values
# Run this script from the root of the repository

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Generating secure values for secrets...${NC}"

# Function to generate a secure random string
generate_secure_string() {
  length=${1:-32}
  cat /dev/urandom | tr -dc 'a-zA-Z0-9!@#$%^&*()_+?><~' | head -c $length
}

# Create a temporary .env file with generated values
ENV_FILE=".env.secrets"

echo "# Generated secure values - DO NOT COMMIT THIS FILE" > $ENV_FILE
echo "# Use these values with the template files in cluster/secrets/templates" >> $ENV_FILE
echo "" >> $ENV_FILE

# Generate values for Zitadel
ZITADEL_MASTERKEY=$(generate_secure_string 32)
ZITADEL_DB_PASSWORD=$(generate_secure_string 24)
ZITADEL_ADMIN_PASSWORD=$(generate_secure_string 16)

echo "# Zitadel Secrets" >> $ENV_FILE
echo "ZITADEL_MASTERKEY=\"$ZITADEL_MASTERKEY\"" >> $ENV_FILE
echo "ZITADEL_DB_PASSWORD=\"$ZITADEL_DB_PASSWORD\"" >> $ENV_FILE
echo "ZITADEL_ADMIN_PASSWORD=\"$ZITADEL_ADMIN_PASSWORD\"" >> $ENV_FILE
echo "" >> $ENV_FILE

# Generate values for NetBird
NETBIRD_API_KEY=$(generate_secure_string 48)

echo "# NetBird Secrets" >> $ENV_FILE
echo "NETBIRD_API_KEY=\"$NETBIRD_API_KEY\"" >> $ENV_FILE
echo "" >> $ENV_FILE

echo -e "${GREEN}Secret values generated and saved to ${ENV_FILE}${NC}"
echo -e "${YELLOW}IMPORTANT: This file contains sensitive information. Do not commit it to your repository.${NC}"
echo -e "${BLUE}Use these values with the template files in cluster/secrets/templates${NC}"
echo -e "${BLUE}After replacing values, encrypt the files with SOPS before committing.${NC}"

echo -e "${GREEN}Secret generation complete!${NC}"
