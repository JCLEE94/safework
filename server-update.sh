#!/bin/bash

# SafeWork 서버 업데이트 스크립트
# 192.168.50.110 서버용 자동 배포

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log "SafeWork 서버 업데이트 시작"

# 최신 이미지 풀
log "최신 이미지 가져오는 중..."
docker pull registry.jclee.me/safework:latest

# 기존 컨테이너 백업 (rollback용)
if docker ps -q -f name=safework | grep -q .; then
    log "기존 컨테이너 백업 중..."
    docker tag $(docker ps -q -f name=safework) safework:backup-$(date +%Y%m%d_%H%M%S) || true
fi

# 기존 컨테이너 중지 및 제거
log "기존 SafeWork 컨테이너 중지 중..."
docker stop safework 2>/dev/null || true
docker rm safework 2>/dev/null || true

# 데이터베이스/Redis 확인 및 시작
log "데이터베이스 상태 확인 중..."
if ! docker ps | grep -q postgres-safework; then
    log "PostgreSQL 시작 중..."
    docker run -d --name postgres-safework \
        --restart unless-stopped \
        -e POSTGRES_DB=health_management \
        -e POSTGRES_USER=admin \
        -e POSTGRES_PASSWORD=safework123 \
        -v /data/safework/postgres:/var/lib/postgresql/data \
        -p 5432:5432 \
        postgres:15
    sleep 10
fi

if ! docker ps | grep -q redis-safework; then
    log "Redis 시작 중..."
    docker run -d --name redis-safework \
        --restart unless-stopped \
        -v /data/safework/redis:/data \
        -p 6379:6379 \
        redis:7-alpine
    sleep 5
fi

# 새 SafeWork 컨테이너 시작
log "새 SafeWork 컨테이너 시작 중..."
docker run -d --name safework \
    --restart unless-stopped \
    -p 33301:3001 \
    -e DATABASE_URL="postgresql://admin:safework123@192.168.50.110:5432/health_management" \
    -e REDIS_URL="redis://192.168.50.110:6379/0" \
    -e JWT_SECRET_KEY="safework-jwt-secret-production" \
    -e SECRET_KEY="safework-encryption-key-production" \
    -e ENVIRONMENT="production" \
    -e DEBUG="false" \
    -e TZ="Asia/Seoul" \
    -e BACKEND_CORS_ORIGINS='["https://safework.jclee.me", "http://192.168.50.110:33301"]' \
    -v /data/safework/uploads:/app/uploads \
    registry.jclee.me/safework:latest

# 헬스체크
log "헬스체크 수행 중..."
sleep 30

for i in {1..10}; do
    if curl -f http://localhost:33301/health &> /dev/null; then
        success "헬스체크 성공!"
        break
    else
        warning "헬스체크 실패 (시도 $i/10), 10초 후 재시도..."
        sleep 10
    fi
done

# 컨테이너 상태 확인
log "컨테이너 상태:"
docker ps | grep safework

# 로그 확인
log "최근 로그:"
docker logs safework --tail 10

success "SafeWork 서버 업데이트 완료!"
echo ""
echo "=== 서비스 정보 ==="
echo "🌐 서버 URL: http://192.168.50.110:33301"
echo "🔗 도메인 URL: https://safework.jclee.me"
echo "📦 이미지: registry.jclee.me/safework:latest"
echo ""
echo "=== 관리 명령어 ==="
echo "로그 확인: docker logs safework -f"
echo "컨테이너 재시작: docker restart safework"
echo "상태 확인: docker ps | grep safework"