#!/bin/bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if KUBECONFIG is set
if [ -z "$KUBECONFIG" ]; then
  if [ -f "./kubeconfig" ]; then
    export KUBECONFIG="$(pwd)/kubeconfig"
    echo -e "${BLUE}Using local kubeconfig file${NC}"
  else
    echo -e "${RED}KUBECONFIG not set and no local kubeconfig file found${NC}"
    echo -e "${YELLOW}You can set it with: export KUBECONFIG=/path/to/kubeconfig${NC}"
    exit 1
  fi
fi

# Get nodes
echo -e "${BLUE}Checking node status...${NC}"
kubectl get nodes -o wide

# Get pods status
echo -e "\n${BLUE}Checking pod status across all namespaces...${NC}"
kubectl get pods -A

# Get Flux status if installed
echo -e "\n${BLUE}Checking Flux status...${NC}"
if kubectl get ns flux-system &>/dev/null; then
  kubectl get kustomizations -A
  echo -e "\n${BLUE}Flux sources:${NC}"
  kubectl get sources -A
else
  echo -e "${YELLOW}Flux not installed yet${NC}"
fi

# Check storage status
echo -e "\n${BLUE}Checking storage status...${NC}"
if kubectl get ns cubefs &>/dev/null; then
  echo -e "${BLUE}CubeFS pods:${NC}"
  kubectl get pods -n cubefs
  echo -e "\n${BLUE}Storage classes:${NC}"
  kubectl get sc
  echo -e "\n${BLUE}Persistent volumes:${NC}"
  kubectl get pv
else
  echo -e "${YELLOW}CubeFS not installed yet${NC}"
fi

# Check kube-vip status
echo -e "\n${BLUE}Checking kube-vip status...${NC}"
kubectl get pods -n kube-system -l name=kube-vip || echo -e "${YELLOW}kube-vip not installed yet${NC}"
echo -e "\n${BLUE}Checking virtual IP accessibility...${NC}"
ping -c 1 192.168.1.100 &>/dev/null && echo -e "${GREEN}Virtual IP is responding${NC}" || echo -e "${RED}Virtual IP is not responding${NC}"

# Check etcd status
echo -e "\n${BLUE}Checking etcd health...${NC}"
kubectl get pods -n kube-system -l component=etcd
echo -e "\n${BLUE}Checking etcd cluster health...${NC}"
ETCD_POD=$(kubectl get pods -n kube-system -l component=etcd -o name | head -1)
if [ -n "$ETCD_POD" ]; then
  kubectl -n kube-system exec $ETCD_POD -- etcdctl endpoint health --cluster
else
  echo -e "${YELLOW}No etcd pod found${NC}"
fi

echo -e "\n${GREEN}Cluster status check complete${NC}"
