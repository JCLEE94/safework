#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# PostgreSQL 시작 준비
echo "📊 PostgreSQL 시작 준비 중..."

# PostgreSQL 데이터 디렉토리 확인 및 초기화
if [ ! -d "/var/lib/postgresql/15/main" ]; then
    echo "⚠️ PostgreSQL 데이터 디렉토리가 없습니다. 초기화 중..."
    mkdir -p /var/lib/postgresql/15/main
    chown -R postgres:postgres /var/lib/postgresql
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/15/main"
fi

# PostgreSQL 설정 파일 수정 (listen_addresses)
if [ -f "/var/lib/postgresql/15/main/postgresql.conf" ]; then
    su - postgres -c "sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = '*'/g\" /var/lib/postgresql/15/main/postgresql.conf"
fi

# PostgreSQL 직접 시작 (시스템 서비스 사용하지 않음)
echo "📊 PostgreSQL 시작 중..."
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl start -D /var/lib/postgresql/15/main -l /var/log/postgresql/postgresql.log -o '-p 5432'" &

# PostgreSQL 시작 대기
sleep 5

# PostgreSQL이 준비될 때까지 대기
echo "⏳ PostgreSQL 준비 대기 중..."
for i in {1..30}; do
    if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo "✅ PostgreSQL 준비 완료"
        break
    fi
    sleep 1
done

# 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 생성 중..."
su - postgres -c "psql -c \"CREATE USER admin WITH PASSWORD 'safework123';\"" || true
su - postgres -c "psql -c \"CREATE DATABASE health_management OWNER admin;\"" || true
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE health_management TO admin;\"" || true

# 데이터베이스 마이그레이션
echo "🔄 데이터베이스 마이그레이션 실행 중..."
export DATABASE_URL="postgresql://admin:safework123@localhost:5432/health_management"
cd /app/backend 2>/dev/null || cd /app
alembic upgrade head || echo "⚠️ 마이그레이션 스킵 (이미 적용됨)"

# FastAPI 백엔드 시작
echo "🎯 SafeWork Pro 백엔드 시작 중..."
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

cd /app
# FastAPI를 포그라운드에서 실행
uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2