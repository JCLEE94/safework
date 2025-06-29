#!/bin/bash
set -e

echo "🚀 SafeWork Pro 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# 외부 PostgreSQL과 Redis 사용
echo "📊 외부 PostgreSQL 및 Redis 사용 중..."
echo "Database URL: $DATABASE_URL"
echo "Redis URL: $REDIS_URL"

# FastAPI 애플리케이션 시작
echo "🐍 FastAPI 서버 시작 중..."
cd /app

# 데이터베이스 연결 테스트
python -c "
import psycopg2
import os
import time

# 데이터베이스 연결 시도 (최대 30초 대기)
for i in range(30):
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'].replace('postgresql+asyncpg://', 'postgresql://'))
        conn.close()
        print('✅ 데이터베이스 연결 성공')
        break
    except Exception as e:
        print(f'⏳ 데이터베이스 연결 대기 중... ({i+1}/30)')
        time.sleep(1)
else:
    print('❌ 데이터베이스 연결 실패')
    exit(1)
"

# 데이터베이스 마이그레이션 실행
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
echo "🌐 접속 주소: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/api/docs"

# FastAPI 서버 실행 (포그라운드)
exec python main.py