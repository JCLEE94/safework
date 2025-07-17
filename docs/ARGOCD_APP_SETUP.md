# ArgoCD Application 설정 가이드

## ArgoCD UI 접속
- URL: https://argo.jclee.me
- 기존 admin 계정으로 로그인

## Application 생성 단계

### 1. 새 Application 생성
- **NEW APP** 버튼 클릭
- **Application Name**: safework
- **Project**: default
- **Sync Policy**: Automatic

### 2. Source 설정
- **Repository URL**: https://charts.jclee.me
- **Chart**: safework
- **Revision**: * (latest)

### 3. Destination 설정
- **Cluster URL**: https://kubernetes.default.svc
- **Namespace**: safework

### 4. Helm Parameters
```yaml
image:
  repository: registry.jclee.me/safework
  tag: latest
  pullPolicy: Always

service:
  type: NodePort
  port: 3001
  nodePort: 32301

resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "1000m"

env:
  - name: ENVIRONMENT
    value: "production"
  - name: DATABASE_URL
    value: "postgresql://admin:password@localhost:5432/health_management"
  - name: REDIS_URL
    value: "redis://localhost:6379/0"
  - name: TZ
    value: "Asia/Seoul"
```

### 5. Sync Options
- ✅ Auto-create namespace
- ✅ Prune resources
- ✅ Self heal

### 6. 접속 정보
- **내부 접속**: http://safework.safework.svc.cluster.local:3001
- **외부 접속**: http://192.168.50.110:32301
- **도메인**: https://safework.jclee.me (192.168.50.110:32301로 포워딩됨)

## CLI로 생성 (대안)
```bash
# ArgoCD CLI 로그인
argocd login argo.jclee.me --username admin --insecure

# Application 생성
argocd app create safework \
  --repo https://charts.jclee.me \
  --helm-chart safework \
  --revision "*" \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace safework \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --helm-set image.repository=registry.jclee.me/safework \
  --helm-set image.tag=latest \
  --helm-set service.type=NodePort \
  --helm-set service.nodePort=32301

# 동기화
argocd app sync safework
```

## 상태 확인
```bash
# Application 상태
argocd app get safework

# Pod 상태
kubectl get pods -n safework

# Service 확인
kubectl get svc -n safework

# 헬스체크
curl http://192.168.50.110:32301/health
```