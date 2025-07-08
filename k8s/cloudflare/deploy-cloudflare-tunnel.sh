#!/bin/bash

# Cloudflare Tunnel 배포 스크립트
set -e

echo "=== SafeWork Cloudflare Tunnel 배포 ==="
echo ""

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 네임스페이스 확인
if kubectl get namespace safework &> /dev/null; then
    echo -e "${GREEN}✓${NC} safework 네임스페이스가 이미 존재합니다."
else
    echo -e "${YELLOW}!${NC} safework 네임스페이스 생성 중..."
    kubectl create namespace safework
fi

# Secret 존재 확인
if kubectl get secret cloudflare-tunnel-token -n safework &> /dev/null; then
    echo -e "${GREEN}✓${NC} Cloudflare Tunnel 토큰이 이미 설정되어 있습니다."
else
    echo -e "${RED}✗${NC} Cloudflare Tunnel 토큰이 설정되지 않았습니다."
    echo "   k8s/cloudflare/tunnel-secret.yaml 파일에 토큰을 설정한 후 다시 실행하세요."
    echo "   또는 setup-tunnel-token.sh 스크립트를 사용하세요."
    exit 1
fi

# 배포 옵션 선택
echo ""
echo "배포 옵션을 선택하세요:"
echo "1) Cloudflare Tunnel만 배포"
echo "2) SafeWork + Cloudflare Tunnel 전체 배포"
echo "3) ArgoCD Application 생성"
read -p "선택 (1-3): " DEPLOY_OPTION

case $DEPLOY_OPTION in
    1)
        echo -e "\n${YELLOW}►${NC} Cloudflare Tunnel 배포 중..."
        
        # Secret 적용
        kubectl apply -f k8s/cloudflare/tunnel-secret.yaml
        
        # ConfigMap 적용
        kubectl apply -f k8s/cloudflare/tunnel-config.yaml
        
        # Deployment 적용
        kubectl apply -f k8s/cloudflare/cloudflared-deployment.yaml
        
        # Service 패치
        kubectl apply -f k8s/cloudflare/safework-service-clusterip.yaml
        
        echo -e "${GREEN}✓${NC} Cloudflare Tunnel 배포 완료!"
        ;;
        
    2)
        echo -e "\n${YELLOW}►${NC} SafeWork + Cloudflare Tunnel 전체 배포 중..."
        
        # Kustomize로 전체 배포
        kubectl apply -k k8s/safework-with-cloudflare/
        
        echo -e "${GREEN}✓${NC} 전체 배포 완료!"
        ;;
        
    3)
        echo -e "\n${YELLOW}►${NC} ArgoCD Application 생성 중..."
        
        # ArgoCD Application 생성
        kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: safework-cloudflare
  namespace: argocd
  finalizers:
  - resources-finalizer.argocd.argoproj.io
spec:
  project: default
  source:
    repoURL: https://github.com/JCLEE94/safework
    targetRevision: main
    path: k8s/safework-with-cloudflare
  destination:
    server: https://kubernetes.default.svc
    namespace: safework
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
        
        echo -e "${GREEN}✓${NC} ArgoCD Application 생성 완료!"
        echo "   ArgoCD 대시보드에서 동기화 상태를 확인하세요."
        ;;
        
    *)
        echo -e "${RED}✗${NC} 잘못된 선택입니다."
        exit 1
        ;;
esac

# 배포 상태 확인
echo -e "\n${YELLOW}►${NC} 배포 상태 확인 중..."
sleep 5

# Pod 상태 확인
echo -e "\n${GREEN}Pods:${NC}"
kubectl get pods -n safework

# cloudflared 상태 확인
if kubectl get deployment cloudflared -n safework &> /dev/null; then
    echo -e "\n${GREEN}Cloudflare Tunnel 상태:${NC}"
    kubectl logs -n safework -l app=cloudflared --tail=20 | grep -E "(Registered|Connected|INF)" || true
fi

echo -e "\n${GREEN}✓${NC} 배포가 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. Cloudflare Zero Trust 대시보드에서 Public Hostname 설정"
echo "   - Subdomain: safework"
echo "   - Domain: jclee.me"
echo "   - Service: http://safework.safework.svc.cluster.local:3001"
echo ""
echo "2. 몇 분 후 https://safework.jclee.me 에서 접속 테스트"
echo ""
echo "문제가 있다면 다음 명령으로 로그를 확인하세요:"
echo "kubectl logs -n safework -l app=cloudflared -f"