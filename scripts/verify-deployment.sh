#\!/bin/bash
# SafeWork Pro 배포 검증 스크립트

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[⚠]${NC} $1"; }

echo "=== SafeWork Pro 배포 검증 시작 ==="

# Kubernetes 연결 확인
log_info "Kubernetes 클러스터 연결 확인..."
if kubectl cluster-info > /dev/null 2>&1; then
    log_success "Kubernetes 클러스터 연결됨"
else
    log_warn "Kubernetes 클러스터 연결 실패"
    exit 1
fi

# 네임스페이스 확인
for ns in production argocd; do
    if kubectl get namespace $ns > /dev/null 2>&1; then
        log_success "네임스페이스 $ns 존재"
    else
        log_warn "네임스페이스 $ns 없음"
    fi
done

# Pod 상태 확인
kubectl get pods -n production 2>/dev/null || log_warn "production 네임스페이스에 Pod 없음"

# ArgoCD Application 확인
kubectl get application safework-prod -n argocd 2>/dev/null && log_success "ArgoCD Application 존재" || log_warn "ArgoCD Application 없음"

log_info "검증 완료"
log_info "유용한 명령어:"
echo "  kubectl get pods -n production"
echo "  kubectl get application -n argocd"
echo "  argocd app sync safework-prod"
EOF < /dev/null
