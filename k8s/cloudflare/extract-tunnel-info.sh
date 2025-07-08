#!/bin/bash

# Cloudflare Tunnel 정보 추출 스크립트
set -e

echo "=== Cloudflare Tunnel 정보 추출 ==="
echo ""

# 토큰 디코딩
if [ -z "$1" ]; then
    echo "사용법: ./extract-tunnel-info.sh <TUNNEL_TOKEN>"
    echo "예시: ./extract-tunnel-info.sh eyJhIjoiYTh..."
    exit 1
fi

TUNNEL_TOKEN="$1"

# Base64 디코딩 (JWT 형식)
echo "🔍 토큰 분석 중..."

# JWT의 payload 부분 추출 (두 번째 부분)
PAYLOAD=$(echo "$TUNNEL_TOKEN" | cut -d'.' -f2)

# Base64 패딩 추가 (필요한 경우)
case $(( ${#PAYLOAD} % 4 )) in
    2) PAYLOAD="${PAYLOAD}==" ;;
    3) PAYLOAD="${PAYLOAD}=" ;;
esac

# 디코딩
DECODED=$(echo "$PAYLOAD" | base64 -d 2>/dev/null || echo "디코딩 실패")

if [ "$DECODED" != "디코딩 실패" ]; then
    echo "✅ 토큰 정보:"
    echo "$DECODED" | jq . 2>/dev/null || echo "$DECODED"
    
    # 터널 ID 추출 (t 필드)
    TUNNEL_ID=$(echo "$DECODED" | jq -r '.t' 2>/dev/null || echo "")
    ACCOUNT_ID=$(echo "$DECODED" | jq -r '.a' 2>/dev/null || echo "")
    
    if [ -n "$TUNNEL_ID" ] && [ "$TUNNEL_ID" != "null" ]; then
        echo ""
        echo "📋 추출된 정보:"
        echo "  TUNNEL_ID: $TUNNEL_ID"
        echo "  ACCOUNT_ID: $ACCOUNT_ID"
        echo ""
        echo "🔧 다음 단계:"
        echo "1. Cloudflare API 토큰 생성:"
        echo "   https://dash.cloudflare.com/profile/api-tokens"
        echo "   권한: Account:Cloudflare Tunnel:Edit, Zone:DNS:Edit"
        echo ""
        echo "2. GitHub Secrets 추가:"
        echo "   CLOUDFLARE_ACCOUNT_ID=$ACCOUNT_ID"
        echo "   CLOUDFLARE_TUNNEL_ID=$TUNNEL_ID"
        echo "   CLOUDFLARE_API_TOKEN=<생성한 API 토큰>"
    fi
else
    echo "❌ 토큰 디코딩 실패"
    echo "토큰이 올바른 형식인지 확인하세요."
fi