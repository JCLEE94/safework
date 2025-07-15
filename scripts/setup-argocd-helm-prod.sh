#!/bin/bash

# 운영 ArgoCD에 SafeWork Helm 차트 배포 설정

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ARGOCD_SERVER="argo.jclee.me"
ARGOCD_USER="admin"
ARGOCD_PASS="bingogo1"
CHART_REPO="https://charts.jclee.me"
CHART_USER="admin"
CHART_PASS="bingogo1"

echo -e "${BLUE}🚀 운영 ArgoCD 서버에 SafeWork Helm 차트 배포 설정${NC}"

# 1. ArgoCD CLI 로그인
echo -e "${BLUE}1. ArgoCD 서버 로그인 중...${NC}"
echo "y" | argocd login $ARGOCD_SERVER \
  --username $ARGOCD_USER \
  --password $ARGOCD_PASS \
  --insecure \
  --grpc-web

echo -e "${GREEN}✅ ArgoCD 로그인 성공${NC}"

# 2. Helm 차트 저장소 추가
echo -e "${BLUE}2. Helm 차트 저장소 추가 중...${NC}"
argocd repo add $CHART_REPO \
  --type helm \
  --name chartmuseum-safework \
  --username $CHART_USER \
  --password $CHART_PASS \
  --grpc-web \
  --upsert || echo "저장소 이미 존재 (무시 가능)"

echo -e "${GREEN}✅ Helm 차트 저장소 추가 완료${NC}"

# 3. 기존 애플리케이션 확인
echo -e "${BLUE}3. 기존 애플리케이션 확인 중...${NC}"
argocd app list --grpc-web | grep safework || echo "SafeWork 애플리케이션 없음"

# 4. SafeWork 애플리케이션 생성/업데이트
echo -e "${BLUE}4. SafeWork 애플리케이션 생성 중...${NC}"
argocd app create safework-prod \
  --repo $CHART_REPO \
  --helm-chart safework \
  --revision "*" \
  --dest-server https://kubernetes.default.svc \
  --dest-namespace safework \
  --sync-policy automated \
  --auto-prune \
  --self-heal \
  --grpc-web \
  --upsert \
  --helm-set image.repository=registry.jclee.me/safework \
  --helm-set image.tag=latest \
  --helm-set service.type=ClusterIP \
  --helm-set ingress.enabled=true \
  --helm-set ingress.hosts[0].host=safework.jclee.me \
  --helm-set ingress.hosts[0].paths[0].path=/ \
  --helm-set ingress.hosts[0].paths[0].pathType=Prefix

echo -e "${GREEN}✅ SafeWork 애플리케이션 생성 완료${NC}"

# 5. 애플리케이션 동기화
echo -e "${BLUE}5. 애플리케이션 동기화 중...${NC}"
argocd app sync safework-prod --grpc-web

# 6. 애플리케이션 상태 확인
echo -e "${BLUE}6. 최종 상태 확인...${NC}"
argocd app get safework-prod --grpc-web

echo -e "${GREEN}✅ 운영 ArgoCD 설정 완료!${NC}"
echo -e "${BLUE}📊 ArgoCD 대시보드: https://$ARGOCD_SERVER/applications/safework-prod${NC}"
echo -e "${BLUE}🌐 애플리케이션 URL: https://safework.jclee.me${NC}"
echo -e "${BLUE}📦 Helm 차트: $CHART_REPO/safework${NC}"