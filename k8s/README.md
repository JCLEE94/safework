# SafeWork Kubernetes 배포 가이드

K8s 전환을 위한 완전한 Kubernetes 배포 구성입니다.

## 📋 구성 요소

### 🏗️ 아키텍처
```
┌─────────────────────────────────────────────────────┐
│                 Kubernetes Cluster                  │
│  ┌─────────────────────────────────────────────────┐ │
│  │              safework namespace              │ │
│  │                                               │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │
│  │  │Frontend  │  │Backend   │  │PostgreSQL│     │ │
│  │  │(Nginx)   │  │(FastAPI) │  │StatefulSet│     │ │
│  │  │Pod×2     │  │Pod×2     │  │Pod×1     │     │ │
│  │  └──────────┘  └──────────┘  └──────────┘     │ │
│  │       │              │              │         │ │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │ │
│  │  │Frontend  │  │Backend   │  │Redis     │     │ │
│  │  │Service   │  │Service   │  │Service   │     │ │
│  │  └──────────┘  └──────────┘  └──────────┘     │ │
│  │                                               │ │
│  └─────────────────────────────────────────────────┘ │
│                         │                           │
│                ┌─────────────────┐                   │
│                │ Nginx Ingress   │                   │
│                │ Controller      │                   │
│                └─────────────────┘                   │
└─────────────────────────────────────────────────────┘
                          │
                 ┌─────────────────┐
                 │ Load Balancer   │
                 │ (External)      │
                 └─────────────────┘
                          │
                    Internet Traffic
              https://safework.jclee.me
```

### 📁 디렉토리 구조
```
k8s/
├── namespace/
│   └── namespace.yaml          # Namespace, ResourceQuota, LimitRange
├── configmap/
│   └── app-config.yaml         # Application, PostgreSQL, Redis 설정
├── secrets/
│   └── app-secrets.yaml        # 민감한 정보 (패스워드, JWT 키)
├── storage/
│   └── persistent-volumes.yaml # PV/PVC for PostgreSQL, Redis, Uploads
├── postgres/
│   └── postgres-statefulset.yaml # PostgreSQL StatefulSet + Service
├── redis/
│   └── redis-deployment.yaml   # Redis Deployment + Service
├── backend/
│   └── backend-deployment.yaml # FastAPI Backend + Service
├── frontend/
│   └── frontend-deployment.yaml # Nginx Frontend + Service
├── ingress/
│   └── ingress.yaml            # Nginx Ingress + TLS
├── deploy.sh                   # 자동 배포 스크립트
└── README.md                   # 이 파일
```

## 🚀 빠른 배포

### 1. 전체 자동 배포
```bash
cd k8s
./deploy.sh deploy
```

### 2. 단계별 배포
```bash
# 1. Namespace 생성
kubectl apply -f namespace/namespace.yaml

# 2. 스토리지 설정
sudo mkdir -p /data/safework/{postgres,redis,uploads}
sudo chown -R $USER:$USER /data/safework
kubectl apply -f storage/persistent-volumes.yaml

# 3. 설정 및 시크릿 배포
kubectl apply -f configmap/app-config.yaml
kubectl apply -f secrets/app-secrets.yaml

# 4. PostgreSQL 배포
kubectl apply -f postgres/postgres-statefulset.yaml
kubectl wait --for=condition=ready pod -l app=postgres -n safework --timeout=300s

# 5. Redis 배포
kubectl apply -f redis/redis-deployment.yaml
kubectl wait --for=condition=ready pod -l app=redis -n safework --timeout=300s

# 6. 백엔드 배포
kubectl apply -f backend/backend-deployment.yaml
kubectl wait --for=condition=ready pod -l app=safework,component=backend -n safework --timeout=600s

# 7. 프론트엔드 배포
kubectl apply -f frontend/frontend-deployment.yaml
kubectl wait --for=condition=ready pod -l app=safework,component=frontend -n safework --timeout=300s

# 8. Ingress 배포
kubectl apply -f ingress/ingress.yaml
```

## 🔧 관리 명령어

### 배포 상태 확인
```bash
./deploy.sh status
# 또는
kubectl get all -n safework
```

### 로그 확인
```bash
./deploy.sh logs
# 또는 개별 컴포넌트
kubectl logs -n safework -l app=postgres --tail=50
kubectl logs -n safework -l app=redis --tail=50
kubectl logs -n safework -l app=safework,component=backend --tail=50
kubectl logs -n safework -l app=safework,component=frontend --tail=50
```

