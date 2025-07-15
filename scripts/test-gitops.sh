#!/bin/bash

# SafeWork GitOps 테스트 스크립트

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 SafeWork GitOps 테스트 스크립트${NC}"

# 환경 변수 설정
NAMESPACE="safework"
ARGOCD_NAMESPACE="argocd"
APP_NAME="safework-gitops"
REGISTRY_URL="registry.jclee.me"
IMAGE_NAME="safework"

# 전체 시스템 상태 확인
check_system_status() {
    echo -e "${BLUE}🔍 시스템 상태 확인 중...${NC}"
    
    # Kubernetes 클러스터 연결 확인
    if kubectl cluster-info &>/dev/null; then
        echo -e "${GREEN}✅ Kubernetes 클러스터 연결됨${NC}"
    else
        echo -e "${RED}❌ Kubernetes 클러스터 연결 실패${NC}"
        exit 1
    fi
    
    # ArgoCD 네임스페이스 확인
    if kubectl get namespace $ARGOCD_NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ ArgoCD 네임스페이스 확인됨${NC}"
    else
        echo -e "${RED}❌ ArgoCD 네임스페이스 없음${NC}"
        exit 1
    fi
    
    # SafeWork 네임스페이스 확인
    if kubectl get namespace $NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ SafeWork 네임스페이스 확인됨${NC}"
    else
        echo -e "${YELLOW}⚠️ SafeWork 네임스페이스 없음 - 생성 중...${NC}"
        kubectl create namespace $NAMESPACE
    fi
}

# ArgoCD 애플리케이션 상태 확인
check_argocd_app() {
    echo -e "${BLUE}🔍 ArgoCD 애플리케이션 상태 확인 중...${NC}"
    
    if kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ ArgoCD 애플리케이션 확인됨${NC}"
        
        # 애플리케이션 상태 확인
        local health=$(kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE -o jsonpath='{.status.health.status}')
        local sync=$(kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE -o jsonpath='{.status.sync.status}')
        
        echo "  Health: $health"
        echo "  Sync: $sync"
        
        if [[ "$health" == "Healthy" && "$sync" == "Synced" ]]; then
            echo -e "${GREEN}✅ 애플리케이션 상태 정상${NC}"
        else
            echo -e "${YELLOW}⚠️ 애플리케이션 상태 확인 필요${NC}"
            kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE -o yaml
        fi
    else
        echo -e "${RED}❌ ArgoCD 애플리케이션 없음${NC}"
        echo "setup-argocd.sh를 실행해주세요"
        exit 1
    fi
}

# 시크릿 확인
check_secrets() {
    echo -e "${BLUE}🔐 시크릿 확인 중...${NC}"
    
    # Docker 레지스트리 시크릿
    if kubectl get secret regcred -n $NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ Docker 레지스트리 시크릿 확인됨${NC}"
    else
        echo -e "${RED}❌ Docker 레지스트리 시크릿 없음${NC}"
        echo "setup-secrets.sh를 실행해주세요"
    fi
    
    # ArgoCD 시크릿
    if kubectl get secret argocd-secret -n $ARGOCD_NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ ArgoCD 시크릿 확인됨${NC}"
    else
        echo -e "${YELLOW}⚠️ ArgoCD 시크릿 없음${NC}"
    fi
}

# 배포 상태 확인
check_deployment() {
    echo -e "${BLUE}🚀 배포 상태 확인 중...${NC}"
    
    # 디플로이먼트 확인
    if kubectl get deployment safework -n $NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ SafeWork 디플로이먼트 확인됨${NC}"
        
        # 파드 상태 확인
        local ready_pods=$(kubectl get deployment safework -n $NAMESPACE -o jsonpath='{.status.readyReplicas}')
        local total_pods=$(kubectl get deployment safework -n $NAMESPACE -o jsonpath='{.spec.replicas}')
        
        echo "  Ready Pods: $ready_pods/$total_pods"
        
        if [[ "$ready_pods" == "$total_pods" ]]; then
            echo -e "${GREEN}✅ 모든 파드가 준비됨${NC}"
        else
            echo -e "${YELLOW}⚠️ 파드 상태 확인 필요${NC}"
            kubectl get pods -n $NAMESPACE
        fi
    else
        echo -e "${RED}❌ SafeWork 디플로이먼트 없음${NC}"
    fi
}

