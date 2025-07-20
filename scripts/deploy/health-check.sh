#!/bin/bash
# Health check script for SafeWork deployment
# 안정화된 헬스체크 스크립트

set -e

# 설정
SERVER_IP="${SERVER_IP:-192.168.50.110}"
NODE_PORT="${NODE_PORT:-32301}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
SLEEP_TIME="${SLEEP_TIME:-10}"

# 색상 코드
GREEN='[0;32m'
YELLOW='[1;33m'
RED='[0;31m'
NC='[0m' # No Color

echo "🏥 SafeWork Deployment Health Check"
echo "=================================="
echo "Target: http://${SERVER_IP}:${NODE_PORT}"
echo "Max attempts: ${MAX_ATTEMPTS}"
echo ""

# 헬스체크 함수
check_endpoint() {
    local endpoint=$1
    local description=$2
    
    if curl -s -f -o /dev/null "http://${SERVER_IP}:${NODE_PORT}${endpoint}" 2>/dev/null; then
        echo -e "${GREEN}✅ ${description}${NC}"
        return 0
    else
        echo -e "${RED}❌ ${description}${NC}"
        return 1
    fi
}

# 메인 헬스체크 루프
for i in $(seq 1 $MAX_ATTEMPTS); do
    echo -e "${YELLOW}[Attempt $i/$MAX_ATTEMPTS]${NC}"
    
    # 기본 헬스체크
    if check_endpoint "/health" "Health endpoint"; then
        # 추가 엔드포인트 검증
        check_endpoint "/api/docs" "API documentation" || true
        check_endpoint "/qr-register" "QR registration page" || true
        
        # 응답 시간 체크
        response_time=$(curl -o /dev/null -s -w '%{time_total}' "http://${SERVER_IP}:${NODE_PORT}/health")
        echo -e "${GREEN}⏱️  Response time: ${response_time}s${NC}"
        
        # 성공
        echo ""
        echo -e "${GREEN}🎉 Deployment is healthy!${NC}"
        exit 0
    fi
    
    # 실패 시 대기
    if [ $i -lt $MAX_ATTEMPTS ]; then
        echo -e "${YELLOW}⏳ Waiting ${SLEEP_TIME} seconds before retry...${NC}"
        sleep $SLEEP_TIME
    fi
    echo ""
done

# 최종 실패
echo -e "${RED}💔 Health check failed after $MAX_ATTEMPTS attempts${NC}"
echo "Please check:"
echo "- Pod status: kubectl get pods -n safework"
echo "- Pod logs: kubectl logs -n safework -l app=safework"
echo "- Service: kubectl get svc -n safework"
exit 1