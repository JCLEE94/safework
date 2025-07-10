# GitHub Actions Workflows

## 활성 워크플로우

### 1. deploy-stable.yml (권장)
- **목적**: 안정화된 메인 CI/CD 파이프라인
- **특징**:
  - GitHub Container Registry (ghcr.io) 사용으로 413 오류 해결
  - 병렬 테스트 실행으로 속도 향상
  - 재시도 로직 및 헬스체크 강화
  - 자동 롤백 기능 포함

### 2. deploy-ghcr.yml
- **목적**: GitHub Container Registry 전용 간단한 배포
- **특징**: 최소 구성, 빠른 배포

### 3. test-quick.yml
- **목적**: PR용 빠른 테스트
- **특징**: 
  - 10분 내 완료
  - 필수 테스트만 실행
  - 코드 품질 체크 포함

### 4. deploy.yml (이전 버전)
- **상태**: 점진적 폐기 예정
- **문제**: 413 오류, 복잡한 구조

## 비활성 워크플로우 (.disabled)
- test.yml
- security.yml
- k8s-deploy.yml
- argocd-simple.yml
- build-deploy.yml
- main-cicd.yml
- main-deploy.yml

## 공통 환경 변수

```yaml
env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1
```

## Self-hosted Runner 설정

```yaml
# npm 캐시 권한 문제 해결
npm_config_cache: ${{ runner.temp }}/.npm

# 서비스 컨테이너 포트
postgres: 25432
redis: 26379
```

## 재사용 가능한 Actions

### retry-docker-push
- 위치: `.github/actions/retry-docker-push/action.yml`
- 용도: Docker push 실패 시 자동 재시도

## 헬퍼 스크립트

### health-check.sh
- 위치: `.github/scripts/health-check.sh`
- 용도: 배포 후 애플리케이션 상태 확인

### rollback.sh
- 위치: `.github/scripts/rollback.sh`
- 용도: 배포 실패 시 자동 롤백

## 트러블슈팅

### 413 Request Entity Too Large
- **해결**: GitHub Container Registry (ghcr.io) 사용
- **대안**: 이미지 크기 최적화

### 테스트 타임아웃
- **해결**: 병렬 실행, 타임아웃 세분화
- **설정**: pytest.ini의 timeout 값 조정

### npm 캐시 권한
- **해결**: `npm_config_cache: ${{ runner.temp }}/.npm`
- **적용**: self-hosted runner 전용

### 서비스 컨테이너 연결 실패
- **해결**: health check 재시도 횟수 증가
- **설정**: `--health-retries 10`, `--health-start-period 30s`

## 권장 사용법

### 새 기능 개발
1. feature 브랜치 생성
2. PR 생성 시 test-quick.yml 자동 실행
3. 머지 시 deploy-stable.yml 자동 실행

### 긴급 배포
```bash
# GitHub UI에서 workflow_dispatch 트리거
# 또는
gh workflow run deploy-stable.yml
```

### 롤백
```bash
# 자동 롤백 (배포 실패 시)
# 또는 수동 실행
.github/scripts/rollback.sh safework default
```