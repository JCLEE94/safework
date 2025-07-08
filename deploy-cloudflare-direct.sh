#!/bin/bash

# Cloudflare Tunnel 직접 배포 스크립트
set -e

echo "=== Cloudflare Tunnel 직접 배포 ==="
echo ""

# 현재 생성된 secret 확인
if [ -f k8s/cloudflare/tunnel-secret.yaml ]; then
    echo "✅ tunnel-secret.yaml 파일 존재"
else
    echo "❌ tunnel-secret.yaml 파일이 없습니다."
    echo "CI/CD에서 생성되지 않았습니다."
    exit 1
fi

# 직접 적용
echo "🚀 Cloudflare 리소스 직접 적용 중..."

# Secret 적용
kubectl apply -f k8s/cloudflare/tunnel-secret.yaml

# ConfigMap 적용
kubectl apply -f k8s/cloudflare/tunnel-config.yaml

# Deployment 적용
kubectl apply -f k8s/cloudflare/cloudflared-deployment.yaml

# Service 변경 (ClusterIP)
kubectl apply -f k8s/cloudflare/safework-service-clusterip.yaml

echo ""
echo "📊 Cloudflare Tunnel 상태:"
kubectl get pods -n safework -l app=cloudflared

echo ""
echo "✅ Cloudflare Tunnel 배포 완료!"
echo ""
echo "확인 명령어:"
echo "- Pod 로그: kubectl logs -n safework -l app=cloudflare -f"
echo "- 접속 테스트: curl https://safework.jclee.me/health"