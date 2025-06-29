#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# PostgreSQL 초기화 및 시작
echo "📊 PostgreSQL 초기화 중..."

# PostgreSQL 사용자로 전환하여 작업
export PGDATA=/var/lib/postgresql/data
export PGUSER=postgres

# PostgreSQL 바이너리 경로
PG_BIN=/usr/lib/postgresql/15/bin

# postgres 사용자로 전환하여 PostgreSQL 초기화 및 시작
if [ ! -f $PGDATA/PG_VERSION ]; then
    echo "📁 PostgreSQL 데이터베이스 초기화..."
    mkdir -p $PGDATA
    chown -R postgres:postgres $PGDATA
    chmod 700 $PGDATA
    
    su - postgres -c "$PG_BIN/initdb -D $PGDATA --locale=ko_KR.UTF-8 --encoding=UTF8 --auth-local=trust --auth-host=md5"
    
    # 설정 파일 수정
    su - postgres -c "echo \"host all all 0.0.0.0/0 md5\" >> $PGDATA/pg_hba.conf"
    su - postgres -c "echo \"listen_addresses = '*'\" >> $PGDATA/postgresql.conf"
    su - postgres -c "echo \"port = 5432\" >> $PGDATA/postgresql.conf"
fi

# PostgreSQL 시작
echo "📊 PostgreSQL 시작 중..."
su - postgres -c "$PG_BIN/postgres -D $PGDATA" &
PG_PID=$!

# PostgreSQL이 준비될 때까지 대기
echo "⏳ PostgreSQL 준비 대기 중..."
for i in {1..30}; do
    if su - postgres -c "$PG_BIN/pg_isready -h localhost -p 5432" >/dev/null 2>&1; then
        echo "✅ PostgreSQL 준비 완료"
        break
    fi
    sleep 1
done

# 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 생성 중..."
su - postgres -c "$PG_BIN/psql -h localhost -p 5432 -c \"CREATE USER admin WITH PASSWORD 'safework123';\"" || true
su - postgres -c "$PG_BIN/psql -h localhost -p 5432 -c \"CREATE DATABASE health_management OWNER admin;\"" || true
su - postgres -c "$PG_BIN/psql -h localhost -p 5432 -c \"GRANT ALL PRIVILEGES ON DATABASE health_management TO admin;\"" || true

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 0.0.0.0 --port 6379

# 잠시 대기 (서비스 준비 시간)
sleep 2

# 데이터베이스 마이그레이션
echo "🔄 데이터베이스 마이그레이션 실행 중..."
export DATABASE_URL="postgresql://admin:safework123@localhost:5432/health_management"
cd /app/backend
alembic upgrade head || echo "⚠️ 마이그레이션 스킵 (이미 적용됨)"

# FastAPI 백엔드 시작
echo "🎯 SafeWork Pro 백엔드 시작 중..."
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

cd /app
# FastAPI를 포그라운드에서 실행 (PostgreSQL은 백그라운드에서 실행 중)
uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2