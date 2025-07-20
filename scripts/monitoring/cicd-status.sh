#!/bin/bash
# CI/CD 상태 모니터링 스크립트

set -e

# 색상 코드
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${BLUE}📊 SafeWork CI/CD Status Dashboard${NC}"
echo "=================================="
date
echo ""

# 1. GitHub Actions 상태
echo -e "${CYAN}[GitHub Actions]${NC}"
if command -v gh &> /dev/null; then
    echo "Recent workflows:"
    gh run list --limit 5 --repo JCLEE94/safework | head -10
else
    echo -e "${YELLOW}GitHub CLI not installed${NC}"
fi
echo ""

# 2. Docker Registry 상태
echo -e "${CYAN}[Docker Registry]${NC}"
echo "Registry: registry.jclee.me"
# 최신 이미지 태그 확인
if command -v docker &> /dev/null; then
    docker images | grep safework | head -5 || echo "No local images"
fi
echo ""

# 3. Kubernetes 상태
echo -e "${CYAN}[Kubernetes]${NC}"
echo "Namespace: safework"
kubectl get deployment safework -n safework -o wide 2>/dev/null || echo -e "${RED}Deployment not found${NC}"
echo ""
kubectl get pods -n safework -l app=safework 2>/dev/null || echo -e "${RED}No pods found${NC}"
echo ""

# 4. ArgoCD 상태
echo -e "${CYAN}[ArgoCD]${NC}"
if command -v argocd &> /dev/null; then
    argocd app get safework --refresh 2>/dev/null | grep -E "(Health Status|Sync Status)" || echo "ArgoCD not configured"
else
    kubectl get application safework -n argocd -o json 2>/dev/null | \
        jq -r '.status | "Health: \(.health.status), Sync: \(.sync.status)"' || \
        echo -e "${YELLOW}ArgoCD status unavailable${NC}"
fi
echo ""

# 5. 엔드포인트 상태
echo -e "${CYAN}[Endpoints Status]${NC}"
endpoints=(
    "http://192.168.50.110:32301/health|Health"
    "http://192.168.50.110:32301/api/docs|API Docs"
    "http://192.168.50.110:32301/qr-register|QR Register"
)

for endpoint in "${endpoints[@]}"; do
    IFS='|' read -r url name <<< "$endpoint"
    if curl -s -f -o /dev/null "$url" --max-time 5 2>/dev/null; then
        echo -e "${GREEN}✅ $name: OK${NC}"
    else
        echo -e "${RED}❌ $name: Failed${NC}"
    fi
done
echo ""

# 6. 리소스 사용량
echo -e "${CYAN}[Resource Usage]${NC}"
kubectl top pod -n safework -l app=safework 2>/dev/null || echo "Metrics not available"
echo ""

# 7. 최근 이벤트
echo -e "${CYAN}[Recent Events]${NC}"
kubectl get events -n safework --sort-by='.lastTimestamp' | tail -5

echo ""
echo "Dashboard updated at: $(date)"