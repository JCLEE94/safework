#!/bin/bash
set -e

echo "🚀 SafeWork Pro 빠른 배포 (로컬 빌드)"
echo "===================================="

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. 기존 컨테이너 중지
echo -e "${BLUE}기존 컨테이너 중지 중...${NC}"
docker stop safework-single 2>/dev/null || echo "중지할 컨테이너가 없습니다"
docker rm safework-single 2>/dev/null || echo "제거할 컨테이너가 없습니다"

# 2. 프론트엔드 빌드
echo -e "${BLUE}프론트엔드 빌드 중...${NC}"
npm install --silent
npm run build

# 3. Docker 이미지 빌드
echo -e "${BLUE}SafeWork Pro 이미지 빌드 중...${NC}"
BUILD_TIME="$(date +'%Y-%m-%d %H:%M:%S KST')"
docker build -f Dockerfile.registry \
  --build-arg BUILD_TIME="$BUILD_TIME" \
  -t safework:latest \
  -t registry.jclee.me/safework:latest \
  .

# 4. 컨테이너 실행
echo -e "${BLUE}SafeWork Pro 컨테이너 실행 중...${NC}"
docker run -d \
  --name safework-single \
  -p 3001:3001 \
  --restart unless-stopped \
  safework:latest

# 5. 헬스체크 대기
echo -e "${YELLOW}헬스체크 대기 중...${NC}"
for i in {1..12}; do
    if curl -s http://localhost:3001/health > /dev/null; then
        echo -e "${GREEN}✅ SafeWork Pro 배포 성공!${NC}"
        break
    else
        echo "헬스체크 대기... ($i/12)"
        sleep 5
    fi
    
    if [ $i -eq 12 ]; then
        echo -e "${RED}❌ 헬스체크 실패${NC}"
        docker logs safework-single --tail 20
        exit 1
    fi
done

# 6. 상태 확인
echo ""
echo "🎉 SafeWork Pro 배포 완료!"
echo "========================="
echo ""
echo "📊 서비스 정보:"
echo "- 🏠 Local URL: http://localhost:3001"
echo "- 🏠 Network URL: http://192.168.50.215:3001"
echo "- ❤️  헬스체크: http://localhost:3001/health"
echo "- 📖 API 문서: http://localhost:3001/api/docs"
echo ""
echo "🐳 컨테이너 상태:"
docker ps --filter "name=safework-single" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "📋 헬스체크 응답:"
curl -s http://localhost:3001/health | jq . 2>/dev/null || curl -s http://localhost:3001/health
echo ""
echo "🔧 유용한 명령어:"
echo "- 로그 확인: docker logs safework-single"
echo "- 컨테이너 재시작: docker restart safework-single"
echo "- 컨테이너 중지: docker stop safework-single"