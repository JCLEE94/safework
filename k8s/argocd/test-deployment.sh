#!/bin/bash

# ArgoCD 자동 배포 테스트 스크립트
# SafeWork Pro ArgoCD 배포 플로우 전체 테스트

set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 환경 변수
ARGOCD_SERVER="${ARGOCD_SERVER:-argo.jclee.me}"
ARGOCD_ADMIN_USER="${ARGOCD_ADMIN_USER:-admin}"
ARGOCD_ADMIN_PASS="${ARGOCD_ADMIN_PASS:-bingogo1}"
REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
IMAGE_NAME="safework"
TEST_TAG="test-$(date +%s)"

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

# 사전 요구사항 확인
check_prerequisites() {
    log_info "사전 요구사항 확인 중..."
    
    local missing_tools=()
    
    # 필수 도구 확인
    for tool in kubectl argocd docker git; do
        if ! command -v $tool &> /dev/null; then
            missing_tools+=($tool)
        fi
    done
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "다음 도구들이 설치되지 않았습니다: ${missing_tools[*]}"
        exit 1
    fi
    
    # Kubernetes 클러스터 연결 확인
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Kubernetes 클러스터에 연결할 수 없습니다."
        exit 1
    fi
    
    # ArgoCD 서버 접근 확인
    if ! argocd login $ARGOCD_SERVER \
        --username $ARGOCD_ADMIN_USER \
        --password $ARGOCD_ADMIN_PASS \
        --insecure &>/dev/null; then
        log_error "ArgoCD 서버에 로그인할 수 없습니다."
        exit 1
    fi
    
    log_success "사전 요구사항 확인 완료"
}

# 현재 상태 확인
check_current_state() {
    log_info "현재 배포 상태 확인 중..."
    
    # ArgoCD 애플리케이션 상태
    if argocd app get safework &>/dev/null; then
        log_info "SafeWork 애플리케이션 상태:"
        argocd app get safework --output compact
    else
        log_warning "SafeWork 애플리케이션이 존재하지 않습니다."
    fi
    
    # Kubernetes 리소스 상태
    echo ""
    log_info "Kubernetes 리소스 상태:"
    kubectl get pods -n safework 2>/dev/null || log_warning "safework namespace가 존재하지 않습니다."
}

# 테스트 이미지 빌드 및 푸시
build_test_image() {
    log_info "테스트 이미지 빌드 및 푸시 중..."
    
    # 현재 디렉토리가 프로젝트 루트인지 확인
    if [ ! -f "Dockerfile" ] && [ ! -f "deployment/Dockerfile.prod" ]; then
        log_error "Dockerfile을 찾을 수 없습니다. 프로젝트 루트에서 실행하세요."
        exit 1
    fi
    
    # Dockerfile 경로 확인
    local dockerfile_path="Dockerfile"
    if [ -f "deployment/Dockerfile.prod" ]; then
        dockerfile_path="deployment/Dockerfile.prod"
    fi
    
    # 테스트 이미지 빌드
    log_info "테스트 이미지 빌드: ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG}"
    docker build -f $dockerfile_path -t ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG} .
    
    # Registry에 푸시
    log_info "Registry에 이미지 푸시 중..."
    docker push ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG}
    
    log_success "테스트 이미지 빌드 및 푸시 완료"
}

# 매니페스트 업데이트
update_manifests() {
    log_info "K8s 매니페스트 업데이트 중..."
    
    # 백업 생성
    cp k8s/backend/backend-deployment.yaml k8s/backend/backend-deployment.yaml.backup
    cp k8s/frontend/frontend-deployment.yaml k8s/frontend/frontend-deployment.yaml.backup
    
    # 이미지 태그 업데이트
    sed -i "s|image: ${REGISTRY_URL}/${IMAGE_NAME}:.*|image: ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG}|g" \
        k8s/backend/backend-deployment.yaml
    
    sed -i "s|image: ${REGISTRY_URL}/${IMAGE_NAME}:.*|image: ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG}|g" \
        k8s/frontend/frontend-deployment.yaml
    
    log_success "매니페스트 업데이트 완료"
}

