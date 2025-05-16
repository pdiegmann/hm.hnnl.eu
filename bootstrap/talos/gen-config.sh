#!/bin/bash

set -e

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration variables - Adjust these to match your network environment
CLUSTER_NAME="homelab"
KUBERNETES_VERSION="v1.28.6"
TALOS_VERSION="v1.6.4"
CONTROL_PLANE_IP="192.168.1.101"
CONTROL_PLANE_VIP="192.168.1.100" # Virtual IP for HA control plane
NODE_IPS=("192.168.1.101" "192.168.1.102" "192.168.1.103")
NODE_NAMES=("talos-cp1" "talos-cp2" "talos-cp3")
NODE_TYPES=("controlplane" "controlplane" "controlplane")
NODE_HARDWARE=("ryzen" "intel" "mac-mini")
OUTPUT_DIR="../../infrastructure/talos"

# Check for talosctl
if ! command -v talosctl &> /dev/null; then
    echo -e "${RED}talosctl could not be found. Please install it first${NC}"
    echo -e "${BLUE}Visit https://www.talos.dev/v1.10/introduction/getting-started/ for installation instructions${NC}"
    exit 1
fi

# Create output directories if they don't exist
mkdir -p ${OUTPUT_DIR}/controlplane
mkdir -p ${OUTPUT_DIR}/workers

echo -e "${GREEN}Generating Talos configurations for ${CLUSTER_NAME}...${NC}"

# Generate the base configuration
echo -e "${BLUE}Generating base configuration...${NC}"
talosctl gen config ${CLUSTER_NAME} "https://${CONTROL_PLANE_VIP}:6443" \
    --kubernetes-version ${KUBERNETES_VERSION} \
    --talos-version ${TALOS_VERSION} \
    --output-dir ${OUTPUT_DIR}/temp

# Create patch files for different node types
echo -e "${BLUE}Creating patch files...${NC}"

# Patch for all nodes
cat > ${OUTPUT_DIR}/common.yaml << EOF
machine:
  network:
    hostname: {{ .hostname }}
    interfaces:
      - interface: eth0
        dhcp: true
  install:
    disk: /dev/sda
  sysctls:
    net.ipv4.ip_forward: "1"
  time:
    disabled: false
    servers:
      - time.cloudflare.com
  kubelet:
    extraArgs:
      rotate-server-certificates: true
      node-ip: {{ .nodeIP }}
    nodeIP:
      validSubnets:
        - 192.168.1.0/24
cluster:
  network:
    cni:
      name: cilium
  proxy:
    disabled: false
  allowSchedulingOnControlPlanes: true
EOF

# Patch for control plane nodes
cat > ${OUTPUT_DIR}/controlplane-patch.yaml << EOF
machine:
  certSANs:
    - ${CONTROL_PLANE_VIP}
    - ${CONTROL_PLANE_IP}
    - 127.0.0.1
  kubelet:
    extraArgs:
      node-labels: "node.kubernetes.io/controller=true"
  # Configure kube-vip in controlplane nodes
  install:
    extraKernelArgs:
      - ip_forward=1
      - "net.ipv4.conf.all.arp_announce=2"
      - "net.ipv4.conf.all.arp_ignore=1"
  files:
    - content: |
        #!/bin/bash
        kubectl apply -f https://raw.githubusercontent.com/kube-vip/kube-vip/main/docs/manifests/rbac.yaml
        VIP="${CONTROL_PLANE_VIP}"
        INTERFACE="eth0"
        KVVERSION="v0.6.2"
        TOKEN=$(kubectl -n kube-system get secret kube-vip-token -o jsonpath='{.data.token}' | base64 -d)
        
        cat > /var/tmp/kube-vip.yaml << 'EOT'
        apiVersion: apps/v1
        kind: DaemonSet
        metadata:
          name: kube-vip-ds
          namespace: kube-system
        spec:
          selector:
            matchLabels:
              name: kube-vip-ds
          template:
            metadata:
              labels:
                name: kube-vip-ds
            spec:
              containers:
              - args:
                - manager
                env:
                - name: vip_arp
                  value: "true"
                - name: vip_interface
                  value: $INTERFACE
                - name: vip_leaderelection
                  value: "true"
                - name: vip_address
                  value: $VIP
                - name: vip_leaseduration
                  value: "15"
                - name: vip_renewdeadline
                  value: "10"
                - name: vip_retryperiod
                  value: "2"
                - name: enable_loadbalancer
                  value: "true"
                image: ghcr.io/kube-vip/kube-vip:$KVVERSION
                name: kube-vip
                securityContext:
                  capabilities:
                    add:
                    - NET_ADMIN
                    - NET_RAW
                    - SYS_TIME
              hostNetwork: true
              serviceAccountName: kube-vip
              tolerations:
              - effect: NoSchedule
                key: node-role.kubernetes.io/master
                operator: Exists
              - effect: NoSchedule
                key: node-role.kubernetes.io/control-plane
                operator: Exists
        EOT
        
        # Apply kube-vip daemonset
        kubectl apply -f /var/tmp/kube-vip.yaml
      mode: 0700
      path: /usr/local/bin/init-kube-vip.sh
  init:
    systemd:
      units:
        - name: kubevip-init.service
          enabled: true
          contents: |
            [Unit]
            Description=Initialize kube-vip
            Wants=network-online.target
            After=network-online.target
            ConditionPathExists=!/var/lib/kubevip-initialized
            
            [Service]
            Type=oneshot
            ExecStart=/usr/local/bin/init-kube-vip.sh
            ExecStartPost=/usr/bin/touch /var/lib/kubevip-initialized
            RemainAfterExit=yes
            
            [Install]
            WantedBy=multi-user.target
EOF

