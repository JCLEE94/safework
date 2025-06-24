# Watchtower 라벨 가이드

## 🏷️ 필수 라벨

운영 서버의 Watchtower가 컨테이너를 자동 업데이트하려면 다음 라벨이 필요합니다:

```yaml
labels:
  # 필수: Watchtower 자동 업데이트 활성화
  - "com.centurylinklabs.watchtower.enable=true"
  
  # 권장: 안전한 종료를 위한 시그널
  - "com.centurylinklabs.watchtower.stop-signal=SIGTERM"
  
  # 권장: 종료 대기 시간
  - "com.centurylinklabs.watchtower.timeout=30s"
```

## 📍 라벨 위치

### docker-compose.yml
```yaml
services:
  health-app:
    image: registry.jclee.me/health-management-system:latest
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
      - "com.centurylinklabs.watchtower.stop-signal=SIGTERM"
      - "com.centurylinklabs.watchtower.timeout=30s"
```

### docker-compose.prod.yml
```yaml
services:
  health-app:
    image: registry.jclee.me/health-management-system:latest
    labels:
      # Watchtower 자동 업데이트 설정
      - "com.centurylinklabs.watchtower.enable=true"
      - "com.centurylinklabs.watchtower.stop-signal=SIGTERM"
      - "com.centurylinklabs.watchtower.timeout=30s"
      - "com.centurylinklabs.watchtower.scope=health"
```

## 🔧 추가 라벨 옵션

### 1. 업데이트 모니터링
```yaml
labels:
  # 특정 스코프로 그룹화
  - "com.centurylinklabs.watchtower.scope=health"
  
  # 업데이트 전/후 스크립트 실행
  - "com.centurylinklabs.watchtower.lifecycle.pre-update=/scripts/backup.sh"
  - "com.centurylinklabs.watchtower.lifecycle.post-update=/scripts/notify.sh"
```

### 2. 메타데이터
```yaml
labels:
  # Docker Compose 프로젝트 정보
  - "com.docker.compose.project=health"
  - "com.docker.compose.service=app"
  
  # 애플리케이션 정보
  - "org.label-schema.name=SafeWork Pro"
  - "org.label-schema.description=건설업 보건관리 시스템"
  - "org.label-schema.vendor=JC Lee"
  - "org.label-schema.url=http://192.168.50.215:3001"
```

## ✅ 라벨 확인 방법

### 1. 로컬에서 확인
```bash
# 라벨 확인
docker inspect health-management-system | grep -A 20 "Labels"

# Watchtower 라벨만 확인
docker inspect health-management-system | grep watchtower
```

### 2. 운영 서버에서 확인
```bash
ssh -p 1111 docker@192.168.50.215 'docker inspect health-management-system | grep watchtower'
```

## 🚀 적용 방법

### 1. 신규 배포
```bash
# GitHub Actions가 자동으로 처리
git push origin main
```

### 2. 기존 컨테이너 업데이트
```bash
# 운영 서버 라벨 업데이트 스크립트 실행
./update-production.sh
```

## ⚠️ 주의사항

1. **라벨 변경 시**: 컨테이너를 재생성해야 적용됨
   ```bash
   docker-compose up -d --force-recreate
   ```

2. **Watchtower 설정 확인**:
   ```bash
   # Watchtower가 label-enable 모드인지 확인
   docker logs watchtower | grep "label-enable"
   ```

3. **업데이트 제외하려면**:
   ```yaml
   labels:
     - "com.centurylinklabs.watchtower.enable=false"
   ```

## 📊 모니터링

```bash
# Watchtower 로그에서 업데이트 확인
docker logs watchtower | grep "health-management-system"

# 실시간 모니터링
docker logs -f watchtower | grep -E "(Checking|Found|Updated).*health"
```