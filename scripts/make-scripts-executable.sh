#!/bin/bash

# This script ensures all scripts in the repository are executable
# Run this script from the root of the repository

set -e

echo "Making scripts executable..."

# Find all .sh files in the repository and make them executable
find . -name "*.sh" -type f -exec chmod +x {} \;

echo "All scripts are now executable!"
