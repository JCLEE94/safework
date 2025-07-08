#!/bin/bash

# Cloudflare GitHub Secrets 설정 스크립트
set -e

echo "=== Cloudflare GitHub Secrets 설정 ==="
echo ""

# 추출된 정보
ACCOUNT_ID="a8d9c67f586acdd15eebcc65ca3aa5bb"
TUNNEL_ID="8ea78906-1a05-44fb-a1bb-e512172cb5ab"

echo "📋 설정할 정보:"
echo "  CLOUDFLARE_ACCOUNT_ID: $ACCOUNT_ID"
echo "  CLOUDFLARE_TUNNEL_ID: $TUNNEL_ID"
echo ""

# API 토큰 입력 받기
echo "🔐 Cloudflare API 토큰이 필요합니다."
echo "   생성 방법:"
echo "   1. https://dash.cloudflare.com/profile/api-tokens 접속"
echo "   2. 'Create Token' 클릭"
echo "   3. 'Custom token' 선택"
echo "   4. 권한 설정:"
echo "      - Account > Cloudflare Tunnel:Edit"
echo "      - Zone > Zone:Read"
echo "      - Zone > DNS:Edit"
echo "   5. 'Continue to summary' > 'Create Token'"
echo ""
read -p "생성한 API 토큰을 입력하세요: " API_TOKEN

if [ -z "$API_TOKEN" ]; then
    echo "❌ API 토큰이 입력되지 않았습니다."
    exit 1
fi

# GitHub Secrets 설정
echo ""
echo "🔧 GitHub Secrets 설정 중..."

# CLOUDFLARE_ACCOUNT_ID
gh secret set CLOUDFLARE_ACCOUNT_ID --body "$ACCOUNT_ID"
echo "✅ CLOUDFLARE_ACCOUNT_ID 설정 완료"

# CLOUDFLARE_TUNNEL_ID
gh secret set CLOUDFLARE_TUNNEL_ID --body "$TUNNEL_ID"
echo "✅ CLOUDFLARE_TUNNEL_ID 설정 완료"

# CLOUDFLARE_API_TOKEN
gh secret set CLOUDFLARE_API_TOKEN --body "$API_TOKEN"
echo "✅ CLOUDFLARE_API_TOKEN 설정 완료"

# 확인
echo ""
echo "📋 설정된 Secrets:"
gh secret list | grep CLOUDFLARE

echo ""
echo "✅ 모든 Cloudflare Secrets가 설정되었습니다!"
echo ""
echo "다음 단계:"
echo "1. CI/CD 파이프라인 실행 (자동으로 라우팅 설정됨)"
echo "2. 몇 분 후 https://safework.jclee.me 접속 확인"