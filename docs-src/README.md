# Homelab Documentation

This directory contains the documentation for the Homelab Kubernetes Cluster, using [MkDocs](https://www.mkdocs.org/) with the [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/) theme.

## Running Locally

To run the documentation locally:

1. Install the required packages:

```bash
pip install -r docs-src/requirements.txt
```

Or install them individually:

```bash
pip install mkdocs-material mkdocs-minify-plugin
```

2. Start the local documentation server:

```bash
cd docs-src
mkdocs serve
```

3. Open your browser and navigate to http://localhost:8000

Changes to the documentation will be automatically reflected in your browser.

## Structure

- `mkdocs.yml` - Main configuration file for MkDocs
- `docs/` - Documentation content
  - `index.md` - Homepage
  - `guide/` - User guides and tutorials
  - `components/` - Component-specific documentation
  - `reference/` - Reference materials
  - `img/` - Images and assets

## Building for Production

The documentation is automatically built and deployed to GitHub Pages when changes are pushed to the main branch. You can also build the documentation manually:

```bash
cd docs-src
mkdocs build
```

The built site will be in the `site/` directory.

## GitHub Pages Deployment

Deployment to GitHub Pages is handled automatically via GitHub Actions. The workflow configuration is in `.github/workflows/deploy-docs.yaml`.