# 서비스 및 인그레스 확인
check_network() {
    echo -e "${BLUE}🌐 네트워크 구성 확인 중...${NC}"
    
    # 서비스 확인
    if kubectl get service safework -n $NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ SafeWork 서비스 확인됨${NC}"
        kubectl get service safework -n $NAMESPACE
    else
        echo -e "${RED}❌ SafeWork 서비스 없음${NC}"
    fi
    
    # 인그레스 확인
    if kubectl get ingress safework -n $NAMESPACE &>/dev/null; then
        echo -e "${GREEN}✅ SafeWork 인그레스 확인됨${NC}"
        kubectl get ingress safework -n $NAMESPACE
    else
        echo -e "${YELLOW}⚠️ SafeWork 인그레스 없음${NC}"
    fi
}

# 애플리케이션 헬스체크
check_health() {
    echo -e "${BLUE}🏥 애플리케이션 헬스체크 중...${NC}"
    
    # 내부 헬스체크
    if kubectl get pods -n $NAMESPACE -l app=safework &>/dev/null; then
        local pod_name=$(kubectl get pods -n $NAMESPACE -l app=safework -o jsonpath='{.items[0].metadata.name}')
        
        if [[ -n "$pod_name" ]]; then
            echo "테스트 파드: $pod_name"
            
            # 파드 내부에서 헬스체크
            if kubectl exec -n $NAMESPACE "$pod_name" -- curl -f http://localhost:3001/health &>/dev/null; then
                echo -e "${GREEN}✅ 내부 헬스체크 성공${NC}"
            else
                echo -e "${YELLOW}⚠️ 내부 헬스체크 실패${NC}"
            fi
        fi
    fi
    
    # 외부 헬스체크
    if curl -f https://safework.jclee.me/health &>/dev/null; then
        echo -e "${GREEN}✅ 외부 헬스체크 성공${NC}"
    else
        echo -e "${YELLOW}⚠️ 외부 헬스체크 실패 또는 아직 배포되지 않음${NC}"
    fi
}

# GitHub Actions 워크플로우 확인
check_github_actions() {
    echo -e "${BLUE}⚙️ GitHub Actions 워크플로우 확인 중...${NC}"
    
    # 워크플로우 파일 확인
    if [[ -f ".github/workflows/ci.yml" ]]; then
        echo -e "${GREEN}✅ CI 워크플로우 파일 확인됨${NC}"
    else
        echo -e "${RED}❌ CI 워크플로우 파일 없음${NC}"
    fi
    
    if [[ -f ".github/workflows/cd.yml" ]]; then
        echo -e "${GREEN}✅ CD 워크플로우 파일 확인됨${NC}"
    else
        echo -e "${RED}❌ CD 워크플로우 파일 없음${NC}"
    fi
}

# 로그 확인
check_logs() {
    echo -e "${BLUE}📋 로그 확인 중...${NC}"
    
    # ArgoCD 애플리케이션 컨트롤러 로그
    echo "ArgoCD 애플리케이션 컨트롤러 로그 (최근 10줄):"
    kubectl logs -n $ARGOCD_NAMESPACE deployment/argocd-application-controller --tail=10 | head -20
    
    echo
    
    # SafeWork 애플리케이션 로그 (있는 경우)
    if kubectl get pods -n $NAMESPACE -l app=safework &>/dev/null; then
        local pod_name=$(kubectl get pods -n $NAMESPACE -l app=safework -o jsonpath='{.items[0].metadata.name}')
        if [[ -n "$pod_name" ]]; then
            echo "SafeWork 애플리케이션 로그 (최근 10줄):"
            kubectl logs -n $NAMESPACE "$pod_name" --tail=10 | head -20
        fi
    fi
}

