#!/bin/bash

# GitHub Secrets 설정 스크립트
# 사용법: ./setup-github-secrets.sh

echo "GitHub Secrets 설정을 시작합니다..."

# GitHub CLI가 설치되어 있는지 확인
if ! command -v gh &> /dev/null; then
    echo "GitHub CLI가 설치되어 있지 않습니다. 설치해주세요."
    echo "설치 방법: https://cli.github.com/manual/installation"
    exit 1
fi

# GitHub 로그인 확인
if ! gh auth status &> /dev/null; then
    echo "GitHub에 로그인되어 있지 않습니다."
    echo "실행: gh auth login"
    exit 1
fi

# Repository 확인
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner 2>/dev/null)
if [ -z "$REPO" ]; then
    echo "GitHub repository를 찾을 수 없습니다."
    echo "현재 디렉토리가 Git repository인지 확인하세요."
    exit 1
fi

echo "Repository: $REPO"
echo ""

# Secrets 설정
echo "필수 GitHub Secrets를 설정합니다..."

# Docker Hub
echo "1. Docker Hub 인증 정보"
gh secret set DOCKER_USERNAME -b "qws941"
gh secret set DOCKER_PASSWORD -b "bingogo1l7!"

# Private Registry (나중에 사용)
echo "2. Private Registry 인증 정보 (현재 비활성화)"
gh secret set REGISTRY_USERNAME -b "qws941"
gh secret set REGISTRY_PASSWORD -b "bingogo1l7!"

# Deployment Server
echo "3. 배포 서버 정보"
gh secret set DEPLOY_HOST -b "192.168.50.215"
gh secret set DEPLOY_USER -b "docker"

# SSH Key 설정
echo "4. SSH 배포 키 설정"
if [ -f ~/.ssh/id_rsa ]; then
    gh secret set DEPLOY_KEY < ~/.ssh/id_rsa
    echo "SSH 키가 설정되었습니다."
else
    echo "경고: ~/.ssh/id_rsa 파일을 찾을 수 없습니다."
    echo "다음 명령으로 직접 설정하세요:"
    echo "gh secret set DEPLOY_KEY < /path/to/your/private/key"
fi

# Optional: Safety API Key (보안 스캔용)
echo ""
echo "5. Optional: Safety API Key (Python 의존성 스캔)"
echo "Safety API Key가 있다면 다음 명령으로 설정하세요:"
echo "gh secret set SAFETY_API_KEY -b 'your-safety-api-key'"

echo ""
echo "설정된 Secrets 목록:"
gh secret list

echo ""
echo "GitHub Actions Secrets 설정이 완료되었습니다!"
echo ""
echo "추가 설정이 필요한 경우:"
echo "- GitHub 웹 UI: https://github.com/$REPO/settings/secrets/actions"
echo "- CLI 명령: gh secret set SECRET_NAME -b 'value'"