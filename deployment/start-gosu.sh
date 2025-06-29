#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중... (gosu 버전)"
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# PostgreSQL 환경 변수 설정
export PGDATA="/var/lib/postgresql/data"
export POSTGRES_DB="health_management"
export POSTGRES_USER="admin"
export POSTGRES_PASSWORD="safework123"

echo "📊 PostgreSQL 초기화 및 시작..."

# PostgreSQL 데이터 디렉토리 준비
mkdir -p "$PGDATA"
mkdir -p /var/run/postgresql
mkdir -p /var/log/postgresql

# 권한 설정 (확실하게)
chown -R postgres:postgres /var/lib/postgresql
chown -R postgres:postgres /var/run/postgresql
chown -R postgres:postgres /var/log/postgresql
chmod 700 "$PGDATA"
chmod 755 /var/run/postgresql

# PostgreSQL 초기화 (gosu 사용)
if [ ! -f "$PGDATA/PG_VERSION" ]; then
    echo "⚠️ PostgreSQL 초기화 중..."
    gosu postgres initdb \
        --encoding=UTF8 \
        --locale=C.UTF-8 \
        --auth-local=trust \
        --auth-host=md5 \
        --username=postgres \
        --pwfile=<(echo 'postgres')
    
    # postgresql.conf 설정
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
    echo "port = 5432" >> "$PGDATA/postgresql.conf"
    echo "max_connections = 100" >> "$PGDATA/postgresql.conf"
    echo "log_destination = 'stderr'" >> "$PGDATA/postgresql.conf"
    echo "logging_collector = off" >> "$PGDATA/postgresql.conf"
    
    # pg_hba.conf 설정
    echo "local all all trust" > "$PGDATA/pg_hba.conf"
    echo "host all all 127.0.0.1/32 trust" >> "$PGDATA/pg_hba.conf"
    echo "host all all ::1/128 trust" >> "$PGDATA/pg_hba.conf"
    echo "host all all 0.0.0.0/0 md5" >> "$PGDATA/pg_hba.conf"
fi

# PostgreSQL 시작 (gosu 사용)
echo "🔥 PostgreSQL 서버 시작..."
gosu postgres pg_ctl start -D "$PGDATA" -l /var/log/postgresql/postgresql.log -w

# PostgreSQL 준비 확인
echo "⏳ PostgreSQL 연결 대기 중..."
for i in {1..30}; do
    if gosu postgres pg_isready -h localhost -p 5432; then
        echo "✅ PostgreSQL 준비 완료"
        break
    fi
    echo "재시도 중... ($i/30)"
    sleep 1
done

# 사용자 및 데이터베이스 생성
echo "👤 사용자 및 데이터베이스 설정..."
gosu postgres psql -c "CREATE USER admin WITH SUPERUSER PASSWORD 'safework123';" || true
gosu postgres psql -c "CREATE DATABASE health_management OWNER admin;" || true
gosu postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE health_management TO admin;" || true

# 연결 테스트
echo "🧪 데이터베이스 연결 테스트..."
if gosu postgres psql -h localhost -U admin -d health_management -c "SELECT 1;" >/dev/null 2>&1; then
    echo "✅ 데이터베이스 연결 성공"
else
    echo "❌ 데이터베이스 연결 실패"
    # 로그 출력
    echo "PostgreSQL 로그:"
    tail -20 /var/log/postgresql/postgresql.log || true
    exit 1
fi

# FastAPI 시작
echo "🎯 SafeWork Pro 백엔드 시작 중..."
export DATABASE_URL="postgresql://admin:safework123@localhost:5432/health_management"
export REDIS_URL="redis://localhost:6379/0"
export JWT_SECRET="safework-pro-jwt-secret-key-2024"
export PORT="${PORT:-3001}"

cd /app
exec uvicorn src.app:app --host 0.0.0.0 --port $PORT --workers 2