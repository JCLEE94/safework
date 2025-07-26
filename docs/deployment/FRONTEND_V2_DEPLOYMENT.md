# SafeWork Frontend V2 Deployment Guide

## Overview

This guide covers the deployment of SafeWork Frontend V2 to Kubernetes and migration from the old system.

## Prerequisites

- Docker installed
- kubectl configured with access to your Kubernetes cluster
- Access to registry.jclee.me
- Kubernetes namespace `safework` created

## Quick Deployment

### 1. Build and Deploy New Frontend

```bash
cd /home/jclee/app/safework
./scripts/deploy/deploy-frontend-v2.sh
```

This script will:
- Build the Docker image
- Push to registry
- Deploy to Kubernetes
- Verify deployment

### 2. Test the New System

```bash
./scripts/deploy/test-frontend-v2.sh
```

### 3. Migrate from Old System

```bash
./scripts/deploy/migrate-to-v2.sh
```

This will:
- Backup current configuration
- Scale down old deployment
- Update ingress routing
- Run data migration
- Optionally delete old resources

## Deployment Options

### Option 1: Direct Deployment (Recommended for Testing)

Deploy V2 alongside V1:
```bash
./scripts/deploy/deploy-frontend-v2.sh
```

Access at: https://safework-v2.jclee.me

### Option 2: Canary Deployment (Recommended for Production)

Gradually shift traffic from V1 to V2:
```bash
./scripts/deploy/canary-deploy-frontend.sh
```

This allows:
- 10% → 50% → 100% traffic progression
- Monitoring between stages
- Easy rollback if issues arise

### Option 3: Blue-Green Deployment

For instant switchover:
1. Deploy V2: `./scripts/deploy/deploy-frontend-v2.sh`
2. Test thoroughly: `./scripts/deploy/test-frontend-v2.sh`
3. Switch traffic: `kubectl patch ingress safework -n safework --type='json' -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value":"safework-frontend-v2"}]'`

## URLs

- **Production V1**: https://safework.jclee.me
- **Production V2**: https://safework-v2.jclee.me (after deployment)

## Rollback Procedure

If issues occur after migration:

```bash
# Scale up old deployment
kubectl scale deployment safework -n safework --replicas=1

# Revert ingress to old frontend
kubectl patch ingress safework -n safework --type='json' \
  -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value":"safework"}]'

# Delete V2 deployment if needed
kubectl delete deployment safework-frontend-v2 -n safework
```

## Monitoring

### Check Deployment Status
```bash
kubectl get pods -n safework -l app=safework-frontend-v2
kubectl get ingress -n safework
```

### View Logs
```bash
kubectl logs -n safework -l app=safework-frontend-v2 -f
```

### Check Metrics
```bash
kubectl top pods -n safework -l app=safework-frontend-v2
```

## CI/CD Pipeline

The GitHub Actions workflow will automatically:
1. Build and test on push to main
2. Build Docker image
3. Push to registry
4. Deploy to Kubernetes
5. Run smoke tests

Trigger manually:
```bash
gh workflow run frontend-v2-deploy.yml
```

## Troubleshooting

### Frontend Not Accessible
1. Check pod status: `kubectl get pods -n safework`
2. Check logs: `kubectl logs -n safework -l app=safework-frontend-v2`
3. Check ingress: `kubectl describe ingress -n safework`

### API Connection Issues
1. Verify backend is running
2. Check nginx proxy configuration
3. Review CORS settings

### Performance Issues
1. Check resource limits
2. Review nginx caching
3. Monitor pod metrics

## Environment Configuration

### Development
```bash
REACT_APP_API_URL=http://localhost:3001
REACT_APP_ENV=development
```

### Production
```bash
REACT_APP_API_URL=https://safework.jclee.me
REACT_APP_ENV=production
```

## Security Checklist

- [ ] HTTPS enabled
- [ ] Security headers configured
- [ ] API authentication working
- [ ] CORS properly configured
- [ ] No sensitive data in frontend code
- [ ] Environment variables secured

## Post-Deployment Tasks

1. **Monitor for 24 hours**
   - Check error rates
   - Monitor performance
   - Review user feedback

2. **Update Documentation**
   - Update user guides
   - Update API documentation
   - Notify team of changes

3. **Clean Up**
   - Remove old deployment (after stability confirmed)
   - Clean up unused images
   - Archive old code

## Support

For issues or questions:
- Check logs: `kubectl logs -n safework -l app=safework-frontend-v2`
- Review deployment status: `kubectl describe deployment -n safework safework-frontend-v2`
- Contact: DevOps team