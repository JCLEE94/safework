# Health Management System - Deployment Guide

## Overview

This guide explains how to deploy the Health Management System without any hardcoded values. All configuration is managed through environment variables.

## Configuration Files

### 1. Environment Templates

- `.env.deploy.example` - Deployment configuration template
- `.env.production.example` - Full production configuration template
- `.env.example` - Development configuration template

### 2. Scripts

- `scripts/env-manager.sh` - Interactive environment configuration manager
- `scripts/generate-secure-values.sh` - Generate secure passwords and secrets
- `deploy-production.sh` - Main deployment script

## Quick Start

### Step 1: Generate Secure Values

```bash
./scripts/generate-secure-values.sh
```

This generates secure random values for:
- JWT_SECRET (64 characters)
- API_KEY_SALT (32 characters)
- POSTGRES_PASSWORD (24 characters)
- REDIS_PASSWORD (24 characters)

### Step 2: Create Production Configuration

```bash
# Option 1: Use the environment manager
./scripts/env-manager.sh
# Select option 2: Create production .env from template

# Option 2: Manual copy
cp .env.production.example .env.production
# Edit .env.production with your values
```

### Step 3: Set Environment Variables

```bash
# Load deployment configuration
source .env.deploy

# Or export individually
export DOCKER_REGISTRY=registry.jclee.me
export DOCKER_IMAGE_NAME=health-management-system
export DEPLOY_TARGET_DIR=/var/services/homes/docker/app/health
```

### Step 4: Deploy

```bash
./deploy-production.sh
```

## Environment Variables Reference

### Docker Configuration
- `DOCKER_REGISTRY` - Private registry URL (default: registry.jclee.me)
- `DOCKER_IMAGE_NAME` - Image name (default: health-management-system)
- `DOCKER_TAG` - Image tag (default: latest)
- `DOCKER_REGISTRY_USER` - Registry username (if auth enabled)
- `DOCKER_REGISTRY_PASS` - Registry password (if auth enabled)

### Deployment Configuration
- `DEPLOY_TARGET_DIR` - Target directory (default: /var/services/homes/docker/app/health)
- `DEPLOY_HOST` - Deployment host
- `DEPLOY_PORT` - SSH port
- `DEPLOY_USER` - SSH user

### Database Configuration
- `POSTGRES_USER` - Database user (default: admin)
- `POSTGRES_PASSWORD` - Database password (REQUIRED)
- `POSTGRES_DB` - Database name (default: health_management)
- `POSTGRES_CONTAINER_NAME` - Container name (default: health-postgres)

### Application Configuration
- `JWT_SECRET` - JWT signing secret (REQUIRED, min 32 chars)
- `JWT_ALGORITHM` - JWT algorithm (default: HS256)
- `JWT_EXPIRATION_MINUTES` - Token expiration (default: 1440)
- `API_KEY_SALT` - API key salt (REQUIRED)

## GitHub Actions Configuration

### Repository Variables
Set in: Settings → Secrets and variables → Actions → Variables

```
DOCKER_REGISTRY=registry.jclee.me
DOCKER_IMAGE_NAME=health-management-system
```

### Repository Secrets
Set in: Settings → Secrets and variables → Actions → Secrets

```
DOCKERHUB_USERNAME=your-dockerhub-username
DOCKERHUB_TOKEN=your-dockerhub-token
REGISTRY_USERNAME=your-registry-username
REGISTRY_PASSWORD=your-registry-password
```

## Security Best Practices

1. **Never commit .env files** - Only commit .env.example templates
2. **Use strong passwords** - Use the generate-secure-values.sh script
3. **Rotate secrets regularly** - Update JWT_SECRET and passwords periodically
4. **Limit access** - Restrict who can access production configurations
5. **Use secrets management** - Consider HashiCorp Vault or AWS Secrets Manager for production

## Troubleshooting

### Validate Configuration
```bash
./scripts/env-manager.sh
# Select option 3: Validate environment configuration
```

### Check Current Configuration (Masked)
```bash
./scripts/env-manager.sh
# Select option 4: Show current configuration (masked)
```

### Backup Configuration
```bash
./scripts/env-manager.sh
# Select option 7: Backup current configuration
```

## Production Checklist

- [ ] Generated secure values using script
- [ ] Created .env.production from template
- [ ] Updated all placeholder values
- [ ] Set GitHub Actions secrets
- [ ] Tested deployment script locally
- [ ] Configured firewall for port 3001
- [ ] Set up database backups
- [ ] Configured monitoring (Watchtower logs)
- [ ] Documented any custom configurations