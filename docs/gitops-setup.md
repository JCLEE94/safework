# SafeWork GitOps CI/CD 구축 가이드

## 개요

SafeWork 프로젝트를 위한 GitOps 기반 CI/CD 파이프라인 구축 가이드입니다. 이 설정은 다음을 포함합니다:

- GitHub Actions 기반 CI/CD
- Helm Chart 패키징 및 ChartMuseum 배포
- ArgoCD를 통한 자동 배포
- ArgoCD Image Updater를 통한 이미지 자동 업데이트

## 아키텍처

```
GitHub → GitHub Actions → Docker Registry → ChartMuseum
                                    ↓
                            ArgoCD + Image Updater
                                    ↓
                              Kubernetes Cluster
```

## 필수 조건

1. **GitHub CLI**: `gh` 명령어 설치 및 인증
2. **kubectl**: Kubernetes 클러스터 접근
3. **ArgoCD CLI**: ArgoCD 애플리케이션 관리
4. **Helm**: v3.13.0 이상

## 빠른 시작

### 1. 초기 설정 실행

```bash
# GitOps 설정 스크립트 실행
./scripts/gitops-setup.sh
```

이 스크립트는 다음을 수행합니다:
- 기존 파일 백업
- GitHub Secrets/Variables 설정
- Helm Chart 생성
- GitHub Actions 워크플로우 생성
- ArgoCD Application 매니페스트 생성

### 2. Kubernetes Secrets 생성

```bash
# production 네임스페이스에 시크릿 생성
./scripts/create-k8s-secrets.sh production
```

### 3. ArgoCD Application 생성

```bash
# ArgoCD에 로그인
argocd login argo.jclee.me --username admin --insecure

# Application 생성
kubectl apply -f argocd-application.yaml
```

### 4. 첫 배포 실행

```bash
git add .
git commit -m "feat: GitOps CI/CD 구성"
git push origin main
```

### 5. 배포 검증

```bash
./scripts/verify-deployment.sh safework production
```

## 구성 상세

### GitHub Secrets

| Secret | 설명 |
|--------|------|
| REGISTRY_URL | Docker 레지스트리 URL (기본: registry.jclee.me) |
| CHARTMUSEUM_URL | ChartMuseum URL (기본: https://charts.jclee.me) |
| CHARTMUSEUM_USERNAME | ChartMuseum 사용자명 |
| CHARTMUSEUM_PASSWORD | ChartMuseum 비밀번호 |

### GitHub Variables

| Variable | 설명 |
|----------|------|
| GITHUB_ORG | GitHub Organization (기본: JCLEE94) |
| APP_NAME | 애플리케이션 이름 (기본: safework) |
| NAMESPACE | Kubernetes 네임스페이스 (기본: production) |

### Helm Chart 구조

```
charts/safework/
├── Chart.yaml              # Chart 메타데이터
├── values.yaml             # 기본 설정값
├── templates/
│   ├── _helpers.tpl        # 템플릿 헬퍼 함수
│   ├── deployment.yaml     # Kubernetes Deployment
│   ├── service.yaml        # Kubernetes Service
│   └── ingress.yaml        # Kubernetes Ingress
└── environments/
    ├── production.yaml     # 프로덕션 환경 설정
    └── staging.yaml        # 스테이징 환경 설정
```

### ArgoCD Image Updater 설정

ArgoCD Image Updater는 deployment.yaml에 다음 어노테이션으로 설정됩니다:

```yaml
annotations:
  argocd-image-updater.argoproj.io/image-list: safework=registry.jclee.me/safework
  argocd-image-updater.argoproj.io/write-back-method: git
  argocd-image-updater.argoproj.io/safework.allow-tags: '^prod-[0-9]{8}-[a-f0-9]{7}$'
  argocd-image-updater.argoproj.io/safework.update-strategy: latest
```

## 이미지 태그 전략

- **Production**: `prod-YYYYMMDD-SHA7` (예: prod-20250122-abc1234)
- **Semantic**: `1.YYYYMMDD.BUILD_NUMBER` (예: 1.20250122.123)
- **Latest**: 최신 프로덕션 빌드

## 배포 워크플로우

1. **코드 푸시**: main 브랜치에 코드 푸시
2. **GitHub Actions**: 
   - Docker 이미지 빌드 및 푸시
   - Helm Chart 패키징 및 ChartMuseum 업로드
3. **ArgoCD Image Updater**:
   - 새 이미지 자동 감지
   - Git에 변경사항 커밋
4. **ArgoCD**:
   - 자동 동기화 및 배포
   - Self-healing 활성화

## 문제 해결

### 1. Chart 업로드 실패
```bash
# ChartMuseum 접근 확인
curl -u admin:password https://charts.jclee.me/api/charts
```

### 2. ArgoCD 동기화 실패
```bash
# ArgoCD 애플리케이션 상태 확인
argocd app get safework --grpc-web

# 수동 동기화
argocd app sync safework
```

### 3. Image Updater 로그 확인
```bash
kubectl logs -n argocd deployment/argocd-image-updater -f
```

## 환경별 배포

### Staging 환경
```bash
# staging values 파일 사용
helm upgrade --install safework-staging ./charts/safework \
  -f ./charts/safework/environments/staging.yaml \
  -n staging
```

### Production 환경
```bash
# production values 파일 사용
helm upgrade --install safework ./charts/safework \
  -f ./charts/safework/environments/production.yaml \
  -n production
```

## 보안 고려사항

1. **Secrets 관리**: Kubernetes Secrets 사용
2. **이미지 서명**: 추후 Cosign 통합 고려
3. **RBAC**: 적절한 권한 설정
4. **네트워크 정책**: 필요시 NetworkPolicy 적용

## 참고 링크

- [ArgoCD 문서](https://argo-cd.readthedocs.io/)
- [ArgoCD Image Updater](https://argocd-image-updater.readthedocs.io/)
- [Helm 문서](https://helm.sh/docs/)
- [ChartMuseum](https://chartmuseum.com/)

---

작성일: 2025-01-22  
버전: 1.0.0