### Health Check
```bash
./deploy.sh health
# 또는 수동으로
kubectl exec -n safework deployment/safework-backend -- curl -f http://localhost:8000/health
kubectl exec -n safework deployment/safework-frontend -- curl -f http://localhost:80/nginx-health
```

### 스케일링
```bash
# 백엔드 스케일 아웃
kubectl scale deployment safework-backend -n safework --replicas=3

# 프론트엔드 스케일 아웃
kubectl scale deployment safework-frontend -n safework --replicas=3
```

## 🔒 보안 설정

### 1. Secret 업데이트
배포 전에 `secrets/app-secrets.yaml`의 기본값들을 변경하세요:
```yaml
stringData:
  DATABASE_PASSWORD: "your-secure-password"
  JWT_SECRET_KEY: "your-jwt-secret-key"
  SECRET_KEY: "your-encryption-key"
```

### 2. Registry Secret 설정
프라이빗 레지스트리 사용 시:
```bash
kubectl create secret docker-registry registry-secret \
  --docker-server=registry.jclee.me \
  --docker-username=your-username \
  --docker-password=your-password \
  --namespace=safework
```

## 📊 모니터링

### 리소스 사용량 확인
```bash
kubectl top pods -n safework
kubectl top nodes
```

### 이벤트 확인
```bash
kubectl get events -n safework --sort-by='.lastTimestamp'
```

### 상세 디버깅
```bash
kubectl describe pod <pod-name> -n safework
kubectl logs <pod-name> -n safework -f
```

## 🌐 네트워크 구성

### 서비스 구성
- **frontend-service**: ClusterIP (포트 80)
- **backend-service**: ClusterIP (포트 8000)
- **postgres-service**: ClusterIP (포트 5432)
- **redis-service**: ClusterIP (포트 6379)

### Ingress 라우팅
- `/api/*` → backend-service:8000
- `/ws/*` → backend-service:8000 (WebSocket)
- `/health` → backend-service:8000
- `/*` → frontend-service:80

### 포트 포워딩 (로컬 테스트용)
```bash
# 프론트엔드 접근
kubectl port-forward -n safework svc/frontend-service 8080:80

# 백엔드 직접 접근
kubectl port-forward -n safework svc/backend-service 8000:8000

# PostgreSQL 접근
kubectl port-forward -n safework svc/postgres-service 5432:5432
```

## 💾 스토리지

### PersistentVolume 구성
- **postgres-pv**: 10Gi (PostgreSQL 데이터)
- **redis-pv**: 2Gi (Redis 데이터)
- **app-uploads-pv**: 5Gi (파일 업로드)

### 백업 및 복원
```bash
# PostgreSQL 백업
kubectl exec -n safework postgres-0 -- pg_dump -U admin health_management > backup.sql

# PostgreSQL 복원
kubectl exec -i -n safework postgres-0 -- psql -U admin health_management < backup.sql
```

## 🚨 트러블슈팅

### 일반적인 문제

1. **Pod이 Pending 상태**
   ```bash
   kubectl describe pod <pod-name> -n safework
   # 리소스 부족이나 스토리지 문제 확인
   ```

2. **이미지 Pull 실패**
   ```bash
   # Registry Secret 확인
   kubectl get secret registry-secret -n safework
   ```

3. **데이터베이스 연결 실패**
   ```bash
   # PostgreSQL Pod 상태 확인
   kubectl logs -n safework postgres-0
   # 서비스 DNS 확인
   kubectl exec -n safework deployment/safework-backend -- nslookup postgres-service
   ```

4. **Health Check 실패**
   ```bash
   # 백엔드 로그 확인
   kubectl logs -n safework -l app=safework,component=backend --tail=100
   ```

### 완전 재시작
```bash
./deploy.sh cleanup
./deploy.sh deploy
```

## 📈 성능 튜닝

### 리소스 제한 조정
각 deployment 파일에서 resources 섹션을 수정:
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### HPA (Horizontal Pod Autoscaler) 설정
```bash
kubectl autoscale deployment safework-backend -n safework --cpu-percent=70 --min=2 --max=10
kubectl autoscale deployment safework-frontend -n safework --cpu-percent=50 --min=2 --max=5
```

## 🔄 업데이트

### 롤링 업데이트
```bash
kubectl set image deployment/safework-backend safework-backend=registry.jclee.me/safework:latest -n safework
kubectl rollout status deployment/safework-backend -n safework
```

### 롤백
```bash
kubectl rollout undo deployment/safework-backend -n safework
```

---

**K8s 전환 완료!** Docker 기반에서 Kubernetes 기반으로 성공적으로 전환되었습니다.

문의사항이나 문제가 있으면 로그를 확인하고 필요시 개별 컴포넌트를 재배포하세요.