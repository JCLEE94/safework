#!/bin/bash

# Cloudflare Tunnel 라우팅 자동 설정 스크립트
set -e

# 필수 환경 변수 확인
if [ -z "$CLOUDFLARE_ACCOUNT_ID" ] || [ -z "$CLOUDFLARE_API_TOKEN" ] || [ -z "$CLOUDFLARE_TUNNEL_ID" ]; then
    echo "❌ 필수 환경 변수가 설정되지 않았습니다:"
    echo "  - CLOUDFLARE_ACCOUNT_ID"
    echo "  - CLOUDFLARE_API_TOKEN"
    echo "  - CLOUDFLARE_TUNNEL_ID"
    exit 1
fi

echo "🔐 Cloudflare Tunnel 라우팅 설정 중..."

# Cloudflare API 엔드포인트
API_URL="https://api.cloudflare.com/client/v4/accounts/${CLOUDFLARE_ACCOUNT_ID}/cfd_tunnel/${CLOUDFLARE_TUNNEL_ID}/configurations"

# 현재 설정 가져오기
echo "📡 현재 터널 설정 확인 중..."
CURRENT_CONFIG=$(curl -s -X GET "$API_URL" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json")

# 설정 JSON 생성
CONFIG_JSON=$(cat <<EOF
{
  "config": {
    "ingress": [
      {
        "hostname": "safework.jclee.me",
        "service": "http://safework.safework.svc.cluster.local:3001",
        "originRequest": {
          "connectTimeout": 30,
          "tlsTimeout": 30,
          "tcpKeepAlive": 30,
          "noHappyEyeballs": false,
          "keepAliveConnections": 100,
          "keepAliveTimeout": 90,
          "httpHostHeader": "",
          "originServerName": "",
          "caPool": "",
          "noTLSVerify": false,
          "disableChunkedEncoding": false,
          "bastionMode": false,
          "proxyAddress": "",
          "proxyPort": 0,
          "proxyType": "",
          "ipRules": []
        }
      },
      {
        "service": "http_status:404"
      }
    ]
  }
}
EOF
)

# 설정 업데이트
echo "🔧 터널 라우팅 설정 업데이트 중..."
RESPONSE=$(curl -s -X PUT "$API_URL" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$CONFIG_JSON")

# 결과 확인
if echo "$RESPONSE" | grep -q '"success":true'; then
    echo "✅ Cloudflare Tunnel 라우팅 설정 완료!"
    echo "🌐 접속 URL: https://safework.jclee.me"
else
    echo "❌ 설정 실패:"
    echo "$RESPONSE" | jq .
    exit 1
fi

# DNS 레코드 확인/생성 (선택사항)
echo ""
echo "📌 DNS 레코드 확인 중..."

# Zone ID 가져오기 (jclee.me 도메인)
ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=jclee.me" \
  -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.result[0].id')

if [ -n "$ZONE_ID" ] && [ "$ZONE_ID" != "null" ]; then
    # CNAME 레코드 확인
    EXISTING_RECORD=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records?type=CNAME&name=safework.jclee.me" \
      -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
      -H "Content-Type: application/json" | jq -r '.result[0]')
    
    if [ "$EXISTING_RECORD" == "null" ]; then
        echo "🔧 DNS CNAME 레코드 생성 중..."
        
        # 터널 CNAME 타겟 가져오기
        TUNNEL_CNAME="${CLOUDFLARE_TUNNEL_ID}.cfargotunnel.com"
        
        # CNAME 레코드 생성
        DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/${ZONE_ID}/dns_records" \
          -H "Authorization: Bearer ${CLOUDFLARE_API_TOKEN}" \
          -H "Content-Type: application/json" \
          -d "{
            \"type\": \"CNAME\",
            \"name\": \"safework\",
            \"content\": \"${TUNNEL_CNAME}\",
            \"ttl\": 1,
            \"proxied\": true
          }")
        
        if echo "$DNS_RESPONSE" | grep -q '"success":true'; then
            echo "✅ DNS CNAME 레코드 생성 완료!"
        else
            echo "⚠️  DNS 레코드 생성 실패 (수동 설정 필요):"
            echo "$DNS_RESPONSE" | jq .
        fi
    else
        echo "✅ DNS CNAME 레코드가 이미 존재합니다."
    fi
else
    echo "⚠️  Zone ID를 찾을 수 없습니다. DNS는 수동으로 설정하세요."
fi

echo ""
echo "🎉 Cloudflare Tunnel 설정이 완료되었습니다!"
echo "몇 분 후 https://safework.jclee.me 에서 접속 가능합니다."