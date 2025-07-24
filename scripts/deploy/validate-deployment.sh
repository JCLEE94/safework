#!/bin/bash
set -e

echo "🔍 SafeWork Pro 배포 검증 스크립트"
echo "==================================="

APP_NAME="safework"
NAMESPACE="production"
REGISTRY_URL="registry.jclee.me"
GITHUB_ORG="JCLEE94"
CHARTMUSEUM_URL="https://charts.jclee.me"
ARGOCD_URL="https://argo.jclee.me"

echo "1. 📊 GitHub Actions 워크플로우 상태 확인"
echo "----------------------------------------"
if command -v gh > /dev/null 2>&1; then
    echo "최근 워크플로우 실행 결과:"
    gh run list --limit 3 --json status,conclusion,displayTitle,createdAt | \
        jq -r '.[] | "\(.displayTitle) - \(.status) (\(.conclusion // "running"))"'
else
    echo "⚠️  GitHub CLI가 설치되지 않음. 수동 확인 필요:"
    echo "   https://github.com/${GITHUB_ORG}/${APP_NAME}/actions"
fi

echo ""
echo "2. 🐳 Docker 이미지 푸시 확인"
echo "----------------------------"
echo "Registry에서 이미지 태그 확인:"
if command -v curl > /dev/null 2>&1; then
    TAGS_RESPONSE=$(curl -s -u admin:bingogo1 https://${REGISTRY_URL}/v2/${GITHUB_ORG}/${APP_NAME}/tags/list 2>/dev/null || echo "")
    if [ -n "$TAGS_RESPONSE" ]; then
        echo "$TAGS_RESPONSE" | jq -r '.tags[]?' | head -5 || echo "JSON 파싱 실패"
    else
        echo "⚠️  Registry API 접근 실패. 수동 확인 필요"
    fi
else
    echo "⚠️  curl이 설치되지 않음. 수동 확인 필요"
fi

echo ""
echo "3. 📦 Helm 차트 업로드 확인"
echo "--------------------------"
echo "ChartMuseum에서 차트 버전 확인:"
if command -v curl > /dev/null 2>&1; then
    CHART_RESPONSE=$(curl -s -u admin:bingogo1 ${CHARTMUSEUM_URL}/api/charts/${APP_NAME} 2>/dev/null || echo "")
    if [ -n "$CHART_RESPONSE" ]; then
        echo "$CHART_RESPONSE" | jq -r '.[].version' | head -5 || echo "JSON 파싱 실패"
    else
        echo "⚠️  ChartMuseum API 접근 실패. 수동 확인 필요"
    fi
else
    echo "⚠️  curl이 설치되지 않음. 수동 확인 필요"
fi

echo ""
echo "4. 🚀 ArgoCD 애플리케이션 동기화 상태 확인"
echo "----------------------------------------"
if command -v argocd > /dev/null 2>&1; then
    if argocd app get ${APP_NAME}-${NAMESPACE} > /dev/null 2>&1; then
        echo "ArgoCD Application 상태:"
        argocd app get ${APP_NAME}-${NAMESPACE} | grep -E "(Health Status|Sync Status|Last Sync)"
    else
        echo "⚠️  ArgoCD Application을 찾을 수 없음: ${APP_NAME}-${NAMESPACE}"
    fi
else
    echo "⚠️  ArgoCD CLI가 설치되지 않음. 수동 확인 필요:"
    echo "   ${ARGOCD_URL}/applications/${APP_NAME}-${NAMESPACE}"
fi

echo ""
echo "5. ☸️  Kubernetes 리소스 확인"
echo "-----------------------------"
if command -v kubectl > /dev/null 2>&1; then
    echo "Namespace 확인:"
    kubectl get namespace ${NAMESPACE} 2>/dev/null || echo "❌ Namespace ${NAMESPACE} 없음"
    
    echo ""
    echo "Pod 상태:"
    kubectl get pods -n ${NAMESPACE} -l app=${APP_NAME} 2>/dev/null || echo "❌ Pod 없음"
    
    echo ""
    echo "Service 상태:"
    kubectl get svc -n ${NAMESPACE} -l app=${APP_NAME} 2>/dev/null || echo "❌ Service 없음"
else
    echo "⚠️  kubectl이 설치되지 않음. 수동 확인 필요"
fi

echo ""
echo "6. 🌐 애플리케이션 헬스체크"
echo "-------------------------"
if command -v curl > /dev/null 2>&1; then
    echo "Production 헬스체크:"
    if curl -f -s https://${APP_NAME}.jclee.me/health > /dev/null 2>&1; then
        echo "✅ https://${APP_NAME}.jclee.me/health - 정상"
    else
        echo "❌ https://${APP_NAME}.jclee.me/health - 실패"
    fi
    
    # NodePort 직접 접근 테스트
    echo "NodePort 직접 접근 테스트:"
    if curl -f -s http://${APP_NAME}.jclee.me:30080/health > /dev/null 2>&1; then
        echo "✅ http://${APP_NAME}.jclee.me:30080/health - 정상"
    else
        echo "❌ http://${APP_NAME}.jclee.me:30080/health - 실패"
    fi
else
    echo "⚠️  curl이 설치되지 않음. 수동 확인 필요:"
    echo "   https://${APP_NAME}.jclee.me/health"
    echo "   http://${APP_NAME}.jclee.me:30080/health"
fi

echo ""
echo "📋 배포 검증 완료"
echo "================="
echo "🔗 유용한 링크:"
echo "  - GitHub Actions: https://github.com/${GITHUB_ORG}/${APP_NAME}/actions"
echo "  - ArgoCD Dashboard: ${ARGOCD_URL}/applications/${APP_NAME}-${NAMESPACE}"
echo "  - Production URL: https://${APP_NAME}.jclee.me"
echo "  - NodePort URL: http://${APP_NAME}.jclee.me:30080"