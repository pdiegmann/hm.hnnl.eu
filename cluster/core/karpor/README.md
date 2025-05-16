# Karpor - Kubernetes Visualization and Intelligence

This directory contains the Kubernetes manifests for deploying [Karpor](https://github.com/KusionStack/karpor) to the homelab cluster.

## Overview

Karpor is an intelligence and visualization tool for Kubernetes that brings advanced Search, Insight, and AI capabilities to your cluster.

## Components

- **Karpor Server**: Backend API server that provides REST APIs to serve the dashboard
- **Karpor Syncer**: Synchronizes cluster resources in real-time
- **ElasticSearch**: Stores synchronized resources and user data
- **ETCD**: Storage for the Karpor Server

## Configuration

The deployment is managed via a HelmRelease that pulls from the official KusionStack Helm repository.

## Usage

Once deployed, Karpor is accessible at: http://karpor.${CLUSTER_DOMAIN}

For more details, see the [Karpor documentation](../../../docs-src/docs/components/karpor.md).

## Troubleshooting

If Karpor is not working as expected:

1. Check the Karpor pods are running:
   ```bash
   kubectl get pods -n karpor
   ```

2. View logs for the server component:
   ```bash
   kubectl logs -n karpor -l app=karpor-server
   ```

3. Verify the ElasticSearch pod is healthy:
   ```bash
   kubectl get pods -n karpor -l app=elasticsearch
   ```
