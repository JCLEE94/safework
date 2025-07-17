# SafeWork GitOps 배포 템플릿

SafeWork Pro 건설업 보건관리 시스템을 위한 GitOps 기반 배포 템플릿입니다.

## 🏗️ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                    SafeWork GitOps Architecture              │
├─────────────────────────────────────────────────────────────┤
│  GitHub Actions CI/CD                                       │
│  ├── Build & Test                                          │
│  ├── Docker Build & Push (registry.jclee.me)              │
│  └── Deploy Trigger                                        │
│                                                             │
│  ArgoCD + Image Updater                                    │
│  ├── Application Sync                                      │
│  ├── Automated Image Updates                               │
│  └── Multi-Environment Management                          │
│                                                             │
│  Kubernetes Environments                                   │
│  ├── Dev (Namespace: dev)                                  │
│  ├── Staging (Namespace: staging)                          │
│  └── Production (Namespace: production)                    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 폴더 구조

```
gitops/
├── k8s-config/                 # Kubernetes 설정
│   ├── base/                   # 기본 리소스
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── kustomization.yaml
│   ├── overlays/               # 환경별 설정
│   │   ├── dev/
│   │   ├── staging/
│   │   └── prod/
│   └── argocd/                 # ArgoCD 애플리케이션
│       └── applications/
├── scripts/                    # 배포 스크립트
│   ├── setup-cluster.sh
│   ├── setup-argocd.sh
│   ├── create-secrets.sh
│   ├── deploy-apps.sh
│   └── emergency-rollback.sh
├── templates/                  # 템플릿 파일
│   ├── github-actions-build.yaml
│   ├── kubeconfig-template.yaml
│   └── env-template.sh
└── README.md                   # 이 문서
```

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 환경 변수 설정
source templates/env-template.sh

# kubeconfig 설정
cp templates/kubeconfig-template.yaml ~/.kube/config-k8s-jclee
export KUBECONFIG=~/.kube/config-k8s-jclee
```

### 2. 클러스터 초기화

```bash
# 클러스터 설정 (네임스페이스 및 시크릿 생성)
./scripts/setup-cluster.sh

# ArgoCD 설정 (기존 설치 확인 및 설정)
./scripts/setup-argocd.sh

# 애플리케이션 시크릿 생성
./scripts/create-secrets.sh
```

### 3. 애플리케이션 배포

```bash
# 모든 애플리케이션 배포
./scripts/deploy-apps.sh

# 또는 개별 배포
kubectl apply -f k8s-config/argocd/applications/safework-dev.yaml
kubectl apply -f k8s-config/argocd/applications/safework-staging.yaml
kubectl apply -f k8s-config/argocd/applications/safework-prod.yaml
```

## 🔧 주요 설정

### ArgoCD Image Updater 설정

각 환경별로 이미지 자동 업데이트가 설정되어 있습니다:

- **Dev**: `dev-*` 태그 자동 업데이트
- **Staging**: `staging-*` 태그 자동 업데이트  
- **Production**: `prod-YYYYMMDD-XXXXXXX` 패턴 자동 업데이트

### 환경별 설정

| 환경 | 네임스페이스 | 레플리카 | 리소스 | 도메인 |
|------|-------------|----------|---------|--------|
| Dev | dev | 1 | 256Mi/100m | http://k8s.jclee.me:30001 |
| Staging | staging | 2 | 512Mi/200m | http://k8s.jclee.me:30002 |
| Production | production | 3 | 1Gi/500m | https://safework.jclee.me |

### 보안 설정

- Harbor Registry 인증 (registry.jclee.me)
- 환경별 시크릿 관리 (.env.secret)
- TLS 인증서 지원
- RBAC 권한 관리

## 🔄 CI/CD 파이프라인

### GitHub Actions 워크플로우

```yaml
# .github/workflows/build.yaml 예시 (templates/github-actions-build.yaml 참조)
name: SafeWork GitOps Build and Deploy

on:
  push:
    branches: [main, develop]
    tags: ['v*']

