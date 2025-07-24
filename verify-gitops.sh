#!/bin/bash
set -e

echo "🔍 GitOps CI/CD 파이프라인 검증 시작..."
echo ""

# 색상 정의
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 체크 함수
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $2"
    else
        echo -e "${RED}✗${NC} $2"
        FAILED=1
    fi
}

FAILED=0

# 1. GitHub CLI 설치 확인
echo "1️⃣ GitHub CLI 확인..."
if command -v gh &> /dev/null; then
    check 0 "GitHub CLI 설치됨"
    if gh auth status &>/dev/null; then
        check 0 "GitHub 로그인 상태"
    else
        check 1 "GitHub 로그인 필요 (gh auth login)"
    fi
else
    check 1 "GitHub CLI 설치 필요"
fi
echo ""

# 2. GitHub Secrets/Variables 확인
echo "2️⃣ GitHub Secrets/Variables 확인..."
if command -v gh &> /dev/null && gh auth status &>/dev/null; then
    # Variables (using API)
    VARS_JSON=$(gh api repos/JCLEE94/safework/actions/variables 2>/dev/null || echo '{"variables":[]}')
    for var in APP_NAME NAMESPACE REGISTRY_URL CHARTMUSEUM_URL ARGOCD_URL; do
        if echo "$VARS_JSON" | jq -e ".variables[] | select(.name==\"$var\")" &>/dev/null; then
            VALUE=$(echo "$VARS_JSON" | jq -r ".variables[] | select(.name==\"$var\") | .value")
            check 0 "Variable $var: $VALUE"
        else
            check 1 "Variable $var 설정 필요"
        fi
    done
    
    # Secrets (값은 보이지 않음)
    for secret in REGISTRY_USERNAME REGISTRY_PASSWORD CHARTMUSEUM_USERNAME CHARTMUSEUM_PASSWORD; do
        if gh secret list | grep -q $secret; then
            check 0 "Secret $secret 설정됨"
        else
            check 1 "Secret $secret 설정 필요"
        fi
    done
else
    echo -e "${YELLOW}⚠${NC} GitHub CLI 로그인이 필요하여 Secrets/Variables 확인 불가"
fi
echo ""

# 3. Kubernetes 환경 확인
echo "3️⃣ Kubernetes 환경 확인..."
if kubectl cluster-info &>/dev/null; then
    check 0 "Kubernetes 클러스터 연결됨"
    
    # Namespace 확인
    if kubectl get namespace safework &>/dev/null; then
        check 0 "Namespace 'safework' 존재"
    else
        check 1 "Namespace 'safework' 생성 필요"
    fi
    
    # Harbor Registry Secret 확인
    if kubectl get secret harbor-registry -n safework &>/dev/null; then
        check 0 "Harbor Registry Secret 존재"
    else
        check 1 "Harbor Registry Secret 생성 필요"
    fi
else
    check 1 "Kubernetes 클러스터 연결 실패"
fi
echo ""

# 4. ArgoCD 확인
echo "4️⃣ ArgoCD 확인..."
if kubectl get namespace argocd &>/dev/null; then
    check 0 "ArgoCD namespace 존재"
    
    # ArgoCD Image Updater 확인
    if kubectl get deployment argocd-image-updater -n argocd &>/dev/null; then
        check 0 "ArgoCD Image Updater 설치됨"
    else
        check 1 "ArgoCD Image Updater 설치 필요"
    fi
    
    # ArgoCD Application 확인
    if kubectl get application safework -n argocd &>/dev/null; then
        check 0 "ArgoCD Application 'safework' 존재"
        
        # Sync 상태 확인
        SYNC_STATUS=$(kubectl get application safework -n argocd -o jsonpath='{.status.sync.status}' 2>/dev/null || echo "Unknown")
        HEALTH_STATUS=$(kubectl get application safework -n argocd -o jsonpath='{.status.health.status}' 2>/dev/null || echo "Unknown")
        
        echo "  - Sync Status: $SYNC_STATUS"
        echo "  - Health Status: $HEALTH_STATUS"
        
        # Image Updater 어노테이션 확인
        ANNOTATIONS=$(kubectl get application safework -n argocd -o jsonpath='{.metadata.annotations}' 2>/dev/null || echo "{}")
        if echo "$ANNOTATIONS" | grep -q "argocd-image-updater.argoproj.io"; then
            check 0 "Image Updater 어노테이션 설정됨"
        else
            check 1 "Image Updater 어노테이션 설정 필요"
        fi
    else
        check 1 "ArgoCD Application 생성 필요"
    fi
else
    check 1 "ArgoCD 설치 필요"
fi
echo ""

