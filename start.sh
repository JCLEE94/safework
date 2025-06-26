#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# PostgreSQL 초기화 및 시작
echo "📊 PostgreSQL 초기화 중..."

# PostgreSQL 사용자 생성 (이미 있을 수 있음)
id -u postgres &>/dev/null || useradd -r -s /bin/bash -d /var/lib/postgresql postgres

# PostgreSQL 데이터 디렉토리 권한 수정
mkdir -p /var/lib/postgresql/data
chown -R postgres:postgres /var/lib/postgresql
chmod 700 /var/lib/postgresql/data

if [ ! -f /var/lib/postgresql/data/PG_VERSION ]; then
    # postgres 사용자로 initdb 실행
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/data --locale=C --encoding=UTF8"
    
    # 설정 파일 수정
    echo "host all all 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf
    echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
fi

# PostgreSQL 시작
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/data -l /var/lib/postgresql/logfile start"

# 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 생성 중..."
su - postgres -c "psql -c \"CREATE USER admin WITH PASSWORD 'safework123';\"" || true
su - postgres -c "psql -c \"CREATE DATABASE health_management OWNER admin;\"" || true
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE health_management TO admin;\"" || true

# Redis 시작
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 0.0.0.0 --port 6379

# 잠시 대기 (서비스 준비 시간)
sleep 5

# Nginx 제거 - FastAPI가 직접 정적 파일 서빙
echo "🌐 Nginx 없이 FastAPI 직접 서빙 설정..."

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