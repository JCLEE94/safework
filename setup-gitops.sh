#!/bin/bash
set -e

# 프로젝트 설정값
APP_NAME="safework"
NAMESPACE="safework"
NODEPORT="32301"

# GitHub Secrets/Variables 설정
REGISTRY_URL="registry.jclee.me"
REGISTRY_USERNAME="admin"
REGISTRY_PASSWORD="bingogo1"
CHARTMUSEUM_URL="https://charts.jclee.me"
CHARTMUSEUM_USERNAME="admin"
CHARTMUSEUM_PASSWORD="bingogo1"
ARGOCD_URL="argo.jclee.me"

echo "🚀 SafeWork GitOps CI/CD 설정 시작..."

# GitHub CLI 로그인 체크
if ! gh auth status &>/dev/null; then
    echo "❌ GitHub CLI 로그인이 필요합니다"
    echo "gh auth login 명령을 실행하세요"
    exit 1
fi

# GitHub Secrets 설정
echo "📝 GitHub Secrets 설정..."
gh secret set REGISTRY_URL -b "${REGISTRY_URL}" || true
gh secret set REGISTRY_USERNAME -b "${REGISTRY_USERNAME}" || true
gh secret set REGISTRY_PASSWORD -b "${REGISTRY_PASSWORD}" || true
gh secret set CHARTMUSEUM_URL -b "${CHARTMUSEUM_URL}" || true
gh secret set CHARTMUSEUM_USERNAME -b "${CHARTMUSEUM_USERNAME}" || true
gh secret set CHARTMUSEUM_PASSWORD -b "${CHARTMUSEUM_PASSWORD}" || true

# GitHub Variables 설정
echo "📝 GitHub Variables 설정..."
gh variable set APP_NAME -b "${APP_NAME}" || true
gh variable set NAMESPACE -b "${NAMESPACE}" || true
gh variable set NODEPORT -b "${NODEPORT}" || true
gh variable set REGISTRY_URL -b "${REGISTRY_URL}" || true
gh variable set CHARTMUSEUM_URL -b "${CHARTMUSEUM_URL}" || true
gh variable set ARGOCD_URL -b "https://${ARGOCD_URL}" || true

# 간단한 GitHub Actions 워크플로우 생성
mkdir -p .github/workflows

cat > .github/workflows/simple-deploy.yml << 'EOF'
name: Simple CI/CD
on:
  push:
    branches: [main]
env:
  REGISTRY: ${{ vars.REGISTRY_URL }}
  IMAGE_NAME: ${{ vars.APP_NAME }}
jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      
      - name: Docker Build & Push
        run: |
          docker login ${{ env.REGISTRY }} -u ${{ secrets.REGISTRY_USERNAME }} -p ${{ secrets.REGISTRY_PASSWORD }}
          docker build -f deployment/Dockerfile -t ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest .
          docker push ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:latest
          
      - name: Update Helm Chart
        run: |
          CHART_VERSION="1.0.${{ github.run_number }}"
          sed -i "s/^version:.*/version: ${CHART_VERSION}/" ./charts/safework/Chart.yaml
          helm package ./charts/safework
          helm cm-push safework-${CHART_VERSION}.tgz charts
          rm -f safework-${CHART_VERSION}.tgz
EOF

# ArgoCD Application 업데이트
cat > k8s/argocd-application.yaml << EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${APP_NAME}
  namespace: argocd
spec:
  project: default
  source:
    repoURL: ${CHARTMUSEUM_URL}
    chart: ${APP_NAME}
    targetRevision: "*"
  destination:
    server: https://kubernetes.default.svc
    namespace: ${NAMESPACE}
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF

echo "✅ 설정 파일 생성 완료"

# Kubernetes 설정
echo "🔧 Kubernetes 설정..."
kubectl create namespace ${NAMESPACE} --dry-run=client -o yaml | kubectl apply -f -

kubectl create secret docker-registry harbor-registry \
  --docker-server=${REGISTRY_URL} \
  --docker-username=${REGISTRY_USERNAME} \
  --docker-password=${REGISTRY_PASSWORD} \
  --namespace=${NAMESPACE} \
  --dry-run=client -o yaml | kubectl apply -f -

# ArgoCD 설정
echo "🔧 ArgoCD 설정..."
kubectl apply -f k8s/argocd-application.yaml

echo "✅ GitOps CI/CD 파이프라인 설정 완료!"
echo ""
echo "다음 단계:"
echo "1. git add . && git commit -m 'feat: 간단한 GitOps 설정' && git push"
echo "2. GitHub Actions: https://github.com/JCLEE94/safework/actions"
echo "3. ArgoCD: https://${ARGOCD_URL}/applications/${APP_NAME}"
echo "4. 서비스: http://192.168.50.110:${NODEPORT}"