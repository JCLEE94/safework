# GitHub Actions Workflows

## 🚀 Active Workflows

### main-deploy.yml (Primary CI/CD Pipeline)
- **Trigger**: Push to `main` branch, PRs to `main`, manual dispatch
- **Purpose**: Complete CI/CD pipeline for production deployment via ArgoCD
- **Features**:
  - Comprehensive test suite (backend + frontend)
  - Security scanning with Trivy
  - Multi-stage Docker build with caching
  - Automated K8s manifest updates
  - ArgoCD auto-sync integration
  - Production health verification
  - Automated rollback notifications

### build-deploy.yml
- **Trigger**: Push to `develop` branch
- **Purpose**: Development deployment using Watchtower
- **Target**: Development environment

### test.yml
- **Trigger**: All pushes and PRs
- **Purpose**: Run test suite only

### security.yml
- **Trigger**: Weekly schedule
- **Purpose**: Regular security vulnerability scanning

## 📁 Deprecated/Disabled Workflows

These workflows have been disabled to prevent conflicts:

- **argocd-simple.yml**: Replaced by main-deploy.yml
- **k8s-deploy.yml**: Replaced by main-deploy.yml
- **docker-build.yml**: Legacy build workflow
- **deploy-hosted.yml**: Old deployment method
- **direct-deploy.yml**: Manual deployment (backup only)

## 🔧 Workflow Management

### To Re-enable a Workflow
Change the trigger from:
```yaml
on:
  workflow_dispatch:
  # Disabled - replaced by main-deploy.yml
```

To:
```yaml
on:
  push:
    branches: [ main ]
```

### Environment Variables Required

#### Registry Secrets
- `REGISTRY_USERNAME` (default: qws9411)
- `REGISTRY_PASSWORD` (default: bingogo1)

#### Deployment Secrets
- `KUBECONFIG`: Base64 encoded kubeconfig for K8s access
- `GITHUB_TOKEN`: For updating manifests

## 📊 Deployment Flow

```
1. Code Push (main) → 2. Tests & Security Scan → 3. Build & Push Image
                                                            ↓
6. Verify Health ← 5. ArgoCD Auto-sync ← 4. Update K8s Manifests
```

## 🏷️ Image Tagging Strategy

- **Production**: `prod-YYYYMMDD-SHA7` (e.g., prod-20250104-abc1234)
- **Development**: `dev-YYYYMMDD-SHA7`
- **Latest**: Always points to the most recent production build

## 🔄 Rollback Procedures

### Via ArgoCD UI
1. Navigate to https://argo.jclee.me/applications/safework
2. Click "History and Rollback"
3. Select previous version
4. Click "Rollback"

### Via CLI
```bash
argocd app rollback safework --server argo.jclee.me
```

## 📝 Notes

- All workflows use self-hosted runners for better performance
- Test containers use ports 15432 (PostgreSQL) and 16379 (Redis)
- Production URL: https://safework.jclee.me
- ArgoCD Dashboard: https://argo.jclee.me