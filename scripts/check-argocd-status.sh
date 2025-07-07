#!/bin/bash

# ArgoCD 상태 확인 스크립트

echo "🔍 ArgoCD 애플리케이션 상태 확인 중..."

# ArgoCD 서버 정보
ARGOCD_SERVER="argo.jclee.me"
APP_NAME="safework"

# 애플리케이션 상태 확인
echo -e "\n📊 애플리케이션 전체 상태:"
argocd app get $APP_NAME --server $ARGOCD_SERVER --grpc-web --insecure 2>/dev/null || echo "❌ ArgoCD 로그인이 필요합니다"

# 리소스 상태 확인
echo -e "\n📋 리소스별 상태:"
argocd app resources $APP_NAME --server $ARGOCD_SERVER --grpc-web --insecure 2>/dev/null || echo "❌ 리소스 정보를 가져올 수 없습니다"

# 이벤트 확인
echo -e "\n🔔 최근 이벤트:"
kubectl get events -n default --sort-by='.lastTimestamp' | tail -20 2>/dev/null || echo "❌ kubectl 액세스가 필요합니다"

# Pod 상태 확인
echo -e "\n🐳 Pod 상태:"
kubectl get pods -l app=safework -o wide 2>/dev/null || echo "❌ Pod 정보를 가져올 수 없습니다"

# Pod 로그 확인 (최근 50줄)
echo -e "\n📜 Pod 로그 (최근 50줄):"
POD_NAME=$(kubectl get pods -l app=safework -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ ! -z "$POD_NAME" ]; then
    kubectl logs $POD_NAME --tail=50 2>/dev/null || echo "❌ 로그를 가져올 수 없습니다"
else
    echo "❌ 실행 중인 Pod를 찾을 수 없습니다"
fi

# PVC 상태 확인
echo -e "\n💾 PVC 상태:"
kubectl get pvc 2>/dev/null | grep -E "(safework|postgres|redis)" || echo "❌ PVC 정보가 없습니다"

# Service 상태 확인
echo -e "\n🔌 Service 상태:"
kubectl get svc -l app=safework 2>/dev/null || echo "❌ Service 정보를 가져올 수 없습니다"

# Ingress 상태 확인
echo -e "\n🌐 Ingress 상태:"
kubectl get ingress 2>/dev/null | grep safework || echo "❌ Ingress 정보가 없습니다"

echo -e "\n✅ 상태 확인 완료"