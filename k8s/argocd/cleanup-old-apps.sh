#!/bin/bash

# 기존 ArgoCD 애플리케이션 정리 스크립트

set -e

NAMESPACE="argocd"
ARGOCD_SERVER="argo.jclee.me"

echo "🧹 기존 ArgoCD 애플리케이션 정리 시작..."

# 1. 기존 애플리케이션 목록 확인
echo "1. 기존 애플리케이션 목록:"
kubectl get applications -n $NAMESPACE | grep safework || echo "safework 관련 애플리케이션 없음"

# 2. 기존 safework 애플리케이션 삭제
echo "2. 기존 safework 애플리케이션 삭제..."
kubectl delete application safework -n $NAMESPACE --ignore-not-found=true

# 3. 기존 Image Updater 관련 리소스 정리
echo "3. ArgoCD Image Updater 관련 리소스 정리..."
kubectl delete configmap argocd-image-updater-config -n $NAMESPACE --ignore-not-found=true
kubectl delete secret argocd-image-updater-secret -n $NAMESPACE --ignore-not-found=true

# 4. 기존 차트 관련 정리
echo "4. 기존 차트 관련 정리..."
rm -f charts/safework-*.tgz || echo "차트 패키지 없음"

# 5. 기존 워크플로우 파일 정리
echo "5. 기존 워크플로우 파일 정리..."
rm -f .github/workflows/ci-cd-pipeline.yml || echo "기존 CI/CD 파이프라인 없음"
rm -f .github/workflows/release.yml || echo "기존 릴리즈 워크플로우 없음"
rm -f .github/workflows/development.yml || echo "기존 개발 워크플로우 없음"

# 6. 상태 확인
echo "6. 정리 후 상태 확인..."
kubectl get applications -n $NAMESPACE | grep safework || echo "✅ safework 애플리케이션 정리 완료"

echo "✅ 기존 리소스 정리 완료!"
echo "🔄 다음 단계: ./k8s/argocd/setup-argocd.sh 실행"