#!/bin/bash
# SafeWork 리팩토링된 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== SafeWork Pro 배포 시작 ===${NC}"

# 환경 변수 확인
if [ -z "$KUBECONFIG" ]; then
    export KUBECONFIG=~/.kube/config
fi

# 1. 네임스페이스 생성
echo -e "${YELLOW}1. 네임스페이스 확인/생성${NC}"
kubectl create namespace safework --dry-run=client -o yaml | kubectl apply -f -

# 2. Registry Secret 생성
echo -e "${YELLOW}2. Registry Secret 생성${NC}"
kubectl create secret docker-registry harbor-registry \
  --docker-server=registry.jclee.me \
  --docker-username=${REGISTRY_USER:-qws9411} \
  --docker-password=${REGISTRY_PASS:-bingogo1} \
  --namespace=safework \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. PVC 생성 (Persistent Volume Claims)
echo -e "${YELLOW}3. Storage 설정${NC}"
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: postgres-pvc
  namespace: safework
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: safework
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
EOF

# 4. Kustomize로 배포
echo -e "${YELLOW}4. Kustomize 배포${NC}"
kubectl apply -k k8s/overlays/production

# 5. 배포 상태 확인
echo -e "${YELLOW}5. 배포 상태 확인${NC}"
kubectl rollout status deployment/safework -n safework --timeout=300s

# 6. Pod 상태 확인
echo -e "${YELLOW}6. Pod 상태${NC}"
kubectl get pods -n safework -l app=safework

# 7. Service 정보
echo -e "${YELLOW}7. Service 정보${NC}"
kubectl get svc safework -n safework

# 8. ArgoCD Application 생성/업데이트
if command -v argocd &> /dev/null; then
    echo -e "${YELLOW}8. ArgoCD Application 설정${NC}"
    kubectl apply -f k8s/argocd/application-refactored.yaml
    
    # ArgoCD 동기화
    argocd app sync safework --prune || echo "ArgoCD sync 실패 - 수동 확인 필요"
else
    echo -e "${YELLOW}8. ArgoCD CLI 없음 - 수동으로 Application 생성 필요${NC}"
fi

# 9. 접속 정보 출력
NODE_PORT=$(kubectl get svc safework -n safework -o jsonpath='{.spec.ports[0].nodePort}')
echo -e "${GREEN}=== 배포 완료 ===${NC}"
echo -e "내부 접속: http://safework.safework.svc.cluster.local:3001"
echo -e "외부 접속: http://<NODE_IP>:${NODE_PORT}"
echo -e "프로덕션 URL: https://safework.jclee.me"

# 10. 헬스체크
echo -e "${YELLOW}10. 헬스체크${NC}"
kubectl exec -n safework deployment/safework -- curl -s http://localhost:3001/health | jq . || echo "헬스체크 실패"