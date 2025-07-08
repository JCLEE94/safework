#!/bin/bash

# Cloudflare Tunnel Token 설정 스크립트
# 사용법: ./setup-tunnel-token.sh

set -e

echo "=== Cloudflare Tunnel Token 설정 ==="
echo ""
echo "이 스크립트는 Cloudflare Tunnel 토큰을 안전하게 Kubernetes Secret으로 저장합니다."
echo ""

# 토큰 입력 받기
read -p "Cloudflare Tunnel 토큰을 입력하세요 (eyJ로 시작하는 긴 문자열): " TUNNEL_TOKEN

# 토큰이 비어있는지 확인
if [ -z "$TUNNEL_TOKEN" ]; then
    echo "오류: 토큰이 입력되지 않았습니다."
    exit 1
fi

# 토큰 형식 확인 (eyJ로 시작하는지)
if [[ ! "$TUNNEL_TOKEN" =~ ^eyJ ]]; then
    echo "경고: 토큰이 'eyJ'로 시작하지 않습니다. 올바른 토큰인지 확인해주세요."
    read -p "계속하시겠습니까? (y/N): " CONTINUE
    if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
        echo "취소되었습니다."
        exit 1
    fi
fi

# Base64 인코딩
ENCODED_TOKEN=$(echo -n "$TUNNEL_TOKEN" | base64 -w 0)

# Secret YAML 파일 생성
cat > k8s/cloudflare/tunnel-secret.yaml <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-tunnel-token
  namespace: safework
type: Opaque
data:
  token: $ENCODED_TOKEN
EOF

echo ""
echo "✅ Secret 파일이 생성되었습니다: k8s/cloudflare/tunnel-secret.yaml"
echo ""
echo "다음 단계:"
echo "1. kubectl apply -f k8s/cloudflare/tunnel-secret.yaml"
echo "2. kubectl apply -f k8s/cloudflare/cloudflared-deployment.yaml"
echo "3. Cloudflare Zero Trust 대시보드에서 라우팅 설정"
echo ""
echo "⚠️  보안 주의사항:"
echo "- tunnel-secret.yaml 파일을 Git에 커밋하지 마세요!"
echo "- .gitignore에 추가하는 것을 권장합니다."