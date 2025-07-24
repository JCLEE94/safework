#!/bin/bash
set -e

echo "🚀 SafeWork Pro GitOps CI/CD 완전 자동화 배포"
echo "============================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "📋 배포 단계:"
echo "1. GitOps CI/CD 기본 설정"
echo "2. Helm Chart 검증 및 업데이트"
echo "3. ArgoCD Application 설정"
echo "4. 배포 테스트 및 검증"
echo ""

read -p "계속 진행하시겠습니까? (y/N): " confirm
if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "배포가 취소되었습니다."
    exit 0
fi

echo ""
echo "🔧 1단계: GitOps CI/CD 기본 설정"
echo "==============================="
$SCRIPT_DIR/setup-gitops-cicd.sh

echo ""
echo "📦 2단계: Helm Chart 검증 및 업데이트"
echo "==================================="
$SCRIPT_DIR/update-helm-chart.sh

echo ""
echo "🚀 3단계: ArgoCD Application 설정"
echo "==============================="
$SCRIPT_DIR/setup-argocd-app.sh

echo ""
echo "📝 4단계: Git 커밋 및 푸시"
echo "========================="
read -p "변경사항을 커밋하고 푸시하시겠습니까? (y/N): " git_confirm
if [[ $git_confirm =~ ^[Yy]$ ]]; then
    git add .
    git commit -m "feat: GitOps CI/CD 파이프라인 구성

- Helm Chart values.yaml 업데이트 (템플릿 적용)
- GitHub Actions 워크플로우 표준화
- ArgoCD Application 설정 최적화
- 배포 자동화 스크립트 추가

🚀 Generated with SafeWork GitOps Template"
    
    git push origin main
    echo "✅ Git 푸시 완료"
else
    echo "ℹ️  Git 푸시 건너뜀. 수동으로 커밋하세요:"
    echo "git add . && git commit -m 'feat: GitOps CI/CD 구성' && git push origin main"
fi

echo ""
echo "⏳ 5단계: 빌드 대기 (30초)"
echo "========================"
echo "GitHub Actions 빌드가 시작될 때까지 대기 중..."
sleep 30

echo ""
echo "🔍 6단계: 배포 검증"
echo "=================="
$SCRIPT_DIR/validate-deployment.sh

echo ""
echo "🎉 SafeWork Pro GitOps CI/CD 배포 완료!"
echo "======================================="
echo ""
echo "✅ 완료된 작업:"
echo "  - GitHub Secrets 및 Variables 설정"
echo "  - Helm Chart 표준화 및 최적화"
echo "  - GitHub Actions 워크플로우 업데이트"
echo "  - ArgoCD Application 구성"
echo "  - Kubernetes 리소스 생성"
echo ""
echo "📊 모니터링 대시보드:"
echo "  - GitHub Actions: https://github.com/JCLEE94/safework/actions"
echo "  - ArgoCD: https://argo.jclee.me/applications/safework-production"
echo "  - Production: https://safework.jclee.me"
echo ""
echo "🔧 유용한 명령어:"
echo "  - 배포 상태 확인: ./scripts/deploy/validate-deployment.sh"
echo "  - ArgoCD 동기화: argocd app sync safework-production"
echo "  - Pod 로그 확인: kubectl logs -n production -l app=safework -f"