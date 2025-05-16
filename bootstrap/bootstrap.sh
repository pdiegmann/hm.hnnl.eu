#!/bin/bash

set -e

# Set up variables
REPO_DIR=$(pwd)
GITHUB_USER="your-github-username"
GITHUB_REPO="homelab"
GITHUB_BRANCH="main"

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for required tools
echo -e "${BLUE}Checking for required tools...${NC}"
for cmd in kubectl talosctl flux; do
  if ! command -v $cmd &> /dev/null; then
    echo -e "${RED}Error: $cmd is not installed.${NC}"
    exit 1
  fi
done

echo -e "${GREEN}All required tools are installed.${NC}"

# Bootstrap process
echo -e "${YELLOW}Starting bootstrap process...${NC}"

# 1. Apply Talos configurations
echo -e "${BLUE}Step 1: Applying Talos configurations${NC}"
read -p "Have you already generated Talos configurations? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${BLUE}Generating Talos configurations...${NC}"
  cd bootstrap/talos
  ./gen-config.sh
  cd $REPO_DIR
fi

echo -e "${BLUE}Applying Talos configurations to nodes...${NC}"
read -p "Continue with applying configurations to nodes? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Get node IPs
  read -p "First control plane IP (Ryzen): " CP1_IP
  read -p "Second control plane IP (Intel): " CP2_IP 
  read -p "Third control plane IP (Mac Mini): " CP3_IP
  
  echo -e "${BLUE}Applying control plane configurations...${NC}"
  talosctl apply-config --insecure --nodes $CP1_IP --file infrastructure/talos/controlplane/talos-cp1.yaml
  talosctl apply-config --insecure --nodes $CP2_IP --file infrastructure/talos/controlplane/talos-cp2.yaml
  talosctl apply-config --insecure --nodes $CP3_IP --file infrastructure/talos/controlplane/talos-cp3.yaml
  
  echo -e "${GREEN}Talos configurations applied successfully!${NC}"
  
  # Bootstrap the cluster
  echo -e "${BLUE}Bootstrapping the cluster...${NC}"
  read -p "Continue with bootstrapping the cluster? [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    talosctl bootstrap --nodes $CP1_IP
    
    echo -e "${BLUE}Waiting for Kubernetes API to be available...${NC}"
    talosctl health --nodes $CP1_IP,$CP2_IP,$CP3_IP --wait-timeout 15m
    
    # Get kubeconfig
    echo -e "${BLUE}Retrieving kubeconfig...${NC}"
    talosctl kubeconfig --nodes $CP1_IP -f ./kubeconfig
    
    echo -e "${GREEN}Cluster bootstrapped successfully!${NC}"
    echo -e "${YELLOW}Kubeconfig has been saved to ./kubeconfig${NC}"
    
    export KUBECONFIG=$REPO_DIR/kubeconfig
    echo -e "${BLUE}Testing connection to Kubernetes...${NC}"
    kubectl get nodes
  fi
fi

# 2. Setup Flux CD
echo -e "${BLUE}Step 2: Setting up Flux CD${NC}"
read -p "Continue with setting up Flux CD? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Create Flux directories
  mkdir -p cluster/flux/flux-system
  
  # Create initial kustomization for flux
  mkdir -p cluster/flux
  
  cat > cluster/flux/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - flux-system
  - infrastructure
  - apps
EOF

  mkdir -p cluster/flux/infrastructure
  cat > cluster/flux/infrastructure/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - namespace.yaml
  - sources
  - controllers
EOF

  mkdir -p cluster/flux/infrastructure/sources
  cat > cluster/flux/infrastructure/sources/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - helm-repositories.yaml
EOF

  cat > cluster/flux/infrastructure/namespace.yaml << EOF
apiVersion: v1
kind: Namespace
metadata:
  name: infrastructure
EOF

  # Setup Flux bootstrap
  echo -e "${BLUE}Bootstrapping Flux...${NC}"
  read -p "GitHub username for Flux: " GITHUB_USER
  read -p "GitHub repository name [${GITHUB_REPO}]: " REPO_INPUT
  GITHUB_REPO=${REPO_INPUT:-$GITHUB_REPO}
  
  flux bootstrap github \
    --owner=${GITHUB_USER} \
    --repository=${GITHUB_REPO} \
    --branch=${GITHUB_BRANCH} \
    --path=cluster/flux \
    --personal
    
  echo -e "${GREEN}Flux bootstrapped successfully!${NC}"
fi

# 3. Setup core components
echo -e "${BLUE}Step 3: Setting up core components${NC}"
read -p "Continue with setting up core components? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo -e "${BLUE}Creating core component manifests...${NC}"
  
  # Create directories
  mkdir -p cluster/core/kube-system
  mkdir -p cluster/core/cubefs
  mkdir -p cluster/core/kubevirt
  
  # Create kustomization file
  cat > cluster/core/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - kube-system
  - cubefs
  - kubevirt
EOF

  echo -e "${GREEN}Core component manifests created!${NC}"
  echo -e "${YELLOW}You'll need to add actual manifests for each component.${NC}"
fi

echo -e "${GREEN}Bootstrap process completed!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Push the repository to GitHub"
echo -e "2. Flux will reconcile the repository and deploy components"
echo -e "3. Add your applications to the 'cluster/apps' directory"
echo -e "${YELLOW}See docs/getting-started.md for detailed instructions${NC}"
