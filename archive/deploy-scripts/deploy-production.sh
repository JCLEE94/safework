#!/bin/bash
set -euo pipefail

# SafeWork Pro 운영 서버 배포 스크립트
# =====================================

echo "🚀 SafeWork Pro 운영 서버 배포 시작..."

# 환경 변수 로드
if [ -f .env.production ]; then
    source .env.production
    echo "✅ 운영 환경 변수 로드 완료"
else
    echo "⚠️  .env.production 파일을 찾을 수 없습니다. 기본값 사용"
fi

# 필수 디렉터리 생성
echo "📁 운영 데이터 디렉터리 설정..."
sudo mkdir -p /opt/safework/{data/{postgres,redis,uploads},logs,backup}
sudo chown -R 1000:1000 /opt/safework
sudo chmod -R 755 /opt/safework

echo "✅ 디렉터리 생성 완료:"
echo "   - /opt/safework/data/postgres (DB 데이터)"
echo "   - /opt/safework/data/redis (캐시 데이터)"
echo "   - /opt/safework/data/uploads (업로드 파일)"
echo "   - /opt/safework/logs (시스템 로그)"
echo "   - /opt/safework/backup (백업 파일)"

# 기존 컨테이너 정리
echo "🧹 기존 컨테이너 정리..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true
docker container prune -f

# 최신 이미지 풀
echo "📥 최신 이미지 다운로드..."
docker pull registry.jclee.me/safework:latest

# 운영 서비스 시작
echo "🔄 운영 서비스 시작..."
docker-compose -f docker-compose.production.yml up -d

# 헬스체크 대기
echo "⏳ 서비스 시작 대기 (최대 3분)..."
sleep 30

# 헬스체크 확인
MAX_ATTEMPTS=18  # 3분 (10초 * 18회)
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "🔍 헬스체크 시도 $ATTEMPT/$MAX_ATTEMPTS..."
    
    if curl -f -s http://192.168.50.215:3001/health >/dev/null 2>&1; then
        echo "✅ 운영 서버 배포 완료!"
        echo "🌐 접속 URL: http://192.168.50.215:3001"
        break
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "❌ 헬스체크 실패 - 로그를 확인하세요"
        docker logs safework --tail=50
        exit 1
    fi
    
    sleep 10
    ((ATTEMPT++))
done

# 배포 상태 확인
echo ""
echo "📊 배포 상태 요약:"
echo "=================="
docker ps --filter name=safework --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "💾 볼륨 현황:"
docker volume ls --filter label=description | grep -i safework || echo "볼륨 없음"

echo ""
echo "🔍 최근 로그 (마지막 10줄):"
docker logs safework --tail=10

echo ""
echo "✅ SafeWork Pro 운영 배포 완료!"
echo "🌐 서비스 URL: http://192.168.50.215:3001"
echo "📊 헬스체크: http://192.168.50.215:3001/health"