# Scripts Directory

This directory contains all operational scripts for the SafeWork project, organized by purpose.

## Directory Structure

```
scripts/
├── deploy/       # Deployment scripts
├── setup/        # Setup and configuration scripts
└── utils/        # Utility scripts
```

## Deploy Scripts

Located in `scripts/deploy/`:
- `deploy-main.sh` - Primary deployment script (formerly deploy-single.sh)
- `deploy-production.sh` - Production deployment
- `deploy-complete.sh` - Complete deployment with all services
- `deploy-with-watchtower.sh` - Deployment with auto-update
- `deploy.sh` - Alternative deployment method
- `direct-deploy.sh` - Direct Docker deployment
- `quick-docker-deploy.sh` - Quick Docker deployment

## Setup Scripts

Located in `scripts/setup/`:
- `setup-argocd-token.sh` - ArgoCD token configuration
- `setup-claude-oauth.sh` - Claude OAuth setup
- `setup-claude-code-runner.sh` - Claude Code runner setup
- `setup-github-secrets.template.sh` - GitHub secrets template
- `install-k8s.sh` - Kubernetes installation
- `install-k8s-server.sh` - K8s server installation
- `k8s-server-install.sh` - Alternative K8s installation

## Utils Scripts

Located in `scripts/utils/`:
- Various utility and helper scripts

## Usage

All scripts should be run from the project root:

```bash
# Example deployment
./scripts/deploy/deploy-main.sh

# Example setup
./scripts/setup/setup-github-secrets.sh
```