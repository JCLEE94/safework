# SafeWork GitOps 설정 가이드

## 📋 개요

SafeWork Pro 프로젝트의 GitOps 기반 CI/CD 파이프라인 설정 가이드입니다.

## 🏗️ 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  GitHub Actions │───▶│   Docker Build  │───▶│  Push Registry  │
│  CI Pipeline    │    │   & Push Image  │    │ registry.jclee.me│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                                              │
         ▼                                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Update K8s     │───▶│   ArgoCD Sync   │───▶│  Kubernetes     │
│  Manifests      │    │   Deployment    │    │  Cluster        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 설정 단계

### 1. 기존 리소스 정리

```bash
# 기존 애플리케이션 정리
chmod +x k8s/argocd/cleanup-old-apps.sh
./k8s/argocd/cleanup-old-apps.sh
```

### 2. GitHub Secrets 설정

GitHub 저장소 설정 → Secrets and variables → Actions에서 다음 시크릿 추가:

#### 필수 시크릿:
```bash
# Docker Registry 접근
DOCKER_USERNAME=your-registry-username
DOCKER_PASSWORD=your-registry-password

# ArgoCD 접근
ARGOCD_USERNAME=admin
ARGOCD_PASSWORD=your-argocd-password

# GitOps 저장소 접근
GITOPS_TOKEN=your-github-token-with-repo-permissions
```

#### 선택적 시크릿:
```bash
# 코드 품질 (선택사항)
CODECOV_TOKEN=your-codecov-token

# 차트 저장소 (선택사항)
CHARTMUSEUM_USERNAME=your-chartmuseum-username
CHARTMUSEUM_PASSWORD=your-chartmuseum-password
```

### 3. ArgoCD 설정

```bash
# ArgoCD 설정 실행
chmod +x k8s/argocd/setup-argocd.sh
./k8s/argocd/setup-argocd.sh
```

### 4. 환경 변수 설정 (GitHub Actions)

`.github/workflows/ci.yml`에서 사용되는 환경 변수:

```yaml
env:
  REGISTRY_URL: registry.jclee.me
  IMAGE_NAME: safework
  DOCKER_BUILDKIT: 1
```

## 🚀 워크플로우

### CI Pipeline (.github/workflows/ci.yml)

1. **테스트 실행**
   - Python 3.11 환경 설정
   - PostgreSQL, Redis 서비스 시작
   - 의존성 설치 및 테스트 실행
   - 커버리지 리포트 생성

2. **보안 스캔**
   - Docker 이미지 빌드
   - Trivy 취약점 스캔
   - SARIF 리포트 업로드

3. **이미지 빌드 & 푸시**
   - Docker 이미지 빌드
   - registry.jclee.me에 푸시
   - 태그 전략: `prod-YYYYMMDD-SHA7`

4. **GitOps 배포**
   - K8s 매니페스트 업데이트
   - Git 커밋 및 푸시
   - ArgoCD 동기화 트리거

### CD Pipeline (.github/workflows/cd.yml)

1. **ArgoCD 동기화**
   - ArgoCD CLI 로그인
   - 애플리케이션 동기화
   - 배포 상태 확인

2. **배포 검증**
   - 헬스체크 실행
   - 배포 상태 알림

## 🔒 보안 설정

### ArgoCD 권한 관리

```yaml
# k8s/argocd/project-safework.yaml
roles:
  - name: safework-admin
    policies:
      - p, proj:safework-project:safework-admin, applications, *, safework-project/*, allow
  - name: safework-developer
    policies:
      - p, proj:safework-project:safework-developer, applications, get, safework-project/*, allow
```

### 네임스페이스 격리

```yaml
destinations:
  - namespace: safework          # 프로덕션
  - namespace: safework-dev      # 개발
  - namespace: safework-staging  # 스테이징
```

## 📊 모니터링

### ArgoCD 대시보드
- **URL**: https://argo.jclee.me/applications/safework-gitops
- **애플리케이션 상태**: 동기화 상태 및 헬스 체크
- **배포 히스토리**: 최근 10개 배포 기록

### 배포 상태 확인

```bash
# 애플리케이션 상태 확인
kubectl get application -n argocd safework-gitops

# 배포 정보 확인
kubectl get configmap -n safework deployment-info -o yaml

# 파드 상태 확인
kubectl get pods -n safework
```

## 🔄 롤백 절차

### 1. ArgoCD를 통한 롤백

```bash
# ArgoCD CLI로 롤백
argocd app rollback safework-gitops --revision <target-revision>

# 또는 웹 UI에서 원하는 리비전 선택 후 롤백
```

### 2. Git을 통한 롤백

```bash
# 이전 커밋으로 되돌리기
git revert <commit-hash>
git push origin main

# ArgoCD가 자동으로 감지하고 롤백 실행
```

## 🚨 트러블슈팅

### 일반적인 문제들

1. **이미지 풀 실패**
   ```bash
   # 레지스트리 인증 확인
   kubectl get secret regcred -n safework
   ```

2. **ArgoCD 동기화 실패**
   ```bash
   # 애플리케이션 상태 확인
   kubectl describe application safework-gitops -n argocd
   ```

3. **Git 푸시 실패**
   ```bash
   # GitHub Token 권한 확인
   # repo, workflow, write:packages 권한 필요
   ```

### 디버깅 명령어

```bash
# ArgoCD 로그 확인
kubectl logs -n argocd deployment/argocd-application-controller

# 동기화 상태 확인
kubectl get application -n argocd safework-gitops -o yaml

# 네임스페이스 이벤트 확인
kubectl get events -n safework --sort-by=.metadata.creationTimestamp
```

## 📈 성능 최적화

### 이미지 최적화
- 멀티 스테이지 빌드 사용
- 캐시 레이어 활용
- 최소 베이스 이미지 사용

### 동기화 최적화
- 자동 동기화 활성화
- 셀프 힐링 기능 사용
- 리소스 필터링 적용

## 🎯 다음 단계

1. **모니터링 설정**: Prometheus, Grafana 통합
2. **알림 설정**: Slack, Discord 통합
3. **다중 환경**: 개발, 스테이징, 프로덕션 환경 분리
4. **보안 강화**: OPA Gatekeeper 정책 적용
5. **백업**: ETCD 백업 및 복원 전략

## 📞 지원

- **ArgoCD 대시보드**: https://argo.jclee.me
- **프로덕션 URL**: https://safework.jclee.me
- **GitHub 저장소**: https://github.com/JCLEE94/safework