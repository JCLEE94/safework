#!/bin/bash

# SafeWork Watchtower API 모니터링 및 검증 도구
# Watchtower API 상태를 지속적으로 모니터링하고 배포 상태를 추적합니다

set -euo pipefail

# 설정
WATCHTOWER_API_URL="${WATCHTOWER_API_URL:-https://watchtower.jclee.me}"
WATCHTOWER_API_TOKEN="${WATCHTOWER_API_TOKEN:-MySuperSecretToken12345}"
PRODUCTION_URL="${PRODUCTION_URL:-https://safework.jclee.me}"
REGISTRY_URL="${REGISTRY_URL:-registry.jclee.me}"
IMAGE_NAME="${IMAGE_NAME:-safework}"
LOG_FILE="${LOG_FILE:-/tmp/watchtower-monitor.log}"
CHECK_INTERVAL="${CHECK_INTERVAL:-30}"

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 로깅 함수
log_with_timestamp() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
    log_with_timestamp "INFO" "$1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    log_with_timestamp "SUCCESS" "$1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    log_with_timestamp "WARNING" "$1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    log_with_timestamp "ERROR" "$1"
}

log_debug() {
    echo -e "${PURPLE}[DEBUG]${NC} $1"
    log_with_timestamp "DEBUG" "$1"
}

# 함수: Watchtower API 헬스체크
check_watchtower_health() {
    local response
    local http_code
    local start_time
    local end_time
    local duration
    
    start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\n%{http_code}" \
        -H "Authorization: Bearer $WATCHTOWER_API_TOKEN" \
        --max-time 10 \
        "$WATCHTOWER_API_URL/v1/status" 2>/dev/null || echo "TIMEOUT\n000")
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        log_success "Watchtower API 정상 (응답시간: ${duration}s)"
        return 0
    elif [ "$http_code" = "000" ]; then
        log_error "Watchtower API 타임아웃 또는 연결 실패"
        return 1
    else
        log_error "Watchtower API 오류 (HTTP $http_code)"
        return 1
    fi
}

# 함수: 프로덕션 애플리케이션 헬스체크
check_production_health() {
    local response
    local http_code
    local start_time
    local end_time
    local duration
    
    start_time=$(date +%s.%N)
    
    response=$(curl -s -w "\n%{http_code}" \
        --max-time 10 \
        "$PRODUCTION_URL/health" 2>/dev/null || echo "TIMEOUT\n000")
    
    end_time=$(date +%s.%N)
    duration=$(echo "$end_time - $start_time" | bc)
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        log_success "SafeWork 애플리케이션 정상 (응답시간: ${duration}s)"
        
        # JSON 응답 파싱 시도
        if echo "$body" | jq . >/dev/null 2>&1; then
            local app_status
            app_status=$(echo "$body" | jq -r '.status // "unknown"')
            local version
            version=$(echo "$body" | jq -r '.version // "unknown"')
            local timestamp
            timestamp=$(echo "$body" | jq -r '.timestamp // "unknown"')
            
            echo "  Status: $app_status | Version: $version | Timestamp: $timestamp"
        fi
        return 0
    elif [ "$http_code" = "000" ]; then
        log_error "SafeWork 애플리케이션 타임아웃 또는 연결 실패"
        return 1
    else
        log_error "SafeWork 애플리케이션 오류 (HTTP $http_code)"
        return 1
    fi
}

# 함수: Docker 레지스트리 헬스체크
check_registry_health() {
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" \
        --max-time 10 \
        "https://$REGISTRY_URL/v2/" 2>/dev/null || echo "TIMEOUT\n000")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        log_success "Docker 레지스트리 정상"
        return 0
    elif [ "$http_code" = "000" ]; then
        log_error "Docker 레지스트리 타임아웃 또는 연결 실패"
        return 1
    else
        log_error "Docker 레지스트리 오류 (HTTP $http_code)"
        return 1
    fi
}

