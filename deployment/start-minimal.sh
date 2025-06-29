#!/bin/bash

echo "🚀 SafeWork Pro 시작 중..."

# Redis 시작
redis-server --daemonize yes

# PostgreSQL 초기화 및 시작
if [ ! -d "/var/lib/postgresql/data" ]; then
    echo "PostgreSQL 초기화 중..."
    mkdir -p /var/lib/postgresql/data
    chown -R postgres:postgres /var/lib/postgresql
    su postgres -c "initdb -D /var/lib/postgresql/data"
fi

echo "PostgreSQL 시작 중..."
su postgres -c "pg_ctl start -D /var/lib/postgresql/data -l /tmp/postgresql.log"
sleep 5

# 데이터베이스 생성
su postgres -c "createuser -s admin" || true
su postgres -c "createdb -O admin health_management" || true
su postgres -c "psql -c \"ALTER USER admin PASSWORD 'safework123';\"" || true

# 환경변수 설정
export DATABASE_URL="postgresql://admin:safework123@localhost:5432/health_management"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

# FastAPI 시작
cd /app
exec uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2