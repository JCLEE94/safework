#!/bin/bash

# SafeWork - ArgoCD를 Cloudflare 터널 기반 Kubernetes API로 업데이트
# Usage: ./update-argocd-to-tunnel.sh [k8s-subdomain] [domain]

set -e

K8S_SUBDOMAIN=${1:-"k8s-api"}
DOMAIN=${2:-"jclee.me"}
TUNNEL_API_URL="https://$K8S_SUBDOMAIN.$DOMAIN"
BACKUP_DIR="backup/argocd-tunnel-$(date +%Y%m%d-%H%M%S)"

echo "🔄 ArgoCD를 Cloudflare 터널 기반 API로 업데이트"
echo "터널 API URL: $TUNNEL_API_URL"

# Step 1: 현재 설정 백업
echo "💾 Step 1: 현재 ArgoCD 설정 백업"
mkdir -p $BACKUP_DIR
argocd app list --grpc-web > $BACKUP_DIR/app-list-before.txt
argocd cluster list --grpc-web > $BACKUP_DIR/cluster-list-before.txt
cp -r k8s/argocd/ $BACKUP_DIR/manifests/
echo "✅ 백업 완료: $BACKUP_DIR"

# Step 2: 터널 접근성 테스트
echo "🔍 Step 2: 터널 API 접근성 테스트"
if curl -k --connect-timeout 30 "$TUNNEL_API_URL/version" > /dev/null 2>&1; then
    echo "✅ 터널 API 접근 가능"
    VERSION=$(curl -k -s "$TUNNEL_API_URL/version" | jq -r '.gitVersion' 2>/dev/null || echo "Unknown")
    echo "Kubernetes 버전: $VERSION"
else
    echo "❌ 터널 API 접근 실패"
    echo "Cloudflare 터널 설정을 먼저 완료해주세요:"
    echo "./scripts/cloudflare/setup-k8s-api-tunnel.sh"
    exit 1
fi

# Step 3: 새 클러스터 kubeconfig 생성
echo "🔧 Step 3: 터널 기반 kubeconfig 생성"
KUBECONFIG_FILE="kubeconfig-tunnel-$K8S_SUBDOMAIN"

# 현재 클러스터에서 CA 데이터와 토큰 추출
CA_DATA=$(kubectl config view --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}')
USER_TOKEN=$(kubectl get secret -n kube-system $(kubectl get serviceaccount -n kube-system default -o jsonpath='{.secrets[0].name}') -o jsonpath='{.data.token}' | base64 -d)

cat > $KUBECONFIG_FILE << EOF
apiVersion: v1
kind: Config
clusters:
- cluster:
    server: $TUNNEL_API_URL
    certificate-authority-data: $CA_DATA
  name: cloudflare-tunnel-cluster
contexts:
- context:
    cluster: cloudflare-tunnel-cluster
    user: tunnel-user
  name: cloudflare-tunnel-context
current-context: cloudflare-tunnel-context
users:
- name: tunnel-user
  user:
    token: $USER_TOKEN
EOF

echo "✅ kubeconfig 생성: $KUBECONFIG_FILE"

# Step 4: 새 kubeconfig로 연결 테스트
echo "🔍 Step 4: 새 kubeconfig 연결 테스트"
if KUBECONFIG=$KUBECONFIG_FILE kubectl get nodes > /dev/null 2>&1; then
    echo "✅ 터널을 통한 kubectl 연결 성공"
else
    echo "❌ 터널을 통한 kubectl 연결 실패"
    echo "kubeconfig 설정을 확인해주세요: $KUBECONFIG_FILE"
    exit 1
fi

# Step 5: ArgoCD에 새 클러스터 추가
echo "🚀 Step 5: ArgoCD에 터널 클러스터 추가"

# 임시로 새 kubeconfig를 기본으로 설정
export KUBECONFIG=$PWD/$KUBECONFIG_FILE

# ArgoCD에 새 클러스터 추가
argocd cluster add cloudflare-tunnel-context \
    --name "cloudflare-tunnel" \
    --grpc-web \
    --upsert \
    --yes

# 원래 kubeconfig로 복원
unset KUBECONFIG

# Step 6: Application 매니페스트 업데이트
echo "📝 Step 6: Application 매니페스트 업데이트"
find k8s/argocd/ -name "*.yaml" -exec grep -l "https://kubernetes.default.svc" {} \; | while read file; do
    echo "업데이트 중: $file"
    sed -i "s|server: https://kubernetes.default.svc|server: $TUNNEL_API_URL|g" "$file"
done

# Step 7: 기존 safework 앱 삭제 및 재생성
echo "🔄 Step 7: SafeWork 애플리케이션 재배포"
argocd app delete safework --grpc-web --yes 2>/dev/null || echo "기존 앱이 없음"
sleep 10

argocd app create --grpc-web -f k8s/argocd/application.yaml

# Step 8: 최종 상태 확인
echo "✅ Step 8: 최종 상태 확인"
sleep 15

echo "클러스터 목록:"
argocd cluster list --grpc-web

echo ""
echo "애플리케이션 상태:"
argocd app get safework --grpc-web

# 상태 저장
argocd app list --grpc-web > $BACKUP_DIR/app-list-after.txt
argocd cluster list --grpc-web > $BACKUP_DIR/cluster-list-after.txt

echo ""
echo "🎉 Cloudflare 터널 기반 ArgoCD 설정 완료!"
echo ""
echo "📊 설정 정보:"
echo "  - 터널 API URL: $TUNNEL_API_URL"
echo "  - ArgoCD 대시보드: https://argo.$DOMAIN/applications/safework"
echo "  - kubeconfig: $KUBECONFIG_FILE"
echo "  - 백업: $BACKUP_DIR"
echo ""
echo "🔧 kubectl 사용법:"
echo "  export KUBECONFIG=$PWD/$KUBECONFIG_FILE"
echo "  kubectl get nodes"
echo ""
echo "⚠️  보안 권장사항:"
echo "1. Cloudflare Access Policy 설정으로 API 서버 접근 제한"
echo "2. 정기적인 토큰 로테이션"
echo "3. 감사 로깅 활성화"