# ArgoCD 동기화 테스트
test_argocd_sync() {
    log_info "ArgoCD 동기화 테스트 중..."
    
    # 애플리케이션이 존재하지 않으면 생성
    if ! argocd app get safework &>/dev/null; then
        log_info "SafeWork 애플리케이션 생성 중..."
        kubectl apply -f k8s/argocd/application.yaml
        sleep 10
    fi
    
    # 강제 새로고침
    log_info "애플리케이션 새로고침 중..."
    argocd app sync safework --force --prune
    
    # 동기화 완료 대기
    log_info "동기화 완료 대기 중..."
    argocd app wait safework --timeout 600 --health
    
    log_success "ArgoCD 동기화 테스트 완료"
}

# 배포 상태 확인
verify_deployment() {
    log_info "배포 상태 검증 중..."
    
    # Pod 상태 확인
    log_info "Pod 상태 확인 중..."
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        local ready_pods=$(kubectl get pods -n safework --no-headers | grep -c "Running" || echo "0")
        local total_pods=$(kubectl get pods -n safework --no-headers | wc -l || echo "0")
        
        if [ "$ready_pods" -gt 0 ] && [ "$ready_pods" -eq "$total_pods" ]; then
            log_success "모든 Pod이 실행 중입니다 ($ready_pods/$total_pods)"
            break
        else
            log_info "Pod 실행 대기 중... ($ready_pods/$total_pods ready) - 시도 $attempt/$max_attempts"
            sleep 10
            ((attempt++))
        fi
    done
    
    if [ $attempt -gt $max_attempts ]; then
        log_warning "일부 Pod이 아직 준비되지 않았습니다."
    fi
    
    # 서비스 상태 확인
    log_info "서비스 상태:"
    kubectl get svc -n safework
    
    # Ingress 상태 확인
    log_info "Ingress 상태:"
    kubectl get ingress -n safework 2>/dev/null || log_info "Ingress가 설정되지 않았습니다."
}

# Health Check 수행
perform_health_check() {
    log_info "Health Check 수행 중..."
    
    local backend_healthy=false
    local frontend_healthy=false
    
    # 백엔드 Health Check
    log_info "백엔드 Health Check..."
    if kubectl exec -n safework deployment/safework-backend -- \
        curl -f -m 10 http://localhost:8000/health &>/dev/null; then
        log_success "백엔드 Health Check 성공"
        backend_healthy=true
    else
        log_warning "백엔드 Health Check 실패"
    fi
    
    # 프론트엔드 Health Check
    log_info "프론트엔드 Health Check..."
    if kubectl exec -n safework deployment/safework-frontend -- \
        curl -f -m 10 http://localhost:80/nginx-health &>/dev/null; then
        log_success "프론트엔드 Health Check 성공"
        frontend_healthy=true
    else
        log_warning "프론트엔드 Health Check 실패"
    fi
    
    # 전체 Health 상태
    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        log_success "전체 Health Check 성공"
        return 0
    else
        log_warning "일부 Health Check 실패"
        return 1
    fi
}

# 롤백 테스트
test_rollback() {
    log_info "롤백 테스트 중..."
    
    # 이전 버전으로 롤백
    log_info "매니페스트를 이전 상태로 복원 중..."
    mv k8s/backend/backend-deployment.yaml.backup k8s/backend/backend-deployment.yaml
    mv k8s/frontend/frontend-deployment.yaml.backup k8s/frontend/frontend-deployment.yaml
    
    # 롤백 동기화
    log_info "롤백 동기화 중..."
    argocd app sync safework --force --prune
    argocd app wait safework --timeout 300 --health
    
    log_success "롤백 테스트 완료"
}

