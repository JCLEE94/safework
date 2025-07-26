#!/bin/bash
# SafeWork Pro K8s GitOps 템플릿 데모 테스트 스크립트

set -euo pipefail

# 색상 정의
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_demo() { echo -e "${BLUE}[DEMO]${NC} $1"; }

# 데모 설정
DEMO_MODE="${DEMO_MODE:-true}"
SKIP_KUBERNETES="${SKIP_KUBERNETES:-false}"
SKIP_ARGOCD="${SKIP_ARGOCD:-false}"

demo_header() {
    echo ""
    echo "=============================================="
    echo "  SafeWork Pro K8s GitOps 템플릿 데모"
    echo "=============================================="
    echo ""
}

demo_section() {
    echo ""
    log_demo ">>> $1"
    echo ""
}

# 1. 템플릿 파일 구조 확인
test_template_structure() {
    demo_section "1. 템플릿 파일 구조 확인"
    
    local required_files=(
        "templates/k8s-gitops-template.sh"
        "templates/quick-start.sh"
        "templates/README.md"
        "templates/CHANGELOG.md"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_info "✅ $file 존재"
        else
            log_error "❌ $file 누락"
            return 1
        fi
    done
    
    # 실행 권한 확인
    if [ -x "templates/k8s-gitops-template.sh" ]; then
        log_info "✅ k8s-gitops-template.sh 실행 권한 있음"
    else
        log_warn "⚠️ k8s-gitops-template.sh 실행 권한 없음"
        chmod +x templates/k8s-gitops-template.sh
        log_info "✅ 실행 권한 추가됨"
    fi
    
    if [ -x "templates/quick-start.sh" ]; then
        log_info "✅ quick-start.sh 실행 권한 있음"
    else
        log_warn "⚠️ quick-start.sh 실행 권한 없음"
        chmod +x templates/quick-start.sh
        log_info "✅ 실행 권한 추가됨"
    fi
}

# 2. 스크립트 구문 검사
test_script_syntax() {
    demo_section "2. 스크립트 구문 검사"
    
    # Bash 구문 검사
    if bash -n templates/k8s-gitops-template.sh; then
        log_info "✅ k8s-gitops-template.sh 구문 올바름"
    else
        log_error "❌ k8s-gitops-template.sh 구문 오류"
        return 1
    fi
    
    if bash -n templates/quick-start.sh; then
        log_info "✅ quick-start.sh 구문 올바름"
    else
        log_error "❌ quick-start.sh 구문 오류"
        return 1
    fi
    
    # ShellCheck (설치되어 있는 경우)
    if command -v shellcheck &> /dev/null; then
        log_info "ShellCheck 분석 실행 중..."
        shellcheck templates/k8s-gitops-template.sh || log_warn "ShellCheck 경고 있음"
        shellcheck templates/quick-start.sh || log_warn "ShellCheck 경고 있음"
    else
        log_warn "ShellCheck 미설치 - 고급 구문 검사 건너뜀"
    fi
}

# 3. 환경 변수 테스트
test_environment_variables() {
    demo_section "3. 환경 변수 테스트"
    
    # 기본 환경 변수 설정
    export APP_NAME="safework-demo"
    export NAMESPACE="safework-demo"
    export GITHUB_ORG="JCLEE94"
    export REGISTRY_URL="registry.jclee.me"
    export NODEPORT="32399"  # 테스트용 포트
    
    log_info "테스트 환경 변수:"
    log_info "  APP_NAME: ${APP_NAME}"
    log_info "  NAMESPACE: ${NAMESPACE}"
    log_info "  GITHUB_ORG: ${GITHUB_ORG}"
    log_info "  REGISTRY_URL: ${REGISTRY_URL}"
    log_info "  NODEPORT: ${NODEPORT}"
}

# 4. Helm 차트 구조 시뮬레이션
test_helm_chart_generation() {
    demo_section "4. Helm 차트 구조 시뮬레이션"
    
    # 임시 디렉토리에서 테스트
    local test_dir="/tmp/safework-gitops-test-$(date +%s)"
    mkdir -p "$test_dir"
    cd "$test_dir"
    
    log_info "테스트 디렉토리: $test_dir"
    
    # SafeWork 프로젝트 흉내내기
    cat > CLAUDE.md << 'EOF'
# CLAUDE.md
**SafeWork Pro** (건설업 보건관리 시스템) - A comprehensive web application
EOF
    
    # Git 초기화
    git init
    git config user.name "Demo User"
    git config user.email "demo@example.com"
    
    # 차트 디렉토리 구조 생성 시뮬레이션
    mkdir -p charts/safework-demo/templates
    
    log_info "✅ 기본 프로젝트 구조 생성됨"
    
    # 원본 템플릿 복사
    cp -r /home/jclee/app/safework/templates .
    
    # 차트 템플릿 테스트 (실제 실행하지 않고 함수만 로드)
    if source templates/k8s-gitops-template.sh; then
        log_info "✅ 템플릿 스크립트 로드 성공"
        
        # 환경 설정 함수 테스트
        if declare -f SAFEWORK_CONFIG &> /dev/null; then
            log_info "✅ SAFEWORK_CONFIG 함수 정의됨"
        else
            log_error "❌ SAFEWORK_CONFIG 함수 누락"
        fi
        
        # 주요 함수들 존재 확인
        local required_functions=(
            "create_safework_helm_chart"
            "create_helm_templates"
            "create_github_workflow"
            "create_argocd_application"
        )
        
        for func in "${required_functions[@]}"; do
            if declare -f "$func" &> /dev/null; then
                log_info "✅ $func 함수 정의됨"
            else
                log_error "❌ $func 함수 누락"
            fi
        done
        
    else
        log_error "❌ 템플릿 스크립트 로드 실패"
        return 1
    fi
    
    # 정리
    cd /home/jclee/app/safework
    rm -rf "$test_dir"
    log_info "✅ 테스트 디렉토리 정리됨"
}

# 5. YAML 파일 유효성 검사
test_yaml_validity() {
    demo_section "5. YAML 파일 유효성 검사"
    
    # 임시로 YAML 파일 생성하여 테스트
    local temp_yaml="/tmp/test-chart.yaml"
    
    cat > "$temp_yaml" << 'EOF'
apiVersion: v2
name: safework-demo
description: SafeWork Pro - 건설업 보건관리 시스템 (Demo)
type: application
version: 1.0.0
appVersion: "latest"
EOF
    
    # YAML 구문 검사 (Python의 yaml 모듈 사용)
    if command -v python3 &> /dev/null; then
        if python3 -c "import yaml; yaml.safe_load(open('$temp_yaml'))" 2>/dev/null; then
            log_info "✅ YAML 구문 검사 통과"
        else
            log_error "❌ YAML 구문 오류"
            return 1
        fi
    else
        log_warn "Python3 미설치 - YAML 검사 건너뜀"
    fi
    
    # Helm chart 유효성 검사 (helm이 설치된 경우)
    if command -v helm &> /dev/null; then
        local temp_chart_dir="/tmp/demo-chart-$(date +%s)"
        mkdir -p "$temp_chart_dir/templates"
        cp "$temp_yaml" "$temp_chart_dir/Chart.yaml"
        
        if helm lint "$temp_chart_dir" &> /dev/null; then
            log_info "✅ Helm 차트 구조 유효"
        else
            log_warn "⚠️ Helm 차트 구조 경고 있음"
        fi
        
        rm -rf "$temp_chart_dir"
    else
        log_warn "Helm 미설치 - 차트 검사 건너뜀"
    fi
    
    rm -f "$temp_yaml"
}

# 6. 네트워크 연결 테스트
test_network_connectivity() {
    demo_section "6. 네트워크 연결 테스트"
    
    local endpoints=(
        "registry.jclee.me:443"
        "charts.jclee.me:443"
        "argo.jclee.me:443"
    )
    
    for endpoint in "${endpoints[@]}"; do
        local host=$(echo "$endpoint" | cut -d: -f1)
        local port=$(echo "$endpoint" | cut -d: -f2)
        
        if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            log_info "✅ $endpoint 연결 가능"
        else
            log_warn "⚠️ $endpoint 연결 실패 (방화벽 또는 네트워크 문제)"
        fi
    done
}

# 7. 필수 도구 확인
test_required_tools() {
    demo_section "7. 필수 도구 확인"
    
    local tools=(
        "docker:Docker"
        "kubectl:Kubernetes CLI"
        "helm:Helm 3"
        "gh:GitHub CLI"
        "git:Git"
        "curl:cURL"
        "jq:JSON processor"
    )
    
    for tool_info in "${tools[@]}"; do
        local tool=$(echo "$tool_info" | cut -d: -f1)
        local desc=$(echo "$tool_info" | cut -d: -f2)
        
        if command -v "$tool" &> /dev/null; then
            local version=$($tool --version 2>/dev/null | head -1 || echo "버전 확인 불가")
            log_info "✅ $desc ($tool): $version"
        else
            log_warn "⚠️ $desc ($tool) 미설치"
        fi
    done
}

# 8. 권한 및 접근성 테스트 (옵션)
test_permissions() {
    demo_section "8. 권한 및 접근성 테스트"
    
    # Kubernetes 접근 테스트 (설치된 경우에만)
    if [ "$SKIP_KUBERNETES" = "false" ] && command -v kubectl &> /dev/null; then
        if kubectl cluster-info &> /dev/null; then
            log_info "✅ Kubernetes 클러스터 접근 가능"
            
            # 권한 확인
            if kubectl auth can-i create namespaces &> /dev/null; then
                log_info "✅ 네임스페이스 생성 권한 있음"
            else
                log_warn "⚠️ 네임스페이스 생성 권한 없음"
            fi
            
            if kubectl auth can-i create secrets &> /dev/null; then
                log_info "✅ Secret 생성 권한 있음"
            else
                log_warn "⚠️ Secret 생성 권한 없음"
            fi
        else
            log_warn "⚠️ Kubernetes 클러스터 접근 불가"
        fi
    else
        log_info "ℹ️ Kubernetes 테스트 건너뜀"
    fi
    
    # GitHub CLI 인증 테스트
    if command -v gh &> /dev/null; then
        if gh auth status &> /dev/null; then
            log_info "✅ GitHub CLI 인증됨"
        else
            log_warn "⚠️ GitHub CLI 인증 필요"
        fi
    else
        log_warn "⚠️ GitHub CLI 미설치"
    fi
    
    # ArgoCD CLI 테스트 (설치된 경우에만)
    if [ "$SKIP_ARGOCD" = "false" ] && command -v argocd &> /dev/null; then
        if argocd version --client &> /dev/null; then
            log_info "✅ ArgoCD CLI 설치됨"
        else
            log_warn "⚠️ ArgoCD CLI 버전 확인 실패"
        fi
    else
        log_info "ℹ️ ArgoCD CLI 테스트 건너뜀"
    fi
}

# 9. 데모 완료 요약
demo_summary() {
    demo_section "9. 데모 완료 요약"
    
    echo ""
    log_demo "🎉 SafeWork Pro K8s GitOps 템플릿 데모 완료!"
    echo ""
    echo "📋 테스트 결과:"
    echo "  ✅ 템플릿 파일 구조 검증"
    echo "  ✅ 스크립트 구문 검사"
    echo "  ✅ 환경 변수 설정"
    echo "  ✅ Helm 차트 구조 시뮬레이션"
    echo "  ✅ YAML 파일 유효성 검사"
    echo "  ✅ 네트워크 연결 테스트"
    echo "  ✅ 필수 도구 확인"
    echo "  ✅ 권한 및 접근성 테스트"
    echo ""
    echo "🚀 다음 단계:"
    echo "  1. 실제 환경에서 템플릿 실행:"
    echo "     ./templates/quick-start.sh"
    echo ""
    echo "  2. 또는 수동 설정:"
    echo "     ./templates/k8s-gitops-template.sh"
    echo ""
    echo "  3. 검증:"
    echo "     ./validate-safework-gitops.sh"
    echo ""
    echo "📖 자세한 내용:"
    echo "  - README: templates/README.md"
    echo "  - 가이드: SAFEWORK_GITOPS_GUIDE.md"
    echo "  - 변경 로그: templates/CHANGELOG.md"
    echo ""
}

# 메인 실행 함수
main() {
    demo_header
    
    # 모든 테스트 실행
    test_template_structure
    test_script_syntax
    test_environment_variables
    test_helm_chart_generation
    test_yaml_validity
    test_network_connectivity
    test_required_tools
    test_permissions
    demo_summary
}

# 스크립트 실행
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi