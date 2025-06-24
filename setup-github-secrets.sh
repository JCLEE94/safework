#!/bin/bash

# GitHub Secrets 설정 스크립트
# GitHub CLI(gh)가 설치되어 있어야 합니다

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔐 GitHub Secrets 설정${NC}"
echo "======================="

# GitHub CLI 설치 확인
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI가 설치되어 있지 않습니다.${NC}"
    echo "설치 방법: https://cli.github.com/"
    exit 1
fi

# GitHub 로그인 확인
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}GitHub에 로그인합니다...${NC}"
    gh auth login
fi

# Repository 확인
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null || echo "")
if [ -z "$REPO" ]; then
    echo -e "${RED}❌ GitHub 저장소를 찾을 수 없습니다.${NC}"
    echo "현재 디렉토리가 Git 저장소인지 확인하세요."
    exit 1
fi

echo -e "${GREEN}✅ 저장소: $REPO${NC}"

# Secrets 설정
echo -e "\n${YELLOW}필수 Secrets 설정 중...${NC}"

# Registry credentials
echo -e "\n1. Docker Registry 인증 정보"
gh secret set REGISTRY_USERNAME -b "qws941" 2>/dev/null && echo -e "${GREEN}✅ REGISTRY_USERNAME 설정 완료${NC}" || echo -e "${YELLOW}⚠️  REGISTRY_USERNAME 이미 존재${NC}"
gh secret set REGISTRY_PASSWORD -b "bingogo1l7!" 2>/dev/null && echo -e "${GREEN}✅ REGISTRY_PASSWORD 설정 완료${NC}" || echo -e "${YELLOW}⚠️  REGISTRY_PASSWORD 이미 존재${NC}"

# Optional: Docker Hub credentials (for base images)
echo -e "\n2. Docker Hub 인증 정보 (선택사항)"
echo "Docker Hub 계정이 있으시면 입력하세요 (없으면 Enter):"
read -p "Docker Hub Username: " DOCKERHUB_USER
if [ ! -z "$DOCKERHUB_USER" ]; then
    read -s -p "Docker Hub Token: " DOCKERHUB_TOKEN
    echo
    gh secret set DOCKERHUB_USERNAME -b "$DOCKERHUB_USER" 2>/dev/null && echo -e "${GREEN}✅ DOCKERHUB_USERNAME 설정 완료${NC}"
    gh secret set DOCKERHUB_TOKEN -b "$DOCKERHUB_TOKEN" 2>/dev/null && echo -e "${GREEN}✅ DOCKERHUB_TOKEN 설정 완료${NC}"
fi

# Optional: SSH key for deployment
echo -e "\n3. SSH 배포 키 (선택사항 - 수동 배포용)"
echo "SSH 키를 설정하시겠습니까? (y/N):"
read -p "" SETUP_SSH
if [[ "$SETUP_SSH" =~ ^[Yy]$ ]]; then
    if [ -f ~/.ssh/id_rsa ]; then
        gh secret set SSH_PRIVATE_KEY < ~/.ssh/id_rsa 2>/dev/null && echo -e "${GREEN}✅ SSH_PRIVATE_KEY 설정 완료${NC}"
    else
        echo -e "${YELLOW}⚠️  ~/.ssh/id_rsa 파일을 찾을 수 없습니다.${NC}"
    fi
    
    gh secret set DEPLOY_HOST -b "192.168.50.215" 2>/dev/null && echo -e "${GREEN}✅ DEPLOY_HOST 설정 완료${NC}"
    gh secret set DEPLOY_PORT -b "1111" 2>/dev/null && echo -e "${GREEN}✅ DEPLOY_PORT 설정 완료${NC}"
    gh secret set DEPLOY_USER -b "docker" 2>/dev/null && echo -e "${GREEN}✅ DEPLOY_USER 설정 완료${NC}"
fi

# 설정된 Secrets 확인
echo -e "\n${BLUE}📋 설정된 Secrets 목록:${NC}"
gh secret list

echo -e "\n${GREEN}✅ GitHub Secrets 설정 완료!${NC}"
echo ""
echo "다음 단계:"
echo "1. 운영 서버 라벨 업데이트: ./update-production.sh"
echo "2. 코드 푸시하여 자동 배포 테스트: git push origin main"