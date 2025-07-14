#!/bin/bash

# SafeWork - Kubernetes API Server 외부 DNS 설정 스크립트
# Usage: ./setup-external-dns.sh <domain> <master-ip>

set -e

DOMAIN=${1:-"k8s-api.jclee.me"}
MASTER_IP=${2}

if [ -z "$MASTER_IP" ]; then
    echo "❌ Error: Master IP is required"
    echo "Usage: $0 <domain> <master-ip>"
    echo "Example: $0 k8s-api.jclee.me 192.168.1.100"
    exit 1
fi

echo "🚀 Setting up external DNS for Kubernetes API Server"
echo "Domain: $DOMAIN"
echo "Master IP: $MASTER_IP"
echo "API URL: https://$DOMAIN:6443"

# Step 1: DNS 해석 확인
echo "🔍 Step 1: DNS 해석 확인"
if nslookup $DOMAIN > /dev/null 2>&1; then
    echo "✅ DNS 해석 성공: $DOMAIN"
    RESOLVED_IP=$(nslookup $DOMAIN | grep -A 1 "Name:" | tail -1 | awk '{print $2}')
    echo "해석된 IP: $RESOLVED_IP"
    
    if [ "$RESOLVED_IP" = "$MASTER_IP" ]; then
        echo "✅ DNS 레코드가 올바르게 설정됨"
    else
        echo "⚠️  DNS 레코드가 다른 IP로 설정됨 (설정: $RESOLVED_IP, 예상: $MASTER_IP)"
    fi
else
    echo "❌ DNS 해석 실패. DNS 레코드를 먼저 설정해주세요."
    echo "다음과 같이 DNS 레코드를 생성하세요:"
    echo "Type: A"
    echo "Name: ${DOMAIN%%.*}"
    echo "Value: $MASTER_IP"
    echo "TTL: 300"
    exit 1
fi

# Step 2: API 서버 접근 테스트
echo "🔍 Step 2: API 서버 접근 테스트"
if curl -k --connect-timeout 10 https://$DOMAIN:6443/version > /dev/null 2>&1; then
    echo "✅ API 서버 접근 성공"
    API_VERSION=$(curl -k -s https://$DOMAIN:6443/version | jq -r '.gitVersion' 2>/dev/null || echo "Unknown")
    echo "Kubernetes 버전: $API_VERSION"
else
    echo "❌ API 서버 접근 실패"
    echo "확인사항:"
    echo "1. 포트 6443이 외부에서 접근 가능한지 확인"
    echo "2. 방화벽 설정 확인"
    echo "3. Kubernetes API 서버 상태 확인"
    
    # 포트 확인
    echo "🔍 포트 6443 접근성 테스트..."
    if nc -zv $MASTER_IP 6443 2>/dev/null; then
        echo "✅ 포트 6443 접근 가능"
    else
        echo "❌ 포트 6443 접근 불가"
        echo "방화벽 설정을 확인하세요:"
        echo "sudo ufw allow 6443/tcp"
    fi
fi

# Step 3: SSL 인증서 확인
echo "🔍 Step 3: SSL 인증서 확인"
SSL_INFO=$(echo | openssl s_client -connect $DOMAIN:6443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -subject -dates 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ SSL 인증서 정보:"
    echo "$SSL_INFO"
    
    # SAN 확인
    SAN_INFO=$(echo | openssl s_client -connect $DOMAIN:6443 -servername $DOMAIN 2>/dev/null | openssl x509 -noout -text 2>/dev/null | grep -A 1 "Subject Alternative Name")
    if echo "$SAN_INFO" | grep -q "$DOMAIN"; then
        echo "✅ SAN에 도메인이 포함됨"
    else
        echo "⚠️  SAN에 도메인이 포함되지 않음. API 서버 인증서 업데이트 필요"
        echo "kube-apiserver.yaml에 다음 설정 추가:"
        echo "--tls-san-dns=$DOMAIN"
    fi
else
    echo "❌ SSL 인증서 확인 실패"
fi

# Step 4: kubeconfig 생성
echo "🔍 Step 4: kubeconfig 템플릿 생성"
KUBECONFIG_FILE="kubeconfig-external-$DOMAIN"
cat > $KUBECONFIG_FILE << EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: https://$DOMAIN:6443
    # certificate-authority-data를 현재 클러스터에서 복사해야 함
    insecure-skip-tls-verify: true  # 임시로 설정, 실제 환경에서는 CA 인증서 사용
  name: external-cluster
contexts:
- context:
    cluster: external-cluster
    user: external-user
  name: external-context
current-context: external-context
users:
- name: external-user
  user:
    # client-certificate-data와 client-key-data를 현재 클러스터에서 복사해야 함
    token: "YOUR_SERVICE_ACCOUNT_TOKEN"
EOF

echo "✅ kubeconfig 템플릿 생성: $KUBECONFIG_FILE"
echo "이 파일을 편집하여 실제 인증 정보를 추가하세요."

# Step 5: ArgoCD 설정 업데이트 준비
echo "🔍 Step 5: ArgoCD 설정 업데이트 준비"
NEW_CLUSTER_URL="https://$DOMAIN:6443"

echo "ArgoCD 클러스터 설정을 업데이트하려면 다음 명령어를 실행하세요:"
echo ""
echo "# 1. 새 클러스터 추가"
echo "argocd cluster add external-context --name external-k8s --grpc-web"
echo ""
echo "# 2. Application 매니페스트 업데이트"
echo "sed -i 's|server: https://kubernetes.default.svc|server: $NEW_CLUSTER_URL|g' k8s/argocd/application.yaml"
echo ""
echo "# 3. Application 재생성"
echo "argocd app delete safework --grpc-web --yes"
echo "argocd app create --grpc-web -f k8s/argocd/application.yaml"

echo ""
echo "🎉 외부 DNS 설정 완료!"
echo "📋 요약:"
echo "  - 도메인: $DOMAIN"
echo "  - API URL: https://$DOMAIN:6443"
echo "  - kubeconfig: $KUBECONFIG_FILE"
echo ""
echo "다음 단계:"
echo "1. kubeconfig 파일에 실제 인증 정보 추가"
echo "2. ArgoCD 클러스터 설정 업데이트"
echo "3. SSL 인증서 SAN 업데이트 (필요한 경우)"