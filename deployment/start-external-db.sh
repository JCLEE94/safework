#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis 시작 (로컬)
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# 외부 PostgreSQL 서버 사용
echo "📊 외부 PostgreSQL 서버 연결 중..."
export DATABASE_URL="postgresql://admin:safework123@host.docker.internal:5432/health_management"

# Docker 내부에서 호스트 접근이 안 되면 직접 IP 사용
if ! pg_isready -h host.docker.internal -p 5432 >/dev/null 2>&1; then
    echo "⚠️ host.docker.internal 연결 실패, 직접 IP 사용"
    export DATABASE_URL="postgresql://admin:safework123@192.168.50.215:5432/health_management"
fi

# PostgreSQL 연결 테스트
echo "⏳ PostgreSQL 연결 대기 중..."
for i in {1..30}; do
    if pg_isready -d "$DATABASE_URL" >/dev/null 2>&1; then
        echo "✅ PostgreSQL 연결 성공"
        break
    fi
    echo "재시도 중... ($i/30)"
    sleep 2
done

# FastAPI 시작
echo "🎯 SafeWork Pro 백엔드 시작 중..."
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

cd /app
exec uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2