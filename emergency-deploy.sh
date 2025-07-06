#!/bin/bash

# 긴급 배포 스크립트
echo "🚨 SafeWork 긴급 배포 시작..."

# SSH를 통한 원격 서버 직접 배포
SERVER_IP="192.168.50.110"
SERVER_PORT="33301"

# 로컬 Docker 이미지 저장
echo "📦 Docker 이미지 저장 중..."
docker save safework:local | gzip > safework-image.tar.gz

# 서버로 이미지 전송
echo "📤 서버로 이미지 전송 중..."
scp safework-image.tar.gz jclee@${SERVER_IP}:/tmp/

# 서버에서 배포 실행
echo "🚀 서버에서 배포 실행..."
ssh jclee@${SERVER_IP} << 'ENDSSH'
cd /tmp
echo "Docker 이미지 로드 중..."
docker load < safework-image.tar.gz

echo "기존 컨테이너 정리..."
docker stop safework 2>/dev/null || true
docker rm safework 2>/dev/null || true

echo "새 컨테이너 시작..."
docker run -d \
  --name safework \
  -p 33301:3001 \
  -e ENVIRONMENT=production \
  -e DATABASE_URL="postgresql://admin:safework123@localhost:5432/health_management" \
  -e REDIS_URL="redis://localhost:6379/0" \
  -e JWT_SECRET="safework-pro-secret-key-2024" \
  -e SECRET_KEY="safework-app-secret-2024" \
  -e HOST=0.0.0.0 \
  -e PORT=3001 \
  --restart unless-stopped \
  safework:local

echo "배포 완료!"
docker ps | grep safework
ENDSSH

# 정리
rm -f safework-image.tar.gz

echo "✅ 긴급 배포 완료!"
echo "🔗 접속 주소: http://${SERVER_IP}:${SERVER_PORT}"
echo "🔗 도메인: https://safework.jclee.me"