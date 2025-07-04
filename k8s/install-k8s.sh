#!/bin/bash

# Kubernetes 클러스터 설치 스크립트 (minikube 사용)
# K8s 전환을 위한 로컬 개발 환경 설정

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

# minikube 설치
install_minikube() {
    log "minikube 설치 중..."
    
    if command -v minikube &> /dev/null; then
        success "minikube가 이미 설치되어 있습니다."
        return
    fi
    
    # minikube 다운로드 및 설치
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    sudo install minikube-linux-amd64 /usr/local/bin/minikube
    rm minikube-linux-amd64
    
    success "minikube 설치 완료"
}

# minikube 클러스터 시작
start_minikube() {
    log "minikube 클러스터 시작 중..."
    
    # 기존 클러스터가 있으면 삭제
    if minikube status &> /dev/null; then
        warning "기존 minikube 클러스터 발견, 삭제 후 재시작..."
        minikube delete
    fi
    
    # minikube 시작 (Docker 드라이버 사용)
    minikube start \
        --driver=docker \
        --cpus=4 \
        --memory=8192 \
        --disk-size=20g \
        --kubernetes-version=v1.28.3 \
        --addons=ingress,dashboard,metrics-server,storage-provisioner
    
    success "minikube 클러스터 시작 완료"
}

# kubectl 컨텍스트 설정
setup_kubectl() {
    log "kubectl 컨텍스트 설정 중..."
    
    # minikube kubectl 컨텍스트로 전환
    minikube update-context
    
    # 클러스터 정보 확인
    kubectl cluster-info
    kubectl get nodes
    
    success "kubectl 설정 완료"
}

# Nginx Ingress Controller 활성화
setup_ingress() {
    log "Nginx Ingress Controller 설정 중..."
    
    # Ingress addon 활성화 (이미 시작시 추가했지만 명시적으로 확인)
    minikube addons enable ingress
    
    # Ingress Controller가 준비될 때까지 대기
    kubectl wait --namespace ingress-nginx \
        --for=condition=ready pod \
        --selector=app.kubernetes.io/component=controller \
        --timeout=300s
    
    success "Nginx Ingress Controller 설정 완료"
}

# 로컬 Docker 레지스트리 설정 (선택사항)
setup_local_registry() {
    log "로컬 Docker 환경 설정 중..."
    
    # minikube Docker 환경 사용
    eval $(minikube docker-env)
    
    log "Docker 환경이 minikube로 설정되었습니다."
    log "이제 'docker build' 명령어가 minikube 내부에서 실행됩니다."
    
    success "Docker 환경 설정 완료"
}

# StorageClass 확인 및 설정
setup_storage() {
    log "StorageClass 설정 확인 중..."
    
    # 기본 StorageClass 확인
    kubectl get storageclass
    
    # local-storage StorageClass 생성 (필요시)
    if ! kubectl get storageclass local-storage &> /dev/null; then
        log "local-storage StorageClass 생성 중..."
        cat << EOF | kubectl apply -f -
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: local-storage
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
        success "local-storage StorageClass 생성 완료"
    else
        success "local-storage StorageClass가 이미 존재합니다"
    fi
}

# cert-manager 설치 (TLS 인증서용)
install_cert_manager() {
    log "cert-manager 설치 중..."
    
    if kubectl get namespace cert-manager &> /dev/null; then
        success "cert-manager가 이미 설치되어 있습니다."
        return
    fi
    
    # cert-manager 설치
    kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
    
    # cert-manager가 준비될 때까지 대기
    kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
    kubectl wait --for=condition=ready pod -l app=webhook -n cert-manager --timeout=300s
    kubectl wait --for=condition=ready pod -l app=cainjector -n cert-manager --timeout=300s
    
    success "cert-manager 설치 완료"
}

# 클러스터 상태 확인
check_cluster() {
    log "클러스터 상태 확인 중..."
    
    echo -e "\n${BLUE}=== Cluster Info ===${NC}"
    kubectl cluster-info
    
    echo -e "\n${BLUE}=== Nodes ===${NC}"
    kubectl get nodes -o wide
    
    echo -e "\n${BLUE}=== Namespaces ===${NC}"
    kubectl get namespaces
    
    echo -e "\n${BLUE}=== StorageClasses ===${NC}"
    kubectl get storageclass
    
    echo -e "\n${BLUE}=== Ingress Controller ===${NC}"
    kubectl get pods -n ingress-nginx
    
    echo -e "\n${BLUE}=== cert-manager ===${NC}"
    kubectl get pods -n cert-manager
    
    success "클러스터 상태 확인 완료"
}

# 메인 설치 함수
main_install() {
    log "Kubernetes 클러스터 설치 시작"
    
    install_minikube
    start_minikube
    setup_kubectl
    setup_ingress
    setup_local_registry
    setup_storage
    install_cert_manager
    check_cluster
    
    success "Kubernetes 클러스터 설치 완료!"
    
    echo -e "\n${GREEN}=== 설치 완료 정보 ===${NC}"
    echo "1. 클러스터 접근: kubectl cluster-info"
    echo "2. 대시보드 열기: minikube dashboard"
    echo "3. Ingress IP 확인: minikube ip"
    echo "4. 서비스 터널: minikube tunnel (새 터미널에서)"
    echo "5. Docker 환경: eval \$(minikube docker-env)"
    echo ""
    echo "이제 SafeWork를 배포할 수 있습니다:"
    echo "  ./deploy.sh deploy"
}

# 정리 함수
cleanup() {
    log "minikube 클러스터 정리 중..."
    minikube delete
    success "클러스터 정리 완료"
}

# 스크립트 매개변수 처리
case "${1:-install}" in
    "install")
        main_install
        ;;
    "cleanup")
        cleanup
        ;;
    "status")
        check_cluster
        ;;
    *)
        echo "사용법: $0 {install|cleanup|status}"
        echo "  install - Kubernetes 클러스터 설치 (기본값)"
        echo "  cleanup - 클러스터 삭제"
        echo "  status  - 클러스터 상태 확인"
        exit 1
        ;;
esac