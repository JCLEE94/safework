#!/bin/bash

# ArgoCD 배포 및 설정 스크립트
# SafeWork Pro ArgoCD 자동화 설정

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 환경 변수
ARGOCD_SERVER="${ARGOCD_SERVER:-argo.jclee.me}"
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

check_prerequisites() {
    log_info "사전 요구사항 확인 중..."
    
    # kubectl 확인
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl이 설치되지 않았습니다."
        exit 1
    fi
    
    # argocd CLI 확인 및 설치
    if ! command -v argocd &> /dev/null; then
        log_warning "ArgoCD CLI가 설치되지 않았습니다. 설치 중..."
        curl -sSL -o argocd-linux-amd64 https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64
        sudo install -m 555 argocd-linux-amd64 /usr/local/bin/argocd
        rm argocd-linux-amd64
        log_success "ArgoCD CLI 설치 완료"
    fi
    
    # 클러스터 연결 확인
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes 클러스터에 연결할 수 없습니다."
        exit 1
    fi
    
    log_success "사전 요구사항 확인 완료"
}

install_argocd() {
    log_info "ArgoCD 설치 중..."
    
    # ArgoCD namespace 생성
    kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
    
    # ArgoCD 설치
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    
    # ArgoCD 서버 대기
    log_info "ArgoCD 서버 시작 대기 중..."
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=argocd-server -n argocd --timeout=300s
    
    log_success "ArgoCD 설치 완료"
}

configure_argocd() {
    log_info "ArgoCD 설정 중..."
    
    # ArgoCD 서버에 로그인
    log_info "ArgoCD 서버에 로그인 중..."
    argocd login $ARGOCD_SERVER \
        --username $ARGOCD_ADMIN_USER \
        --password $ARGOCD_ADMIN_PASS \
        --insecure
    
    # 사용자 계정 생성
    log_info "사용자 계정 생성 중..."
    argocd account update-password \
        --account $ARGOCD_USER \
        --new-password $ARGOCD_USER_PASS \
        --current-password $ARGOCD_ADMIN_PASS || true
    
    log_success "ArgoCD 설정 완료"
}

setup_repository_secrets() {
    log_info "Repository secrets 설정 중..."
    
    # GitHub repository secret 생성
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
EOF
    
    # Registry secret 생성
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
    
    log_success "Repository secrets 설정 완료"
}

create_project() {
    log_info "ArgoCD 프로젝트 생성 중..."
    
    kubectl apply -f project.yaml
    
    log_success "ArgoCD 프로젝트 생성 완료"
}

create_application() {
    log_info "ArgoCD 애플리케이션 생성 중..."
    
    # 애플리케이션이 이미 존재하는지 확인
    if argocd app get safework &>/dev/null; then
        log_warning "SafeWork 애플리케이션이 이미 존재합니다. 업데이트 중..."
        kubectl apply -f application.yaml
    else
        log_info "새로운 SafeWork 애플리케이션 생성 중..."
        kubectl apply -f application.yaml
    fi
    
    # 애플리케이션 동기화
    log_info "애플리케이션 동기화 중..."
    argocd app sync safework --prune --force
    
    # 동기화 완료 대기
    log_info "동기화 완료 대기 중..."
    argocd app wait safework --timeout 600 --health
    
    log_success "ArgoCD 애플리케이션 생성 완료"
}

verify_deployment() {
    log_info "배포 상태 확인 중..."
    
    # ArgoCD 애플리케이션 상태 확인
    argocd app get safework
    
    # Kubernetes 리소스 상태 확인
    echo ""
    log_info "Kubernetes 리소스 상태:"
    kubectl get pods -n safework
    kubectl get svc -n safework
    kubectl get ingress -n safework
    
    # Health check
    log_info "헬스 체크 수행 중..."
    sleep 30
    
    if kubectl exec -n safework deployment/safework-backend -- curl -f http://localhost:8000/health &>/dev/null; then
        log_success "백엔드 헬스 체크 성공"
    else
        log_warning "백엔드 헬스 체크 실패"
    fi
    
    if kubectl exec -n safework deployment/safework-frontend -- curl -f http://localhost:80/nginx-health &>/dev/null; then
        log_success "프론트엔드 헬스 체크 성공"
    else
        log_warning "프론트엔드 헬스 체크 실패"
    fi
    
    log_success "배포 상태 확인 완료"
}

print_summary() {
    echo ""
    echo "=================================================="
    log_success "SafeWork ArgoCD 배포 완료!"
    echo "=================================================="
    echo ""
    echo "🔗 ArgoCD Dashboard: https://$ARGOCD_SERVER"
    echo "👤 Username: $ARGOCD_ADMIN_USER"
    echo "🔑 Password: $ARGOCD_ADMIN_PASS"
    echo ""
    echo "📱 Application: https://safework.jclee.me"
    echo "📊 GitHub: https://github.com/$GITHUB_USER/safework"
    echo "🐳 Registry: $REGISTRY_URL/safework"
    echo ""
    echo "🚀 ArgoCD 애플리케이션: safework"
    echo "📂 소스 경로: k8s/"
    echo "🎯 대상 네임스페이스: safework"
    echo ""
    echo "=================================================="
}

# 메인 함수
main() {
    case "${1:-install}" in
        "install")
            log_info "SafeWork ArgoCD 전체 설치 시작..."
            check_prerequisites
            install_argocd
            configure_argocd
            setup_repository_secrets
            create_project
            create_application
            verify_deployment
            print_summary
            ;;
        "configure")
            log_info "ArgoCD 설정만 수행..."
            check_prerequisites
            configure_argocd
            setup_repository_secrets
            create_project
            create_application
            ;;
        "sync")
            log_info "애플리케이션 동기화..."
            argocd app sync safework --prune --force
            argocd app wait safework --timeout 600 --health
            verify_deployment
            ;;
        "status")
            log_info "배포 상태 확인..."
            argocd app get safework
            kubectl get all -n safework
            ;;
        "logs")
            log_info "애플리케이션 로그 확인..."
            kubectl logs -n safework -l app=safework,component=backend --tail=50
            echo "---"
            kubectl logs -n safework -l app=safework,component=frontend --tail=50
            ;;
        "delete")
            log_warning "SafeWork 애플리케이션 삭제..."
            argocd app delete safework --cascade
            kubectl delete namespace safework --ignore-not-found
            ;;
        "help")
            echo "사용법: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  install   - ArgoCD 및 SafeWork 애플리케이션 전체 설치 (기본값)"
            echo "  configure - ArgoCD 설정 및 애플리케이션 생성만 수행"
            echo "  sync      - 애플리케이션 동기화"
            echo "  status    - 배포 상태 확인"
            echo "  logs      - 애플리케이션 로그 확인"
            echo "  delete    - SafeWork 애플리케이션 삭제"
            echo "  help      - 도움말 표시"
            ;;
        *)
            log_error "알 수 없는 명령어: $1"
            log_info "사용법: $0 [install|configure|sync|status|logs|delete|help]"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"