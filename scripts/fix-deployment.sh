#!/bin/bash

# SafeWork Deployment 충돌 해결 스크립트

echo "🔧 SafeWork Deployment 충돌을 해결합니다..."

# 1. ArgoCD 애플리케이션 삭제 (리소스는 유지)
echo "📦 ArgoCD 애플리케이션 일시 삭제..."
argocd app delete safework --cascade=false || true

# 2. 기존 Deployment 삭제
echo "🗑️ 기존 Deployment 삭제 중..."
kubectl delete deployment safework postgres redis -n safework --ignore-not-found=true

# 3. PVC는 데이터 보존을 위해 유지
echo "💾 PersistentVolumeClaim은 유지됩니다..."

# 4. 잠시 대기
echo "⏳ 30초 대기 중..."
sleep 30

# 5. ArgoCD 애플리케이션 재생성
echo "🚀 ArgoCD 애플리케이션 재생성..."
argocd app create safework \
  --repo https://github.com/JCLEE94/safework.git \
  --path charts/safework \
  --revision main \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace safework \
  --sync-policy automated \
  --self-heal \
  --sync-option CreateNamespace=true \
  --sync-option Replace=true \
  --sync-option PrunePropagationPolicy=foreground

# 6. 동기화
echo "🔄 애플리케이션 동기화 중..."
sleep 5
argocd app sync safework

# 7. 상태 확인
echo "✅ 완료! 애플리케이션 상태:"
argocd app get safework

echo ""
echo "🌐 접속 URL: https://safework.jclee.me"
echo "🔍 ArgoCD Dashboard: https://argo.jclee.me/applications/safework"