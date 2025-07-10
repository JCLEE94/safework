#!/bin/bash

# SafeWork Kubernetes Deployment Script
# K8s 전환을 위한 전체 배포 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 사전 요구사항 확인
check_prerequisites() {
    log "사전 요구사항 확인 중..."
    
    # kubectl 확인
    if ! command -v kubectl &> /dev/null; then
        error "kubectl이 설치되지 않았습니다."
        exit 1
    fi
    
    # 클러스터 연결 확인
    if ! kubectl cluster-info &> /dev/null; then
        error "Kubernetes 클러스터에 연결할 수 없습니다."
        exit 1
    fi
    
    success "사전 요구사항 확인 완료"
}

# 네임스페이스 생성
deploy_namespace() {
    log "네임스페이스 배포 중..."
    kubectl apply -f namespace/namespace.yaml
    success "네임스페이스 배포 완료"
}

# 스토리지 설정
deploy_storage() {
    log "스토리지 설정 중..."
    
    # 호스트 디렉토리 생성 (필요시)
    log "호스트 디렉토리 생성 중..."
    sudo mkdir -p /data/safework/{postgres,redis,uploads}
    sudo chown -R $USER:$USER /data/safework
    sudo chmod -R 755 /data/safework
    
    kubectl apply -f storage/persistent-volumes.yaml
    success "스토리지 설정 완료"
}

# ConfigMap 및 Secret 배포
deploy_config() {
    log "ConfigMap 및 Secret 배포 중..."
    kubectl apply -f configmap/app-config.yaml
    kubectl apply -f secrets/app-secrets.yaml
    success "ConfigMap 및 Secret 배포 완료"
}

# PostgreSQL 배포
deploy_postgres() {
    log "PostgreSQL 배포 중..."
    kubectl apply -f postgres/postgres-statefulset.yaml
    
    # PostgreSQL이 준비될 때까지 대기
    log "PostgreSQL이 준비될 때까지 대기 중..."
    kubectl wait --for=condition=ready pod -l app=postgres -n safework --timeout=300s
    success "PostgreSQL 배포 완료"
}

# Redis 배포
deploy_redis() {
    log "Redis 배포 중..."
    kubectl apply -f redis/redis-deployment.yaml
    
    # Redis가 준비될 때까지 대기
    log "Redis가 준비될 때까지 대기 중..."
    kubectl wait --for=condition=ready pod -l app=redis -n safework --timeout=300s
    success "Redis 배포 완료"
}

# 백엔드 배포
deploy_backend() {
    log "SafeWork 백엔드 배포 중..."
    kubectl apply -f backend/backend-deployment.yaml
    
    # 백엔드가 준비될 때까지 대기
    log "백엔드가 준비될 때까지 대기 중..."
    kubectl wait --for=condition=ready pod -l app=safework,component=backend -n safework --timeout=600s
    success "백엔드 배포 완료"
}

# 프론트엔드 배포
deploy_frontend() {
    log "SafeWork 프론트엔드 배포 중..."
    kubectl apply -f frontend/frontend-deployment.yaml
    
    # 프론트엔드가 준비될 때까지 대기
    log "프론트엔드가 준비될 때까지 대기 중..."
    kubectl wait --for=condition=ready pod -l app=safework,component=frontend -n safework --timeout=300s
    success "프론트엔드 배포 완료"
}

# Ingress 배포
deploy_ingress() {
    log "Ingress 배포 중..."
    
    # Nginx Ingress Controller가 설치되어 있는지 확인
    if ! kubectl get ingressclass nginx &> /dev/null; then
        warning "Nginx Ingress Controller가 설치되지 않았습니다."
        log "Nginx Ingress Controller 설치 중..."
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/cloud/deploy.yaml
        kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=300s
    fi
    
    kubectl apply -f ingress/ingress.yaml
    success "Ingress 배포 완료"
}

