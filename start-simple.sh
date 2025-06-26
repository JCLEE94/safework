#!/bin/bash
set -e

echo "🚀 SafeWork Pro 단순화 버전 시작 중..."
echo "Build Time: $BUILD_TIME"
echo "Timezone: $TZ"

# Redis만 시작 (메모리 캐시용)
echo "📊 Redis 시작 중..."
redis-server --daemonize yes --bind 127.0.0.1 --port 6379

# 환경 변수 설정 (SQLite 사용)
export DATABASE_URL="sqlite:///app/data/health_management.db"
export REDIS_URL="redis://127.0.0.1:6379/0"

# 데이터 디렉토리 생성
mkdir -p /app/data

# FastAPI 애플리케이션 시작
echo "🐍 FastAPI 서버 시작 중..."
cd /app

echo "🎉 SafeWork Pro 서버 시작 완료!"
echo "🌐 접속 주소: http://localhost:3001"
echo "📚 API 문서: http://localhost:3001/api/docs"

# FastAPI 서버 실행 (포그라운드)
exec python main.py