#!/bin/bash

# SafeWork GitOps 시크릿 설정 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔐 SafeWork GitOps 시크릿 설정 스크립트${NC}"

# 필수 환경 변수 체크
check_required_vars() {
    local required_vars=(
        "DOCKER_USERNAME"
        "DOCKER_PASSWORD"
        "ARGOCD_USERNAME"
        "ARGOCD_PASSWORD"
        "GITOPS_TOKEN"
    )
    
    echo -e "${YELLOW}📋 필수 환경 변수 확인 중...${NC}"
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo -e "${RED}❌ $var 환경 변수가 설정되지 않았습니다${NC}"
            exit 1
        else
            echo -e "${GREEN}✅ $var 설정됨${NC}"
        fi
    done
}

# GitHub Secrets 설정 가이드
setup_github_secrets() {
    echo -e "${BLUE}🔧 GitHub Secrets 설정 가이드${NC}"
    echo
    echo "다음 시크릿을 GitHub 저장소에 추가해주세요:"
    echo "GitHub 저장소 → Settings → Secrets and variables → Actions"
    echo
    echo -e "${YELLOW}필수 시크릿:${NC}"
    echo "DOCKER_USERNAME=your-registry-username"
    echo "DOCKER_PASSWORD=your-registry-password"
    echo "ARGOCD_USERNAME=admin"
    echo "ARGOCD_PASSWORD=your-argocd-password"
    echo "GITOPS_TOKEN=your-github-token-with-repo-permissions"
    echo
    echo -e "${YELLOW}선택적 시크릿:${NC}"
    echo "CODECOV_TOKEN=your-codecov-token"
    echo "CHARTMUSEUM_USERNAME=your-chartmuseum-username"
    echo "CHARTMUSEUM_PASSWORD=your-chartmuseum-password"
    echo
}

# Kubernetes 시크릿 생성
create_k8s_secrets() {
    echo -e "${BLUE}🔐 Kubernetes 시크릿 생성 중...${NC}"
    
    # 네임스페이스 생성
    kubectl create namespace safework --dry-run=client -o yaml | kubectl apply -f -
    
    # Docker 레지스트리 시크릿
    kubectl create secret docker-registry regcred \
        --docker-server=registry.jclee.me \
        --docker-username="${DOCKER_USERNAME}" \
        --docker-password="${DOCKER_PASSWORD}" \
        --docker-email=admin@jclee.me \
        --namespace=safework \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}✅ Docker 레지스트리 시크릿 생성됨${NC}"
    
    # ArgoCD 시크릿
    kubectl create secret generic argocd-secret \
        --from-literal=username="${ARGOCD_USERNAME}" \
        --from-literal=password="${ARGOCD_PASSWORD}" \
        --namespace=argocd \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}✅ ArgoCD 시크릿 생성됨${NC}"
    
    # GitOps 토큰 시크릿
    kubectl create secret generic gitops-secret \
        --from-literal=token="${GITOPS_TOKEN}" \
        --namespace=argocd \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo -e "${GREEN}✅ GitOps 토큰 시크릿 생성됨${NC}"
}

# ArgoCD 설정 확인
verify_argocd_setup() {
    echo -e "${BLUE}🔍 ArgoCD 설정 확인 중...${NC}"
    
    # ArgoCD 애플리케이션 상태 확인
    if kubectl get application safework-gitops -n argocd &>/dev/null; then
        echo -e "${GREEN}✅ ArgoCD 애플리케이션 확인됨${NC}"
        kubectl get application safework-gitops -n argocd
    else
        echo -e "${YELLOW}⚠️ ArgoCD 애플리케이션이 없습니다. setup-argocd.sh를 실행해주세요${NC}"
    fi
    
    # 네임스페이스 확인
    if kubectl get namespace safework &>/dev/null; then
        echo -e "${GREEN}✅ safework 네임스페이스 확인됨${NC}"
    else
        echo -e "${RED}❌ safework 네임스페이스가 없습니다${NC}"
    fi
}

# 설정 검증
verify_setup() {
    echo -e "${BLUE}🧪 설정 검증 중...${NC}"
    
    # 시크릿 확인
    echo "Docker 레지스트리 시크릿:"
    kubectl get secret regcred -n safework -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d | jq . 2>/dev/null || echo "시크릿 확인 실패"
    
    echo
    echo "ArgoCD 시크릿:"
    kubectl get secret argocd-secret -n argocd -o jsonpath='{.data.username}' | base64 -d 2>/dev/null || echo "시크릿 확인 실패"
    
    echo
    echo "GitOps 토큰 시크릿:"
    kubectl get secret gitops-secret -n argocd &>/dev/null && echo "GitOps 토큰 시크릿 존재" || echo "GitOps 토큰 시크릿 없음"
}

# 환경 변수 템플릿 생성
create_env_template() {
    echo -e "${BLUE}📄 환경 변수 템플릿 생성 중...${NC}"
    
    cat > .env.template << 'EOF'
# SafeWork GitOps 환경 변수 템플릿
# .env 파일로 복사하여 사용하세요: cp .env.template .env

# Docker Registry 설정
DOCKER_USERNAME=your-registry-username
DOCKER_PASSWORD=your-registry-password

# ArgoCD 설정
ARGOCD_USERNAME=admin
ARGOCD_PASSWORD=your-argocd-password
ARGOCD_SERVER=argo.jclee.me

# GitHub 설정
GITOPS_TOKEN=your-github-token-with-repo-permissions

# 선택적 설정
CODECOV_TOKEN=your-codecov-token
CHARTMUSEUM_USERNAME=your-chartmuseum-username
CHARTMUSEUM_PASSWORD=your-chartmuseum-password

# 애플리케이션 설정
REGISTRY_URL=registry.jclee.me
IMAGE_NAME=safework
ARGOCD_APP_NAME=safework-gitops
EOF
    
    echo -e "${GREEN}✅ 환경 변수 템플릿 생성됨: .env.template${NC}"
}

# 메인 실행
main() {
    echo -e "${GREEN}🚀 SafeWork GitOps 시크릿 설정 시작...${NC}"
    echo
    
    # 환경 변수 템플릿 생성
    create_env_template
    
    # GitHub Secrets 설정 가이드
    setup_github_secrets
    
    # 사용자 확인
    echo -e "${YELLOW}환경 변수가 설정되었습니까? (y/N)${NC}"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        # 필수 환경 변수 체크
        check_required_vars
        
        # Kubernetes 시크릿 생성
        create_k8s_secrets
        
        # ArgoCD 설정 확인
        verify_argocd_setup
        
        # 설정 검증
        verify_setup
        
        echo
        echo -e "${GREEN}✅ 시크릿 설정 완료!${NC}"
        echo -e "${BLUE}📊 다음 단계:${NC}"
        echo "1. GitHub Actions 워크플로우 확인"
        echo "2. ArgoCD 대시보드 확인: https://argo.jclee.me"
        echo "3. 첫 배포 테스트: git push origin main"
    else
        echo -e "${YELLOW}환경 변수를 설정한 후 다시 실행해주세요${NC}"
        echo "1. .env.template를 .env로 복사"
        echo "2. .env 파일 편집"
        echo "3. source .env"
        echo "4. 이 스크립트 재실행"
    fi
}

# 스크립트 실행
main "$@"