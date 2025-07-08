#!/bin/bash

# Cloudflare Tunnel 리소스 직접 적용 스크립트
set -e

echo "=== Cloudflare Tunnel 배포 ==="
echo ""

# 네임스페이스 확인
kubectl create namespace safework --dry-run=client -o yaml | kubectl apply -f -

# Secret이 이미 있는지 확인
if kubectl get secret cloudflare-tunnel-token -n safework &> /dev/null; then
    echo "✅ Cloudflare Tunnel secret이 이미 존재합니다."
else
    if [ -f k8s/cloudflare/tunnel-secret.yaml ]; then
        echo "📦 Cloudflare Tunnel secret 적용 중..."
        kubectl apply -f k8s/cloudflare/tunnel-secret.yaml
    else
        echo "❌ tunnel-secret.yaml 파일을 찾을 수 없습니다."
        echo "   CI/CD에서 생성되거나 setup-tunnel-token.sh를 실행하세요."
        exit 1
    fi
fi

# ConfigMap 적용
echo "📋 ConfigMap 적용 중..."
kubectl apply -f k8s/cloudflare/tunnel-config.yaml

# Deployment 적용
echo "🚀 Cloudflare Tunnel deployment 적용 중..."
kubectl apply -f k8s/cloudflare/cloudflared-deployment.yaml

# Service 패치 (ClusterIP로 변경)
echo "🔧 Service를 ClusterIP로 변경 중..."
kubectl apply -f k8s/cloudflare/safework-service-clusterip.yaml

# 상태 확인
echo ""
echo "📊 배포 상태:"
kubectl get pods -n safework -l app=cloudflared
echo ""
echo "✅ Cloudflare Tunnel 배포 완료!"
echo ""
echo "로그 확인: kubectl logs -n safework -l app=cloudflared -f"