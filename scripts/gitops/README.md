# GitOps Scripts

## Quick Commands

### Deploy to Production
```bash
git add . && git commit -m "feat: your feature" && git push
```

### Manual Docker Build & Push
```bash
# Login
docker login registry.jclee.me -u admin -p bingogo1

# Build
docker build -f deployment/Dockerfile.prod -t registry.jclee.me/safework:latest .

# Push
docker push registry.jclee.me/safework:latest
```

### Manual Helm Chart Upload
```bash
cd k8s/helm
helm package safework
curl -X POST -u admin:bingogo1 \
  --data-binary "@safework-*.tgz" \
  "https://charts.jclee.me/api/charts"
```

### Check Status
```bash
# Docker Registry
curl -s -u admin:bingogo1 https://registry.jclee.me/v2/_catalog | jq .

# ChartMuseum
curl -s -u admin:bingogo1 https://charts.jclee.me/api/charts/safework | jq '.[0]'

# Production Health
curl -s https://safework.jclee.me/health | jq .
```

### ArgoCD Sync
```bash
# Force sync
kubectl patch application -n argocd safework --type merge \
  -p '{"metadata":{"annotations":{"argocd.argoproj.io/refresh":"hard"}}}'

# Check sync status
kubectl get application -n argocd safework -o json | jq '.status.sync'
```