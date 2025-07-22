#\!/bin/bash
# GitHub Actions Secret 설정 가이드

echo "=== GitHub Actions Secret 설정 가이드 ==="
echo
echo "GitHub Repository Settings > Secrets and variables > Actions에서 다음 Secret을 추가하세요:"
echo
echo "📦 Registry Secrets:"
echo "  REGISTRY_URL: registry.jclee.me"
echo "  REGISTRY_USERNAME: admin"
echo "  REGISTRY_PASSWORD: bingogo1"
echo
echo "📊 ChartMuseum Secrets:"
echo "  CHARTMUSEUM_URL: https://charts.jclee.me"
echo "  CHARTMUSEUM_USERNAME: admin"
echo "  CHARTMUSEUM_PASSWORD: bingogo1"
echo
echo "🚀 ArgoCD URL:"
echo "  ARGOCD_URL: https://argo.jclee.me"
echo
echo "=== GitHub CLI를 사용한 자동 설정 ==="
echo "gh secret set REGISTRY_URL --body 'registry.jclee.me'"
echo "gh secret set REGISTRY_USERNAME --body 'admin'"
echo "gh secret set REGISTRY_PASSWORD --body 'bingogo1'"
echo "gh secret set CHARTMUSEUM_URL --body 'https://charts.jclee.me'"
echo "gh secret set CHARTMUSEUM_USERNAME --body 'admin'"
echo "gh secret set CHARTMUSEUM_PASSWORD --body 'bingogo1'"
echo "gh secret set ARGOCD_URL --body 'https://argo.jclee.me'"
EOF < /dev/null
