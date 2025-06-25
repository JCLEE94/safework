#!/bin/bash

# SafeWork Pro All-in-One Container 직접 실행 스크립트
# docker-compose 없이 docker run으로 직접 실행

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SafeWork Pro All-in-One 컨테이너 시작${NC}"
echo -e "${GREEN}========================================${NC}"

# 환경 변수 로드
if [ -f .env.all-in-one ]; then
    set -a
    source .env.all-in-one
    set +a
    echo -e "${GREEN}✓ 환경 변수 로드 완료${NC}"
else
    echo -e "${YELLOW}⚠ .env.all-in-one 파일이 없습니다. 기본값을 사용합니다.${NC}"
fi

# 빌드 시간 설정
export BUILD_TIME="$(date +'%Y-%m-%d %H:%M:%S') KST"
echo -e "${GREEN}✓ 빌드 시간: $BUILD_TIME${NC}"

# 기존 컨테이너 정리
echo -e "${YELLOW}기존 컨테이너 정리 중...${NC}"
docker stop safework-pro-all-in-one 2>/dev/null || true
docker rm safework-pro-all-in-one 2>/dev/null || true

# Docker 이미지 빌드
echo -e "${YELLOW}Docker 이미지 빌드 중...${NC}"
docker build \
    --build-arg BUILD_TIME="$BUILD_TIME" \
    --build-arg DATABASE_URL="$DATABASE_URL" \
    --build-arg REDIS_URL="$REDIS_URL" \
    --build-arg JWT_SECRET="$JWT_SECRET" \
    --build-arg DEBUG="$DEBUG" \
    --build-arg LOG_LEVEL="$LOG_LEVEL" \
    -t safework-pro-aio:latest \
    -f Dockerfile.all-in-one \
    .

# 볼륨 생성
echo -e "${YELLOW}Docker 볼륨 생성 중...${NC}"
docker volume create safework-pro_postgres_data || true
docker volume create safework-pro_app_uploads || true
docker volume create safework-pro_app_logs || true
docker volume create safework-pro_redis_data || true

# 컨테이너 실행
echo -e "${YELLOW}컨테이너 시작 중...${NC}"
docker run -d \
    --name safework-pro-all-in-one \
    -p 3001:3001 \
    -v safework-pro_postgres_data:/var/lib/postgresql/data \
    -v safework-pro_app_uploads:/app/uploads \
    -v safework-pro_app_logs:/app/logs \
    -v safework-pro_redis_data:/var/lib/redis \
    -e POSTGRES_USER="$POSTGRES_USER" \
    -e POSTGRES_PASSWORD="$POSTGRES_PASSWORD" \
    -e POSTGRES_DB="$POSTGRES_DB" \
    -e DATABASE_URL="$DATABASE_URL" \
    -e REDIS_URL="$REDIS_URL" \
    -e JWT_SECRET="$JWT_SECRET" \
    -e DEBUG="$DEBUG" \
    -e LOG_LEVEL="$LOG_LEVEL" \
    -e TZ="$TZ" \
    --restart unless-stopped \
    safework-pro-aio:latest

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
    docker logs --tail=50 safework-pro-all-in-one
    exit 1
fi

# 배포 정보 출력
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}배포 완료!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "접속 URL: ${GREEN}http://localhost:3001${NC}"
echo -e "컨테이너: ${GREEN}safework-pro-all-in-one${NC}"
echo -e ""
echo -e "${YELLOW}유용한 명령어:${NC}"
echo -e "로그 확인: docker logs -f safework-pro-all-in-one"
echo -e "컨테이너 접속: docker exec -it safework-pro-all-in-one bash"
echo -e "PostgreSQL 접속: docker exec -it safework-pro-all-in-one psql -U admin -d health_management"
echo -e "Redis 접속: docker exec -it safework-pro-all-in-one redis-cli"
echo -e ""
echo -e "${YELLOW}볼륨 관리:${NC}"
echo -e "볼륨 목록: docker volume ls | grep safework"
echo -e "볼륨 정보: docker volume inspect safework-pro_postgres_data"
echo -e ""
echo -e "${GREEN}========================================${NC}"