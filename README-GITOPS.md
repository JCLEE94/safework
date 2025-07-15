# SafeWork GitOps CI/CD 파이프라인

## 📋 개요

SafeWork Pro 프로젝트에 GitOps 방식의 CI/CD 파이프라인을 구성했습니다. 기존 Image Updater 방식에서 더 안정적인 GitHub Actions → ArgoCD 방식으로 전환합니다.

## 🏗️ 새로운 아키텍처

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Git Push      │───▶│ GitHub Actions  │───▶│ Docker Build    │
│   (main)        │    │   CI Pipeline   │    │ & Push Image    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                 │                       │
                                 ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   ArgoCD Sync   │◀───│ Update K8s      │◀───│ Push to         │
│   Deployment    │    │ Manifests       │    │ Registry        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│   Kubernetes    │
│   Cluster       │
└─────────────────┘
```

## 🚀 설정 단계

### 1. 기존 리소스 정리

```bash
# 기존 ArgoCD 애플리케이션 및 Image Updater 정리
./k8s/argocd/cleanup-old-apps.sh
```

### 2. GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions에서 다음 설정:

#### 필수 시크릿
- `DOCKER_USERNAME`: registry.jclee.me 사용자명
- `DOCKER_PASSWORD`: registry.jclee.me 비밀번호
- `ARGOCD_USERNAME`: ArgoCD 사용자명 (admin)
- `ARGOCD_PASSWORD`: ArgoCD 비밀번호
- `GITOPS_TOKEN`: GitHub 토큰 (repo 권한)

#### 선택적 시크릿
- `CODECOV_TOKEN`: 코드 커버리지 (선택사항)
- `CHARTMUSEUM_USERNAME`: 차트 저장소 사용자명
- `CHARTMUSEUM_PASSWORD`: 차트 저장소 비밀번호

### 3. Kubernetes 시크릿 설정

```bash
# 환경 변수 설정 후 실행
export DOCKER_USERNAME=your-username
export DOCKER_PASSWORD=your-password
export ARGOCD_USERNAME=admin
export ARGOCD_PASSWORD=your-password
export GITOPS_TOKEN=your-token

# 시크릿 설정 실행
./scripts/setup-secrets.sh
```

### 4. ArgoCD 애플리케이션 설정

```bash
# 새로운 GitOps 애플리케이션 설정
./k8s/argocd/setup-argocd.sh
```

### 5. 시스템 검증

```bash
# 전체 시스템 테스트
./scripts/test-gitops.sh
```

## 📁 파일 구조

### 새로 생성된 파일들

```
.github/workflows/
├── ci.yml                    # 새로운 CI 파이프라인
└── cd.yml                    # 새로운 CD 파이프라인

k8s/argocd/
├── application-gitops.yaml   # 새로운 ArgoCD 애플리케이션
├── project-safework.yaml     # ArgoCD 프로젝트 설정
├── cleanup-old-apps.sh       # 기존 리소스 정리
└── setup-argocd.sh          # ArgoCD 설정

scripts/
├── setup-secrets.sh         # 시크릿 설정
└── test-gitops.sh          # GitOps 테스트

docs/
└── GITOPS_SETUP.md         # 상세 설정 가이드
```

### 정리된 파일들

```
# 기존 파일들이 새로운 방식으로 대체됨
.github/workflows/ci-cd-pipeline.yml  → .github/workflows/ci.yml
k8s/argocd/application.yaml          → k8s/argocd/application-gitops.yaml
```

## 🔄 워크플로우

### CI 파이프라인 (`.github/workflows/ci.yml`)

**트리거**: `main`, `develop` 브랜치 push 또는 PR

1. **테스트 단계**
   - Python 환경 설정
   - PostgreSQL, Redis 서비스 시작
   - 의존성 설치 및 테스트 실행
   - 코드 커버리지 리포트

2. **보안 스캔**
   - Docker 이미지 빌드
   - Trivy 취약점 스캔
   - 보안 리포트 업로드

3. **이미지 빌드**
   - 멀티 플랫폼 Docker 이미지 빌드
   - registry.jclee.me에 푸시
   - 태그 전략: `prod-YYYYMMDD-SHA7`

4. **GitOps 배포**
   - K8s 매니페스트 업데이트
   - Git 커밋 및 푸시
   - ArgoCD 동기화 트리거

### CD 파이프라인 (`.github/workflows/cd.yml`)

**트리거**: K8s 매니페스트 변경 또는 수동 실행

1. **ArgoCD 동기화**
   - ArgoCD CLI 로그인
   - 애플리케이션 동기화
   - 배포 상태 확인

2. **배포 검증**
   - 애플리케이션 헬스체크
   - 배포 완료 알림

## 🔐 보안 설정

### RBAC 구성

```yaml
# ArgoCD 프로젝트 레벨 권한
roles:
  - name: safework-admin     # 전체 관리 권한
  - name: safework-developer # 읽기 및 동기화 권한
