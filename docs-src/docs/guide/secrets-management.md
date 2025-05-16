# Using SOPS for Secret Management

This guide explains how to use SOPS (Secrets OPerationS) to securely manage Kubernetes secrets in your homelab repository.

## Prerequisites

- Install SOPS: [https://github.com/getsops/sops#1-download-the-binary](https://github.com/getsops/sops#1-download-the-binary)
- Install age: [https://github.com/FiloSottile/age#installation](https://github.com/FiloSottile/age#installation)

## Setup

1. Generate an age key pair:

```bash
# Run the script to generate a new AGE key
./scripts/sops/generate-key.sh
```

This script:
- Creates a new age key pair in the `.sops/age.agekey` file
- Updates the `.sops.yaml` file with the public key
- Adds the private key to `.gitignore` to prevent it from being committed

2. Save your private key somewhere safe (e.g., password manager or secure backup)

## Creating and Managing Secrets

### 1. Create a Secret Template

Create a YAML file with your Kubernetes secret using the standard format:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-secret
  namespace: my-namespace
type: Opaque
stringData:
  username: admin
  password: my-password
```

### 2. Encrypt the Secret

Encrypt the secret using SOPS:

```bash
# Use the helper script
./scripts/sops/encrypt.sh path/to/secret.yaml

# Or manually
SOPS_AGE_KEY_FILE=./.sops/age.agekey sops --encrypt --in-place path/to/secret.yaml
```

The encrypted file will look something like:

```yaml
apiVersion: v1
kind: Secret
metadata:
    name: my-secret
    namespace: my-namespace
type: Opaque
stringData:
    username: ENC[AES256_GCM,data:kTkD1uM=,iv:epW3...,tag:tGr0...,type:str]
    password: ENC[AES256_GCM,data:tzjPpFg/TrHH,iv:J+qV...,tag:Qy1d...,type:str]
sops:
    kms: []
    gcp_kms: []
    azure_kv: []
    hc_vault: []
    age:
        - recipient: age1...
          enc: |
            ...
    lastmodified: "2023-04-26T09:25:21Z"
    mac: ENC[AES256_GCM,data:cPkD...,iv:nrN/...,tag:bVH4...,type:str]
    pgp: []
    unencrypted_suffix: _unencrypted
    version: 3.7.3
```

### 3. View or Decrypt Secrets

To view a secret without creating a file:

```bash
# Use the helper script
./scripts/sops/decrypt.sh path/to/encrypted-secret.yaml

# Or manually
SOPS_AGE_KEY_FILE=./.sops/age.agekey sops --decrypt path/to/encrypted-secret.yaml
```

To save a decrypted file:

```bash
# Using the script
./scripts/sops/decrypt.sh path/to/encrypted-secret.yaml --stdout > decrypted.yaml

# Or manually
SOPS_AGE_KEY_FILE=./.sops/age.agekey sops --decrypt path/to/encrypted-secret.yaml > decrypted.yaml
```

## Using with Flux CD

Flux can automatically decrypt SOPS encrypted secrets when deploying to Kubernetes.

1. Create a Kubernetes secret with your AGE key:

```bash
cat << EOF > ./cluster/flux/flux-system/age-secret.yaml
apiVersion: v1
kind: Secret
metadata:
    name: sops-age
    namespace: flux-system
stringData:
    age.agekey: $(cat ./.sops/age.agekey)
EOF

# Encrypt this secret too!
./scripts/sops/encrypt.sh ./cluster/flux/flux-system/age-secret.yaml
```

2. Tell Flux to use SOPS decryption:

```yaml
# In cluster/flux/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - flux-system
  - sources
  - core
patchesStrategicMerge:
  - patches/kustomize-controller.yaml
```

```yaml
# In cluster/flux/patches/kustomize-controller.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kustomize-controller
  namespace: flux-system
spec:
  template:
    spec:
      containers:
      - name: manager
        env:
        - name: SOPS_AGE_KEY_FILE
          value: /etc/fluxcd/keys/age.agekey
        volumeMounts:
        - name: sops-age
          mountPath: /etc/fluxcd/keys
          readOnly: true
      volumes:
      - name: sops-age
        secret:
          secretName: sops-age
          defaultMode: 0400
```

3. Add encrypted secrets to your repository and commit them

## Best Practices

1. **Never commit unencrypted secrets** to the Git repository
2. **Backup your age key** in a secure location
3. **Use multiple keys** for different environments or teams
4. **Rotate keys** periodically for better security
5. **Store templates** separately from encrypted secrets

## Troubleshooting

- **Error: "failed to get the data key"**: You might be using the wrong key. Ensure your AGE key file contains the right private key.
- **Error: "could not find common data"**: The file might not be a valid SOPS encrypted file.

## Additional Resources

- [SOPS Documentation](https://github.com/getsops/sops)
- [Flux SOPS Integration](https://fluxcd.io/flux/guides/mozilla-sops/)
- [AGE Encryption Tool](https://github.com/FiloSottile/age)