# 5. GitHub Actions Workflow 확인
echo "5️⃣ GitHub Actions Workflow 확인..."
if [ -f ".github/workflows/gitops-deploy.yml" ]; then
    check 0 "GitHub Actions GitOps workflow 파일 존재"
    
    # GitHub-hosted runner 사용 확인
    if grep -q "runs-on: ubuntu-latest" .github/workflows/gitops-deploy.yml; then
        check 0 "GitHub-hosted runners 사용 설정됨"
    else
        check 1 "Self-hosted runner를 GitHub-hosted로 변경 필요"
    fi
    
    # Service containers 설정 확인
    if grep -q "services:" .github/workflows/gitops-deploy.yml; then
        check 0 "Service containers (PostgreSQL, Redis) 설정됨"
    else
        check 1 "Service containers 설정 필요"
    fi
else
    check 1 "GitHub Actions GitOps workflow 파일 없음"
fi
echo ""

# 6. ChartMuseum 연결 테스트
echo "6️⃣ ChartMuseum 연결 확인..."
if command -v helm &> /dev/null; then
    if helm repo list | grep -q charts; then
        check 0 "ChartMuseum 저장소 추가됨"
        if helm repo update charts &>/dev/null; then
            check 0 "ChartMuseum 접근 가능"
        else
            check 1 "ChartMuseum 접근 실패"
        fi
    else
        check 1 "ChartMuseum 저장소 추가 필요"
    fi
else
    check 1 "Helm 설치 필요"
fi
echo ""

# 7. Docker 환경 확인
echo "7️⃣ Docker 환경 확인..."
if command -v docker &> /dev/null; then
    check 0 "Docker 설치됨"
    if docker info &>/dev/null; then
        check 0 "Docker daemon 실행 중"
    else
        check 1 "Docker daemon 실행 필요"
    fi
else
    check 1 "Docker 설치 필요"
fi
echo ""

# 8. Python 환경 확인 (로컬 테스트용)
echo "8️⃣ Python 환경 확인 (로컬 테스트)..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    check 0 "Python 설치됨 ($PYTHON_VERSION)"
    
    if [ -f "requirements.txt" ]; then
        check 0 "requirements.txt 파일 존재"
    else
        check 1 "requirements.txt 파일 없음"
    fi
else
    echo -e "${YELLOW}⚠${NC} Python 미설치 (CI/CD는 GitHub Actions에서 실행됨)"
fi
echo ""

# 9. 현재 배포 상태 확인
echo "9️⃣ 현재 배포 상태..."
if command -v kubectl &> /dev/null && kubectl get namespace safework &>/dev/null; then
    echo "Kubernetes Pods:"
    kubectl get pods -n safework --no-headers | while read line; do
        POD_NAME=$(echo $line | awk '{print $1}')
        STATUS=$(echo $line | awk '{print $3}')
        if [ "$STATUS" = "Running" ]; then
            echo -e "  ${GREEN}✓${NC} $POD_NAME ($STATUS)"
        else
            echo -e "  ${RED}✗${NC} $POD_NAME ($STATUS)"
        fi
    done
    
    echo ""
    echo "Service 상태:"
    kubectl get svc -n safework --no-headers | while read line; do
        SVC_NAME=$(echo $line | awk '{print $1}')
        TYPE=$(echo $line | awk '{print $2}')
        echo "  - $SVC_NAME ($TYPE)"
    done
fi
echo ""

# 최종 결과
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 모든 검증 통과!${NC}"
    echo ""
    echo "🚀 배포 프로세스:"
    echo "1. 코드 변경 후 커밋: git add . && git commit -m 'feat: 새 기능'"
    echo "2. main 브랜치로 푸시: git push origin main"
    echo "3. GitHub Actions가 자동으로:"
    echo "   - 백엔드/프론트엔드 테스트 실행"
    echo "   - Docker 이미지 빌드 및 푸시 (prod-YYYYMMDD-SHA 태그)"
    echo "   - Helm 차트 업데이트 및 ChartMuseum 푸시"
    echo "   - ArgoCD Image Updater가 새 이미지 감지 및 자동 배포"
    echo ""
    echo "📊 모니터링 링크:"
    echo "- GitHub Actions: https://github.com/JCLEE94/safework/actions"
    echo "- ArgoCD Dashboard: https://argo.jclee.me/applications/safework"
    echo "- Production: https://safework.jclee.me"
    echo "- Harbor Registry: https://registry.jclee.me"
else
    echo -e "${RED}❌ 일부 검증 실패${NC}"
    echo ""
    echo "위의 실패 항목을 수정한 후 다시 실행하세요."
    echo ""
    echo "💡 주요 설정 명령어:"
    echo ""
    echo "# ArgoCD Image Updater 설치:"
    echo "kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"
    echo ""
    echo "# GitHub Secrets 설정:"
    echo "gh secret set REGISTRY_USERNAME -b 'admin'"
    echo "gh secret set REGISTRY_PASSWORD -b 'your-password'"
    echo ""
    echo "# Kubernetes namespace 생성:"
    echo "kubectl create namespace safework"
    echo ""
    echo "# Registry secret 생성:"
    echo "kubectl create secret docker-registry harbor-registry \\"
    echo "  --docker-server=registry.jclee.me \\"
    echo "  --docker-username=admin \\"
    echo "  --docker-password=your-password \\"
    echo "  --namespace=safework"
fi