#!/bin/bash

# SafeWork - Kubernetes API Server Cloudflare 터널 설정 스크립트
# Cloudflare Zero Trust 대시보드에서 수동 설정이 필요합니다.

set -e

DOMAIN=${1:-"jclee.me"}
K8S_SUBDOMAIN=${2:-"k8s-api"}
TUNNEL_NAME=${3:-"safework-tunnel"}

echo "🚀 Kubernetes API Server Cloudflare 터널 설정"
echo "도메인: $DOMAIN"
echo "K8S API 서브도메인: $K8S_SUBDOMAIN"
echo "전체 URL: https://$K8S_SUBDOMAIN.$DOMAIN"

echo ""
echo "📋 Cloudflare Zero Trust 대시보드 설정 가이드"
echo "=========================================="
echo ""
echo "1. Cloudflare Zero Trust 대시보드 접속:"
echo "   https://one.dash.cloudflare.com/"
echo ""
echo "2. Access > Tunnels > $TUNNEL_NAME 선택"
echo ""
echo "3. Public Hostnames 탭에서 'Add a public hostname' 클릭"
echo ""
echo "4. 다음과 같이 설정:"
echo "   ┌─────────────────────────────────────────────────────────┐"
echo "   │ Subdomain: $K8S_SUBDOMAIN                                        │"
echo "   │ Domain: $DOMAIN                                         │"
echo "   │ Path: /*                                                │"
echo "   │ Service Type: HTTPS                                     │"
echo "   │ URL: https://kubernetes.default.svc.cluster.local:443  │"
echo "   └─────────────────────────────────────────────────────────┘"
echo ""
echo "5. Additional application settings (고급 설정):"
echo "   ┌─────────────────────────────────────────────────────────┐"
echo "   │ TLS Settings:                                           │"
echo "   │   ✓ No TLS Verify (클러스터 내부 인증서용)                   │"
echo "   │   ✓ Origin Server Name: kubernetes.default.svc.cluster.local │"
echo "   │                                                         │"
echo "   │ HTTP Settings:                                          │"
echo "   │   Host Header: $K8S_SUBDOMAIN.$DOMAIN                           │"
echo "   └─────────────────────────────────────────────────────────┘"
echo ""
echo "6. 'Save hostname' 클릭"
echo ""

# DNS 확인 함수
check_dns() {
    echo "🔍 DNS 전파 확인 중..."
    local retries=0
    local max_retries=30
    
    while [ $retries -lt $max_retries ]; do
        if nslookup $K8S_SUBDOMAIN.$DOMAIN > /dev/null 2>&1; then
            echo "✅ DNS 전파 완료: $K8S_SUBDOMAIN.$DOMAIN"
            return 0
        else
            echo "⏳ DNS 전파 대기 중... ($((retries+1))/$max_retries)"
            sleep 10
            retries=$((retries+1))
        fi
    done
    
    echo "❌ DNS 전파 시간 초과. 수동으로 확인해주세요."
    return 1
}

# API 접근 테스트 함수
test_api_access() {
    echo "🔍 API 서버 접근 테스트..."
    local api_url="https://$K8S_SUBDOMAIN.$DOMAIN"
    
    if curl -k --connect-timeout 30 "$api_url/version" > /dev/null 2>&1; then
        echo "✅ API 서버 접근 성공: $api_url"
        
        # API 버전 정보 표시
        local version_info=$(curl -k -s "$api_url/version" 2>/dev/null | jq -r '.gitVersion' 2>/dev/null || echo "Unknown")
        echo "Kubernetes 버전: $version_info"
        return 0
    else
        echo "❌ API 서버 접근 실패: $api_url"
        echo "터널 설정을 다시 확인해주세요."
        return 1
    fi
}

echo "⏳ Cloudflare 터널 설정을 완료한 후 Enter를 눌러주세요..."
read -p "설정 완료 후 계속하려면 Enter를 누르세요: "

# DNS 및 접근성 테스트
if check_dns && test_api_access; then
    echo ""
    echo "🎉 Kubernetes API Server 터널 설정 완료!"
    echo ""
    echo "📊 설정 정보:"
    echo "  - API URL: https://$K8S_SUBDOMAIN.$DOMAIN"
    echo "  - ArgoCD 대시보드: https://argo.$DOMAIN"
    echo "  - SafeWork 앱: https://safework.$DOMAIN"
    echo ""
    echo "🔧 다음 단계:"
    echo "1. ArgoCD 클러스터 설정 업데이트:"
    echo "   ./scripts/setup/update-argocd-cluster.sh https://$K8S_SUBDOMAIN.$DOMAIN"
    echo ""
    echo "2. kubeconfig 생성:"
    echo "   kubectl config set-cluster cloudflare-cluster --server=https://$K8S_SUBDOMAIN.$DOMAIN"
    echo ""
    echo "3. Access Policy 설정 (보안 강화):"
    echo "   - Cloudflare Zero Trust > Access > Applications"
    echo "   - $K8S_SUBDOMAIN.$DOMAIN에 대한 접근 정책 생성"
else
    echo ""
    echo "❌ 설정 실패. 다음을 확인해주세요:"
    echo "1. Cloudflare 터널 설정이 올바른지 확인"
    echo "2. DNS 전파 완료 대기 (최대 5분)"
    echo "3. 클러스터 내부에서 kubernetes.default.svc.cluster.local:443 접근 가능한지 확인"
fi