#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중... (PostgreSQL 공식 방법)"
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# PostgreSQL 환경 설정 (공식 이미지 방식)
export PGDATA="/var/lib/postgresql/data"
export POSTGRES_DB="health_management"
export POSTGRES_USER="admin"
export POSTGRES_PASSWORD="safework123"

echo "📊 PostgreSQL 설정 중..."

# 필요한 디렉토리 생성
mkdir -p "$PGDATA"
mkdir -p /var/run/postgresql

# 권한 설정
chown -R postgres:postgres /var/lib/postgresql
chown -R postgres:postgres /var/run/postgresql

# PostgreSQL 초기화 (postgres 사용자로)
if [ ! -s "$PGDATA/PG_VERSION" ]; then
    echo "⚠️ PostgreSQL 초기화 중..."
    
    # 환경 변수를 postgres 사용자에게 전달하여 initdb 실행
    runuser -u postgres -- bash -c "
        export PGDATA='$PGDATA'
        export PATH=/usr/lib/postgresql/15/bin:\$PATH
        initdb --encoding=UTF8 --locale=C.UTF-8 --auth-local=trust --auth-host=md5
    "
    
    # 설정 파일 수정
    echo "listen_addresses = '*'" >> "$PGDATA/postgresql.conf"
    echo "port = 5432" >> "$PGDATA/postgresql.conf"
    echo "max_connections = 100" >> "$PGDATA/postgresql.conf"
    
    # pg_hba.conf 수정
    cat > "$PGDATA/pg_hba.conf" << EOF
# TYPE  DATABASE        USER            ADDRESS                 METHOD
local   all             all                                     trust
host    all             all             127.0.0.1/32            trust
host    all             all             ::1/128                 trust
host    all             all             0.0.0.0/0               md5
EOF

    chown postgres:postgres "$PGDATA/postgresql.conf"
    chown postgres:postgres "$PGDATA/pg_hba.conf"
fi

# PostgreSQL 시작
echo "🔥 PostgreSQL 서버 시작..."
runuser -u postgres -- bash -c "
    export PGDATA='$PGDATA'
    export PATH=/usr/lib/postgresql/15/bin:\$PATH
    pg_ctl start -w -t 60 -l /tmp/postgresql.log
"

# PostgreSQL 준비 확인
echo "⏳ PostgreSQL 연결 대기 중..."
for i in {1..30}; do
    if runuser -u postgres -- bash -c "export PATH=/usr/lib/postgresql/15/bin:\$PATH; pg_isready -h localhost -p 5432"; then
        echo "✅ PostgreSQL 준비 완료"
        break
    fi
    echo "재시도 중... ($i/30)"
    sleep 1
done

# 사용자 및 데이터베이스 생성
echo "👤 사용자 및 데이터베이스 설정..."
runuser -u postgres -- bash -c "export PATH=/usr/lib/postgresql/15/bin:\$PATH; psql -c \"DROP USER IF EXISTS admin;\"" || true
runuser -u postgres -- bash -c "export PATH=/usr/lib/postgresql/15/bin:\$PATH; psql -c \"CREATE USER admin WITH SUPERUSER PASSWORD 'safework123';\"" || true
runuser -u postgres -- bash -c "export PATH=/usr/lib/postgresql/15/bin:\$PATH; psql -c \"DROP DATABASE IF EXISTS health_management;\"" || true
runuser -u postgres -- bash -c "export PATH=/usr/lib/postgresql/15/bin:\$PATH; psql -c \"CREATE DATABASE health_management OWNER admin;\"" || true

# 연결 테스트
echo "🧪 데이터베이스 연결 테스트..."
if runuser -u postgres -- bash -c "export PATH=/usr/lib/postgresql/15/bin:\$PATH; psql -h localhost -U admin -d health_management -c 'SELECT 1;'" >/dev/null 2>&1; then
    echo "✅ 데이터베이스 연결 성공"
else
    echo "❌ 데이터베이스 연결 실패"
    echo "PostgreSQL 로그:"
    cat /tmp/postgresql.log || true
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