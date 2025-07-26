#!/bin/bash
set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 로깅 함수
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 환경 변수 설정
NAMESPACE="safework"
REGISTRY_URL="registry.jclee.me"
REGISTRY_USERNAME="admin"
REGISTRY_PASSWORD="bingogo1"
CHARTMUSEUM_URL="https://charts.jclee.me"
CHARTMUSEUM_USERNAME="admin"
CHARTMUSEUM_PASSWORD="bingogo1"
ARGOCD_URL="argo.jclee.me"
ARGOCD_USERNAME="admin"
ARGOCD_PASSWORD="bingogo1"

log_info "SafeWork Pro GitOps 환경 설정 시작"

# 1. Kubernetes 네임스페이스 생성
log_info "Kubernetes 네임스페이스 생성 중..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

# 2. Registry Secret 생성
log_info "Registry Secret 생성 중..."
kubectl create secret docker-registry harbor-registry \
  --docker-server=${REGISTRY_URL} \
  --docker-username=${REGISTRY_USERNAME} \
  --docker-password=${REGISTRY_PASSWORD} \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -

# 3. ArgoCD Repository 등록
log_info "ArgoCD Repository 등록 중..."

# ArgoCD CLI 설치 확인
if ! command -v argocd &> /dev/null; then
  log_warn "ArgoCD CLI가 설치되지 않았습니다. 설치 중..."
  curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
  sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
  rm argocd-linux-amd64
fi

# ArgoCD 로그인
log_info "ArgoCD 로그인 중..."
if argocd login ${ARGOCD_URL} --username ${ARGOCD_USERNAME} --password ${ARGOCD_PASSWORD} --insecure --grpc-web; then
  log_info "ArgoCD 로그인 성공"
else
  log_error "ArgoCD 로그인 실패"
  exit 1
fi

# Repository 등록 확인 및 추가
log_info "ChartMuseum Repository 등록 중..."
if argocd repo list | grep -q "${CHARTMUSEUM_URL}"; then
  log_info "Repository가 이미 등록되어 있습니다."
else
  argocd repo add ${CHARTMUSEUM_URL} \
    --type helm \
    --username ${CHARTMUSEUM_USERNAME} \
    --password ${CHARTMUSEUM_PASSWORD}
  log_info "Repository 등록 완료"
fi

# 4. ArgoCD Application 생성
log_info "ArgoCD Application 생성 중..."
if argocd app get safework-gitops --grpc-web > /dev/null 2>&1; then
  log_info "Application이 이미 존재합니다. 업데이트 중..."
  argocd app create -f argocd-application-gitops.yaml --upsert --grpc-web
else
  log_info "새로운 Application 생성 중..."
  argocd app create -f argocd-application-gitops.yaml --grpc-web
fi

# 5. 초기 동기화
log_info "초기 동기화 수행 중..."
argocd app sync safework-gitops --grpc-web

log_info "✅ SafeWork Pro GitOps 환경 설정 완료"
echo ""
echo "🌐 접속 정보:"
echo "- 프로덕션 사이트: https://safework.jclee.me"
echo "- NodePort 접속: NodePort 32301"
echo "- ArgoCD 대시보드: https://${ARGOCD_URL}/applications/safework-gitops"
echo "- ChartMuseum: ${CHARTMUSEUM_URL}"
echo ""
echo "📋 다음 단계:"
echo "1. 코드 변경 후 git push를 하면 자동 배포됩니다"
echo "2. ArgoCD 대시보드에서 배포 상태를 확인하세요"
echo "3. kubectl get pods -n ${NAMESPACE}로 Pod 상태를 확인하세요"