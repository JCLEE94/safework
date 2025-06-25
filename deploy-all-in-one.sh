#!/bin/bash

# SafeWork Pro All-in-One Container 배포 스크립트
# Single container deployment with PostgreSQL + Redis + App

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}SafeWork Pro All-in-One 컨테이너 배포${NC}"
echo -e "${GREEN}========================================${NC}"

# 환경 변수 로드
if [ -f .env.all-in-one ]; then
    export $(cat .env.all-in-one | grep -v '^#' | xargs)
    echo -e "${GREEN}✓ 환경 변수 로드 완료${NC}"
else
    echo -e "${YELLOW}⚠ .env.all-in-one 파일이 없습니다. 기본값을 사용합니다.${NC}"
fi

# 빌드 시간 설정
export BUILD_TIME="$(date +'%Y-%m-%d %H:%M:%S') KST"
echo -e "${GREEN}✓ 빌드 시간: $BUILD_TIME${NC}"

# 기존 컨테이너 정리
echo -e "${YELLOW}기존 컨테이너 정리 중...${NC}"
docker compose -f docker compose.all-in-one.yml down || true

# 볼륨 백업 옵션
if [ "$1" == "--backup-volumes" ]; then
    echo -e "${YELLOW}볼륨 백업 중...${NC}"
    BACKUP_DIR="./backups/$(date +'%Y%m%d_%H%M%S')"
    mkdir -p "$BACKUP_DIR"
    
    # PostgreSQL 데이터 백업
    if docker volume inspect safework-pro_postgres_data >/dev/null 2>&1; then
        docker run --rm -v safework-pro_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
        echo -e "${GREEN}✓ PostgreSQL 데이터 백업 완료${NC}"
    fi
    
    # 업로드 파일 백업
    if docker volume inspect safework-pro_app_uploads >/dev/null 2>&1; then
        docker run --rm -v safework-pro_app_uploads:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/app_uploads.tar.gz -C /data .
        echo -e "${GREEN}✓ 업로드 파일 백업 완료${NC}"
    fi
fi

# Docker 이미지 빌드
echo -e "${YELLOW}Docker 이미지 빌드 중...${NC}"
docker compose -f docker compose.all-in-one.yml build --no-cache

# 컨테이너 시작
echo -e "${YELLOW}컨테이너 시작 중...${NC}"
docker compose -f docker compose.all-in-one.yml up -d

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
    docker compose -f docker compose.all-in-one.yml logs --tail=50
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
echo -e "로그 확인: docker compose -f docker compose.all-in-one.yml logs -f"
echo -e "컨테이너 접속: docker exec -it safework-pro-all-in-one bash"
echo -e "PostgreSQL 접속: docker exec -it safework-pro-all-in-one psql -U admin -d health_management"
echo -e "Redis 접속: docker exec -it safework-pro-all-in-one redis-cli"
echo -e ""
echo -e "${YELLOW}볼륨 관리:${NC}"
echo -e "볼륨 목록: docker volume ls | grep safework"
echo -e "볼륨 정보: docker volume inspect safework-pro_postgres_data"
echo -e ""
echo -e "${GREEN}========================================${NC}"