# Deployment Scripts

This directory contains the main deployment scripts for SafeWork.

## Main Scripts

- `deploy-main.sh` - Primary deployment script (previously deploy-single.sh)
- `deploy.sh` - Alternative deployment method
- `deploy-production.sh` - Production deployment script
- `deploy-complete.sh` - Complete deployment with all services
- `deploy-with-watchtower.sh` - Deployment with auto-update via Watchtower

## Usage

The main deployment method is:

```bash
./scripts/deploy/deploy-main.sh
```

For production deployment:

```bash
./scripts/deploy/deploy-production.sh
```