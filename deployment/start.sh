#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# PostgreSQL 초기화 및 시작
echo "📊 PostgreSQL 초기화 중..."

# PostgreSQL 데이터를 /app/pgdata에 저장 (권한 문제 회피)
export PGDATA=/app/pgdata
export PGUSER=postgres
mkdir -p $PGDATA || true

# PostgreSQL 바이너리 경로 찾기
PG_BIN=$(find /usr -name pg_ctl -type f 2>/dev/null | head -1 | xargs dirname)
echo "📁 PostgreSQL 바이너리 경로: $PG_BIN"

if [ ! -f $PGDATA/PG_VERSION ]; then
    # postgres 사용자로 전환하여 initdb 실행
    chown -R postgres:postgres $PGDATA
    su - postgres -c "$PG_BIN/initdb -D $PGDATA --locale=C --encoding=UTF8 --auth-local=trust --auth-host=md5"
    
    # 설정 파일 수정
    echo "host all all 0.0.0.0/0 md5" >> $PGDATA/pg_hba.conf
    echo "listen_addresses = '*'" >> $PGDATA/postgresql.conf
    echo "port = 5432" >> $PGDATA/postgresql.conf
    chown postgres:postgres $PGDATA/*.conf
fi

# PostgreSQL 시작 (백그라운드)
su - postgres -c "$PG_BIN/pg_ctl -D $PGDATA -l /app/postgresql.log start" || {
    echo "⚠️ PostgreSQL 시작 실패, 로그 확인:"
    cat /app/postgresql.log || true
    echo "📁 데이터 디렉토리 상태:"
    ls -la $PGDATA/ || true
    exit 1
}

# 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 생성 중..."
# PostgreSQL이 완전히 시작될 때까지 대기
sleep 5
export PGPASSWORD=postgres
su - postgres -c "$PG_BIN/psql -h localhost -c \"CREATE USER admin WITH PASSWORD 'safework123';\"" || true
su - postgres -c "$PG_BIN/psql -h localhost -c \"CREATE DATABASE health_management OWNER admin;\"" || true
su - postgres -c "$PG_BIN/psql -h localhost -c \"GRANT ALL PRIVILEGES ON DATABASE health_management TO admin;\"" || true

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 0.0.0.0 --port 6379

# 잠시 대기 (서비스 준비 시간)
sleep 5

# Nginx 제거 - FastAPI가 직접 정적 파일 서빙
echo "🌐 Nginx 없이 FastAPI 직접 서빙 설정..."

# 환경 변수 설정 (All-in-One)
export DATABASE_URL="postgresql+asyncpg://admin:safework123@localhost:5432/health_management"
export REDIS_URL="redis://localhost:6379/0"

# FastAPI 애플리케이션 시작
echo "🐍 FastAPI 서버 시작 중..."
cd /app

# 데이터베이스 마이그레이션 실행 (있는 경우)
python -c "
import asyncio
from src.config.database import init_db

async def main():
    try:
        await init_db()
        print('✅ 데이터베이스 초기화 완료')
    except Exception as e:
        print(f'⚠️ 데이터베이스 초기화 오류: {e}')

asyncio.run(main())
"

echo "🎉 SafeWork Pro 서버 시작 완료!"
echo "🌐 접속 주소: http://localhost:3001"
echo "📚 API 문서: http://localhost:3001/api/docs"

# FastAPI 서버 실행 (포그라운드)
exec python main.py