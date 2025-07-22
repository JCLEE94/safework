# GitOps Manual Process

## 1. Docker Image Build
```bash
docker build -f deployment/Dockerfile.prod -t registry.jclee.me/safework:latest .
docker push registry.jclee.me/safework:latest
```

## 2. Helm Chart Update
```bash
cd k8s/helm
helm package safework
curl -X POST -u admin:bingogo1 --data-binary "@safework-*.tgz" "https://charts.jclee.me/api/charts"
```

## 3. ArgoCD Sync
ArgoCD will automatically detect the new chart version and deploy it.

## Status
- Registry: registry.jclee.me ✅
- ChartMuseum: charts.jclee.me ✅  
- ArgoCD: argo.jclee.me ✅
- Production: safework.jclee.me ✅
