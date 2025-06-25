#!/bin/bash

# SafeWork Pro Docker 직접 실행 스크립트
# docker-compose 없이 docker 명령어로 직접 실행

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SafeWork Pro 서비스 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 빌드 시간 설정
export BUILD_TIME="$(date +'%Y-%m-%d %H:%M:%S') KST"
echo -e "${GREEN}✓ 빌드 시간: $BUILD_TIME${NC}"

# 네트워크 생성
echo -e "${YELLOW}Docker 네트워크 생성 중...${NC}"
docker network create health-network 2>/dev/null || true

# 볼륨 생성
echo -e "${YELLOW}Docker 볼륨 생성 중...${NC}"
docker volume create postgres_data || true
docker volume create redis_data || true

# 기존 컨테이너 정리
echo -e "${YELLOW}기존 컨테이너 정리 중...${NC}"
docker stop health-postgres health-redis health-app-1 2>/dev/null || true
docker rm health-postgres health-redis health-app-1 2>/dev/null || true

# PostgreSQL 시작
echo -e "${YELLOW}PostgreSQL 시작 중...${NC}"
docker run -d \
    --name health-postgres \
    --network health-network \
    -e POSTGRES_USER=admin \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=health_management \
    -e TZ=Asia/Seoul \
    -v postgres_data:/var/lib/postgresql/data \
    --health-cmd="pg_isready -U admin -d health_management" \
    --health-interval=10s \
    --health-timeout=5s \
    --health-retries=5 \
    --restart unless-stopped \
    postgres:15-alpine

# Redis 시작
echo -e "${YELLOW}Redis 시작 중...${NC}"
docker run -d \
    --name health-redis \
    --network health-network \
    -v redis_data:/data \
    --health-cmd="redis-cli ping" \
    --health-interval=10s \
    --health-timeout=5s \
    --health-retries=5 \
    --restart unless-stopped \
    redis:7-alpine redis-server --appendonly yes

# 서비스 준비 대기
echo -e "${YELLOW}서비스 준비 대기 중...${NC}"
sleep 10

# 애플리케이션 이미지 빌드
echo -e "${YELLOW}애플리케이션 이미지 빌드 중...${NC}"
docker build \
    --build-arg BUILD_TIME="$BUILD_TIME" \
    -t health-app:latest \
    .

# 애플리케이션 시작
echo -e "${YELLOW}애플리케이션 시작 중...${NC}"
docker run -d \
    --name health-app-1 \
    --network health-network \
    -p 3001:8000 \
    -e DATABASE_URL=postgresql://admin:password@health-postgres:5432/health_management \
    -e REDIS_URL=redis://health-redis:6379/0 \
    -e JWT_SECRET=your-secret-key-here \
    -e DEBUG=false \
    -e LOG_LEVEL=INFO \
    -e TZ=Asia/Seoul \
    -v $(pwd)/uploads:/app/uploads \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/dist:/app/dist \
    --restart unless-stopped \
    health-app:latest

# 헬스체크 대기
echo -e "${YELLOW}서비스 준비 대기 중...${NC}"
RETRIES=30
while [ $RETRIES -gt 0 ]; do
    if curl -f http://localhost:3001/health >/dev/null 2>&1; then
        echo -e "${GREEN}✓ 서비스가 정상적으로 시작되었습니다!${NC}"
        break
    fi
    echo -n "."
    sleep 2
    RETRIES=$((RETRIES-1))
done

if [ $RETRIES -eq 0 ]; then
    echo -e "${RED}✗ 서비스 시작 실패${NC}"
    echo -e "${YELLOW}로그 확인:${NC}"
    docker logs --tail=50 health-app-1
    exit 1
fi

# 배포 정보 출력
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "접속 URL: ${GREEN}http://localhost:3001${NC}"
echo -e ""
echo -e "${YELLOW}컨테이너 상태:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep health
echo -e ""
echo -e "${YELLOW}유용한 명령어:${NC}"
echo -e "애플리케이션 로그: docker logs -f health-app-1"
echo -e "PostgreSQL 접속: docker exec -it health-postgres psql -U admin -d health_management"
echo -e "Redis 접속: docker exec -it health-redis redis-cli"
echo -e ""
echo -e "${GREEN}========================================${NC}"