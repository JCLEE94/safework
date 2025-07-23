#!/bin/bash
set -e

APP_NAME=${1:-safework}
NAMESPACE=${2:-production}

echo "=== 배포 검증 시작 ==="
echo "App: $APP_NAME, Namespace: $NAMESPACE"

# 1. GitHub Actions 상태 확인
echo -n "1. GitHub Actions 실행 상태: "
LAST_RUN=$(gh run list --limit 1 --json status,conclusion,name --jq '.[0]')
echo "$LAST_RUN"

# 2. Helm Chart 확인
echo -n "2. ChartMuseum에서 Chart 확인: "
curl -s https://charts.jclee.me/api/charts/${APP_NAME} | jq -r '.[0].version' || echo "Chart not found"

# 3. ArgoCD 애플리케이션 상태
echo "3. ArgoCD 애플리케이션 상태:"
argocd app get ${APP_NAME} --grpc-web || echo "ArgoCD app not found"

# 4. Kubernetes 리소스 확인
echo "4. Kubernetes 리소스:"
kubectl get all -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME}

# 5. Pod 이미지 확인
echo -n "5. 실행 중인 이미지: "
kubectl get pods -n ${NAMESPACE} -l app.kubernetes.io/name=${APP_NAME} -o jsonpath='{.items[0].spec.containers[0].image}' || echo "No pods found"
echo

# 6. 헬스체크
echo -n "6. 애플리케이션 헬스체크: "
curl -sf https://${APP_NAME}.jclee.me/health || echo "Health check failed"
echo

echo "=== 검증 완료 ==="