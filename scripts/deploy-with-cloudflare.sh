#!/bin/bash

# SafeWork Pro - Cloudflare Tunnel 배포 스크립트
set -e

echo "=== SafeWork Pro Cloudflare Tunnel 배포 ==="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# GitHub CLI 확인
if ! command -v gh &> /dev/null; then
    echo -e "${RED}✗${NC} GitHub CLI가 설치되지 않았습니다."
    echo "   설치: https://cli.github.com/"
    exit 1
fi

# GitHub 인증 확인
if ! gh auth status &> /dev/null; then
    echo -e "${RED}✗${NC} GitHub에 로그인되어 있지 않습니다."
    echo "   실행: gh auth login"
    exit 1
fi

echo -e "${BLUE}ℹ${NC} GitHub Secrets 확인 중..."

# CLOUDFLARE_TUNNEL_TOKEN 확인
if gh secret list | grep -q "CLOUDFLARE_TUNNEL_TOKEN"; then
    echo -e "${GREEN}✓${NC} CLOUDFLARE_TUNNEL_TOKEN이 설정되어 있습니다."
else
    echo -e "${RED}✗${NC} CLOUDFLARE_TUNNEL_TOKEN이 설정되지 않았습니다."
    echo ""
    echo "다음 단계를 따라 설정하세요:"
    echo "1. https://github.com/JCLEE94/safework/settings/secrets/actions 접속"
    echo "2. 'New repository secret' 클릭"
    echo "3. Name: CLOUDFLARE_TUNNEL_TOKEN"
    echo "4. Secret: eyJhIjoiYThkOWM2N2Y1ODZhY2RkMTVlZWJjYzY1Y2EzYWE1YmIiLCJ0IjoiOGVhNzg5MDYtMWEwNS00NGZiLWExYmItZTUxMjE3MmNiNWFiIiwicyI6Ill6RXlZVEUwWWpRdE1tVXlNUzAwWmpRMExXSTVaR0V0WkdNM085UY3pOV1ExT1RGbSJ9"
    echo ""
    read -p "Secret을 설정한 후 Enter를 누르세요..."
fi

# ArgoCD Application 업데이트 확인
echo -e "\n${BLUE}ℹ${NC} ArgoCD Application 업데이트 옵션:"
echo "1) 기존 Application 유지 (Cloudflare 없음)"
echo "2) Cloudflare Tunnel 포함하여 업데이트"
read -p "선택 (1-2): " ARGOCD_OPTION

if [ "$ARGOCD_OPTION" == "2" ]; then
    echo -e "\n${YELLOW}►${NC} ArgoCD Application 업데이트 중..."
    kubectl apply -f k8s/argocd/application-cloudflare.yaml
    echo -e "${GREEN}✓${NC} ArgoCD Application이 Cloudflare 버전으로 업데이트되었습니다."
fi

# Git 변경사항 확인
echo -e "\n${BLUE}ℹ${NC} Git 상태 확인 중..."
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}!${NC} 커밋되지 않은 변경사항이 있습니다:"
    git status -s
    echo ""
    read -p "변경사항을 커밋하고 푸시하시겠습니까? (y/N): " COMMIT_CHANGES
    
    if [[ "$COMMIT_CHANGES" =~ ^[Yy]$ ]]; then
        git add .
        git commit -m "feat: Add Cloudflare Tunnel integration

- Add Cloudflare Tunnel deployment manifests
- Update CI/CD pipeline to handle Cloudflare secrets
- Add kustomization for integrated deployment
- Update service to ClusterIP for tunnel-only access"
        git push
        echo -e "${GREEN}✓${NC} 변경사항이 푸시되었습니다."
    fi
else
    echo -e "${GREEN}✓${NC} 모든 변경사항이 이미 커밋되어 있습니다."
fi

# CI/CD 트리거
echo -e "\n${BLUE}ℹ${NC} CI/CD 파이프라인 상태 확인 중..."
LATEST_RUN=$(gh run list --limit 1 --json databaseId,status,conclusion --jq '.[0]')
RUN_ID=$(echo $LATEST_RUN | jq -r '.databaseId')
RUN_STATUS=$(echo $LATEST_RUN | jq -r '.status')

if [ "$RUN_STATUS" == "in_progress" ]; then
    echo -e "${YELLOW}►${NC} CI/CD 파이프라인이 이미 실행 중입니다."
    echo "   실행 ID: $RUN_ID"
    echo "   상태 확인: gh run view $RUN_ID"
else
    echo -e "${BLUE}ℹ${NC} 새 배포를 시작하시겠습니까?"
    echo "   이 작업은 CI/CD 파이프라인을 트리거합니다."
    read -p "계속하시겠습니까? (y/N): " TRIGGER_DEPLOY
    
    if [[ "$TRIGGER_DEPLOY" =~ ^[Yy]$ ]]; then
        echo -e "\n${YELLOW}►${NC} CI/CD 파이프라인 트리거 중..."
        gh workflow run deploy.yml
        
        # 새 실행 ID 가져오기
        sleep 3
        NEW_RUN=$(gh run list --limit 1 --json databaseId --jq '.[0].databaseId')
        echo -e "${GREEN}✓${NC} CI/CD 파이프라인이 시작되었습니다."
        echo "   실행 ID: $NEW_RUN"
        echo ""
        echo "진행 상황 확인:"
        echo "  gh run watch $NEW_RUN"
        echo "  gh run view $NEW_RUN --web"
    fi
fi

# Cloudflare 대시보드 설정 안내
echo -e "\n${BLUE}ℹ${NC} Cloudflare Zero Trust 대시보드 설정:"
echo "1. https://one.dash.cloudflare.com/ 접속"
echo "2. Networks > Tunnels > 생성한 터널 선택"
echo "3. Configure 탭 > Public Hostname 추가:"
echo "   - Subdomain: safework"
echo "   - Domain: jclee.me"
echo "   - Service: http://safework.safework.svc.cluster.local:3001"
echo ""
echo -e "${GREEN}✓${NC} 배포 프로세스가 시작되었습니다!"
echo ""
echo "다음 명령으로 상태를 확인하세요:"
echo "- CI/CD 상태: gh run list --limit 5"
echo "- ArgoCD 상태: kubectl get app -n argocd safework"
echo "- Pod 상태: kubectl get pods -n safework"
echo "- Cloudflare 로그: kubectl logs -n safework -l app=cloudflared -f"