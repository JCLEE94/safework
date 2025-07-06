#!/bin/bash

# SafeWork 직접 배포 스크립트 (ArgoCD 우회)
set -e

echo "🚀 SafeWork 직접 배포 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 서버 정보
DEPLOY_HOST="${DEPLOY_HOST:-192.168.50.110}"
DEPLOY_USER="${DEPLOY_USER:-jclee}"
DEPLOY_PORT="33301"

echo -e "${YELLOW}📦 Docker 이미지 준비...${NC}"

# 로컬에서 이미지 태그
docker tag safework:local registry.jclee.me/safework:direct-$(date +%Y%m%d-%H%M%S)

# 배포 스크립트 생성
cat > /tmp/safework-deploy.sh << 'EOF'
#!/bin/bash
set -e

echo "🔧 SafeWork 서버 배포 중..."

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
docker stop safework 2>/dev/null || true
docker rm safework 2>/dev/null || true

# 이미지 가져오기
echo "📥 최신 이미지 가져오기..."
docker pull registry.jclee.me/safework:latest || {
    echo "⚠️ Registry에서 이미지를 가져올 수 없습니다. 로컬 이미지 사용..."
}

# 새 컨테이너 실행
echo "🚀 새 컨테이너 시작..."
docker run -d \
  --name safework \
  --restart unless-stopped \
  -p 33301:3001 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="postgresql://admin:safework123@postgres-safework:5432/health_management" \
  -e REDIS_URL="redis://redis-safework:6379/0" \
  -e JWT_SECRET="safework-pro-secret-key-2024" \
  -e SECRET_KEY="safework-app-secret-2024" \
  -e HOST="0.0.0.0" \
  -e PORT="3001" \
  -e TZ="Asia/Seoul" \
  -v /data/safework/uploads:/app/uploads \
  -v /data/safework/logs:/app/logs \
  --network safework-network \
  registry.jclee.me/safework:latest

# 네트워크 생성 (없으면)
docker network create safework-network 2>/dev/null || true

# PostgreSQL 실행 (없으면)
if ! docker ps | grep -q postgres-safework; then
    echo "🐘 PostgreSQL 시작..."
    docker run -d \
      --name postgres-safework \
      --restart unless-stopped \
      --network safework-network \
      -e POSTGRES_DB=health_management \
      -e POSTGRES_USER=admin \
      -e POSTGRES_PASSWORD=safework123 \
      -v /data/safework/postgres:/var/lib/postgresql/data \
      postgres:15
    sleep 10
fi

# Redis 실행 (없으면)
if ! docker ps | grep -q redis-safework; then
    echo "📮 Redis 시작..."
    docker run -d \
      --name redis-safework \
      --restart unless-stopped \
      --network safework-network \
      -v /data/safework/redis:/data \
      redis:7-alpine
    sleep 5
fi

# 헬스체크
echo "🏥 헬스체크 중..."
sleep 20
for i in {1..10}; do
    if curl -s http://localhost:33301/health > /dev/null; then
        echo "✅ SafeWork가 정상적으로 실행 중입니다!"
        docker ps | grep safework
        exit 0
    else
        echo "⏳ 대기 중... ($i/10)"
        sleep 5
    fi
done

echo "❌ 헬스체크 실패"
docker logs safework --tail=50
exit 1
EOF

# 원격 서버에 스크립트 전송 및 실행
echo -e "${YELLOW}📤 원격 서버로 배포 스크립트 전송...${NC}"
scp /tmp/safework-deploy.sh ${DEPLOY_USER}@${DEPLOY_HOST}:/tmp/

echo -e "${YELLOW}🚀 원격 서버에서 배포 실행...${NC}"
ssh ${DEPLOY_USER}@${DEPLOY_HOST} "chmod +x /tmp/safework-deploy.sh && sudo /tmp/safework-deploy.sh"

# 정리
rm -f /tmp/safework-deploy.sh

echo -e "${GREEN}✅ 배포 완료!${NC}"
echo -e "${GREEN}🔗 접속 주소: http://${DEPLOY_HOST}:${DEPLOY_PORT}${NC}"
echo -e "${GREEN}🔗 도메인: https://safework.jclee.me${NC}"

# 최종 헬스체크
echo -e "${YELLOW}🏥 최종 헬스체크...${NC}"
sleep 5
if curl -s http://${DEPLOY_HOST}:${DEPLOY_PORT}/health | jq .; then
    echo -e "${GREEN}✅ 서비스가 정상적으로 작동 중입니다!${NC}"
else
    echo -e "${RED}⚠️ 서비스 접속 실패. 로그를 확인하세요.${NC}"
    ssh ${DEPLOY_USER}@${DEPLOY_HOST} "docker logs safework --tail=50"
fi