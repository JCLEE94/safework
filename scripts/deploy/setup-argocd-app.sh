#!/bin/bash
set -e

echo "🚀 ArgoCD Application 설정 스크립트"
echo "===================================="

# ArgoCD 설정값
ARGOCD_URL="${ARGOCD_URL:-https://argo.jclee.me}"
ARGOCD_USERNAME="${ARGOCD_USERNAME:-admin}"
ARGOCD_PASSWORD="${ARGOCD_PASSWORD:-bingogo1}"
CHARTMUSEUM_URL="${CHARTMUSEUM_URL:-https://charts.jclee.me}"
CHARTMUSEUM_USERNAME="${CHARTMUSEUM_USERNAME:-admin}"
CHARTMUSEUM_PASSWORD="${CHARTMUSEUM_PASSWORD:-bingogo1}"
APP_NAME="safework"
NAMESPACE="production"

echo "📋 설정 정보:"
echo "  ArgoCD URL: $ARGOCD_URL"
echo "  ChartMuseum URL: $CHARTMUSEUM_URL"
echo "  Application: $APP_NAME"
echo "  Namespace: $NAMESPACE"

# ArgoCD 로그인
echo "🔐 ArgoCD 로그인..."
if ! argocd login $ARGOCD_URL --username $ARGOCD_USERNAME --password $ARGOCD_PASSWORD --insecure --grpc-web; then
    echo "❌ ArgoCD 로그인 실패"
    echo "수동으로 로그인 후 다음 명령어 실행:"
    echo "argocd login $ARGOCD_URL --username $ARGOCD_USERNAME --password $ARGOCD_PASSWORD --insecure --grpc-web"
    exit 1
fi

# Repository 추가
echo "📦 ChartMuseum Repository 등록..."
if ! argocd repo list | grep -q "$CHARTMUSEUM_URL"; then
    argocd repo add $CHARTMUSEUM_URL --type helm --username $CHARTMUSEUM_USERNAME --password $CHARTMUSEUM_PASSWORD
    echo "✅ Repository 등록 완료"
else
    echo "ℹ️  Repository 이미 등록됨"
fi

# Kubernetes 네임스페이스 생성
echo "🔧 Kubernetes 네임스페이스 생성..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Docker Registry Secret 생성
echo "🔐 Docker Registry Secret 생성..."
kubectl create secret docker-registry harbor-registry \
  --docker-server=registry.jclee.me \
  --docker-username=admin \
  --docker-password=bingogo1 \
  --namespace=$NAMESPACE \
  --dry-run=client -o yaml | kubectl apply -f -

# ArgoCD Application 생성
echo "🚀 ArgoCD Application 생성..."
if argocd app get $APP_NAME-$NAMESPACE > /dev/null 2>&1; then
    echo "ℹ️  Application 이미 존재, 업데이트 수행..."
    kubectl apply -f argocd-application.yaml
else
    echo "📝 새 Application 생성..."
    kubectl apply -f argocd-application.yaml
fi

# Application 동기화
echo "🔄 Application 동기화..."
argocd app sync $APP_NAME-$NAMESPACE

echo "✅ ArgoCD Application 설정 완료"
echo ""
echo "📊 확인 링크:"
echo "  - ArgoCD Dashboard: $ARGOCD_URL/applications/$APP_NAME-$NAMESPACE"
echo "  - Application Status: argocd app get $APP_NAME-$NAMESPACE"
echo "  - Kubernetes Resources: kubectl get pods,svc -n $NAMESPACE"