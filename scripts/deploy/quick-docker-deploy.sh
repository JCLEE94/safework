#!/bin/bash

# 기존 Docker 배포로 빠른 전환
# K8s 문제 해결 중 임시 사용

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

log "SafeWork Docker 배포 (K8s 대안)"

# 기존 컨테이너 정리
log "기존 SafeWork 컨테이너 정리 중..."
docker stop safework 2>/dev/null || true
docker rm safework 2>/dev/null || true

# 네트워크 생성 (있으면 무시)
docker network create safework-net 2>/dev/null || true

# PostgreSQL 컨테이너 시작
log "PostgreSQL 컨테이너 시작 중..."
docker run -d --name postgres-safework \
    --network safework-net \
    -e POSTGRES_DB=health_management \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=safework123 \
    -v /data/safework/postgres:/var/lib/postgresql/data \
    postgres:15 || warning "PostgreSQL 컨테이너가 이미 실행 중입니다"

# Redis 컨테이너 시작
log "Redis 컨테이너 시작 중..."
docker run -d --name redis-safework \
    --network safework-net \
    -v /data/safework/redis:/data \
    redis:7-alpine || warning "Redis 컨테이너가 이미 실행 중입니다"

# 잠시 대기
sleep 5

# SafeWork 앱 빌드 및 실행
log "SafeWork 앱 컨테이너 시작 중..."
cd /home/jclee/app/safework

# 환경변수 설정으로 컨테이너 실행
docker run -d --name safework \
    --network safework-net \
    -p 3001:3001 \
    -e DATABASE_URL="postgresql://admin:safework123@postgres-safework:5432/health_management" \
    -e REDIS_URL="redis://redis-safework:6379/0" \
    -e JWT_SECRET_KEY="your-super-secret-jwt-key" \
    -e SECRET_KEY="your-super-secret-encryption-key" \
    -e ENVIRONMENT="production" \
    -e TZ="Asia/Seoul" \
    -v /data/safework/uploads:/app/uploads \
    registry.jclee.me/safework:latest

sleep 10

# 상태 확인
log "컨테이너 상태 확인 중..."
docker ps | grep safework

# 헬스 체크
log "헬스 체크 수행 중..."
curl -f http://localhost:3001/health || warning "헬스 체크 실패"

success "SafeWork Docker 배포 완료!"
echo ""
echo "접속 URL: http://localhost:3001"
echo "로그 확인: docker logs safework -f"
echo "중지: docker stop safework postgres-safework redis-safework"