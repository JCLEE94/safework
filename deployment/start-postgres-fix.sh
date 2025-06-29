#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# PostgreSQL 시작 - 더 간단한 접근법
echo "📊 PostgreSQL 시작 중..."

# postgres 사용자로 전환하여 실행
export PGDATA="/var/lib/postgresql/data"
export POSTGRES_USER="admin"
export POSTGRES_PASSWORD="safework123"
export POSTGRES_DB="health_management"

# 데이터 디렉토리 생성
mkdir -p "$PGDATA"
chown -R postgres:postgres /var/lib/postgresql

# postgres 사용자로 PostgreSQL 초기화 및 시작
su - postgres -s /bin/bash << 'EOF'
export PGDATA="/var/lib/postgresql/data"

# 초기화 (필요한 경우)
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "PostgreSQL 초기화 중..."
    initdb --encoding=UTF8 --locale=C.UTF-8
fi

# PostgreSQL 시작
pg_ctl start -l /tmp/postgresql.log

# 대기
sleep 5

# 사용자 및 데이터베이스 생성
createuser -s admin || true
psql -c "ALTER USER admin PASSWORD 'safework123';" || true
createdb -O admin health_management || true
EOF

# FastAPI 시작
echo "🎯 SafeWork Pro 백엔드 시작 중..."
export DATABASE_URL="postgresql://admin:safework123@localhost:5432/health_management"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

cd /app
uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2