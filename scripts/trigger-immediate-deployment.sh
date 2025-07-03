#!/bin/bash

# SafeWork 즉시 배포 트리거 스크립트
# Watchtower HTTP API를 사용하여 즉시 배포를 실행합니다

set -euo pipefail

# 설정
WATCHTOWER_API_URL="${WATCHTOWER_API_URL:-https://watchtower.jclee.me}"
WATCHTOWER_API_TOKEN="${WATCHTOWER_API_TOKEN:-MySuperSecretToken12345}"
PRODUCTION_URL="${PRODUCTION_URL:-https://safework.jclee.me}"
REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
IMAGE_NAME="${IMAGE_NAME:-safework}"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로깅 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 함수: Watchtower 상태 확인
check_watchtower_status() {
    log_info "Watchtower API 상태 확인 중..."
    
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $WATCHTOWER_API_TOKEN" \
        "$WATCHTOWER_API_URL/v1/status" 2>/dev/null || echo "ERROR\n000")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        log_success "Watchtower API 연결 성공"
        echo "Status: $body"
        return 0
    else
        log_error "Watchtower API 연결 실패 (HTTP $http_code)"
        return 1
    fi
}

# 함수: 즉시 업데이트 트리거
trigger_immediate_update() {
    log_info "즉시 배포 업데이트 트리거 중..."
    
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $WATCHTOWER_API_TOKEN" \
        -H "Content-Type: application/json" \
        "$WATCHTOWER_API_URL/v1/update" 2>/dev/null || echo "ERROR\n000")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
        log_success "배포 업데이트가 성공적으로 트리거되었습니다"
        echo "Response: $body"
        return 0
    else
        log_error "배포 업데이트 트리거 실패 (HTTP $http_code)"
        echo "Response: $body"
        return 1
    fi
}

# 함수: 특정 컨테이너 업데이트
trigger_container_update() {
    local container_name="$1"
    log_info "컨테이너 '$container_name' 업데이트 트리거 중..."
    
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" \
        -X POST \
        -H "Authorization: Bearer $WATCHTOWER_API_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"container\": \"$container_name\"}" \
        "$WATCHTOWER_API_URL/v1/update" 2>/dev/null || echo "ERROR\n000")
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "204" ]; then
        log_success "컨테이너 '$container_name' 업데이트가 트리거되었습니다"
        return 0
    else
        log_error "컨테이너 업데이트 트리거 실패 (HTTP $http_code)"
        return 1
    fi
}

# 함수: 배포 상태 모니터링
monitor_deployment() {
    log_info "배포 상태 모니터링 시작..."
    
    local max_attempts=30
    local attempt=1
    local deployment_success=false
    
    while [ $attempt -le $max_attempts ]; do
        log_info "배포 상태 확인 중... ($attempt/$max_attempts)"
        
        # 애플리케이션 헬스체크
        if curl -f -s "$PRODUCTION_URL/health" > /dev/null 2>&1; then
            # 헬스체크 응답 확인
            local health_response
            health_response=$(curl -s "$PRODUCTION_URL/health" 2>/dev/null || echo '{}')
            
            log_success "애플리케이션이 정상적으로 응답하고 있습니다"
            echo "Health Response: $health_response"
            
            deployment_success=true
            break
        else
            log_warning "애플리케이션이 아직 준비되지 않았습니다. 20초 후 다시 시도..."
        fi
        
        sleep 20
        attempt=$((attempt + 1))
    done
    
    if [ "$deployment_success" = true ]; then
        log_success "배포가 성공적으로 완료되었습니다!"
        return 0
    else
        log_error "배포 검증이 실패했습니다 ($max_attempts 시도 후)"
        return 1
    fi
}

# 함수: 레지스트리 상태 확인
check_registry_status() {
    log_info "Docker 레지스트리 상태 확인 중..."
    
    if curl -f -s "https://$REGISTRY_URL/v2/" > /dev/null 2>&1; then
        log_success "Docker 레지스트리 연결 성공"
        return 0
    else
        log_warning "Docker 레지스트리 연결 확인 불가"
        return 1
    fi
}

# 함수: 현재 이미지 정보 확인
check_current_image() {
    log_info "현재 SafeWork 이미지 정보 확인 중..."
    
    local image_info
    if command -v docker >/dev/null 2>&1; then
        image_info=$(docker images "$REGISTRY_URL/$IMAGE_NAME" --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}\t{{.Size}}" 2>/dev/null || echo "이미지 정보 없음")
        echo "Current Images:"
        echo "$image_info"
    else
        log_warning "Docker 명령어를 사용할 수 없습니다"
    fi
}

# 메인 함수
main() {
    echo "=================================================="
    echo "🚀 SafeWork 즉시 배포 트리거"
    echo "=================================================="
    echo "Watchtower API: $WATCHTOWER_API_URL"
    echo "Production URL: $PRODUCTION_URL"
    echo "Registry: $REGISTRY_URL"
    echo "Image: $IMAGE_NAME"
    echo "=================================================="
    echo
    
    # 1. Watchtower 상태 확인
    if ! check_watchtower_status; then
        log_error "Watchtower API 상태 확인 실패"
        exit 1
    fi
    echo
    
    # 2. 레지스트리 상태 확인
    check_registry_status
    echo
    
    # 3. 현재 이미지 정보 확인
    check_current_image
    echo
    
    # 4. 즉시 업데이트 트리거
    if [ $# -gt 0 ]; then
        # 특정 컨테이너 지정
        trigger_container_update "$1"
    else
        # 전체 업데이트
        trigger_immediate_update
    fi
    echo
    
    # 5. 배포 모니터링
    if monitor_deployment; then
        echo
        echo "=================================================="
        log_success "🎉 배포가 성공적으로 완료되었습니다!"
        echo "🔗 확인: $PRODUCTION_URL"
        echo "🔍 헬스체크: $PRODUCTION_URL/health"
        echo "=================================================="
    else
        echo
        echo "=================================================="
        log_error "❌ 배포 검증에 실패했습니다"
        echo "🔧 로그 확인: docker logs safework"
        echo "🔍 헬스체크: $PRODUCTION_URL/health"
        echo "=================================================="
        exit 1
    fi
}

# 사용법 출력
usage() {
    echo "사용법: $0 [container_name]"
    echo
    echo "옵션:"
    echo "  container_name    특정 컨테이너만 업데이트 (선택사항)"
    echo
    echo "예제:"
    echo "  $0                # 모든 컨테이너 업데이트"
    echo "  $0 safework       # safework 컨테이너만 업데이트"
    echo
    echo "환경변수:"
    echo "  WATCHTOWER_API_URL    Watchtower API URL (기본값: https://watchtower.jclee.me)"
    echo "  WATCHTOWER_API_TOKEN  Watchtower API 토큰 (기본값: MySuperSecretToken12345)"
    echo "  PRODUCTION_URL        프로덕션 URL (기본값: https://safework.jclee.me)"
    echo "  REGISTRY_URL          Docker 레지스트리 URL (기본값: registry.jclee.me)"
    echo "  IMAGE_NAME            이미지 이름 (기본값: safework)"
}

# 스크립트 시작
if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
    usage
    exit 0
fi

main "$@"