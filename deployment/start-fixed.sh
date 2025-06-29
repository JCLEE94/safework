#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# PostgreSQL 시작 (외부 PostgreSQL 사용)
echo "📊 PostgreSQL 연결 대기 중..."
# 외부 PostgreSQL 서버 사용 (192.168.50.215:5432)
export DATABASE_URL="postgresql://admin:safework123@192.168.50.215:5432/health_management"

# FastAPI 백엔드 시작
echo "🎯 SafeWork Pro 백엔드 시작 중..."
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

cd /app
# FastAPI를 포그라운드에서 실행
uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2