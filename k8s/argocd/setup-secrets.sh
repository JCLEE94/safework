#!/bin/bash

# ArgoCD Secrets 설정 스크립트
# GitHub Repository, Registry, API 접근을 위한 secrets 설정

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 환경 변수 (제공된 값들)
ARGOCD_SERVER="${ARGOCD_SERVER:-argo.jclee.me}"
ARGOCD_API="${ARGOCD_API:-eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJhcmdvY2QiLCJzdWIiOiJhZG1pbjphcGlLZXkiLCJuYmYiOjE3NTE1ODkwMTAsImlhdCI6MTc1MTU4OTAxMCwianRpIjoiNjg0Y2NhYmQtMWUwNi00M2E1LTlkMGEtMzRlNzE4NGMzNDUzIn0.0wNIBxenEi2_ALlhjzkmlMyWtid7gfsJj8no2CEjI"}"
ARGOCD_ADMIN_USER="${ARGOCD_ADMIN_USER:-admin}"
ARGOCD_ADMIN_PASS="${ARGOCD_ADMIN_PASS:-bingogo1}"
ARGOCD_USER="${ARGOCD_USER:-jclee}"
ARGOCD_USER_PASS="${ARGOCD_USER_PASS:-bingogo1}"
GITHUB_USER="${GITHUB_USER:-JCLEE94}"
GITHUB_TOKEN="${GITHUB_TOKEN:-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}"
REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
REGISTRY_USER="${REGISTRY_USER:-qws9411}"
REGISTRY_PASS="${REGISTRY_PASS:-bingogo1}"

# 함수 정의
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# ArgoCD namespace 생성
create_argocd_namespace() {
    log_info "ArgoCD namespace 생성 중..."
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
    log_success "ArgoCD namespace 생성 완료"
}

# GitHub Repository Secret 생성
create_github_repo_secret() {
    log_info "GitHub Repository Secret 생성 중..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: safework-repo
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: git
  url: https://github.com/${GITHUB_USER}/safework.git
  username: ${GITHUB_USER}
  password: ${GITHUB_TOKEN}
  project: default
EOF
    
    log_success "GitHub Repository Secret 생성 완료"
}

# Docker Registry Secret 생성 (ArgoCD용)
create_registry_secret_argocd() {
    log_info "ArgoCD Registry Secret 생성 중..."
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: registry-secret-argocd
  namespace: argocd
  labels:
    argocd.argoproj.io/secret-type: repository
type: Opaque
stringData:
  type: helm
  name: registry-jclee-me
  url: ${REGISTRY_URL}
  username: ${REGISTRY_USER}
  password: ${REGISTRY_PASS}
EOF
    
    log_success "ArgoCD Registry Secret 생성 완료"
}

# SafeWork namespace 생성
create_safework_namespace() {
    log_info "SafeWork namespace 생성 중..."
    kubectl create namespace safework --dry-run=client -o yaml | kubectl apply -f -
    log_success "SafeWork namespace 생성 완료"
}

# Docker Registry Secret 생성 (SafeWork namespace용)
create_registry_secret_safework() {
    log_info "SafeWork Registry Secret 생성 중..."
    
    # Docker config JSON 생성
    AUTH_STRING=$(echo -n "${REGISTRY_USER}:${REGISTRY_PASS}" | base64 -w 0)
    DOCKER_CONFIG=$(echo "{\"auths\":{\"${REGISTRY_URL}\":{\"username\":\"${REGISTRY_USER}\",\"password\":\"${REGISTRY_PASS}\",\"auth\":\"${AUTH_STRING}\"}}}" | base64 -w 0)
    
    kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: registry-secret
  namespace: safework
  labels:
    app: safework
    component: registry
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: ${DOCKER_CONFIG}
EOF
    
    log_success "SafeWork Registry Secret 생성 완료"
}

# GitHub Actions Secrets 가이드 출력
print_github_secrets_guide() {
    echo ""
    echo "=================================================="
    log_info "GitHub Actions Secrets 설정 가이드"
    echo "=================================================="
    echo ""
    echo "다음 secrets을 GitHub Repository > Settings > Secrets and variables > Actions에 추가하세요:"
    echo ""
    echo "🔐 ArgoCD 접근:"
    echo "ARGOCD_ADMIN_USER = ${ARGOCD_ADMIN_USER}"
    echo "ARGOCD_ADMIN_PASS = ${ARGOCD_ADMIN_PASS}"
    echo "ARGOCD_API_TOKEN = ${ARGOCD_API}"
    echo ""
    echo "🐳 Docker Registry 접근:"
    echo "DOCKER_USERNAME = ${REGISTRY_USER}"
    echo "DOCKER_PASSWORD = ${REGISTRY_PASS}"
    echo ""
    echo "🐙 GitHub 접근 (선택사항):"
    echo "GITHUB_TOKEN = ${GITHUB_TOKEN}"
    echo ""
    echo "=================================================="
}

# ArgoCD API Token 확인
verify_argocd_token() {
    log_info "ArgoCD API Token 확인 중..."
    
    # ArgoCD CLI로 로그인 테스트
    if command -v argocd &> /dev/null; then
        if argocd login ${ARGOCD_SERVER} \
            --username ${ARGOCD_ADMIN_USER} \
            --password ${ARGOCD_ADMIN_PASS} \
            --insecure &>/dev/null; then
            log_success "ArgoCD 로그인 성공"
        else
            log_warning "ArgoCD 로그인 실패 - 수동으로 확인 필요"
        fi
    else
        log_warning "ArgoCD CLI가 설치되지 않음 - 로그인 테스트 생략"
    fi
}

# Secrets 상태 확인
verify_secrets() {
    log_info "생성된 Secrets 확인 중..."
    
    echo ""
    log_info "ArgoCD namespace secrets:"
    kubectl get secrets -n argocd | grep -E "(safework-repo|registry-secret-argocd)" || log_warning "ArgoCD secrets 없음"
    
    echo ""
    log_info "SafeWork namespace secrets:"
    kubectl get secrets -n safework | grep "registry-secret" || log_warning "SafeWork registry secret 없음"
    
    echo ""
    log_success "Secrets 상태 확인 완료"
}

# 메인 함수
main() {
    case "${1:-setup}" in
        "setup")
            log_info "ArgoCD Secrets 전체 설정 시작..."
            create_argocd_namespace
            create_github_repo_secret
            create_registry_secret_argocd
            create_safework_namespace
            create_registry_secret_safework
            verify_argocd_token
            verify_secrets
            print_github_secrets_guide
            ;;
        "github")
            log_info "GitHub Repository Secret만 설정..."
            create_argocd_namespace
            create_github_repo_secret
            ;;
        "registry")
            log_info "Registry Secrets만 설정..."
            create_argocd_namespace
            create_safework_namespace
            create_registry_secret_argocd
            create_registry_secret_safework
            ;;
        "verify")
            log_info "Secrets 상태 확인..."
            verify_secrets
            ;;
        "guide")
            print_github_secrets_guide
            ;;
        "help")
            echo "사용법: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  setup    - 모든 secrets 설정 (기본값)"
            echo "  github   - GitHub repository secret만 설정"
            echo "  registry - Registry secrets만 설정"
            echo "  verify   - 생성된 secrets 상태 확인"
            echo "  guide    - GitHub Actions secrets 설정 가이드"
            echo "  help     - 도움말 표시"
            ;;
        *)
            log_error "알 수 없는 명령어: $1"
            log_info "사용법: $0 [setup|github|registry|verify|guide|help]"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"