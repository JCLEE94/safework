# SafeWork Pro CI/CD 설정 가이드

## 개요

SafeWork Pro는 GitOps 기반의 자동화된 CI/CD 파이프라인을 사용합니다.

### 아키텍처

```
GitHub Push → GitHub Actions → Docker Registry → ChartMuseum → ArgoCD → Kubernetes
     ↓              ↓               ↓              ↓           ↓          ↓
  코드 변경    → 병렬 테스트/빌드 → 이미지 저장 → 차트 업로드 → 자동 동기화 → 운영 배포
```

## 🚀 주요 구성 요소

### 1. GitHub Actions 워크플로우
- **위치**: `.github/workflows/safework-cicd.yml`
- **트리거**: main/develop 브랜치 push, 태그 push, PR
- **병렬 실행**: 코드 품질, 백엔드 테스트, 프론트엔드 빌드

### 2. Docker Registry
- **URL**: registry.jclee.me
- **이미지**: jclee94/safework
- **인증**: GitHub Secrets로 관리

### 3. Helm Chart
- **위치**: `k8s/helm/safework/`
- **저장소**: ChartMuseum (https://charts.jclee.me)
- **버전 관리**: 자동 태깅 및 업로드

### 4. ArgoCD
- **URL**: https://argo.jclee.me
- **Application**: safework-prod
- **동기화**: 자동 (Image Updater 포함)

## 🔧 필수 설정

### GitHub Secrets
```bash
# 레지스트리 인증
REGISTRY_USERNAME: admin
REGISTRY_PASSWORD: bingogo1

# ChartMuseum 인증
CHARTMUSEUM_USERNAME: admin
CHARTMUSEUM_PASSWORD: bingogo1

# Kubernetes 접근
K8S_TOKEN: [Kubernetes 서비스 계정 토큰]
```

### GitHub Variables
```bash
REGISTRY_URL: registry.jclee.me
CHARTMUSEUM_URL: https://charts.jclee.me
GITHUB_ORG: JCLEE94
APP_NAME: safework
K8S_CLUSTER: https://k8s.jclee.me:443
ARGOCD_URL: https://argo.jclee.me
```

## 📋 배포 프로세스

### 1. 자동 배포 (권장)
```bash
# 코드 변경 후 커밋 & 푸시
git add .
git commit -m "feat: 새로운 기능 추가"
git push origin main

# 결과: 자동으로 CI/CD 파이프라인 실행
# 1. 코드 품질 검사 (병렬)
# 2. 테스트 실행 (병렬)
# 3. Docker 이미지 빌드 & 푸시
# 4. ArgoCD Image Updater가 자동 감지 & 배포
```

### 2. 버전 릴리스
```bash
# 태그 생성 및 푸시
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# 결과: 추가로 Helm 차트 패키징 & 업로드
```

### 3. 수동 배포
```bash
# 운영 환경 설정
./scripts/setup-production.sh

# 시크릿 재생성
./scripts/recreate-secrets.sh
```

## 🔍 모니터링 및 디버깅

### 파이프라인 상태 확인
```bash
# GitHub Actions 상태
gh run list --limit 5

# ArgoCD 애플리케이션 상태
kubectl get application safework-prod -n argocd

# 운영 환경 Pod 상태
kubectl get pods -n production
```

### 로그 확인
```bash
# 애플리케이션 로그
kubectl logs -f deployment/safework -n production

# ArgoCD Image Updater 로그
kubectl logs -n argocd deployment/argocd-image-updater -f

# GitHub Actions 실패 로그
gh run view <run-id> --log-failed
```

### 문제 해결
```bash
# ArgoCD 강제 동기화
kubectl patch application safework-prod -n argocd \
  -p '{"operation":{"sync":{}}}' --type merge

# 배포 재시작
kubectl rollout restart deployment/safework -n production

# 이미지 확인
docker pull registry.jclee.me/jclee94/safework:latest
```

## 🛠️ 개발 워크플로우

### Pull Request 워크플로우
1. 기능 브랜치 생성: `git checkout -b feature/새기능`
2. 코드 변경 및 테스트 작성
3. PR 생성: 자동으로 테스트 실행 (배포는 실행되지 않음)
4. 코드 리뷰 및 승인
5. main 브랜치로 merge: 자동 배포 트리거

### 핫픽스 워크플로우
1. 핫픽스 브랜치: `git checkout -b hotfix/critical-fix`
2. 빠른 수정 및 테스트
3. main과 develop에 동시 merge
4. 필요시 즉시 태그 릴리스

## 📊 파이프라인 성능

### 실행 시간 (목표)
- 코드 품질 검사: ~5분
- 백엔드 테스트: ~10분 (병렬)
- 프론트엔드 빌드: ~8분 (병렬)
- Docker 빌드 & 푸시: ~15분
- ArgoCD 동기화: ~5분
- **총 소요시간: ~25-30분**

### 병렬 처리
- 코드 품질, 백엔드 테스트, 프론트엔드 빌드가 동시 실행
- 매트릭스 전략으로 단위/통합 테스트 병렬 실행

## 🔐 보안 고려사항

### 이미지 보안 스캔
- Trivy를 사용한 취약점 스캔
- 빌드 프로세스에서 자동 실행
- SARIF 형식으로 GitHub Security에 업로드

### 시크릿 관리
- 모든 민감정보는 GitHub Secrets로 관리
- Kubernetes 시크릿으로 런타임 보안
- 정기적인 시크릿 로테이션 권장

## 🔧 유용한 명령어

### 환경 설정
```bash
# GitHub Secrets 설정 (gh CLI 사용)
bash scripts/setup/environment-template.sh

# 로컬 환경 변수 로드
source scripts/setup/environment-template.sh

# kubeconfig 설정
export KUBECONFIG=k8s/kubeconfig-template.yaml
```

### 디버깅
```bash
# 레지스트리 연결 테스트
curl -u admin:bingogo1 https://registry.jclee.me/v2/_catalog

# ChartMuseum 연결 테스트  
curl -u admin:bingogo1 https://charts.jclee.me/api/charts

# 애플리케이션 헬스체크
curl https://safework.jclee.me/health
```

### 응급 복구
```bash
# 이전 버전으로 롤백
kubectl rollout undo deployment/safework -n production

# ArgoCD에서 수동 롤백
# 1. ArgoCD UI에서 History 탭 방문
# 2. 이전 버전 선택 후 Rollback

# 시크릿 문제 해결
bash scripts/recreate-secrets.sh
```

## 📈 모니터링 대시보드

### 접속 URL
- **프로덕션**: https://safework.jclee.me
- **ArgoCD**: https://argo.jclee.me
- **Registry**: https://registry.jclee.me  
- **Charts**: https://charts.jclee.me

### 상태 확인
- GitHub Actions: 레포지토리 Actions 탭
- ArgoCD: Applications 화면
- Kubernetes: `kubectl get all -n production`

---

## ⚡ Quick Start

새로운 개발자를 위한 빠른 시작 가이드:

```bash
# 1. 레포지토리 클론
git clone https://github.com/JCLEE94/safework.git
cd safework

# 2. 환경 설정 확인
source scripts/setup/environment-template.sh

# 3. 로컬 개발 환경 시작
docker-compose -f docker-compose.dev.yml up --build

# 4. 변경사항 커밋 (자동 배포 트리거)
git add .
git commit -m "feat: 새로운 기능"
git push origin main

# 5. 배포 상태 모니터링
gh run list --limit 3
kubectl get application safework-prod -n argocd -w
```

**🎉 이제 SafeWork Pro CI/CD 파이프라인이 준비되었습니다!**