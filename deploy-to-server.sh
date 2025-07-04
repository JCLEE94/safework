#!/bin/bash

# SafeWork 서버 배포 스크립트
# safework.jclee.me -> 192.168.50.110:33301

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 서버 정보
SERVER_HOST="192.168.50.110"
SERVER_PORT="33301"
TARGET_URL="http://${SERVER_HOST}:${SERVER_PORT}"
DOMAIN_URL="https://safework.jclee.me"

log "SafeWork 서버 배포 시작 (${SERVER_HOST}:${SERVER_PORT})"

# 1. 현재 프로젝트 빌드
log "프로젝트 빌드 중..."
cd /home/jclee/app/safework

# Docker 이미지 빌드
log "Docker 이미지 빌드 중..."
docker build -t safework:latest .

# 이미지 태그
docker tag safework:latest registry.jclee.me/safework:latest

# 레지스트리에 푸시
log "레지스트리에 이미지 푸시 중..."
docker push registry.jclee.me/safework:latest

# 2. 서버 연결 테스트
log "서버 연결 테스트 중..."
if ping -c 1 ${SERVER_HOST} &> /dev/null; then
    success "서버 연결 확인됨 (${SERVER_HOST})"
else
    error "서버 연결 실패 (${SERVER_HOST})"
    exit 1
fi

# 3. 서버 배포 스크립트 생성
log "서버 배포 스크립트 생성 중..."
cat > server-deploy.sh << 'EOF'
#!/bin/bash

# 서버측 배포 스크립트
echo "SafeWork 서버 배포 시작..."

# 기존 컨테이너 정리
docker stop safework 2>/dev/null || true
docker rm safework 2>/dev/null || true

# PostgreSQL 시작 (없으면 생성)
if ! docker ps | grep -q postgres-safework; then
    echo "PostgreSQL 시작 중..."
    docker run -d --name postgres-safework \
        --restart unless-stopped \
        -e POSTGRES_DB=health_management \
        -e POSTGRES_USER=admin \
        -e POSTGRES_PASSWORD=safework123 \
        -v /data/safework/postgres:/var/lib/postgresql/data \
        -p 5432:5432 \
        postgres:15
    sleep 10
fi

# Redis 시작 (없으면 생성)
if ! docker ps | grep -q redis-safework; then
    echo "Redis 시작 중..."
    docker run -d --name redis-safework \
        --restart unless-stopped \
        -v /data/safework/redis:/data \
        -p 6379:6379 \
        redis:7-alpine
    sleep 5
fi

# 최신 이미지 풀
echo "최신 이미지 가져오는 중..."
docker pull registry.jclee.me/safework:latest

# SafeWork 앱 시작
echo "SafeWork 앱 시작 중..."
docker run -d --name safework \
    --restart unless-stopped \
    -p 33301:3001 \
    -e DATABASE_URL="postgresql://admin:safework123@192.168.50.110:5432/health_management" \
    -e REDIS_URL="redis://192.168.50.110:6379/0" \
    -e JWT_SECRET_KEY="safework-jwt-secret-production" \
    -e SECRET_KEY="safework-encryption-key-production" \
    -e ENVIRONMENT="production" \
    -e DEBUG="false" \
    -e TZ="Asia/Seoul" \
    -e BACKEND_CORS_ORIGINS='["https://safework.jclee.me", "http://192.168.50.110:33301"]' \
    -v /data/safework/uploads:/app/uploads \
    registry.jclee.me/safework:latest

# 잠시 대기 후 상태 확인
sleep 15

echo "컨테이너 상태:"
docker ps | grep safework

echo "헬스 체크:"
curl -f http://localhost:33301/health || echo "헬스 체크 실패"

echo "SafeWork 배포 완료!"
echo "URL: http://192.168.50.110:33301"
EOF

chmod +x server-deploy.sh

# 4. 서버에 스크립트 복사 및 실행
log "서버에 배포 스크립트 전송 중..."

# SSH 키 확인
if [ -f ~/.ssh/id_rsa ]; then
    SSH_KEY="-i ~/.ssh/id_rsa"
else
    SSH_KEY=""
fi

# 서버에 스크립트 복사 (SSH 또는 scp 사용)
if command -v scp &> /dev/null; then
    scp ${SSH_KEY} server-deploy.sh root@${SERVER_HOST}:/tmp/ 2>/dev/null || \
    scp ${SSH_KEY} server-deploy.sh ubuntu@${SERVER_HOST}:/tmp/ 2>/dev/null || \
    warning "SCP 전송 실패, 수동 복사 필요"
fi

# 5. 서버에서 실행
log "서버에서 배포 실행 중..."
if command -v ssh &> /dev/null; then
    ssh ${SSH_KEY} root@${SERVER_HOST} "bash /tmp/server-deploy.sh" 2>/dev/null || \
    ssh ${SSH_KEY} ubuntu@${SERVER_HOST} "sudo bash /tmp/server-deploy.sh" 2>/dev/null || \
    warning "SSH 실행 실패, 수동 실행 필요"
fi

# 6. 배포 확인
log "배포 확인 중..."
sleep 10

# 서버 헬스 체크
if curl -f ${TARGET_URL}/health &> /dev/null; then
    success "서버 배포 성공! (${TARGET_URL})"
else
    warning "서버 헬스 체크 실패"
fi

# 도메인 헬스 체크
if curl -f ${DOMAIN_URL}/health &> /dev/null; then
    success "도메인 배포 성공! (${DOMAIN_URL})"
else
    warning "도메인 헬스 체크 실패"
fi

# 7. 정리
rm -f server-deploy.sh

success "SafeWork 서버 배포 완료!"
echo ""
echo "=== 배포 정보 ==="
echo "서버 URL: ${TARGET_URL}"
echo "도메인 URL: ${DOMAIN_URL}"
echo "포트: ${SERVER_PORT}"
echo ""
echo "=== 확인 명령어 ==="
echo "curl ${TARGET_URL}/health"
echo "curl ${DOMAIN_URL}/health"
echo ""
echo "=== SSH 접속 (수동 확인시) ==="
echo "ssh root@${SERVER_HOST}"
echo "docker logs safework -f"