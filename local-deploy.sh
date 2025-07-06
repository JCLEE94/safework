#!/bin/bash

# SafeWork 로컬 배포 스크립트
echo "🚀 SafeWork 로컬 배포 시작..."

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
docker stop safework postgres-safework redis-safework 2>/dev/null || true
docker rm safework postgres-safework redis-safework 2>/dev/null || true

# 네트워크 생성
echo "🌐 Docker 네트워크 생성..."
docker network create safework-network 2>/dev/null || true

# PostgreSQL 시작
echo "🐘 PostgreSQL 시작..."
docker run -d \
  --name postgres-safework \
  --restart unless-stopped \
  --network safework-network \
  -e POSTGRES_DB=health_management \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=safework123 \
  -e TZ=Asia/Seoul \
  -v $(pwd)/data/postgres:/var/lib/postgresql/data \
  postgres:15

# Redis 시작
echo "📮 Redis 시작..."
docker run -d \
  --name redis-safework \
  --restart unless-stopped \
  --network safework-network \
  -v $(pwd)/data/redis:/data \
  redis:7-alpine

# 잠시 대기
echo "⏳ 데이터베이스 초기화 대기..."
sleep 10

# SafeWork 시작
echo "🚀 SafeWork 애플리케이션 시작..."
docker run -d \
  --name safework \
  --restart unless-stopped \
  --network safework-network \
  -p 33301:3001 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="postgresql://admin:safework123@postgres-safework:5432/health_management" \
  -e REDIS_URL="redis://redis-safework:6379/0" \
  -e JWT_SECRET="safework-pro-secret-key-2024" \
  -e SECRET_KEY="safework-app-secret-2024" \
  -e HOST="0.0.0.0" \
  -e PORT="3001" \
  -e TZ="Asia/Seoul" \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/instance:/app/instance \
  safework:local

# 상태 확인
echo "📊 컨테이너 상태:"
docker ps | grep -E "safework|postgres|redis"

# 헬스체크
echo "🏥 헬스체크 대기..."
sleep 20

for i in {1..10}; do
    if curl -s http://localhost:33301/health | jq .; then
        echo "✅ SafeWork가 정상적으로 실행 중입니다!"
        echo "🔗 접속 주소: http://localhost:33301"
        exit 0
    else
        echo "⏳ 대기 중... ($i/10)"
        sleep 5
    fi
done

echo "❌ 헬스체크 실패. 로그 확인:"
docker logs safework --tail=50