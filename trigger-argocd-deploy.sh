#!/bin/bash

# ArgoCD 배포 트리거 스크립트
echo "🚀 ArgoCD를 통한 SafeWork 배포 시작..."

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 1. 코드 변경사항 커밋
echo -e "${YELLOW}📝 변경사항 확인...${NC}"
git status

# 2. 이미지 태그 업데이트
NEW_TAG="v$(date +%Y%m%d-%H%M%S)"
echo -e "${BLUE}🏷️ 새 이미지 태그: ${NEW_TAG}${NC}"

# deployment.yaml 이미지 태그 업데이트
sed -i "s|image: registry.jclee.me/safework:.*|image: registry.jclee.me/safework:${NEW_TAG}|g" k8s/safework/deployment.yaml

# 3. 변경사항 커밋 및 푸시
echo -e "${YELLOW}📤 변경사항 커밋 및 푸시...${NC}"
git add -A
git commit -m "deploy: trigger ArgoCD deployment with tag ${NEW_TAG}

- Updated image tag to ${NEW_TAG}
- Triggered by manual deployment script
"
git push origin main

# 4. GitHub Actions 상태 확인
echo -e "${BLUE}⏳ GitHub Actions 실행 대기...${NC}"
echo "GitHub Actions 확인: https://github.com/JCLEE94/safework/actions"
echo ""
echo "다음 명령어로 실행 상태 확인:"
echo "  gh run list --workflow=argocd-deploy.yml --limit=1"
echo "  gh run watch"
echo ""

# 5. ArgoCD 수동 동기화 (옵션)
echo -e "${GREEN}💡 ArgoCD 수동 동기화 명령어:${NC}"
echo "  argocd app sync safework --force"
echo "  argocd app wait safework --health"
echo ""
echo -e "${GREEN}✅ 배포 트리거 완료!${NC}"
echo "ArgoCD 대시보드: https://argo.jclee.me/applications/safework"