#!/bin/bash

# SafeWork Pro 서비스 상태 체크 스크립트

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}SafeWork Pro 서비스 상태 점검${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Docker 상태 체크
echo -e "${YELLOW}1. Docker 서비스 상태${NC}"
if systemctl is-active --quiet docker; then
    echo -e "${GREEN}✓ Docker 서비스 실행 중${NC}"
else
    echo -e "${RED}✗ Docker 서비스가 실행되지 않음${NC}"
    echo -e "${YELLOW}  시작 명령: sudo systemctl start docker${NC}"
fi
echo ""

# 2. 실행 중인 컨테이너 체크
echo -e "${YELLOW}2. 실행 중인 컨테이너${NC}"
CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(health|safework)" || echo "없음")
if [ "$CONTAINERS" = "없음" ]; then
    echo -e "${RED}✗ SafeWork Pro 관련 컨테이너가 실행되지 않음${NC}"
else
    echo "$CONTAINERS"
fi
echo ""

# 3. 포트 체크
echo -e "${YELLOW}3. 포트 상태${NC}"
for PORT in 3001 8000; do
    if ss -tuln | grep -q ":$PORT "; then
        echo -e "${GREEN}✓ 포트 $PORT: 사용 중${NC}"
        PROCESS=$(ss -tlnp | grep ":$PORT " 2>/dev/null | awk '{print $NF}' || echo "알 수 없음")
        echo -e "  프로세스: $PROCESS"
    else
        echo -e "${RED}✗ 포트 $PORT: 미사용${NC}"
    fi
done
echo ""

# 4. Docker Compose 파일 체크
echo -e "${YELLOW}4. Docker Compose 설정 파일${NC}"
for FILE in docker-compose.yml docker-compose.all-in-one.yml docker-compose.dev.yml docker-compose.prod.yml; do
    if [ -f "$FILE" ]; then
        echo -e "${GREEN}✓ $FILE 존재${NC}"
    else
        echo -e "${RED}✗ $FILE 없음${NC}"
    fi
done
echo ""

# 5. 환경변수 파일 체크
echo -e "${YELLOW}5. 환경변수 파일${NC}"
for FILE in .env .env.all-in-one .env.development .env.production; do
    if [ -f "$FILE" ]; then
        echo -e "${GREEN}✓ $FILE 존재${NC}"
    else
        echo -e "${YELLOW}○ $FILE 없음${NC}"
    fi
done
echo ""

# 6. 빌드된 파일 체크
echo -e "${YELLOW}6. 빌드 아티팩트${NC}"
if [ -d "dist" ] && [ -f "dist/index.html" ]; then
    echo -e "${GREEN}✓ React 빌드 파일 존재${NC}"
    echo -e "  dist 크기: $(du -sh dist | cut -f1)"
else
    echo -e "${RED}✗ React 빌드 파일 없음${NC}"
    echo -e "${YELLOW}  빌드 명령: npm run build${NC}"
fi
echo ""

# 7. 헬스체크
echo -e "${YELLOW}7. 헬스체크 시도${NC}"
for PORT in 3001 8000; do
    echo -n "포트 $PORT 체크 중... "
    if timeout 2 curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ 응답 성공${NC}"
        RESPONSE=$(curl -s http://localhost:$PORT/health | head -c 100)
        echo -e "  응답: $RESPONSE..."
    else
        echo -e "${RED}✗ 응답 없음${NC}"
    fi
done
echo ""

# 8. 배포 권장사항
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}배포 권장사항${NC}"
echo -e "${BLUE}========================================${NC}"

if ! docker ps | grep -q -E "(health|safework)"; then
    echo -e "${YELLOW}서비스가 실행되지 않고 있습니다. 다음 명령어로 시작하세요:${NC}"
    echo ""
    echo -e "${GREEN}1. 일반 배포 (3개 컨테이너):${NC}"
    echo "   cd /home/jclee/app/health"
    echo "   docker-compose up -d"
    echo ""
    echo -e "${GREEN}2. All-in-One 배포 (단일 컨테이너):${NC}"
    echo "   cd /home/jclee/app/health"
    echo "   ./deploy-all-in-one.sh"
    echo ""
    echo -e "${GREEN}3. 개발 모드:${NC}"
    echo "   cd /home/jclee/app/health"
    echo "   docker-compose -f docker-compose.dev.yml up -d"
fi

echo ""
echo -e "${BLUE}========================================${NC}"