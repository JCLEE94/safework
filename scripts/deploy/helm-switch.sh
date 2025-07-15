#!/bin/bash

# Helm 기반 SafeWork 배포로 전환 스크립트

echo "🔄 SafeWork를 Helm Charts 기반으로 전환합니다..."

# 1. 기존 애플리케이션 삭제 (cascade=false로 리소스는 유지)
echo "📦 기존 ArgoCD 애플리케이션 삭제 중..."
argocd app delete safework-helm --cascade=false 2>/dev/null || true
argocd app delete safework --cascade=false 2>/dev/null || true

# 2. 잠시 대기
echo "⏳ 30초 대기 중..."
sleep 30

# 3. Helm Repository 업데이트
echo "📊 Helm repository 업데이트 중..."
helm repo add jclee https://charts.jclee.me
helm repo update

# 4. ArgoCD Application 생성 (Helm)
echo "🚀 새로운 Helm 기반 ArgoCD Application 생성 중..."
cat <<EOF | kubectl apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: safework
  namespace: argocd
  annotations:
    argocd-image-updater.argoproj.io/image-list: safework=registry.jclee.me/safework:latest
    argocd-image-updater.argoproj.io/safework.allow-tags: regexp:^prod-[0-9]{8}-[a-f0-9]{7}$
    argocd-image-updater.argoproj.io/safework.update-strategy: latest
    argocd-image-updater.argoproj.io/safework.helm.image-name: image.repository
    argocd-image-updater.argoproj.io/safework.helm.image-tag: image.tag
    argocd-image-updater.argoproj.io/write-back-method: git
    argocd-image-updater.argoproj.io/git-branch: main
spec:
  project: default
  source:
    repoURL: https://charts.jclee.me
    targetRevision: 0.1.1
    chart: safework
    helm:
      releaseName: safework
      values: |
        image:
          repository: registry.jclee.me/safework
          tag: prod-20250715-56bc40a
        
        service:
          nodePort: 32301
        
        jwtSecret: "production-jwt-secret-key"
        
        createNamespace: false
  
  destination:
    server: https://kubernetes.default.svc
    namespace: safework
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
    - Replace=true
    retry:
      limit: 5
      backoff:
        duration: 5s
        factor: 2
        maxDuration: 3m
EOF

# 5. 상태 확인
echo "✅ Helm 기반 SafeWork 배포 완료!"
echo "📊 애플리케이션 상태:"
argocd app get safework

echo ""
echo "🌐 접속 URL: https://safework.jclee.me"
echo "🔍 ArgoCD Dashboard: https://argo.jclee.me/applications/safework"