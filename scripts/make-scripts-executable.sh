#!/bin/bash
# Helper script to make all scripts executable

# Make DNS scripts executable
chmod +x $(git rev-parse --show-toplevel)/scripts/dns/*.sh

echo "All scripts are now executable."
