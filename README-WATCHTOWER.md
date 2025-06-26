# SafeWork Pro - Watchtower 자동 배포 가이드

## 🚀 개요

Watchtower를 사용한 무중단 자동 배포 시스템입니다. SSH 접속이나 수동 배포 없이 Docker 이미지 푸시만으로 자동 배포가 이루어집니다.

## 📋 설정 방법

### 1. 운영 서버에서 Watchtower 설치

```bash
# Docker 레지스트리 로그인
docker login registry.jclee.me -u qws941 -p bingogo1l7!

# Watchtower 실행
docker run -d \
  --name watchtower \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v ~/.docker/config.json:/config.json:ro \
  -e WATCHTOWER_POLL_INTERVAL=30 \
  -e WATCHTOWER_CLEANUP=true \
  -e WATCHTOWER_LABEL_ENABLE=true \
  -e DOCKER_CONFIG=/config.json \
  containrrr/watchtower:latest
```

### 2. SafeWork Pro 컨테이너 실행

```bash
docker run -d \
  --name safework \
  --restart unless-stopped \
  -p 3001:3001 \
  -v safework_data:/var/lib/postgresql/data \
  -v safework_redis:/var/lib/redis \
  -l "com.centurylinklabs.watchtower.enable=true" \
  registry.jclee.me/safework:latest
```

## 🔄 배포 프로세스

1. **코드 푸시**: `git push origin main`
2. **GitHub Actions**: 자동으로 테스트 및 Docker 이미지 빌드
3. **Registry Push**: `registry.jclee.me/safework:latest` 업데이트
4. **Watchtower 감지**: 30초 내에 새 이미지 감지
5. **자동 배포**: 기존 컨테이너 중지 → 새 컨테이너 시작
6. **헬스체크**: 실패 시 자동 롤백

## 📊 모니터링

### Watchtower 로그 확인
```bash
# 실시간 로그
docker logs -f watchtower

# 최근 업데이트 확인
docker logs watchtower | grep "Updated"
```

### 컨테이너 상태 확인
```bash
# 실행 중인 컨테이너
docker ps | grep safework

# 버전 확인
docker inspect safework | grep "BUILD_TIME"
```

## ⚙️ 설정 옵션

### Watchtower 환경 변수
- `WATCHTOWER_POLL_INTERVAL`: 확인 주기 (초, 기본: 30)
- `WATCHTOWER_CLEANUP`: 이전 이미지 자동 삭제 (기본: true)
- `WATCHTOWER_LABEL_ENABLE`: 라벨 필터링 사용 (기본: true)

### 컨테이너 라벨
```yaml
labels:
  - "com.centurylinklabs.watchtower.enable=true"  # Watchtower 감시 활성화
  - "com.centurylinklabs.watchtower.stop-signal=SIGTERM"  # 종료 시그널
  - "com.centurylinklabs.watchtower.timeout=60s"  # 종료 대기 시간
```

## 🚨 트러블슈팅

### 이미지를 못 찾는 경우
```bash
# 레지스트리 인증 재설정
docker logout registry.jclee.me
docker login registry.jclee.me -u qws941 -p bingogo1l7!

# Watchtower 재시작
docker restart watchtower
```

### 업데이트가 안 되는 경우
```bash
# 수동으로 이미지 확인
docker pull registry.jclee.me/safework:latest

# 라벨 확인
docker inspect safework | grep watchtower
```

## 🔐 보안 고려사항

1. **레지스트리 인증**: Docker config.json을 통한 안전한 인증
2. **네트워크 보안**: HTTPS를 통한 이미지 전송
3. **최소 권한**: Watchtower는 Docker 소켓 접근만 필요

## 📈 장점

- ✅ **무중단 배포**: 자동 롤링 업데이트
- ✅ **자동 롤백**: 헬스체크 실패 시 이전 버전 유지
- ✅ **간편한 설정**: 한 번 설정으로 영구 사용
- ✅ **리소스 효율**: 최소한의 리소스 사용
- ✅ **실시간 배포**: 푸시 후 1분 내 배포 완료