# 로그 수집
collect_logs() {
    log_info "로그 수집 중..."
    
    local log_dir="test-logs-$(date +%Y%m%d-%H%M%S)"
    mkdir -p $log_dir
    
    # ArgoCD 애플리케이션 로그
    argocd app logs safework > $log_dir/argocd-app.log 2>&1 || true
    
    # Kubernetes 이벤트
    kubectl get events -n safework --sort-by='.lastTimestamp' > $log_dir/k8s-events.log 2>&1 || true
    
    # Pod 로그
    kubectl logs -n safework -l app=safework,component=backend --tail=100 > $log_dir/backend-pods.log 2>&1 || true
    kubectl logs -n safework -l app=safework,component=frontend --tail=100 > $log_dir/frontend-pods.log 2>&1 || true
    
    # 리소스 상태
    kubectl get all -n safework -o yaml > $log_dir/k8s-resources.yaml 2>&1 || true
    
    log_success "로그가 $log_dir 디렉토리에 저장되었습니다."
}

# 정리 작업
cleanup() {
    log_info "정리 작업 수행 중..."
    
    # 테스트 이미지 정리 (선택사항)
    if [ "${1:-}" = "full" ]; then
        log_info "테스트 이미지 삭제 중..."
        docker rmi ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG} 2>/dev/null || true
    fi
    
    log_success "정리 작업 완료"
}

# 테스트 결과 요약
print_summary() {
    echo ""
    echo "=================================================="
    log_info "ArgoCD 배포 테스트 결과 요약"
    echo "=================================================="
    echo ""
    echo "🔧 테스트 환경:"
    echo "  - ArgoCD 서버: $ARGOCD_SERVER"
    echo "  - Registry: $REGISTRY_URL"
    echo "  - 테스트 이미지: ${REGISTRY_URL}/${IMAGE_NAME}:${TEST_TAG}"
    echo ""
    echo "📊 테스트 결과:"
    
    # ArgoCD 애플리케이션 상태
    if argocd app get safework --output compact | grep -q "Healthy"; then
        echo "  ✅ ArgoCD 애플리케이션: Healthy"
    else
        echo "  ❌ ArgoCD 애플리케이션: 상태 확인 필요"
    fi
    
    # Kubernetes 리소스 상태
    local running_pods=$(kubectl get pods -n safework --no-headers | grep -c "Running" || echo "0")
    local total_pods=$(kubectl get pods -n safework --no-headers | wc -l || echo "0")
    echo "  📦 실행 중인 Pod: $running_pods/$total_pods"
    
    echo ""
    echo "🔗 유용한 링크:"
    echo "  - ArgoCD Dashboard: https://$ARGOCD_SERVER/applications/safework"
    echo "  - Application URL: https://safework.jclee.me"
    echo ""
    echo "=================================================="
}

# 메인 함수
main() {
    case "${1:-full}" in
        "full")
            log_info "ArgoCD 자동 배포 전체 테스트 시작..."
            check_prerequisites
            check_current_state
            build_test_image
            update_manifests
            test_argocd_sync
            verify_deployment
            perform_health_check
            test_rollback
            collect_logs
            cleanup
            print_summary
            ;;
        "sync")
            log_info "동기화 테스트만 수행..."
            check_prerequisites
            test_argocd_sync
            verify_deployment
            perform_health_check
            ;;
        "health")
            log_info "Health Check만 수행..."
            check_prerequisites
            verify_deployment
            perform_health_check
            ;;
        "rollback")
            log_info "롤백 테스트만 수행..."
            check_prerequisites
            test_rollback
            verify_deployment
            ;;
        "logs")
            log_info "로그 수집만 수행..."
            collect_logs
            ;;
        "status")
            log_info "현재 상태만 확인..."
            check_current_state
            verify_deployment
            ;;
        "help")
            echo "사용법: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  full     - 전체 테스트 수행 (기본값)"
            echo "  sync     - 동기화 테스트만 수행"
            echo "  health   - Health Check만 수행"
            echo "  rollback - 롤백 테스트만 수행"
            echo "  logs     - 로그 수집만 수행"
            echo "  status   - 현재 상태만 확인"
            echo "  help     - 도움말 표시"
            ;;
        *)
            log_error "알 수 없는 명령어: $1"
            log_info "사용법: $0 [full|sync|health|rollback|logs|status|help]"
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"