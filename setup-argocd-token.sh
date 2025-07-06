#!/bin/bash

# ArgoCD Token 설정 스크립트
echo "🔐 ArgoCD Authentication Token 설정"

# ArgoCD 서버 정보
ARGOCD_SERVER="argo.jclee.me"
ARGOCD_USER="admin"
ARGOCD_PASS="bingogo1"

echo "📋 ArgoCD 토큰 생성 방법:"
echo ""
echo "1. ArgoCD CLI 설치 (이미 설치되어 있다면 건너뛰기):"
echo "   curl -sSL -o /usr/local/bin/argocd https://github.com/argoproj/argo-cd/releases/latest/download/argocd-linux-amd64"
echo "   chmod +x /usr/local/bin/argocd"
echo ""
echo "2. ArgoCD 로그인:"
echo "   argocd login ${ARGOCD_SERVER} --username ${ARGOCD_USER} --password ${ARGOCD_PASS} --insecure"
echo ""
echo "3. CI/CD용 계정 생성:"
echo "   argocd account generate-token --account github-actions"
echo ""
echo "4. GitHub Secrets에 토큰 추가:"
echo "   - Repository Settings > Secrets and variables > Actions"
echo "   - New repository secret"
echo "   - Name: ARGOCD_AUTH_TOKEN"
echo "   - Value: [생성된 토큰]"
echo ""
echo "또는 GitHub CLI 사용:"
echo "   gh secret set ARGOCD_AUTH_TOKEN --body='생성된토큰값'"
echo ""

# ArgoCD RBAC 설정 파일 생성
cat > argocd-rbac-patch.yaml << 'EOF'
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-rbac-cm
  namespace: argocd
data:
  policy.csv: |
    p, role:github-actions, applications, *, */*, allow
    p, role:github-actions, clusters, get, *, allow
    p, role:github-actions, repositories, get, *, allow
    g, github-actions, role:github-actions
  policy.default: role:readonly
EOF

echo "5. RBAC 정책 적용 (선택사항):"
echo "   kubectl apply -f argocd-rbac-patch.yaml"
echo ""
echo "✅ 설정 완료 후 GitHub Actions가 ArgoCD를 통해 자동 배포할 수 있습니다."