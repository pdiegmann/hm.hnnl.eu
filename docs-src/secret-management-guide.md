# Secret Management Guide

This guide provides best practices for managing secrets in your homelab Kubernetes cluster.

## Secret Management with SOPS and AGE

### Initial Setup

1. **Generate AGE Key Pair**

```bash
# Install age if not already installed
# On Ubuntu/Debian:
# sudo apt install age

# Generate a key pair
age-keygen -o age.agekey

# The output will show your public key, which should be added to .sops.yaml
# The private key is stored in the age.agekey file
```

2. **Update .sops.yaml**

Replace the placeholder AGE public key in `.sops.yaml` with your actual public key:

```yaml
creation_rules:
  # Encrypt with AGE
  - path_regex: .*.ya?ml
    encrypted_regex: ^(data|stringData)$
    age: >-
      age1your-actual-public-key-here
```

3. **Store Private Key Securely**

- **NEVER** commit your private key to the repository
- Store the private key securely (e.g., password manager, secure USB drive)
- Consider using a key management system for production environments

### Encrypting Secrets

1. **Generate Secret Values**

Use the provided `generate-secret-values.sh` script to create secure random values:

```bash
./scripts/generate-secret-values.sh
```

2. **Apply Values to Templates**

Use the generated values to replace placeholders in template files:

```bash
# Example for manual replacement
export SOPS_AGE_KEY_FILE=path/to/age.agekey
envsubst < cluster/secrets/templates/zitadel-secrets-template.yaml > cluster/secrets/zitadel/zitadel-secrets.yaml
```

3. **Encrypt Secrets**

```bash
# Set the AGE key file location
export SOPS_AGE_KEY_FILE=path/to/age.agekey

# Encrypt the secret
sops --encrypt --in-place cluster/secrets/zitadel/zitadel-secrets.yaml
```

### Viewing and Editing Encrypted Secrets

```bash
# View decrypted content
sops --decrypt cluster/secrets/zitadel/zitadel-secrets.yaml

# Edit in-place
sops cluster/secrets/zitadel/zitadel-secrets.yaml
```

### Secret Rotation

Regularly rotate secrets to maintain security:

1. Generate new secret values
2. Update and re-encrypt secret files
3. Apply the changes to your cluster

## Best Practices

1. **Use Templates**: Store template files with placeholders, not actual secrets
2. **Automate Generation**: Use scripts to generate secure random values
3. **Encrypt Before Commit**: Always encrypt secrets before committing to the repository
4. **Limit Access**: Restrict access to the AGE private key
5. **Regular Rotation**: Establish a schedule for rotating sensitive credentials
6. **Audit**: Regularly audit who has access to secrets and when they were last rotated

## Flux Integration

Flux automatically decrypts SOPS-encrypted secrets when applying them to the cluster, as long as the private key is available to Flux.

For more information, see the [Flux documentation on Mozilla SOPS](https://fluxcd.io/flux/guides/mozilla-sops/).
