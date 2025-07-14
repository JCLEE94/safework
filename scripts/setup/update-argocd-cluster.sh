#!/bin/bash

# SafeWork - ArgoCD 클러스터를 외부 DNS로 업데이트
# Usage: ./update-argocd-cluster.sh <external-dns-url>

set -e

EXTERNAL_URL=${1:-"https://k8s-api.jclee.me:6443"}
BACKUP_DIR="backup/argocd-$(date +%Y%m%d-%H%M%S)"

echo "🔄 ArgoCD 클러스터 설정을 외부 DNS로 업데이트"
echo "외부 URL: $EXTERNAL_URL"

# Step 1: 백업 생성
echo "💾 Step 1: 현재 설정 백업"
mkdir -p $BACKUP_DIR
cp -r k8s/argocd/ $BACKUP_DIR/
argocd app list --grpc-web > $BACKUP_DIR/app-list.txt
argocd cluster list --grpc-web > $BACKUP_DIR/cluster-list.txt
echo "✅ 백업 완료: $BACKUP_DIR"

# Step 2: 기존 safework 앱 백업 및 삭제
echo "🗑️  Step 2: 기존 safework 애플리케이션 백업 및 삭제"
argocd app get safework --grpc-web > $BACKUP_DIR/safework-app.yaml 2>/dev/null || echo "safework 앱이 존재하지 않음"
argocd app delete safework --grpc-web --yes 2>/dev/null || echo "safework 앱 삭제 완료 또는 존재하지 않음"

# Step 3: Application 매니페스트 업데이트
echo "📝 Step 3: Application 매니페스트 업데이트"
find k8s/argocd/ -name "*.yaml" -exec grep -l "https://kubernetes.default.svc" {} \; | while read file; do
    echo "업데이트 중: $file"
    sed -i "s|server: https://kubernetes.default.svc|server: $EXTERNAL_URL|g" "$file"
done

# 변경사항 확인
echo "📋 변경된 파일들:"
grep -r "$EXTERNAL_URL" k8s/argocd/ --include="*.yaml" | cut -d: -f1 | sort | uniq

# Step 4: 새 클러스터 설정으로 애플리케이션 재생성
echo "🚀 Step 4: 새 설정으로 애플리케이션 재생성"
sleep 5  # ArgoCD가 삭제를 완료할 시간 제공

argocd app create --grpc-web -f k8s/argocd/application.yaml

# Step 5: 상태 확인
echo "✅ Step 5: 새 애플리케이션 상태 확인"
sleep 10
argocd app get safework --grpc-web

echo ""
echo "🎉 ArgoCD 클러스터 업데이트 완료!"
echo "📊 대시보드: https://argo.jclee.me/applications/safework"
echo "🔗 새 클러스터 URL: $EXTERNAL_URL"
echo "💾 백업 위치: $BACKUP_DIR"
echo ""
echo "애플리케이션이 OutOfSync 상태인 경우:"
echo "argocd app sync safework --grpc-web"