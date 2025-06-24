#!/bin/bash

# Nginx Proxy Manager API를 사용한 Docker Registry 설정 스크립트

NPM_URL="http://192.168.50.215:1413"
NPM_USER="qws941@kakao.com"
NPM_PASS="bingogo1l7!"

echo "1. Nginx Proxy Manager API 로그인..."
TOKEN=$(curl -s -X POST "$NPM_URL/api/tokens" \
  -H "Content-Type: application/json" \
  -d "{\"identity\":\"$NPM_USER\",\"secret\":\"$NPM_PASS\"}" | jq -r '.token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "로그인 실패. 사용자명과 비밀번호를 확인하세요."
  exit 1
fi

echo "로그인 성공!"

# 2. 기존 registry.jclee.me 프록시 호스트 찾기
echo "2. 기존 registry.jclee.me 설정 확인..."
HOSTS=$(curl -s -X GET "$NPM_URL/api/nginx/proxy-hosts" \
  -H "Authorization: Bearer $TOKEN")

HOST_ID=$(echo "$HOSTS" | jq -r '.[] | select(.domain_names[] == "registry.jclee.me") | .id' | head -1)

if [ ! -z "$HOST_ID" ]; then
  echo "기존 설정 발견 (ID: $HOST_ID). 삭제 중..."
  curl -s -X DELETE "$NPM_URL/api/nginx/proxy-hosts/$HOST_ID" \
    -H "Authorization: Bearer $TOKEN"
fi

# 3. 새로운 Docker Registry 프록시 호스트 생성
echo "3. Docker Registry 프록시 호스트 생성..."

PROXY_CONFIG=$(cat <<EOF
{
  "domain_names": ["registry.jclee.me"],
  "forward_scheme": "http",
  "forward_host": "192.168.50.215",
  "forward_port": 1234,
  "access_list_id": 0,
  "certificate_id": 0,
  "ssl_forced": false,
  "caching_enabled": false,
  "block_exploits": false,
  "advanced_config": "# Docker Registry v2 설정\nclient_max_body_size 0;\nchunked_transfer_encoding on;\n\nlocation /v2/ {\n    proxy_pass http://192.168.50.215:1234;\n    proxy_set_header Host \$http_host;\n    proxy_set_header X-Real-IP \$remote_addr;\n    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n    proxy_set_header X-Forwarded-Proto \$scheme;\n    proxy_set_header Authorization \$http_authorization;\n    proxy_set_header Docker-Content-Digest \$http_docker_content_digest;\n    proxy_request_buffering off;\n    proxy_buffering off;\n    proxy_http_version 1.1;\n    proxy_read_timeout 900;\n    proxy_connect_timeout 900;\n    proxy_send_timeout 900;\n    proxy_redirect off;\n}\n\nlocation / {\n    proxy_pass http://192.168.50.215:1234;\n    proxy_set_header Host \$http_host;\n    proxy_set_header X-Real-IP \$remote_addr;\n    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;\n    proxy_set_header X-Forwarded-Proto \$scheme;\n    proxy_buffering off;\n    proxy_request_buffering off;\n}",
  "meta": {
    "letsencrypt_agree": false,
    "dns_challenge": false
  },
  "allow_websocket_upgrade": true,
  "http2_support": false,
  "hsts_enabled": false,
  "hsts_subdomains": false,
  "enabled": true
}
EOF
)

RESULT=$(curl -s -X POST "$NPM_URL/api/nginx/proxy-hosts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PROXY_CONFIG")

NEW_ID=$(echo "$RESULT" | jq -r '.id')

if [ "$NEW_ID" != "null" ] && [ ! -z "$NEW_ID" ]; then
  echo "성공! 새로운 프록시 호스트 생성됨 (ID: $NEW_ID)"
  echo ""
  echo "4. 테스트 명령어:"
  echo "   curl http://registry.jclee.me/v2/"
  echo "   docker push registry.jclee.me/health:latest"
else
  echo "실패! 응답:"
  echo "$RESULT" | jq .
fi