jobs:
  test:     # 테스트 실행
  build:    # Docker 이미지 빌드
  deploy:   # 환경별 배포
```

### 배포 흐름

1. **코드 푸시** → GitHub Actions 트리거
2. **테스트 실행** → 통합 테스트 및 코드 검증
3. **이미지 빌드** → Docker 이미지 생성 및 Harbor 푸시
4. **ArgoCD 동기화** → Image Updater가 자동 배포
5. **상태 모니터링** → 배포 상태 및 헬스 체크

## 🛠️ 운영 명령어

### 상태 확인

```bash
# 애플리케이션 상태 확인
argocd app list
argocd app get safework-prod

# 파드 상태 확인
kubectl get pods -n production
kubectl logs -n production -l app=safework

# 서비스 상태 확인
kubectl get svc -n production
```

### 배포 관리

```bash
# 수동 동기화
argocd app sync safework-prod

# 강제 동기화
argocd app sync safework-prod --force --prune

# 이미지 업데이트 확인
kubectl get configmap argocd-image-updater-config -n argocd -o yaml
```

### 롤백

```bash
# 이전 버전으로 롤백
./scripts/emergency-rollback.sh prod

# 특정 버전으로 롤백
./scripts/emergency-rollback.sh prod 5

# 롤백 히스토리 확인
argocd app history safework-prod
```

## 📋 체크리스트

### 배포 전 준비사항

- [ ] Kubernetes 클러스터 접근 권한 확인
- [ ] Harbor Registry 접근 권한 확인
- [ ] GitHub Personal Access Token 생성
- [ ] 환경별 시크릿 값 준비
- [ ] 도메인 및 TLS 인증서 준비

### 배포 후 검증

- [ ] 모든 파드가 Running 상태인지 확인
- [ ] 서비스 엔드포인트 접근 가능한지 테스트
- [ ] 헬스 체크 API 응답 확인
- [ ] 로그에 오류가 없는지 확인
- [ ] ArgoCD 애플리케이션 상태가 Healthy인지 확인

## 🔗 주요 URL

- **Kubernetes API**: https://k8s.jclee.me:443
- **ArgoCD UI**: https://argo.jclee.me
- **Harbor Registry**: https://registry.jclee.me
- **Production App**: https://safework.jclee.me

## 📞 문제 해결

### 일반적인 문제

1. **이미지 Pull 실패**
   ```bash
   # Harbor 시크릿 재생성
   kubectl delete secret harbor-registry -n production
   kubectl create secret docker-registry harbor-registry \
     --docker-server=registry.jclee.me \
     --docker-username=admin \
     --docker-password=bingogo1 \
     --namespace=production
   ```

2. **ArgoCD 동기화 실패**
   ```bash
   # 애플리케이션 새로고침
   argocd app refresh safework-prod
   argocd app sync safework-prod --force
   ```

3. **파드 시작 실패**
   ```bash
   # 파드 상태 및 로그 확인
   kubectl describe pod -n production -l app=safework
   kubectl logs -n production -l app=safework --previous
   ```

### 긴급 상황 대응

1. **서비스 중단**
   ```bash
   # 즉시 이전 버전으로 롤백
   ./scripts/emergency-rollback.sh prod
   ```

2. **데이터베이스 연결 오류**
   ```bash
   # 시크릿 확인 및 재생성
   kubectl get secret safework-secret -n production -o yaml
   ```

3. **부하 급증**
   ```bash
   # 수동 스케일링
   kubectl scale deployment safework -n production --replicas=5
   ```

## 📚 추가 자료

- [ArgoCD 공식 문서](https://argo-cd.readthedocs.io/)
- [Kustomize 사용법](https://kustomize.io/)
- [Kubernetes 배포 가이드](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/)
- [Harbor Registry 사용법](https://goharbor.io/docs/)

---

**Version**: 1.0.0  
**Updated**: 2025-01-17  
**Maintainer**: SafeWork Pro Development Team  
**Status**: ✅ Ready for Production