#!/bin/bash
set -e

# 환경변수 파일 로드
if [ -f ".env" ]; then
    source .env
fi

echo "🚀 SafeWork Pro 단일 컨테이너 배포 시작..."

# 원격 서버 정보 - 환경변수 우선
REMOTE_HOST="${REMOTE_HOST:-192.168.50.215}"
REMOTE_PORT="${REMOTE_PORT:-1111}"
REMOTE_USER="${REMOTE_USER:-docker}"
DOCKER_REGISTRY="${DOCKER_REGISTRY:-registry.jclee.me}"
APP_NAME="${APP_NAME:-safework}"

# 빌드 시간 설정
export BUILD_TIME=$(TZ=Asia/Seoul date "+%Y-%m-%d %H:%M:%S KST")
echo "Build Time: $BUILD_TIME"

# 1. Docker 이미지 빌드
echo "🔨 Docker 이미지 빌드 중..."
docker build -f Dockerfile.prod \
  --build-arg BUILD_TIME="$BUILD_TIME" \
  -t $DOCKER_REGISTRY/$APP_NAME:latest \
  --no-cache .

# 2. 이미지 푸시
echo "📤 Docker 이미지 푸시 중..."
docker push $DOCKER_REGISTRY/$APP_NAME:latest

# 3. docker-compose.single.yml 복사
echo "📋 설정 파일 복사 중..."
scp -P $REMOTE_PORT docker-compose.single.yml $REMOTE_USER@$REMOTE_HOST:~/app/health/

# 4. 원격 서버에서 기존 컨테이너 정리 및 새 단일 컨테이너 시작
echo "🚀 원격 서버에서 단일 컨테이너 배포 중..."
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << 'EOF'
cd ~/app/health

# 기존 컨테이너 모두 중지 및 제거
echo "🧹 기존 컨테이너 정리 중..."
/usr/local/bin/docker-compose -f docker-compose.simple.yml down || true
/usr/local/bin/docker-compose -f docker-compose.yml down || true

# 이미지 업데이트
echo "📥 최신 이미지 다운로드 중..."
/usr/local/bin/docker pull registry.jclee.me/safework:latest

# 단일 컨테이너로 시작
echo "🎯 단일 컨테이너 시작 중..."
export BUILD_TIME="$(TZ=Asia/Seoul date '+%Y-%m-%d %H:%M:%S KST')"
/usr/local/bin/docker-compose -f docker-compose.single.yml up -d

# 상태 확인
sleep 10
echo "✅ 컨테이너 상태:"
/usr/local/bin/docker ps | grep safework

# 로그 확인
echo "📋 최근 로그:"
/usr/local/bin/docker logs --tail 20 safework-all-in-one
EOF

# 5. 헬스 체크
echo "🏥 헬스 체크 중..."
sleep 15
HEALTH_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://$REMOTE_HOST:3001/health || echo "000")

if [ "$HEALTH_STATUS" = "200" ]; then
    echo "✅ 배포 성공! 단일 컨테이너로 실행 중"
    echo "🌐 접속 URL: http://$REMOTE_HOST:3001"
    echo "📚 API 문서: http://$REMOTE_HOST:3001/api/docs"
else
    echo "❌ 헬스 체크 실패 (HTTP $HEALTH_STATUS)"
    echo "📋 컨테이너 로그 확인:"
    ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "/usr/local/bin/docker logs --tail 50 safework-all-in-one"
    exit 1
fi