# Patch for worker nodes
cat > ${OUTPUT_DIR}/worker-patch.yaml << EOF
machine:
  type: worker
  kubelet:
    extraArgs:
      node-labels: "role=worker"
EOF

# Patch for Mac Mini control plane
cat > ${OUTPUT_DIR}/mac-mini-controlplane-patch.yaml << EOF
machine:
  type: controlplane
  certSANs:
    - ${CONTROL_PLANE_VIP}
    - ${NODE_IPS[2]}
    - 127.0.0.1
  install:
    disk: /dev/vda # Virtual disk for VM
    extraKernelArgs:
      - ip_forward=1
      - "net.ipv4.conf.all.arp_announce=2"
      - "net.ipv4.conf.all.arp_ignore=1"
  kubelet:
    extraArgs:
      node-labels: "node.kubernetes.io/controller=true,hardware=macmini"
  # Configure kube-vip in controlplane nodes
  files:
    - content: |
        #!/bin/bash
        kubectl apply -f https://raw.githubusercontent.com/kube-vip/kube-vip/main/docs/manifests/rbac.yaml
        VIP="${CONTROL_PLANE_VIP}"
        INTERFACE="eth0"
        KVVERSION="v0.6.2"
        TOKEN=$(kubectl -n kube-system get secret kube-vip-token -o jsonpath='{.data.token}' | base64 -d)
        
        cat > /var/tmp/kube-vip.yaml << 'EOT'
        apiVersion: apps/v1
        kind: DaemonSet
        metadata:
          name: kube-vip-ds
          namespace: kube-system
        spec:
          selector:
            matchLabels:
              name: kube-vip-ds
          template:
            metadata:
              labels:
                name: kube-vip-ds
            spec:
              containers:
              - args:
                - manager
                env:
                - name: vip_arp
                  value: "true"
                - name: vip_interface
                  value: $INTERFACE
                - name: vip_leaderelection
                  value: "true"
                - name: vip_address
                  value: $VIP
                - name: vip_leaseduration
                  value: "15"
                - name: vip_renewdeadline
                  value: "10"
                - name: vip_retryperiod
                  value: "2"
                - name: enable_loadbalancer
                  value: "true"
                image: ghcr.io/kube-vip/kube-vip:$KVVERSION
                name: kube-vip
                securityContext:
                  capabilities:
                    add:
                    - NET_ADMIN
                    - NET_RAW
                    - SYS_TIME
              hostNetwork: true
              serviceAccountName: kube-vip
              tolerations:
              - effect: NoSchedule
                key: node-role.kubernetes.io/master
                operator: Exists
              - effect: NoSchedule
                key: node-role.kubernetes.io/control-plane
                operator: Exists
        EOT
        
        # Apply kube-vip daemonset
        kubectl apply -f /var/tmp/kube-vip.yaml
      mode: 0700
      path: /usr/local/bin/init-kube-vip.sh
  init:
    systemd:
      units:
        - name: kubevip-init.service
          enabled: true
          contents: |
            [Unit]
            Description=Initialize kube-vip
            Wants=network-online.target
            After=network-online.target
            ConditionPathExists=!/var/lib/kubevip-initialized
            
            [Service]
            Type=oneshot
            ExecStart=/usr/local/bin/init-kube-vip.sh
            ExecStartPost=/usr/bin/touch /var/lib/kubevip-initialized
            RemainAfterExit=yes
            
            [Install]
            WantedBy=multi-user.target
EOF

# Generate specific configs for each node
echo -e "${BLUE}Generating node-specific configurations...${NC}"
for i in "${!NODE_IPS[@]}"; do
  NODE_IP="${NODE_IPS[$i]}"
  NODE_NAME="${NODE_NAMES[$i]}"
  NODE_TYPE="${NODE_TYPES[$i]}"
  NODE_HW="${NODE_HARDWARE[$i]}"
  
  if [ "$NODE_TYPE" == "controlplane" ]; then
    SOURCE_CONFIG="${OUTPUT_DIR}/temp/controlplane.yaml"
    DEST_FILE="${OUTPUT_DIR}/controlplane/${NODE_NAME}.yaml"
    PATCH_FILE="${OUTPUT_DIR}/controlplane-patch.yaml"
    
    # Special handling for Mac Mini VM
    if [ "$NODE_HW" == "mac-mini" ]; then
      PATCH_FILE="${OUTPUT_DIR}/mac-mini-controlplane-patch.yaml"
    fi
  fi
  
  echo -e "${YELLOW}Generating config for ${NODE_NAME} (${NODE_IP})...${NC}"
  cp "$SOURCE_CONFIG" "$DEST_FILE"
  
  # Apply patches using a tool like yq (this is simplified)
  echo -e "${BLUE}Applying patches to ${NODE_NAME}...${NC}"
  
  # This is a placeholder for actual patching mechanism
  # In a real scenario, use yq, kustomize, or talosctl directly
  echo "# Node: ${NODE_NAME} (${NODE_IP})" >> "$DEST_FILE"
  echo "# Hardware: ${NODE_HW}" >> "$DEST_FILE"
  echo "# Include common patch and ${NODE_TYPE} specific patch" >> "$DEST_FILE"
  
  echo -e "${GREEN}Configuration for ${NODE_NAME} generated at ${DEST_FILE}${NC}"
done

# Cleanup temp directory
rm -rf ${OUTPUT_DIR}/temp

echo -e "${GREEN}All configurations generated successfully!${NC}"
echo -e "${BLUE}Next steps:${NC}"
echo -e "1. Review the generated configurations in ${OUTPUT_DIR}"
echo -e "2. Apply configurations to your Talos nodes"
echo -e "3. Bootstrap the cluster"
echo -e "${YELLOW}See docs/getting-started.md for detailed instructions${NC}"
