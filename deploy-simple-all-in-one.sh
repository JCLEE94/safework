#!/bin/bash

# SafeWork Pro Simple All-in-One Container 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SafeWork Pro Simple All-in-One 배포${NC}"
echo -e "${GREEN}========================================${NC}"

# 빌드 시간 설정
export BUILD_TIME="$(date +'%Y-%m-%d %H:%M:%S') KST"
echo -e "${GREEN}✓ 빌드 시간: $BUILD_TIME${NC}"

# 기존 컨테이너 정리
echo -e "${YELLOW}기존 컨테이너 정리 중...${NC}"
docker stop safework-pro-simple health-app-1 health-postgres health-redis 2>/dev/null || true
docker rm safework-pro-simple health-app-1 health-postgres health-redis 2>/dev/null || true

# Docker 이미지 빌드
echo -e "${YELLOW}Docker 이미지 빌드 중...${NC}"
docker build \
    --build-arg BUILD_TIME="$BUILD_TIME" \
    -t safework-pro-simple:latest \
    -f Dockerfile.simple-all-in-one \
    .

# 볼륨 생성
echo -e "${YELLOW}Docker 볼륨 생성 중...${NC}"
docker volume create safework_postgres_data 2>/dev/null || true
docker volume create safework_app_uploads 2>/dev/null || true
docker volume create safework_app_logs 2>/dev/null || true
docker volume create safework_redis_data 2>/dev/null || true

# 네트워크 생성
echo -e "${YELLOW}Docker 네트워크 생성 중...${NC}"
docker network create safework-network 2>/dev/null || true

# 컨테이너 실행
echo -e "${YELLOW}컨테이너 시작 중...${NC}"
docker run -d \
    --name safework-pro-simple \
    --network safework-network \
    -p 3001:3001 \
    -v safework_postgres_data:/var/lib/postgresql/data \
    -v safework_app_uploads:/app/uploads \
    -v safework_app_logs:/app/logs \
    -v safework_redis_data:/var/lib/redis \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=safework123 \
    -e POSTGRES_DB=health_management \
    -e DATABASE_URL=postgresql://admin:safework123@localhost:5432/health_management \
    -e REDIS_URL=redis://localhost:6379/0 \
    -e JWT_SECRET=safework-pro-secret-key-2024 \
    -e DEBUG=false \
    -e LOG_LEVEL=INFO \
    -e TZ=Asia/Seoul \
    --restart unless-stopped \
    safework-pro-simple:latest

# 헬스체크 대기
echo -e "${YELLOW}서비스 준비 대기 중...${NC}"
RETRIES=60
while [ $RETRIES -gt 0 ]; do
    if curl -f http://localhost:3001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 서비스가 정상적으로 시작되었습니다!${NC}"
        break
    fi
    echo -n "."
    sleep 3
    RETRIES=$((RETRIES-1))
done

if [ $RETRIES -eq 0 ]; then
    echo -e "${RED}✗ 서비스 시작 실패${NC}"
    echo -e "${YELLOW}로그 확인:${NC}"
    docker logs --tail=50 safework-pro-simple
    exit 1
fi

# 배포 정보 출력
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "접속 URL: ${GREEN}http://localhost:3001${NC}"
echo -e "컨테이너: ${GREEN}safework-pro-simple${NC}"
echo -e ""
echo -e "${YELLOW}컨테이너 상태:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep safework
echo -e ""
echo -e "${YELLOW}유용한 명령어:${NC}"
echo -e "로그 확인: docker logs -f safework-pro-simple"
echo -e "컨테이너 접속: docker exec -it safework-pro-simple bash"
echo -e "PostgreSQL 접속: docker exec -it safework-pro-simple psql -U admin -d health_management"
echo -e "Redis 접속: docker exec -it safework-pro-simple redis-cli"
echo -e ""
echo -e "${YELLOW}볼륨 관리:${NC}"
echo -e "볼륨 목록: docker volume ls | grep safework"
echo -e "볼륨 정보: docker volume inspect safework_postgres_data"
echo -e ""
echo -e "${GREEN}========================================${NC}"