# 테스트 배포 시뮬레이션
simulate_deployment() {
    echo -e "${BLUE}🎭 테스트 배포 시뮬레이션...${NC}"
    
    # 현재 이미지 태그 확인
    local current_image=$(kubectl get deployment safework -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "없음")
    echo "현재 이미지: $current_image"
    
    # 새 이미지 태그 생성
    local new_tag="test-$(date +%Y%m%d-%H%M%S)"
    echo "테스트 태그: $new_tag"
    
    # 매니페스트 업데이트 시뮬레이션
    echo "매니페스트 업데이트 시뮬레이션..."
    sed -n "s|image: registry.jclee.me/safework:.*|image: registry.jclee.me/safework:$new_tag|p" k8s/safework/deployment.yaml && echo "✅ 매니페스트 업데이트 가능"
    
    echo -e "${GREEN}✅ 배포 시뮬레이션 완료${NC}"
}

# 종합 리포트 생성
generate_report() {
    echo -e "${BLUE}📊 종합 리포트 생성 중...${NC}"
    
    local report_file="gitops-test-report-$(date +%Y%m%d-%H%M%S).md"
    
    cat > "$report_file" << EOF
# SafeWork GitOps 테스트 리포트

생성 시간: $(date)

## 시스템 상태

### Kubernetes 클러스터
- 상태: $(kubectl cluster-info &>/dev/null && echo "정상" || echo "비정상")
- 네임스페이스: $(kubectl get namespace $NAMESPACE &>/dev/null && echo "정상" || echo "비정상")

### ArgoCD 애플리케이션
- 애플리케이션: $(kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE &>/dev/null && echo "존재" || echo "없음")
- Health: $(kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE -o jsonpath='{.status.health.status}' 2>/dev/null || echo "알 수 없음")
- Sync: $(kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE -o jsonpath='{.status.sync.status}' 2>/dev/null || echo "알 수 없음")

### 배포 상태
- 디플로이먼트: $(kubectl get deployment safework -n $NAMESPACE &>/dev/null && echo "존재" || echo "없음")
- 파드 상태: $(kubectl get pods -n $NAMESPACE -l app=safework --no-headers 2>/dev/null | wc -l || echo "0")개

### 네트워크
- 서비스: $(kubectl get service safework -n $NAMESPACE &>/dev/null && echo "존재" || echo "없음")
- 인그레스: $(kubectl get ingress safework -n $NAMESPACE &>/dev/null && echo "존재" || echo "없음")

### 헬스체크
- 내부: $(kubectl get pods -n $NAMESPACE -l app=safework &>/dev/null && echo "가능" || echo "불가능")
- 외부: $(curl -f https://safework.jclee.me/health &>/dev/null && echo "성공" || echo "실패")

## 권장 사항

$(kubectl get application $APP_NAME -n $ARGOCD_NAMESPACE &>/dev/null || echo "- ArgoCD 애플리케이션 설정 필요")
$(kubectl get secret regcred -n $NAMESPACE &>/dev/null || echo "- Docker 레지스트리 시크릿 설정 필요")
$(kubectl get deployment safework -n $NAMESPACE &>/dev/null || echo "- SafeWork 배포 필요")

## 다음 단계

1. 부족한 구성 요소 설정
2. GitHub Actions 워크플로우 테스트
3. 실제 배포 진행
4. 모니터링 설정

EOF
    
    echo -e "${GREEN}✅ 리포트 생성 완료: $report_file${NC}"
}

# 메인 실행
main() {
    echo -e "${GREEN}🚀 SafeWork GitOps 테스트 시작...${NC}"
    echo
    
    # 시스템 상태 확인
    check_system_status
    echo
    
    # ArgoCD 애플리케이션 확인
    check_argocd_app
    echo
    
    # 시크릿 확인
    check_secrets
    echo
    
    # 배포 상태 확인
    check_deployment
    echo
    
    # 네트워크 확인
    check_network
    echo
    
    # 헬스체크
    check_health
    echo
    
    # GitHub Actions 확인
    check_github_actions
    echo
    
    # 로그 확인
    check_logs
    echo
    
    # 배포 시뮬레이션
    simulate_deployment
    echo
    
    # 종합 리포트 생성
    generate_report
    
    echo
    echo -e "${GREEN}✅ GitOps 테스트 완료!${NC}"
    echo -e "${BLUE}📊 다음 단계:${NC}"
    echo "1. 생성된 리포트 확인"
    echo "2. 부족한 구성 요소 설정"
    echo "3. 실제 배포 테스트"
    echo "4. ArgoCD 대시보드 확인: https://argo.jclee.me/applications/$APP_NAME"
}

# 스크립트 실행
main "$@"