# 배포 상태 확인
check_deployment() {
    log "배포 상태 확인 중..."
    
    echo -e "\n${BLUE}=== Namespace 상태 ===${NC}"
    kubectl get ns safework
    
    echo -e "\n${BLUE}=== PersistentVolume 상태 ===${NC}"
    kubectl get pv | grep safework
    
    echo -e "\n${BLUE}=== PersistentVolumeClaim 상태 ===${NC}"
    kubectl get pvc -n safework
    
    echo -e "\n${BLUE}=== ConfigMap 및 Secret 상태 ===${NC}"
    kubectl get configmap,secret -n safework
    
    echo -e "\n${BLUE}=== Pod 상태 ===${NC}"
    kubectl get pods -n safework -o wide
    
    echo -e "\n${BLUE}=== Service 상태 ===${NC}"
    kubectl get svc -n safework
    
    echo -e "\n${BLUE}=== Ingress 상태 ===${NC}"
    kubectl get ingress -n safework
    
    echo -e "\n${BLUE}=== 전체 리소스 상태 ===${NC}"
    kubectl get all -n safework
}

# 로그 확인
check_logs() {
    log "애플리케이션 로그 확인 중..."
    
    echo -e "\n${BLUE}=== PostgreSQL 로그 ===${NC}"
    kubectl logs -n safework -l app=postgres --tail=10 || true
    
    echo -e "\n${BLUE}=== Redis 로그 ===${NC}"
    kubectl logs -n safework -l app=redis --tail=10 || true
    
    echo -e "\n${BLUE}=== Backend 로그 ===${NC}"
    kubectl logs -n safework -l app=safework,component=backend --tail=10 || true
    
    echo -e "\n${BLUE}=== Frontend 로그 ===${NC}"
    kubectl logs -n safework -l app=safework,component=frontend --tail=10 || true
}

# Health check
health_check() {
    log "Health check 수행 중..."
    
    # 백엔드 health check
    if kubectl get svc backend-service -n safework &> /dev/null; then
        log "백엔드 서비스 health check..."
        kubectl exec -n safework deployment/safework-backend -- curl -f http://localhost:8000/health || warning "백엔드 health check 실패"
    fi
    
    # 프론트엔드 health check
    if kubectl get svc frontend-service -n safework &> /dev/null; then
        log "프론트엔드 서비스 health check..."
        kubectl exec -n safework deployment/safework-frontend -- curl -f http://localhost:80/nginx-health || warning "프론트엔드 health check 실패"
    fi
}

# 정리 함수 (선택적)
cleanup() {
    read -p "기존 리소스를 정리하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log "기존 리소스 정리 중..."
        kubectl delete namespace safework --ignore-not-found=true
        kubectl delete pv postgres-pv redis-pv app-uploads-pv --ignore-not-found=true
        success "리소스 정리 완료"
    fi
}

# 메인 배포 함수
main_deploy() {
    log "SafeWork Kubernetes 배포 시작"
    
    check_prerequisites
    deploy_namespace
    deploy_storage
    deploy_config
    deploy_postgres
    deploy_redis
    deploy_backend
    deploy_frontend
    deploy_ingress
    
    success "모든 구성 요소 배포 완료!"
    
    check_deployment
    health_check
    
    log "배포 완료! 다음 명령어로 상태를 확인할 수 있습니다:"
    echo "  kubectl get all -n safework"
    echo "  kubectl logs -n safework -l app=safework,component=backend"
    echo "  kubectl port-forward -n safework svc/frontend-service 8080:80"
}

# 스크립트 매개변수 처리
case "${1:-deploy}" in
    "deploy")
        main_deploy
        ;;
    "cleanup")
        cleanup
        ;;
    "status")
        check_deployment
        ;;
    "logs")
        check_logs
        ;;
    "health")
        health_check
        ;;
    *)
        echo "사용법: $0 {deploy|cleanup|status|logs|health}"
        echo "  deploy  - 전체 배포 실행 (기본값)"
        echo "  cleanup - 리소스 정리"
        echo "  status  - 배포 상태 확인"
        echo "  logs    - 로그 확인"
        echo "  health  - Health check 수행"
        exit 1
        ;;
esac