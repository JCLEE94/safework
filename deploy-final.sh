#!/bin/bash
set -e

echo "SafeWork Pro - 최종 배포 스크립트"
echo "================================="

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 함수 정의
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 1. 현재 실행 중인 컨테이너 확인
log_info "현재 실행 중인 컨테이너 확인..."
echo "현재 실행 중인 health 관련 컨테이너:"
docker ps --filter "name=health" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true
docker ps --filter "name=safework" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" || true

# 2. 기존 컨테이너 중지 (사용자 확인)
read -p "기존 health 관련 컨테이너를 중지하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "기존 health 관련 컨테이너 중지 중..."
    
    # health 관련 컨테이너 중지
    docker stop $(docker ps -q --filter "name=health") 2>/dev/null || log_warning "중지할 health 컨테이너가 없습니다"
    
    # 기존 safework 컨테이너 중지
    docker stop safework-single 2>/dev/null || log_warning "중지할 safework-single 컨테이너가 없습니다"
    
    log_success "기존 컨테이너 중지 완료"
else
    log_warning "기존 컨테이너 중지를 건너뜁니다"
fi

# 3. 볼륨 디렉토리 설정
log_info "볼륨 디렉토리 설정 실행..."
if [ -f "./setup-volumes.sh" ]; then
    ./setup-volumes.sh
    log_success "볼륨 디렉토리 설정 완료"
else
    log_error "setup-volumes.sh 파일을 찾을 수 없습니다"
    exit 1
fi

# 4. 프론트엔드 빌드
log_info "프론트엔드 빌드 실행..."
npm install
npm run build
log_success "프론트엔드 빌드 완료"

# 5. 빌드 시간 환경변수 설정
export BUILD_TIME="$(date +'%Y-%m-%d %H:%M:%S KST')"
log_info "빌드 시간 설정: $BUILD_TIME"

# 6. 최종 docker-compose 실행 (빌드 포함)
log_info "SafeWork Pro 단일 컨테이너 배포 시작..."
docker-compose -f docker-compose.final.yml down 2>/dev/null || true
docker-compose -f docker-compose.final.yml up -d --build

# 7. 배포 확인
log_info "배포 상태 확인 중..."
sleep 10

# 컨테이너 상태 확인
if docker ps --filter "name=safework-single" --filter "status=running" | grep -q safework-single; then
    log_success "SafeWork Pro 컨테이너 실행 중"
else
    log_error "SafeWork Pro 컨테이너 실행 실패"
    docker logs safework-single --tail 20
    exit 1
fi

# 8. 헬스체크
log_info "헬스체크 수행 중..."
for i in {1..12}; do
    if curl -s http://localhost:3001/health > /dev/null; then
        log_success "헬스체크 통과 (시도 $i/12)"
        break
    else
        log_warning "헬스체크 대기 중... ($i/12)"
        sleep 5
    fi
    
    if [ $i -eq 12 ]; then
        log_error "헬스체크 실패"
        docker logs safework-single --tail 20
        exit 1
    fi
done

# 9. 최종 상태 출력
echo ""
echo "🎉 SafeWork Pro 배포 완료!"
echo "=========================="
echo ""
echo "📊 서비스 정보:"
echo "- 🌐 Public URL: https://safework.jclee.me"
echo "- 🏠 Local URL: http://192.168.50.215:3001"
echo "- 🏠 Localhost: http://localhost:3001"
echo "- ❤️  헬스체크: http://localhost:3001/health"
echo "- 📖 API 문서: http://localhost:3001/api/docs"
echo "- 🏥 건설업 보건관리 시스템"
echo ""
echo "🐳 컨테이너 정보:"
docker ps --filter "name=safework-single" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
echo ""
echo "💾 볼륨 정보:"
docker volume ls --filter "name=safework" --format "table {{.Name}}\t{{.Driver}}\t{{.Scope}}"
echo ""
echo "📋 로그 확인:"
echo "docker logs safework-single"
echo ""
echo "🔄 재시작:"
echo "docker-compose -f docker-compose.final.yml restart"
echo ""

# 10. 헬스체크 응답 표시
log_info "현재 헬스체크 응답:"
curl -s http://localhost:3001/health | jq . 2>/dev/null || curl -s http://localhost:3001/health

log_success "배포 스크립트 실행 완료!"