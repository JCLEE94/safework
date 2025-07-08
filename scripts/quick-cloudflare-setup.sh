#!/bin/bash

# Cloudflare 빠른 설정 스크립트
set -e

echo "=== Cloudflare Tunnel 빠른 설정 ==="
echo ""
echo "이 스크립트는 Cloudflare API 토큰만 있으면 모든 설정을 자동으로 완료합니다."
echo ""

# API 토큰 생성 안내
echo "📌 먼저 Cloudflare API 토큰을 생성하세요:"
echo "1. https://dash.cloudflare.com/profile/api-tokens 접속"
echo "2. 'Create Token' 클릭"
echo "3. 'Custom token' 선택"
echo "4. 권한 설정:"
echo "   - Account > Cloudflare Tunnel: Edit"
echo "   - Zone > Zone: Read"
echo "   - Zone > DNS: Edit"
echo "5. 'Create Token' 클릭 후 토큰 복사"
echo ""
read -p "API 토큰을 입력하세요: " API_TOKEN

if [ -z "$API_TOKEN" ]; then
    echo "❌ API 토큰이 입력되지 않았습니다."
    exit 1
fi

# 미리 추출된 정보
ACCOUNT_ID="a8d9c67f586acdd15eebcc65ca3aa5bb"
TUNNEL_ID="8ea78906-1a05-44fb-a1bb-e512172cb5ab"

echo ""
echo "🔧 GitHub Secrets 설정 중..."

# GitHub Secrets 설정
gh secret set CLOUDFLARE_ACCOUNT_ID --body "$ACCOUNT_ID"
gh secret set CLOUDFLARE_TUNNEL_ID --body "$TUNNEL_ID"
gh secret set CLOUDFLARE_API_TOKEN --body "$API_TOKEN"

echo "✅ 모든 Secrets 설정 완료!"

# 즉시 라우팅 설정 시도
echo ""
read -p "지금 바로 Cloudflare 라우팅을 설정하시겠습니까? (y/N): " SETUP_NOW

if [[ "$SETUP_NOW" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🌐 Cloudflare 라우팅 설정 중..."
    
    export CLOUDFLARE_ACCOUNT_ID="$ACCOUNT_ID"
    export CLOUDFLARE_TUNNEL_ID="$TUNNEL_ID"
    export CLOUDFLARE_API_TOKEN="$API_TOKEN"
    
    if [ -f k8s/cloudflare/setup-tunnel-routing.sh ]; then
        ./k8s/cloudflare/setup-tunnel-routing.sh
    else
        echo "❌ 라우팅 스크립트를 찾을 수 없습니다."
    fi
fi

echo ""
echo "🎉 설정이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. 변경사항 커밋 및 푸시"
echo "2. CI/CD 파이프라인이 자동으로 실행됨"
echo "3. 몇 분 후 https://safework.jclee.me 접속 확인"
echo ""
echo "확인 명령어:"
echo "- CI/CD 상태: gh run list --limit 1"
echo "- Secrets 확인: gh secret list | grep CLOUDFLARE"