#!/bin/bash

# Production Server Update Script
# 운영 서버의 docker-compose.yml 업데이트 및 Watchtower 라벨 적용

set -e

# Configuration
REMOTE_HOST="192.168.50.215"
REMOTE_PORT="1111"
REMOTE_USER="docker"
REMOTE_PATH="~/app/health"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🚀 운영 서버 Watchtower 라벨 업데이트${NC}"
echo "========================================"

# Step 1: 현재 설정 백업
echo -e "\n${YELLOW}1. 현재 설정 백업${NC}"
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd ~/app/health
if [ -f docker-compose.yml ]; then
    cp docker-compose.yml docker-compose.yml.backup.$(date +%Y%m%d-%H%M%S)
    echo "✅ 백업 완료"
fi
EOF

# Step 2: docker-compose.prod.yml 복사
echo -e "\n${YELLOW}2. 새로운 docker-compose.yml 업로드${NC}"
scp -P $REMOTE_PORT docker-compose.prod.yml $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/docker-compose.yml
echo -e "${GREEN}✅ 업로드 완료${NC}"

# Step 3: 라벨 확인 및 적용
echo -e "\n${YELLOW}3. Watchtower 라벨 적용${NC}"
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd ~/app/health

# 현재 컨테이너 상태 확인
echo "현재 컨테이너 상태:"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep health || true

# 새로운 설정으로 재시작 (라벨 적용)
echo -e "\n컨테이너 재시작 중..."
/usr/local/bin/docker-compose up -d

# 라벨 확인
echo -e "\n적용된 라벨 확인:"
docker inspect health-management-system | grep -A 10 "Labels" | grep watchtower || echo "❌ Watchtower 라벨이 없습니다!"

# 헬스체크
echo -e "\n헬스체크 중..."
sleep 5
if curl -f http://localhost:3001/health > /dev/null 2>&1; then
    echo "✅ 애플리케이션 정상 작동"
else
    echo "❌ 헬스체크 실패"
fi
EOF

# Step 4: Watchtower 상태 확인
echo -e "\n${YELLOW}4. Watchtower 상태 확인${NC}"
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << 'EOF'
# Watchtower 실행 여부 확인
if docker ps | grep -q watchtower; then
    echo "✅ Watchtower 실행 중"
    echo -e "\n최근 로그:"
    docker logs watchtower --tail 5 2>&1 | grep -E "(Checking|Found|Updated)" || echo "아직 업데이트 로그 없음"
else
    echo "❌ Watchtower가 실행되고 있지 않습니다!"
    echo "다음 명령으로 Watchtower를 시작하세요:"
    echo "docker run -d --name watchtower --restart always -v /var/run/docker.sock:/var/run/docker.sock -v ~/.docker/config.json:/config.json:ro -e WATCHTOWER_POLL_INTERVAL=30 -e WATCHTOWER_LABEL_ENABLE=true -e DOCKER_CONFIG=/config.json containrrr/watchtower"
fi
EOF

# Summary
echo -e "\n${BLUE}📊 업데이트 요약${NC}"
echo "=================="
echo -e "${GREEN}✅ docker-compose.yml 업데이트 완료${NC}"
echo -e "${GREEN}✅ Watchtower 라벨 적용 완료${NC}"
echo ""
echo "이제 GitHub Actions에서 이미지를 푸시하면"
echo "Watchtower가 자동으로 배포합니다!"
echo ""
echo -e "${YELLOW}테스트 방법:${NC}"
echo "1. 코드 수정 후 git push origin main"
echo "2. GitHub Actions 완료 대기 (2-3분)"
echo "3. Watchtower 로그 확인: ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST 'docker logs -f watchtower'"