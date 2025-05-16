# DNS and Access Configuration for Homelab - Implementation Summary

I've created a comprehensive dual-access system for your homelab that allows services to be accessible both locally (LAN) and externally (via NetBird). Here's a summary of what's been implemented:

## Components Created

1. **Bind9 DNS Server**
   - Setup as a Kubernetes deployment in the `dns` namespace
   - Configured to handle local DNS resolution for `local.hm.hnnl.eu`
   - Integrated with External-DNS for automatic DNS record management

2. **ExternalDNS Configuration**
   - Updated original ExternalDNS to handle external domain (`ext.hm.hnnl.eu`)
   - Created a second ExternalDNS instance for local domain (`local.hm.hnnl.eu`)
   - Set up selective targeting via annotations

3. **NetBird Integration**
   - Updated NetBird configuration to properly handle DNS
   - Ensures secure external access without exposing services to the internet

4. **Demo Application**
   - Created a demo deployment `dual-access-demo` that shows three access patterns:
     - Both local and external access
     - Local-only access
     - External-only access

5. **Automation Scripts**
   - `generate-tsig-key.sh`: Creates TSIG key for Bind9/ExternalDNS integration
   - `update-network-config.sh`: Updates network configuration with local IPs

6. **Documentation**
   - Detailed setup instructions in `docs-src/dns-access-setup.md`
   - Architecture diagram to visualize the system
   - Updated main README.md with new features

## How It Works

1. **Local Access Flow**:
   - Local clients use `local.hm.hnnl.eu` to access services
   - Bind9 resolves these domains to local Kubernetes service IPs
   - ExternalDNS-Local automatically updates Bind9 when services change

2. **External Access Flow**:
   - External clients (with NetBird installed) use `ext.hm.hnnl.eu`
   - Cloudflare DNS resolves these domains
   - NetBird creates a secure tunnel to access the services
   - No direct internet exposure of your services

3. **Service Configuration**:
   - Services control their accessibility via simple annotations:
     ```yaml
     annotations:
       external-dns.alpha.kubernetes.io/target-type: "both" # or "internal" or "external"
     ```

## Next Steps

To complete the setup, you'll need to:

1. Run the initialization scripts:
   ```bash
   bash scripts/make-scripts-executable.sh
   bash scripts/dns/update-network-config.sh
   bash scripts/dns/generate-tsig-key.sh
   ```

2. Encrypt the TSIG key with SOPS:
   ```bash
   sops --encrypt --in-place cluster/core/bind9/tsig-key-secret.yaml
   ```

3. Commit and push changes to your repository for Flux to apply them

4. Configure your local network devices to use the Bind9 DNS server (the IP address will be shown after running `update-network-config.sh`)

5. For external devices, ensure they have NetBird installed and properly configured

Everything is designed to work seamlessly with your existing Flux-based GitOps workflow. The system should automatically detect services and update DNS records accordingly, making it easy to add new applications.
