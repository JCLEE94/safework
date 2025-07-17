# SafeWork Pro 리팩토링 및 운영 배포 개선 완료

## 📋 수행된 작업

### 1. **K8s 매니페스트 구조 개선**
- ✅ Kustomize 기반 구조로 재구성
- ✅ Base + Overlays 패턴 적용
- ✅ 환경별 설정 분리 (production)
- ✅ ConfigMap과 Secret 관리 개선

### 2. **CI/CD 파이프라인 최적화**
- ✅ Self-hosted runner 유지
- ✅ 캐싱 전략 추가
- ✅ 병렬 처리 개선
- ✅ 헬스체크 및 롤백 전략 포함

### 3. **배포 프로세스 간소화**
- ✅ 통합 배포 스크립트 작성
- ✅ ArgoCD Application 설정 개선
- ✅ Image Updater 연동 설정

## 🚀 사용 방법

### 1. 로컬 개발
```bash
# Docker Compose로 개발 환경 실행
docker-compose -f docker-compose.dev.yml up --build
```

### 2. 운영 배포
```bash
# 자동 배포 (GitHub Actions)
git add .
git commit -m "feat: 기능 추가"
git push origin main

# 수동 배포
./scripts/deploy/deploy-refactored.sh
```

### 3. ArgoCD 확인
```bash
# ArgoCD UI 접속
open https://argo.jclee.me

# CLI로 상태 확인
argocd app get safework
argocd app sync safework
```

## 📁 개선된 구조

```
k8s/
├── base/                    # Kustomize 기본 리소스
│   ├── deployment.yaml      # 기본 Deployment
│   ├── service.yaml         # NodePort Service
│   ├── configmap.yaml       # 설정 ConfigMap
│   └── kustomization.yaml   # Base Kustomization
├── overlays/                # 환경별 설정
│   └── production/          # 운영 환경
│       ├── deployment-patch.yaml
│       └── kustomization.yaml
└── argocd/                  # ArgoCD 설정
    └── application-refactored.yaml
```

## 🔧 주요 개선사항

### 1. **성능 최적화**
- Docker 이미지 빌드 캐싱
- 병렬 테스트 실행
- 리소스 요청/제한 설정

### 2. **안정성 향상**
- Health/Readiness Probe 설정
- 자동 롤백 메커니즘
- PVC를 통한 데이터 영속성

### 3. **운영 편의성**
- 단일 명령어 배포
- ArgoCD 자동 동기화
- 명확한 환경 분리

## 📊 배포 상태 모니터링

### Kubernetes
```bash
# Pod 상태
kubectl get pods -n safework

# 로그 확인
kubectl logs -n safework -l app=safework -f

# 리소스 사용량
kubectl top pods -n safework
```

### ArgoCD
```bash
# Application 상태
argocd app get safework

# 동기화 이력
argocd app history safework
```

## 🔍 트러블슈팅

### Registry 인증 문제
```bash
# Secret 재생성
kubectl delete secret harbor-registry -n safework
kubectl create secret docker-registry harbor-registry \
  --docker-server=registry.jclee.me \
  --docker-username=qws9411 \
  --docker-password=bingogo1 \
  --namespace=safework
```

### Pod 시작 실패
```bash
# 상세 로그 확인
kubectl describe pod -n safework <pod-name>
kubectl logs -n safework <pod-name> --previous
```

### ArgoCD 동기화 실패
```bash
# 수동 동기화
argocd app sync safework --force
argocd app refresh safework
```

## 📝 다음 단계

1. **모니터링 강화**
   - Prometheus/Grafana 연동
   - 알림 설정

2. **보안 강화**
   - Secret 관리 개선 (Sealed Secrets)
   - Network Policy 적용

3. **확장성 개선**
   - HPA (Horizontal Pod Autoscaler) 설정
   - Ingress Controller 설정

---
작성일: 2025-01-17
작성자: SafeWork Pro DevOps Team