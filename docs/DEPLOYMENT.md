# Private Deployment Guide

## Overview

This guide covers the deployment process for SafeWork Pro using a private Docker registry and GitHub Actions CI/CD.

## Prerequisites

- Docker and Docker Compose installed
- Access to private registry (registry.jclee.me)
- GitHub repository with Actions enabled
- SSH access to production server

## Initial Setup

### 1. Configure GitHub Secrets

Run the setup script to configure all required secrets:

```bash
./scripts/setup-github-secrets.sh
```

Required secrets:
- **DOCKERHUB_USERNAME**: Your Docker Hub username
- **DOCKERHUB_TOKEN**: Docker Hub access token (not password!)
- **REGISTRY_USERNAME**: Private registry username
- **REGISTRY_PASSWORD**: Private registry password
- **DEPLOY_HOST**: Production server (safework.jclee.me)
- **DEPLOY_USER**: SSH username (docker)
- **DEPLOY_PASSWORD**: SSH password
- **DEPLOY_PORT**: SSH port (1111)

### 2. Configure Production Environment

1. Copy the production environment template:
   ```bash
   cp .env.production.template .env.production
   ```

2. Update all values with secure production credentials

3. **Important**: Never commit `.env.production` to version control!

## Deployment Methods

### Method 1: Automated via GitHub Actions

Simply push to the main branch:

```bash
git push origin main
```

The GitHub Actions workflow will:
1. Run all tests
2. Build Docker images
3. Push to private registry
4. Deploy to production server
5. Verify deployment health

### Method 2: Manual Deployment

Use the deployment script:

```bash
# Production deployment (default)
./deploy.sh

# Staging deployment
./deploy.sh staging

# Development deployment
./deploy.sh dev
```

The script will:
1. Run tests (abort if failed)
2. Build frontend
3. Build Docker image with timestamp
4. Test image locally
5. Push to registry.jclee.me
6. Deploy to remote server
7. Verify deployment

## Private Registry Configuration

### Docker Compose Production

The `docker-compose.prod.yml` file is configured to pull from the private registry:

```yaml
services:
  health-app:
    image: registry.jclee.me/health-management-system:latest
```

### Registry Authentication

On the production server, ensure Docker is logged into the private registry:

```bash
docker login registry.jclee.me
```

## Monitoring Deployment

### Health Checks

- Application health: http://192.168.50.215:3001/health
- API documentation: http://192.168.50.215:3001/api/docs
- Real-time monitoring: http://192.168.50.215:3001/monitoring

### Logs

View recent logs:

```bash
# On production server
docker-compose logs --tail=100 health-app

# Via SSH
ssh -p 1111 docker@192.168.50.215 "cd ~/app/health && docker-compose logs --tail=100 health-app"
```

### Container Status

```bash
# On production server
docker-compose ps

# Via SSH
ssh -p 1111 docker@192.168.50.215 "cd ~/app/health && docker-compose ps"
```

## Rollback Procedure

If deployment fails or issues are detected:

### Automatic Rollback

The deployment script creates backup tags before updating:

```bash
# On production server
docker tag registry.jclee.me/health-management-system:backup-YYYYMMDD-HHMMSS registry.jclee.me/health-management-system:latest
docker-compose up -d
```

### Manual Rollback

1. List available backup images:
   ```bash
   docker images | grep health-management-system
   ```

2. Tag the backup as latest:
   ```bash
   docker tag registry.jclee.me/health-management-system:backup-20250119-143000 registry.jclee.me/health-management-system:latest
   ```

3. Restart containers:
   ```bash
   docker-compose up -d
   ```

## Security Considerations

1. **Secrets Management**
   - Use GitHub Secrets for CI/CD
   - Never commit credentials to repository
   - Rotate secrets regularly

2. **Registry Security**
   - Use HTTPS for registry communication
   - Implement registry access controls
   - Monitor registry access logs

3. **Production Environment**
   - Use strong passwords
   - Enable firewall rules
   - Implement fail2ban for SSH
   - Regular security updates

## Troubleshooting

### Registry Push Fails

```bash
# Check Docker login
docker login registry.jclee.me

# Verify registry connectivity
curl https://registry.jclee.me/v2/
```

### Deployment Verification Fails

```bash
# Check container status
docker-compose ps

# View detailed logs
docker-compose logs --tail=200 health-app

# Test health endpoint manually
curl -v http://localhost:3001/health
```

### SSH Connection Issues

```bash
# Test SSH connection
ssh -p 1111 docker@192.168.50.215 "echo 'Connection successful'"

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
```

## Maintenance

### Regular Tasks

1. **Weekly**
   - Review application logs
   - Check disk space
   - Monitor performance metrics

2. **Monthly**
   - Update dependencies
   - Rotate logs
   - Review security alerts

3. **Quarterly**
   - Update base Docker images
   - Review and rotate secrets
   - Performance optimization

### Backup Strategy

1. **Database Backups**
   ```bash
   # Automated daily backups
   docker exec health-postgres pg_dump -U admin health_management > backup-$(date +%Y%m%d).sql
   ```

2. **Volume Backups**
   ```bash
   # Backup Docker volumes
   docker run --rm -v health_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres-data-$(date +%Y%m%d).tar.gz /data
   ```

## Support

For issues or questions:
1. Check application logs
2. Review this documentation
3. Create an issue in the GitHub repository