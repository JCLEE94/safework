#!/bin/bash

# GitHub Token Secret 설정 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 GitHub Token 설정${NC}"
echo

# GitHub Token 입력
echo -e "${YELLOW}GitHub Personal Access Token을 입력하세요:${NC}"
echo "필요한 권한: repo (전체), write:packages"
read -s GITHUB_TOKEN

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ GitHub Token이 입력되지 않았습니다${NC}"
    exit 1
fi

# GitHub Secrets에 추가
echo -e "${BLUE}GitHub Secrets에 GITHUB_TOKEN 추가 중...${NC}"
gh secret set GITHUB_TOKEN --body="$GITHUB_TOKEN"

# ArgoCD에 시크릿 추가
echo -e "${BLUE}ArgoCD에 GitHub Token 시크릿 추가 중...${NC}"

# Kubernetes Secret 업데이트
kubectl patch secret safework-secrets -n safework \
  --type='json' \
  -p='[{"op": "add", "path": "/data/GITHUB_TOKEN", "value": "'$(echo -n "$GITHUB_TOKEN" | base64 -w 0)'"}]' \
  --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}✅ GitHub Token이 설정되었습니다${NC}"
echo
echo -e "${YELLOW}참고사항:${NC}"
echo "- GitHub Secrets: GITHUB_TOKEN"
echo "- Kubernetes Secret: safework-secrets (namespace: safework)"
echo "- 환경변수: GITHUB_TOKEN"
echo
echo -e "${BLUE}앱 재시작:${NC}"
echo "argocd app sync safework --server argo.jclee.me --grpc-web --insecure"