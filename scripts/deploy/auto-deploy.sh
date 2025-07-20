#!/bin/bash
# 자동 배포 스크립트
# CI/CD 파이프라인과 연동하여 안정적인 배포 수행

set -e

# 색상 코드
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# 설정
NAMESPACE="safework"
APP_NAME="safework"
REGISTRY="registry.jclee.me"
TIMEOUT=300

echo -e "${BLUE}🚀 SafeWork Auto Deployment${NC}"
echo "============================"
echo "Namespace: $NAMESPACE"
echo "App: $APP_NAME"
echo ""

# 1. ArgoCD 동기화 상태 확인
echo -e "${YELLOW}1. Checking ArgoCD sync status...${NC}"
if command -v argocd &> /dev/null; then
    SYNC_STATUS=$(argocd app get $APP_NAME -o json | jq -r '.status.sync.status' 2>/dev/null || echo "Unknown")
    echo "Sync status: $SYNC_STATUS"
    
    if [ "$SYNC_STATUS" == "OutOfSync" ]; then
        echo -e "${YELLOW}Syncing application...${NC}"
        argocd app sync $APP_NAME --force || true
    fi
else
    echo -e "${YELLOW}ArgoCD CLI not available, using kubectl${NC}"
fi

# 2. 현재 deployment 상태 확인
echo -e "${YELLOW}2. Checking current deployment...${NC}"
kubectl get deployment $APP_NAME -n $NAMESPACE -o wide || {
    echo -e "${RED}Deployment not found!${NC}"
    exit 1
}

# 3. 이미지 업데이트 (필요 시)
if [ -n "$1" ]; then
    IMAGE_TAG="$1"
    echo -e "${YELLOW}3. Updating image to: $IMAGE_TAG${NC}"
    kubectl set image deployment/$APP_NAME $APP_NAME=$REGISTRY/$APP_NAME:$IMAGE_TAG -n $NAMESPACE
else
    echo -e "${YELLOW}3. Rolling restart deployment...${NC}"
    kubectl rollout restart deployment/$APP_NAME -n $NAMESPACE
fi

# 4. Rollout 상태 모니터링
echo -e "${YELLOW}4. Monitoring rollout status...${NC}"
kubectl rollout status deployment/$APP_NAME -n $NAMESPACE --timeout=${TIMEOUT}s || {
    echo -e "${RED}Rollout failed!${NC}"
    echo "Rolling back..."
    kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE
    exit 1
}

# 5. Pod 상태 확인
echo -e "${YELLOW}5. Checking pod status...${NC}"
kubectl get pods -n $NAMESPACE -l app=$APP_NAME

# 6. 헬스체크 실행
echo -e "${YELLOW}6. Running health check...${NC}"
if [ -f "$(dirname "$0")/health-check.sh" ]; then
    bash "$(dirname "$0")/health-check.sh"
else
    # 간단한 헬스체크
    for i in {1..10}; do
        if curl -f -s http://192.168.50.110:32301/health > /dev/null; then
            echo -e "${GREEN}✅ Health check passed!${NC}"
            break
        fi
        echo "Attempt $i/10..."
        sleep 5
    done
fi

# 7. 배포 정보 출력
echo ""
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo "===================================="
kubectl get deployment $APP_NAME -n $NAMESPACE -o json | jq -r '.spec.template.spec.containers[0].image'
echo ""
echo "Access URLs:"
echo "- Application: http://192.168.50.110:32301"
echo "- Health: http://192.168.50.110:32301/health"
echo "- API Docs: http://192.168.50.110:32301/api/docs"
echo "- QR Register: http://192.168.50.110:32301/qr-register"