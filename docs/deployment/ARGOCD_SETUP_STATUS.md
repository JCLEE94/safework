# ArgoCD Application Setup Status

**Date**: 2025-01-14  
**ArgoCD URL**: https://argo.jclee.me  
**Credentials**: admin / bingogo1

## Application Configuration

### Successfully Configured ✅

1. **Repository Access**
   - GitHub repository added with authentication
   - URL: https://github.com/JCLEE94/safework.git
   - Authentication: GitHub token configured

2. **Application Created**
   - Name: safework
   - Namespace: safework
   - Path: k8s/safework
   - Sync Policy: Automated with Prune and Self-Heal

3. **Image Updater Annotations**
   ```yaml
   argocd-image-updater.argoproj.io/image-list: safework=registry.jclee.me/safework:latest
   argocd-image-updater.argoproj.io/safework.update-strategy: latest
   argocd-image-updater.argoproj.io/safework.allow-tags: "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$"
   argocd-image-updater.argoproj.io/write-back-method: git
   argocd-image-updater.argoproj.io/git-branch: main
   ```

### Current Issues ⚠️

1. **Sync Issue**
   - ArgoCD is detecting a phantom Kustomization resource
   - This is preventing the sync from completing
   - Error: "The Kubernetes API could not find kustomize.config.k8s.io/Kustomization"

2. **Resources Pending**
   - All resources are in OutOfSync status
   - Resources include: namespace, secrets, services, deployments

## Resolution Steps

### Option 1: Manual UI Sync (Recommended)
1. Access ArgoCD UI: https://argo.jclee.me
2. Login with: admin / bingogo1
3. Navigate to the safework application
4. Click "Sync" button
5. In the sync dialog, uncheck the Kustomization resource if visible
6. Click "Synchronize"

### Option 2: CLI Force Sync
```bash
# Delete and recreate without directory recurse
argocd app delete safework --grpc-web --yes
argocd app create safework \
  --repo https://github.com/JCLEE94/safework.git \
  --path k8s/safework \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace safework \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --sync-option CreateNamespace=true \
  --grpc-web
```

### Option 3: Create Base Kustomization
Create a minimal kustomization.yaml in k8s/safework/:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - namespace.yaml
  - secrets.yaml
  - regcred.yaml
  - postgres.yaml
  - redis.yaml
  - deployment.yaml
  - service.yaml
```

## Next Steps

1. **Once Synced**:
   - Verify all pods are running
   - Check service endpoints
   - Test application access

2. **Image Updater Verification**:
   - Push a new image with tag format: `prod-YYYYMMDD-SHA7`
   - Monitor Image Updater logs
   - Verify automatic deployment

3. **Production Access**:
   - Application URL: https://safework.jclee.me
   - Health check: https://safework.jclee.me/health

## ArgoCD CLI Commands Reference

```bash
# Login
argocd login argo.jclee.me --username admin --password bingogo1 --insecure

# List apps
argocd app list --grpc-web

# Get app details
argocd app get safework --grpc-web

# Sync app
argocd app sync safework --grpc-web

# Check app history
argocd app history safework --grpc-web

# View logs
argocd app logs safework --grpc-web --follow
```

## Registry Configuration

For ArgoCD Image Updater to work, ensure:
1. Registry credentials are configured in ArgoCD
2. GitHub Actions pushes images with correct tag format
3. Image Updater has write access to Git repository

---
**Note**: The phantom Kustomization issue may be an ArgoCD cache problem. If it persists, consider restarting the ArgoCD application controller.