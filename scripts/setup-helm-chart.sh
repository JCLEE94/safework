#!/bin/bash

# SafeWork Helm 차트 저장소 설정 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎯 SafeWork Helm 차트 저장소 설정${NC}"

# 1. Helm 차트 저장소 시크릿 생성
echo -e "${BLUE}1. Helm 차트 저장소 시크릿 생성 중...${NC}"
kubectl apply -f k8s/argocd/helm-repo-secret.yaml
echo -e "${GREEN}✅ Helm 차트 저장소 시크릿 생성 완료${NC}"

# 2. 기존 GitOps 애플리케이션 삭제 (선택사항)
echo -e "${YELLOW}2. 기존 애플리케이션 정리...${NC}"
kubectl delete application safework-gitops -n argocd --ignore-not-found=true || echo "기존 애플리케이션 없음"

# 3. Helm 기반 ArgoCD 애플리케이션 생성
echo -e "${BLUE}3. Helm 기반 ArgoCD 애플리케이션 생성 중...${NC}"
kubectl apply -f k8s/argocd/application-helm.yaml
echo -e "${GREEN}✅ Helm 기반 애플리케이션 생성 완료${NC}"

# 4. Helm 차트 저장소 확인
echo -e "${BLUE}4. Helm 차트 저장소 확인 중...${NC}"
# ArgoCD에서 직접 차트 확인
kubectl exec -n argocd deployment/argocd-repo-server -- helm repo add chartmuseum https://charts.jclee.me --username admin --password bingogo1 || echo "차트 저장소 추가 실패 (무시 가능)"
kubectl exec -n argocd deployment/argocd-repo-server -- helm search repo chartmuseum/safework || echo "차트 검색 실패 (무시 가능)"

# 5. 애플리케이션 상태 확인
echo -e "${BLUE}5. 애플리케이션 상태 확인 중...${NC}"
sleep 5
kubectl get application safework-helm -n argocd

# 6. 초기 동기화
echo -e "${BLUE}6. 초기 동기화 중...${NC}"
kubectl patch application safework-helm -n argocd --type='merge' --patch='{"operation":{"sync":{}}}'

# 7. 최종 상태 확인
echo -e "${BLUE}7. 최종 상태 확인...${NC}"
sleep 10
kubectl get application safework-helm -n argocd

echo -e "${GREEN}✅ Helm 차트 설정 완료!${NC}"
echo -e "${BLUE}📊 차트 저장소: https://charts.jclee.me${NC}"
echo -e "${BLUE}📊 ArgoCD 대시보드: https://argo.jclee.me/applications/safework-helm${NC}"
echo -e "${BLUE}🔄 수동 동기화: kubectl patch application safework-helm -n argocd --type='merge' --patch='{\"operation\":{\"sync\":{}}}'${NC}"