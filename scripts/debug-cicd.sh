#!/bin/bash
# CI/CD 상태 디버깅 스크립트

echo "🔍 CI/CD Pipeline Debug Report"
echo "=============================="
echo "Generated at: $(date)"
echo ""

# 1. GitHub Actions 상태 확인
echo "📊 GitHub Actions Status:"
echo "------------------------"
gh run list --workflow=gitops-optimized.yml --limit=5 2>/dev/null || echo "❌ Failed to fetch workflow runs"
echo ""

# 2. 최근 커밋 확인
echo "📝 Recent Commits:"
echo "-----------------"
git log --oneline -5
echo ""

# 3. 현재 브랜치 상태
echo "🌿 Current Branch Status:"
echo "------------------------"
git status
echo ""

# 4. Docker 이미지 확인
echo "🐳 Docker Registry Check:"
echo "------------------------"
echo "Registry: registry.jclee.me/safework"
echo "Latest tags should include:"
echo "  - latest"
echo "  - prod-$(date +%Y%m%d)-<sha>"
echo "  - 1.$(date +%Y%m%d).<build_number>"
echo ""

# 5. Kubernetes 배포 상태
echo "☸️  Kubernetes Deployment Status:"
echo "--------------------------------"
kubectl get deployment safework -n safework -o wide 2>/dev/null || echo "❌ Failed to get deployment status"
echo ""

# 6. Pod 상태
echo "🏃 Pod Status:"
echo "-------------"
kubectl get pods -n safework -l app=safework 2>/dev/null || echo "❌ Failed to get pod status"
echo ""

# 7. 최근 이벤트
echo "📅 Recent Events:"
echo "----------------"
kubectl get events -n safework --sort-by='.lastTimestamp' | tail -10 2>/dev/null || echo "❌ Failed to get events"
echo ""

# 8. ArgoCD 상태
echo "🔄 ArgoCD Application Status:"
echo "----------------------------"
kubectl get application safework -n argocd -o jsonpath='{.status.sync.status}' 2>/dev/null || echo "❌ Failed to get ArgoCD status"
echo ""

# 9. 배포 이미지 확인
echo "🖼️  Current Deployed Image:"
echo "-------------------------"
kubectl get deployment safework -n safework -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "❌ Failed to get image info"
echo ""

# 10. Health Check
echo "💊 Health Check:"
echo "---------------"
curl -s -f http://192.168.50.110:32301/health | jq . 2>/dev/null || echo "❌ Health check failed"
echo ""

# 11. QR Route Check
echo "📱 QR Route Check:"
echo "-----------------"
curl -s -o /dev/null -w "%{http_code}" http://192.168.50.110:32301/qr-register 2>/dev/null || echo "❌ QR route check failed"
echo ""

echo "✅ Debug report complete!"
echo ""
echo "🔧 Troubleshooting Tips:"
echo "----------------------"
echo "1. If workflow failed: Check 'gh run view <run-id> --log-failed'"
echo "2. If image not updated: Check ArgoCD Image Updater logs"
echo "3. If deployment stuck: Check 'kubectl describe pod <pod-name> -n safework'"
echo "4. If health check fails: Check 'kubectl logs <pod-name> -n safework'"