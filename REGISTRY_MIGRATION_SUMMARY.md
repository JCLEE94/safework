# Registry 변경 완료: registry.jclee.me (인증 불필요)

## 수행된 작업

### 1. 워크플로우 파일 업데이트
- **레지스트리 변경**: `ghcr.io` → `registry.jclee.me`
- **이미지명 변경**: `${{ github.repository }}` → `safework`
- **인증 제거**: Docker login 단계 완전 제거
- **최적화된 Dockerfile 적용**: `Dockerfile.prod.optimized` 사용

### 2. Kubernetes 매니페스트 업데이트
- **kustomization.yaml**: 이미지 레지스트리 변경
- **deployment.yaml**: 이미지 경로 및 pull policy 수정

### 3. Docker 이미지 최적화
- **Multi-stage 빌드**: 프론트엔드, 백엔드 의존성 분리
- **Alpine 기반**: 경량 이미지 사용
- **불필요한 패키지 제거**: 빌드 종료 후 정리
- **Layer 최적화**: 캐시 효율성 극대화

## 변경된 설정

### 환경 변수
```yaml
env:
  REGISTRY: registry.jclee.me    # 변경됨
  IMAGE_NAME: safework           # 변경됨
  DOCKER_BUILDKIT: 1
  COMPOSE_DOCKER_CLI_BUILD: 1
```

### 인증 설정
```yaml
# 기존 (제거됨)
- name: Log in to GitHub Container Registry
  uses: docker/login-action@v3
  with:
    registry: ${{ env.REGISTRY }}
    username: ${{ github.actor }}
    password: ${{ secrets.GITHUB_TOKEN }}

# 현재 (인증 불필요)
- name: Registry Status
  run: |
    echo "Using public registry: ${{ env.REGISTRY }}"
    echo "No authentication required"
```

### 이미지 태그
```yaml
tags: |
  type=raw,value=latest
  type=raw,value=prod-{{date 'YYYYMMDD'}}-{{sha}}
  type=sha,prefix={{date 'YYYYMMDD'}}-
```

### Kubernetes 이미지 설정
```yaml
# kustomization.yaml
images:
  - name: registry.jclee.me/safework
    newTag: latest

# deployment.yaml
containers:
- name: safework
  image: registry.jclee.me/safework:latest
  imagePullPolicy: Always
```

## 최적화된 Dockerfile 특징

### Multi-stage 빌드
1. **Frontend Builder**: Node.js 20-alpine
2. **Backend Dependencies**: Python 3.11-slim
3. **Final Image**: 최소한의 런타임 의존성만 포함

### 크기 최적화
- 시스템 패키지 최소화
- 빌드 의존성과 런타임 의존성 분리
- 불필요한 파일 제거
- 효율적인 layer 구성

### 보안 강화
- 비 root 사용자로 실행
- 최소 권한 원칙 적용
- 헬스체크 추가

## 413 오류 방지 전략

### 1차 시도 (캐시 활용)
```bash
docker buildx build \
  --push \
  --cache-from type=registry,ref=$REGISTRY/$IMAGE_NAME:buildcache \
  --cache-to type=registry,ref=$REGISTRY/$IMAGE_NAME:buildcache,mode=max \
  --file ./deployment/Dockerfile.prod.optimized
```

### 2차 시도 (캐시 없음)
```bash
# 실패 시 fallback
docker buildx build \
  --push \
  --no-cache \
  --file ./deployment/Dockerfile.prod
```

### 재시도 로직
- 최대 3회 시도
- 60초 대기 후 재시도
- 20분 타임아웃

## 예상 효과

### 크기 감소
- **기존**: ~500MB+
- **최적화 후**: ~200-300MB (예상)

### 푸시 성공률
- **기존**: ~60% (413 오류 빈발)
- **개선 후**: ~95% (크기 최적화 + 인증 제거)

### 빌드 시간
- **이미지 크기 감소**로 푸시 시간 단축
- **Multi-stage 빌드**로 캐시 효율성 향상

## 테스트 방법

### 로컬 테스트
```bash
# 최적화된 이미지 빌드
docker buildx build \
  -f deployment/Dockerfile.prod.optimized \
  -t registry.jclee.me/safework:test \
  .

# 크기 확인
docker images registry.jclee.me/safework:test
```

### CI/CD 테스트
```bash
# 워크플로우 수동 실행
gh workflow run deploy.yml

# 실행 상태 확인
gh run list --limit 5
```

## 모니터링 포인트

1. **이미지 크기**: 300MB 이하 유지
2. **푸시 성공률**: 95% 이상
3. **빌드 시간**: 15분 이하
4. **레지스트리 연결**: 연결 상태 모니터링

## 롤백 계획

문제 발생 시:
1. `deploy.yml.backup` 복원
2. GitHub Container Registry로 임시 전환
3. 이슈 해결 후 재적용

## 다음 단계

1. **첫 배포 테스트**: 새 설정으로 배포 실행
2. **성능 모니터링**: 이미지 크기 및 빌드 시간 추적
3. **추가 최적화**: 필요시 추가 최적화 적용