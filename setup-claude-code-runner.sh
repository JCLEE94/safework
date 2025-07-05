#!/bin/bash

# Self-hosted runner에서 Claude Code OAuth 설정 스크립트
# 사용법: ./setup-claude-code-runner.sh

set -e

echo "🤖 Self-hosted Runner Claude Code OAuth 설정"
echo "============================================="

# Claude Code 설치 확인
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code CLI가 설치되지 않았습니다"
    echo ""
    echo "설치 방법:"
    echo "1. npm install -g @anthropic/claude-code"
    echo "2. 또는 공식 설치 가이드를 따르세요"
    echo "   https://github.com/anthropics/claude-code"
    exit 1
fi

echo "✅ Claude Code CLI 발견: $(which claude)"
echo "📋 버전: $(claude --version 2>/dev/null || echo 'Unknown')"

# OAuth 상태 확인
echo ""
echo "🔍 OAuth 인증 상태 확인..."

if claude auth status &>/dev/null; then
    echo "✅ Claude Code OAuth 인증이 이미 완료되었습니다"
    echo ""
    echo "👤 현재 사용자 정보:"
    claude auth status || echo "상태 정보를 가져올 수 없습니다"
    echo ""
    echo "🔄 인증을 다시 하려면 다음 명령어를 실행하세요:"
    echo "claude auth logout"
    echo "claude auth login"
else
    echo "❌ Claude Code OAuth 인증이 필요합니다"
    echo ""
    echo "🔐 OAuth 인증 프로세스 시작..."
    echo "👤 브라우저가 열리면 GitHub 계정으로 인증해주세요"
    echo ""
    
    # Interactive OAuth login
    if claude auth login; then
        echo ""
        echo "✅ Claude Code OAuth 인증 완료!"
        echo ""
        echo "👤 인증된 사용자 정보:"
        claude auth status || echo "상태 정보를 가져올 수 없습니다"
    else
        echo ""
        echo "❌ Claude Code OAuth 인증 실패"
        echo ""
        echo "🔧 수동 인증 방법:"
        echo "1. 터미널에서 'claude auth login' 실행"
        echo "2. 브라우저에서 GitHub 인증 완료"
        echo "3. 터미널로 돌아와서 인증 코드 입력"
        exit 1
    fi
fi

echo ""
echo "🧪 Claude Code 연결 테스트..."

# Test basic claude command
if claude chat --message "Hello, can you confirm you're working?" &>/dev/null; then
    echo "✅ Claude Code 연결 테스트 성공"
else
    echo "⚠️ Claude Code 연결 테스트 실패 (OAuth 인증은 완료됨)"
fi

echo ""
echo "📋 GitHub Actions runner 설정 완료!"
echo ""
echo "🔄 이제 GitHub Actions에서 Claude Code 분석이 실행됩니다:"
echo "1. Push/PR 시 자동으로 Claude Code OAuth 상태 확인"
echo "2. 인증된 경우 MCP 도구를 사용한 보안 분석 실행"
echo "3. 분석 결과는 Actions 로그에서 확인 가능"
echo ""
echo "✅ 설정 완료!"