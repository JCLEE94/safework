# Watchtower 자동 배포 설정 가이드

## 🚀 운영 서버 Watchtower 설정

### 1. Watchtower 설치 (운영 서버에서 실행)
```bash
# SSH 접속
ssh -p 1111 docker@192.168.50.215

# Watchtower 디렉토리 생성
mkdir -p /volume1/app/watchtower
cd /volume1/app/watchtower

# docker-compose.yml 생성
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/services/homes/docker/.docker/config.json:/config/config.json:ro
    environment:
      - WATCHTOWER_POLL_INTERVAL=30
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_LABEL_ENABLE=true
      - WATCHTOWER_ROLLING_RESTART=true
      - DOCKER_CONFIG=/config
      - WATCHTOWER_HTTP_API_SKIP_TLS_VERIFY=true
      - TZ=Asia/Seoul
    command: --interval 30 --cleanup
EOF

# Watchtower 시작
/usr/local/bin/docker-compose up -d
```

### 2. 애플리케이션 컨테이너 라벨 확인
```bash
# health 컨테이너에 Watchtower 라벨이 있는지 확인
docker inspect health-management-system | grep -A 5 Labels

# 필요시 라벨 추가
docker update --label-add com.centurylinklabs.watchtower.enable=true health-management-system
```

### 3. 동작 확인
```bash
# Watchtower 로그 확인
docker logs -f watchtower

# 예상 로그:
# time="2025-06-25T01:30:00+09:00" level=info msg="Watchtower 1.5.3"
# time="2025-06-25T01:30:00+09:00" level=info msg="Using authentication credentials from Docker config"
# time="2025-06-25T01:30:00+09:00" level=info msg="Checking for updates every 30 seconds"
```

## 🔄 배포 프로세스

### 개발자 작업
1. 코드 수정
2. `git push origin main`
3. **끝** - 나머지는 자동

### 자동 프로세스
1. GitHub Actions가 Docker 이미지 빌드
2. registry.jclee.me로 푸시
3. Watchtower가 30초 내 감지
4. 새 이미지 자동 pull
5. 컨테이너 재시작 (무중단)
6. 이전 이미지 정리

## 📊 모니터링

### Watchtower 상태 확인
```bash
# 실시간 로그
docker logs -f watchtower

# 최근 업데이트 확인
docker logs watchtower | grep "Found new"

# 컨테이너 업데이트 시간
docker inspect health-management-system | grep -A 2 "Started"
```

### 문제 해결
```bash
# Watchtower 재시작
docker restart watchtower

# 수동 이미지 업데이트 (테스트용)
docker pull registry.jclee.me/health:latest
docker-compose up -d health-app

# Registry 인증 확인
docker login registry.jclee.me
```

## ⚙️ 고급 설정

### 알림 설정 (선택사항)
```yaml
environment:
  # Slack 알림
  - WATCHTOWER_NOTIFICATIONS=slack
  - WATCHTOWER_NOTIFICATION_SLACK_HOOK_URL=https://hooks.slack.com/...
  
  # 이메일 알림
  - WATCHTOWER_NOTIFICATIONS=email
  - WATCHTOWER_NOTIFICATION_EMAIL_TO=admin@example.com
```

### 특정 컨테이너만 모니터링
```yaml
# 라벨 기반 필터링 (현재 설정)
- WATCHTOWER_LABEL_ENABLE=true

# 또는 이름 기반
command: --interval 30 health-management-system redis postgres
```

## 🔒 보안 고려사항

1. **Private Registry 인증**
   - Docker config.json 자동 마운트
   - 권한: 읽기 전용 (`:ro`)

2. **네트워크 보안**
   - Registry는 HTTPS 사용
   - 내부 네트워크만 허용

3. **컨테이너 격리**
   - Watchtower는 별도 컨테이너
   - 최소 권한 원칙 적용