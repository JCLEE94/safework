#!/bin/bash
set -e

echo "🚀 SafeWork Pro GitOps CI/CD 구축 스크립트"
echo "=================================================="

# 기존 파일 정리
echo "📁 기존 설정 파일 정리..."
rm -f docker-compose.yml *.log .env.* || true

# GitHub CLI 로그인 체크
echo "🔐 GitHub CLI 로그인 확인..."
if ! gh auth status > /dev/null 2>&1; then
    echo "⚠️  GitHub CLI 로그인이 필요합니다."
    echo "다음 명령어로 로그인 후 다시 실행하세요:"
    echo "gh auth login"
    exit 1
fi

# 프로젝트 설정값 (SafeWork Pro 기준)
GITHUB_ORG="${GITHUB_ORG:-JCLEE94}"
APP_NAME="${APP_NAME:-safework}"
NAMESPACE="${NAMESPACE:-production}"
NODEPORT="${NODEPORT:-30080}"

echo "📋 프로젝트 설정:"
echo "  - GitHub Organization: ${GITHUB_ORG}"
echo "  - Application Name: ${APP_NAME}"
echo "  - Namespace: ${NAMESPACE}"
echo "  - NodePort: ${NODEPORT}"

# GitHub Secrets/Variables 설정 (SafeWork Pro 기존 설정 기준)
REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
REGISTRY_USERNAME="${REGISTRY_USERNAME:-admin}"
REGISTRY_PASSWORD="${REGISTRY_PASSWORD:-bingogo1}"
CHARTMUSEUM_URL="${CHARTMUSEUM_URL:-https://charts.jclee.me}"
CHARTMUSEUM_USERNAME="${CHARTMUSEUM_USERNAME:-admin}"
CHARTMUSEUM_PASSWORD="${CHARTMUSEUM_PASSWORD:-bingogo1}"
ARGOCD_URL="${ARGOCD_URL:-https://argo.jclee.me}"

echo "🔑 GitHub Secrets 설정..."
gh secret list | grep -q "REGISTRY_URL" || gh secret set REGISTRY_URL -b "${REGISTRY_URL}"
gh secret list | grep -q "REGISTRY_USERNAME" || gh secret set REGISTRY_USERNAME -b "${REGISTRY_USERNAME}"
gh secret list | grep -q "REGISTRY_PASSWORD" || gh secret set REGISTRY_PASSWORD -b "${REGISTRY_PASSWORD}"
gh secret list | grep -q "CHARTMUSEUM_URL" || gh secret set CHARTMUSEUM_URL -b "${CHARTMUSEUM_URL}"
gh secret list | grep -q "CHARTMUSEUM_USERNAME" || gh secret set CHARTMUSEUM_USERNAME -b "${CHARTMUSEUM_USERNAME}"
gh secret list | grep -q "CHARTMUSEUM_PASSWORD" || gh secret set CHARTMUSEUM_PASSWORD -b "${CHARTMUSEUM_PASSWORD}"

echo "📊 GitHub Variables 설정..."
gh variable list | grep -q "REGISTRY_URL" || gh variable set REGISTRY_URL -b "${REGISTRY_URL}"
gh variable list | grep -q "APP_NAME" || gh variable set APP_NAME -b "${APP_NAME}"
gh variable list | grep -q "NAMESPACE" || gh variable set NAMESPACE -b "${NAMESPACE}"
gh variable list | grep -q "NODEPORT" || gh variable set NODEPORT -b "${NODEPORT}"
gh variable list | grep -q "ARGOCD_URL" || gh variable set ARGOCD_URL -b "${ARGOCD_URL}"
gh variable list | grep -q "CHARTMUSEUM_URL" || gh variable set CHARTMUSEUM_URL -b "${CHARTMUSEUM_URL}"

echo "✅ GitHub Secrets 및 Variables 설정 완료"

echo ""
echo "🎯 다음 단계:"
echo "1. Helm Chart 업데이트: ./scripts/deploy/update-helm-chart.sh"
echo "2. GitHub Actions 워크플로우 업데이트: ./scripts/deploy/update-github-workflow.sh"
echo "3. ArgoCD Application 설정: ./scripts/deploy/setup-argocd-app.sh"
echo "4. 배포 테스트: git add . && git commit -m 'feat: GitOps CI/CD 구성' && git push origin main"
echo ""
echo "📊 모니터링 링크:"
echo "  - GitHub Actions: https://github.com/${GITHUB_ORG}/${APP_NAME}/actions"
echo "  - ArgoCD Dashboard: ${ARGOCD_URL}/applications/${APP_NAME}-${NAMESPACE}"
echo "  - Production: https://${APP_NAME}.jclee.me"