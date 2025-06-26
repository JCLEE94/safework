#!/bin/bash
set -euo pipefail

# SafeWork Pro - Watchtower 배포 가이드
echo "🐳 SafeWork Pro Watchtower 자동 배포 설정"
echo "========================================="

# 레지스트리 인증 확인
echo "📝 Docker 레지스트리 로그인 중..."
docker login registry.jclee.me -u qws941 -p bingogo1l7!

echo "✅ 레지스트리 인증 완료"

# Watchtower 실행
echo "🚀 Watchtower 시작 중..."
docker-compose -f docker-compose.watchtower.yml up -d

echo "✅ Watchtower 시작 완료"

# 상태 확인
echo "📊 Watchtower 상태 확인..."
docker ps | grep watchtower

echo ""
echo "🎯 Watchtower 설정 완료!"
echo ""
echo "📋 동작 방식:"
echo "  1. GitHub Actions가 새 이미지를 registry.jclee.me에 푸시"
echo "  2. Watchtower가 30초마다 레지스트리 확인"
echo "  3. 새 이미지 감지 시 자동으로 safework 컨테이너 업데이트"
echo "  4. 헬스체크 실패 시 자동 롤백"
echo ""
echo "🔍 로그 확인:"
echo "  docker logs -f watchtower"
echo ""
echo "⚙️ SafeWork Pro 컨테이너 실행:"
echo "  docker-compose -f docker-compose.production.yml up -d"
echo ""