```

### 네임스페이스 격리

```yaml
destinations:
  - namespace: safework          # 프로덕션
  - namespace: safework-dev      # 개발
  - namespace: safework-staging  # 스테이징
```

## 📊 모니터링

### 주요 URL

- **ArgoCD 대시보드**: https://argo.jclee.me/applications/safework-gitops
- **프로덕션 서비스**: https://safework.jclee.me
- **헬스체크**: https://safework.jclee.me/health

### 명령어

```bash
# 애플리케이션 상태 확인
kubectl get application -n argocd safework-gitops

# 배포 정보 확인
kubectl get configmap -n safework deployment-info -o yaml

# 파드 상태 확인
kubectl get pods -n safework

# ArgoCD 로그
kubectl logs -n argocd deployment/argocd-application-controller
```

## 🔧 트러블슈팅

### 일반적인 문제

1. **GitHub Actions 실패**
   - 시크릿 설정 확인
   - 저장소 권한 확인
   - 워크플로우 로그 확인

2. **ArgoCD 동기화 실패**
   - 매니페스트 문법 확인
   - 네임스페이스 존재 확인
   - RBAC 권한 확인

3. **이미지 풀 실패**
   - 레지스트리 시크릿 확인
   - 이미지 태그 확인
   - 네트워크 연결 확인

### 디버깅 명령어

```bash
# 전체 시스템 상태 확인
./scripts/test-gitops.sh

# ArgoCD 애플리케이션 상세 정보
kubectl describe application safework-gitops -n argocd

# 이벤트 확인
kubectl get events -n safework --sort-by=.metadata.creationTimestamp

# 로그 확인
kubectl logs -n safework deployment/safework
```

## 🎯 다음 단계

1. **첫 배포 테스트**
   ```bash
   # 작은 변경사항 커밋
   git add .
   git commit -m "test: GitOps 파이프라인 테스트"
   git push origin main
   ```

2. **모니터링 설정**
   - Prometheus, Grafana 통합
   - 알림 설정 (Slack, Discord)

3. **다중 환경 구성**
   - 개발, 스테이징 환경 분리
   - 환경별 브랜치 전략

4. **보안 강화**
   - OPA Gatekeeper 정책
   - 시크릿 관리 (Sealed Secrets)

## 💡 주요 개선사항

1. **안정성 향상**
   - Image Updater 의존성 제거
   - 명시적 Git 커밋 기록
   - 더 나은 오류 처리

2. **투명성 개선**
   - 모든 배포 변경사항이 Git 히스토리에 기록
   - 배포 정보 ConfigMap 자동 생성
   - 상세한 로그 및 메트릭

3. **유연성 증대**
   - 환경별 워크플로우 분리
   - 수동 배포 지원
   - 롤백 기능 향상

## 📞 지원

문제 발생 시 다음을 확인해주세요:

1. **GitHub Actions 로그**: 저장소 Actions 탭
2. **ArgoCD 대시보드**: https://argo.jclee.me
3. **시스템 테스트**: `./scripts/test-gitops.sh`
4. **설정 가이드**: `docs/GITOPS_SETUP.md`

---

**GitOps 파이프라인 버전**: 1.0.0  
**마지막 업데이트**: 2025-01-15  
**관리자**: SafeWork Pro 개발팀