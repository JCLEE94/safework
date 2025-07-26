#!/bin/bash
# SafeWork Pro K8s GitOps 빠른 시작 스크립트

set -euo pipefail

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# SafeWork 프로젝트 확인
check_safework_project() {
    if [ ! -f "CLAUDE.md" ] || ! grep -q "SafeWork Pro" CLAUDE.md 2>/dev/null; then
        log_error "SafeWork Pro 프로젝트가 아닙니다!"
        log_error "이 스크립트는 SafeWork Pro 프로젝트에서만 실행되어야 합니다."
        exit 1
    fi
    
    log_info "✅ SafeWork Pro 프로젝트 확인됨"
}

# 필수 도구 확인
check_prerequisites() {
    log_info "필수 도구 확인 중..."
    
    local missing_tools=()
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        missing_tools+=("docker")
    fi
    
    # kubectl 확인
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    # Helm 확인
    if ! command -v helm &> /dev/null; then
        missing_tools+=("helm")
    fi
    
    # GitHub CLI 확인
    if ! command -v gh &> /dev/null; then
        missing_tools+=("gh")
    fi
    
    # Git 확인
    if ! command -v git &> /dev/null; then
        missing_tools+=("git")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "다음 도구들이 필요합니다:"
        for tool in "${missing_tools[@]}"; do
            echo "  - $tool"
        done
        log_error "설치 후 다시 실행하세요."
        exit 1
    fi
    
    log_info "✅ 필수 도구 확인 완료"
}

# Kubernetes 연결 확인
check_kubernetes() {
    log_info "Kubernetes 클러스터 연결 확인 중..."
    
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes 클러스터에 연결할 수 없습니다!"
        log_error "kubectl 설정을 확인하세요."
        exit 1
    fi
    
    # 네임스페이스 권한 확인
    if ! kubectl auth can-i create namespaces &> /dev/null; then
        log_warn "네임스페이스 생성 권한이 없을 수 있습니다."
    fi
    
    log_info "✅ Kubernetes 클러스터 연결 확인됨"
}

# GitHub 인증 확인
check_github_auth() {
    log_info "GitHub 인증 확인 중..."
    
    if ! gh auth status &> /dev/null; then
        log_warn "GitHub CLI 인증이 필요합니다."
        log_info "GitHub 로그인을 진행합니다..."
        gh auth login
    fi
    
    log_info "✅ GitHub 인증 확인됨"
}

# 기본값 설정
set_defaults() {
    # 현재 디렉토리명을 앱 이름으로 사용
    export APP_NAME="${APP_NAME:-$(basename $(pwd))}"
    export NAMESPACE="${NAMESPACE:-${APP_NAME}}"
    
    # SafeWork 기본 설정
    export GITHUB_ORG="${GITHUB_ORG:-JCLEE94}"
    export REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
    export CHARTMUSEUM_URL="${CHARTMUSEUM_URL:-https://charts.jclee.me}"
    export ARGOCD_URL="${ARGOCD_URL:-argo.jclee.me}"
    
    log_info "기본 설정:"
    log_info "  앱 이름: ${APP_NAME}"
    log_info "  네임스페이스: ${NAMESPACE}"
    log_info "  GitHub 조직: ${GITHUB_ORG}"
    log_info "  Registry: ${REGISTRY_URL}"
}

# 메인 실행 함수
main() {
    echo "🚀 SafeWork Pro K8s GitOps 빠른 시작"
    echo "===================================="
    echo ""
    
    # 1. 프로젝트 확인
    check_safework_project
    
    # 2. 필수 도구 확인
    check_prerequisites
    
    # 3. Kubernetes 연결 확인
    check_kubernetes
    
    # 4. GitHub 인증 확인
    check_github_auth
    
    # 5. 기본값 설정
    set_defaults
    
    echo ""
    log_info "🎯 모든 사전 요구사항이 충족되었습니다!"
    echo ""
    
    # 사용자 확인
    read -p "SafeWork Pro GitOps 파이프라인을 설정하시겠습니까? (y/N): " confirm
    
    if [[ $confirm =~ ^[Yy] ]]; then
        log_info "GitOps 파이프라인 설정을 시작합니다..."
        
        # 메인 템플릿 실행
        if [ -f "templates/k8s-gitops-template.sh" ]; then
            ./templates/k8s-gitops-template.sh
        else
            log_error "templates/k8s-gitops-template.sh 파일을 찾을 수 없습니다!"
            exit 1
        fi
        
        echo ""
        log_info "🎉 SafeWork Pro GitOps 파이프라인 설정이 완료되었습니다!"
        echo ""
        echo "다음 단계:"
        echo "1. 검증: ./validate-safework-gitops.sh"
        echo "2. 커밋: git add . && git commit -m 'feat: GitOps 파이프라인 설정' && git push"
        echo "3. 모니터링: GitHub Actions 및 ArgoCD 확인"
        
    else
        log_info "GitOps 파이프라인 설정이 취소되었습니다."
    fi
}

# 스크립트 실행
main "$@"