# 함수: 컨테이너 상태 확인
check_container_status() {
    if command -v docker >/dev/null 2>&1; then
        local containers
        containers=$(docker ps --filter "ancestor=$REGISTRY_URL/$IMAGE_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "No containers found")
        
        if [ "$containers" != "No containers found" ] && [ -n "$containers" ]; then
            log_success "실행 중인 SafeWork 컨테이너:"
            echo "$containers"
        else
            log_warning "SafeWork 컨테이너가 실행되고 있지 않습니다"
        fi
    else
        log_warning "Docker 명령어를 사용할 수 없습니다"
    fi
}

# 함수: 최신 이미지 정보 확인
check_latest_image() {
    if command -v docker >/dev/null 2>&1; then
        local latest_image
        latest_image=$(docker images "$REGISTRY_URL/$IMAGE_NAME:latest" --format "{{.CreatedAt}}" 2>/dev/null | head -n1)
        
        if [ -n "$latest_image" ]; then
            log_info "최신 SafeWork 이미지: $latest_image"
        else
            log_warning "로컬에 SafeWork 이미지가 없습니다"
        fi
    fi
}

# 함수: 시스템 리소스 모니터링
check_system_resources() {
    if command -v docker >/dev/null 2>&1; then
        local docker_stats
        docker_stats=$(docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null | grep -i safework || echo "SafeWork 컨테이너 통계 없음")
        
        if [ "$docker_stats" != "SafeWork 컨테이너 통계 없음" ]; then
            log_info "SafeWork 컨테이너 리소스 사용량:"
            echo "$docker_stats"
        fi
    fi
    
    # 시스템 메모리 사용량
    if command -v free >/dev/null 2>&1; then
        local memory_info
        memory_info=$(free -h | grep "Mem:" | awk '{print "사용중: "$3" / 전체: "$2" ("$3/$2*100"%)"}')
        log_info "시스템 메모리: $memory_info"
    fi
    
    # 디스크 사용량
    if command -v df >/dev/null 2>&1; then
        local disk_info
        disk_info=$(df -h / | tail -n1 | awk '{print "사용중: "$3" / 전체: "$2" ("$5")"}')
        log_info "루트 디스크: $disk_info"
    fi
}

# 함수: 배포 이벤트 로그 분석
analyze_deployment_logs() {
    if [ -f "$LOG_FILE" ]; then
        local recent_errors
        recent_errors=$(tail -n 100 "$LOG_FILE" | grep -c "ERROR" || echo "0")
        local recent_successes
        recent_successes=$(tail -n 100 "$LOG_FILE" | grep -c "SUCCESS" || echo "0")
        
        log_info "최근 100개 로그 이벤트: 성공 $recent_successes, 오류 $recent_errors"
        
        if [ "$recent_errors" -gt 5 ]; then
            log_warning "최근 오류가 많이 발생했습니다 ($recent_errors개)"
        fi
    fi
}

# 함수: 종합 상태 리포트
generate_status_report() {
    echo
    echo "=================================================="
    echo "📊 SafeWork 시스템 상태 리포트"
    echo "=================================================="
    echo "시간: $(date)"
    echo "모니터링 간격: ${CHECK_INTERVAL}초"
    echo "로그 파일: $LOG_FILE"
    echo "=================================================="
    
    # 각 서비스 상태 확인
    local watchtower_status="❌"
    local production_status="❌"
    local registry_status="❌"
    
    if check_watchtower_health; then
        watchtower_status="✅"
    fi
    
    if check_production_health; then
        production_status="✅"
    fi
    
    if check_registry_health; then
        registry_status="✅"
    fi
    
    echo
    echo "🔍 서비스 상태:"
    echo "  Watchtower API: $watchtower_status $WATCHTOWER_API_URL"
    echo "  SafeWork App:   $production_status $PRODUCTION_URL"
    echo "  Docker Registry: $registry_status $REGISTRY_URL"
    echo
    
    # 컨테이너 및 이미지 정보
    echo "🐳 컨테이너 정보:"
    check_container_status
    echo
    check_latest_image
    echo
    
    # 시스템 리소스
    echo "📈 시스템 리소스:"
    check_system_resources
    echo
    
    # 로그 분석
    echo "📋 로그 분석:"
    analyze_deployment_logs
    echo
    
    echo "=================================================="
}

# 함수: 연속 모니터링
continuous_monitoring() {
    log_info "연속 모니터링 시작... (Ctrl+C로 중지)"
    
    while true; do
        generate_status_report
        
        echo "⏳ ${CHECK_INTERVAL}초 후 다음 검사..."
        echo
        
        sleep "$CHECK_INTERVAL"
    done
}

# 함수: 트러블슈팅 가이드
show_troubleshooting_guide() {
    echo "=================================================="
    echo "🔧 트러블슈팅 가이드"
    echo "=================================================="
    echo
    echo "1. Watchtower API 연결 실패:"
    echo "   - API 토큰 확인: WATCHTOWER_API_TOKEN"
    echo "   - URL 확인: $WATCHTOWER_API_URL"
    echo "   - 네트워크 연결 확인"
    echo
    echo "2. SafeWork 애플리케이션 오류:"
    echo "   - 컨테이너 로그 확인: docker logs safework"
    echo "   - 포트 확인: docker ps"
    echo "   - 헬스체크 엔드포인트: $PRODUCTION_URL/health"
    echo
    echo "3. Docker 레지스트리 연결 실패:"
    echo "   - 레지스트리 상태 확인: curl -I https://$REGISTRY_URL/v2/"
    echo "   - 인증 정보 확인"
    echo
    echo "4. 즉시 배포 트리거:"
    echo "   - 수동 트리거: $0 --trigger"
    echo "   - 특정 컨테이너: $0 --trigger safework"
    echo
    echo "5. 로그 분석:"
    echo "   - 전체 로그: tail -f $LOG_FILE"
    echo "   - 오류만: grep ERROR $LOG_FILE"
    echo "   - 성공만: grep SUCCESS $LOG_FILE"
    echo "=================================================="
}

# 함수: 사용법 출력
usage() {
    echo "SafeWork Watchtower API 모니터링 및 검증 도구"
    echo
    echo "사용법: $0 [옵션]"
    echo
    echo "옵션:"
    echo "  --monitor, -m        연속 모니터링 모드"
    echo "  --status, -s         현재 상태 확인 (기본값)"
    echo "  --trigger [container] 즉시 배포 트리거"
    echo "  --troubleshoot, -t   트러블슈팅 가이드 표시"
    echo "  --help, -h           이 도움말 표시"
    echo
    echo "환경변수:"
    echo "  WATCHTOWER_API_URL    Watchtower API URL"
    echo "  WATCHTOWER_API_TOKEN  Watchtower API 토큰"
    echo "  PRODUCTION_URL        프로덕션 URL"
    echo "  CHECK_INTERVAL        모니터링 간격 (초, 기본값: 30)"
    echo "  LOG_FILE              로그 파일 경로"
    echo
    echo "예제:"
    echo "  $0                    # 상태 확인"
    echo "  $0 --monitor          # 연속 모니터링"
    echo "  $0 --trigger          # 모든 컨테이너 업데이트"
    echo "  $0 --trigger safework # safework 컨테이너만 업데이트"
}

# 메인 함수
main() {
    # 로그 파일 초기화
    mkdir -p "$(dirname "$LOG_FILE")"
    
    case "${1:-status}" in
        --monitor|-m)
            continuous_monitoring
            ;;
        --status|-s|status)
            generate_status_report
            ;;
        --trigger)
            if [ $# -gt 1 ]; then
                log_info "특정 컨테이너 '$2' 업데이트 트리거..."
                ../scripts/trigger-immediate-deployment.sh "$2"
            else
                log_info "전체 배포 업데이트 트리거..."
                ../scripts/trigger-immediate-deployment.sh
            fi
            ;;
        --troubleshoot|-t)
            show_troubleshooting_guide
            ;;
        --help|-h|help)
            usage
            ;;
        *)
            generate_status_report
            ;;
    esac
}

# 시그널 핸들러 설정
trap 'log_info "모니터링 중지됨"; exit 0' INT TERM

# 스크립트 시작
main "$@"