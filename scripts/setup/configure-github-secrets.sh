#!/bin/bash
# GitHub Secrets 설정 스크립트
# 안정적인 CI/CD를 위한 필수 설정

set -e

# 색상 코드
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "🔐 GitHub Secrets Configuration"
echo "=============================="

# 필수 환경 변수 확인
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}❌ GITHUB_TOKEN이 설정되지 않았습니다${NC}"
    echo "export GITHUB_TOKEN=your_github_personal_access_token"
    exit 1
fi

# Repository 정보
REPO="JCLEE94/safework"

# GitHub CLI를 사용한 Secrets 설정
echo -e "${YELLOW}Setting up repository secrets...${NC}"

# Registry 인증 정보
gh secret set REGISTRY_USERNAME -b "admin" -R $REPO
gh secret set REGISTRY_PASSWORD -b "bingogo1" -R $REPO

# 추가 설정 (필요 시)
# gh secret set DATABASE_URL -b "postgresql://..." -R $REPO
# gh secret set REDIS_URL -b "redis://..." -R $REPO

echo -e "${GREEN}✅ Secrets configured successfully${NC}"

# Variables 설정
echo -e "${YELLOW}Setting up repository variables...${NC}"

gh variable set REGISTRY_URL -b "registry.jclee.me" -R $REPO
gh variable set K8S_NAMESPACE -b "safework" -R $REPO
gh variable set NODE_PORT -b "32301" -R $REPO

echo -e "${GREEN}✅ Variables configured successfully${NC}"

# 현재 설정 확인
echo ""
echo "📋 Current configuration:"
echo "========================"
gh secret list -R $REPO
echo ""
gh variable list -R $REPO