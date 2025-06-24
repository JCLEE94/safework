#!/bin/bash
# GitHub Secrets Migration Script
# 기존 qws941/health → JCLEE94/health

set -e

echo "🔄 GitHub Secrets Migration 시작..."

# 필수 Secrets 목록 (값은 보안상 표시 안됨)
echo "📝 필요한 Secrets 목록:"

echo "
# 필수 Private Registry Secrets
REGISTRY_USERNAME=qws941
REGISTRY_PASSWORD=bingogo1l7!

# 필수 Docker Hub Secrets  
DOCKER_USERNAME=qws941
DOCKER_PASSWORD=bingogo1l7!

# 선택사항 (SSH 배포 제거했으므로 불필요하지만 보관)
DEPLOY_HOST=192.168.50.215
DEPLOY_PORT=1111
DEPLOY_USER=docker
DEPLOY_SSH_KEY=[SSH_PRIVATE_KEY]

# 기타 (중복, 정리 가능)
DOCKERHUB_TOKEN=[TOKEN]
DOCKERHUB_USERNAME=qws941
DOCKER_REGISTRY=registry.jclee.me
"

echo "🔧 새 저장소에 Secrets 설정:"
echo "gh secret set REGISTRY_USERNAME -b \"qws941\" --repo JCLEE94/health"
echo "gh secret set REGISTRY_PASSWORD -b \"bingogo1l7!\" --repo JCLEE94/health"
echo "gh secret set DOCKER_USERNAME -b \"qws941\" --repo JCLEE94/health"
echo "gh secret set DOCKER_PASSWORD -b \"bingogo1l7!\" --repo JCLEE94/health"

echo "
⚠️  보안 참고사항:
- 실제 비밀번호는 이 파일에 저장하지 마세요
- GitHub CLI로 직접 설정하거나 웹 UI 사용
- 이 스크립트는 참고용입니다
"

# 자동 설정 (선택사항)
read -p "🤖 자동으로 필수 Secrets를 설정하시겠습니까? (y/N): " AUTO_SET

if [[ $AUTO_SET =~ ^[Yy]$ ]]; then
    echo "🔧 필수 Secrets 자동 설정 중..."
    
    gh secret set REGISTRY_USERNAME -b "qws941" --repo JCLEE94/health
    gh secret set REGISTRY_PASSWORD -b "bingogo1l7!" --repo JCLEE94/health
    gh secret set DOCKER_USERNAME -b "qws941" --repo JCLEE94/health
    gh secret set DOCKER_PASSWORD -b "bingogo1l7!" --repo JCLEE94/health
    
    echo "✅ 필수 Secrets 설정 완료!"
    
    # 설정 확인
    echo "📋 설정된 Secrets 확인:"
    gh secret list --repo JCLEE94/health
else
    echo "🔧 수동 설정을 위한 명령어:"
    echo "gh secret set REGISTRY_USERNAME -b \"qws941\" --repo JCLEE94/health"
    echo "gh secret set REGISTRY_PASSWORD -b \"bingogo1l7!\" --repo JCLEE94/health"
    echo "gh secret set DOCKER_USERNAME -b \"qws941\" --repo JCLEE94/health"
    echo "gh secret set DOCKER_PASSWORD -b \"bingogo1l7!\" --repo JCLEE94/health"
fi

echo "✅ Migration 스크립트 완료!"