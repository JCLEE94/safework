#!/bin/bash

# SafeWork Pro Health Management System - Monitoring Script
# Monitors system health and sends alerts

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="health-management-system"
HEALTH_URL="${HEALTH_URL:-http://localhost:3001/health}"
METRICS_URL="${METRICS_URL:-http://localhost:3001/api/v1/monitoring/metrics}"
LOG_FILE="${PROJECT_DIR}/logs/monitor.log"

# Thresholds
CPU_THRESHOLD=80
MEMORY_THRESHOLD=85
DISK_THRESHOLD=90
RESPONSE_TIME_THRESHOLD=2000  # milliseconds

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $1"
    echo -e "${BLUE}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_success() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] [SUCCESS] $1"
    echo -e "${GREEN}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_warning() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] [WARNING] $1"
    echo -e "${YELLOW}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

log_error() {
    local message="[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $1"
    echo -e "${RED}$message${NC}"
    echo "$message" >> "$LOG_FILE"
}

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Check if service is running
check_service_status() {
    log_info "Checking service status..."
    
    cd "$PROJECT_DIR"
    
    # Check Docker containers
    local containers_status
    containers_status=$(docker-compose ps --format json 2>/dev/null || echo "[]")
    
    if [[ "$containers_status" == "[]" ]]; then
        log_error "No containers are running"
        return 1
    fi
    
    # Parse container status
    local healthy_containers=0
    local total_containers=0
    
    while IFS= read -r container; do
        if [[ -n "$container" ]]; then
            total_containers=$((total_containers + 1))
            local status
            status=$(echo "$container" | jq -r '.State' 2>/dev/null || echo "unknown")
            
            if [[ "$status" == "running" ]]; then
                healthy_containers=$((healthy_containers + 1))
            else
                log_warning "Container $(echo "$container" | jq -r '.Name') is $status"
            fi
        fi
    done <<< "$(echo "$containers_status" | jq -c '.[]' 2>/dev/null || echo "")"
    
    if [[ $healthy_containers -eq $total_containers ]] && [[ $total_containers -gt 0 ]]; then
        log_success "All $total_containers containers are running"
        return 0
    else
        log_error "$healthy_containers/$total_containers containers are healthy"
        return 1
    fi
}

# Check application health endpoint
check_health_endpoint() {
    log_info "Checking health endpoint: $HEALTH_URL"
    
    local start_time
    start_time=$(date +%s%3N)
    
    local response
    local http_code
    
    response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$HEALTH_URL" --max-time 10 2>/dev/null || echo "HTTPSTATUS:000")
    http_code=$(echo "$response" | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
    response_body=$(echo "$response" | sed -e 's/HTTPSTATUS:.*//g')
    
    local end_time
    end_time=$(date +%s%3N)
    local response_time=$((end_time - start_time))
    
    if [[ "$http_code" == "200" ]]; then
        if [[ $response_time -lt $RESPONSE_TIME_THRESHOLD ]]; then
            log_success "Health check passed (${response_time}ms)"
        else
            log_warning "Health check passed but slow (${response_time}ms > ${RESPONSE_TIME_THRESHOLD}ms)"
        fi
        return 0
    else
        log_error "Health check failed: HTTP $http_code (${response_time}ms)"
        log_error "Response: $response_body"
        return 1
    fi
}

# Check system metrics
check_system_metrics() {
    log_info "Checking system metrics..."
    
    local metrics_response
    metrics_response=$(curl -s "$METRICS_URL" --max-time 10 2>/dev/null || echo "{}")
    
    if [[ "$metrics_response" == "{}" ]]; then
        log_warning "Could not retrieve metrics from $METRICS_URL"
        return 1
    fi
    
    # Parse metrics using basic text processing (no jq dependency required)
    local cpu_percent
    local memory_percent
    local disk_percent
    
    cpu_percent=$(echo "$metrics_response" | grep -o '"cpu_percent":[0-9.]*' | cut -d: -f2 || echo "0")
    memory_percent=$(echo "$metrics_response" | grep -o '"memory_percent":[0-9.]*' | cut -d: -f2 || echo "0")
    disk_percent=$(echo "$metrics_response" | grep -o '"disk_percent":[0-9.]*' | cut -d: -f2 || echo "0")
    
    # Convert to integers for comparison
    cpu_int=$(printf "%.0f" "$cpu_percent" 2>/dev/null || echo "0")
    memory_int=$(printf "%.0f" "$memory_percent" 2>/dev/null || echo "0")
    disk_int=$(printf "%.0f" "$disk_percent" 2>/dev/null || echo "0")
    
    local alerts=()
    
    # Check CPU
    if [[ $cpu_int -gt $CPU_THRESHOLD ]]; then
        alerts+=("CPU usage high: ${cpu_percent}%")
        log_warning "CPU usage high: ${cpu_percent}% (threshold: ${CPU_THRESHOLD}%)"
    else
        log_info "CPU usage: ${cpu_percent}%"
    fi
    
    # Check Memory
    if [[ $memory_int -gt $MEMORY_THRESHOLD ]]; then
        alerts+=("Memory usage high: ${memory_percent}%")
        log_warning "Memory usage high: ${memory_percent}% (threshold: ${MEMORY_THRESHOLD}%)"
    else
        log_info "Memory usage: ${memory_percent}%"
    fi
    
    # Check Disk
    if [[ $disk_int -gt $DISK_THRESHOLD ]]; then
        alerts+=("Disk usage high: ${disk_percent}%")
        log_warning "Disk usage high: ${disk_percent}% (threshold: ${DISK_THRESHOLD}%)"
    else
        log_info "Disk usage: ${disk_percent}%"
    fi
    
    if [[ ${#alerts[@]} -gt 0 ]]; then
        return 1
    else
        log_success "All system metrics within normal ranges"
        return 0
    fi
}

# Check database connectivity
check_database() {
    log_info "Checking database connectivity..."
    
    cd "$PROJECT_DIR"
    
    # Try to connect to PostgreSQL container
    local db_check
    db_check=$(docker-compose exec -T postgres pg_isready -U admin -d health_management 2>/dev/null || echo "failed")
    
    if [[ "$db_check" == *"accepting connections"* ]]; then
        log_success "Database is accepting connections"
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

# Check Redis connectivity
check_redis() {
    log_info "Checking Redis connectivity..."
    
    cd "$PROJECT_DIR"
    
    # Try to ping Redis container
    local redis_check
    redis_check=$(docker-compose exec -T redis redis-cli ping 2>/dev/null || echo "failed")
    
    if [[ "$redis_check" == "PONG" ]]; then
        log_success "Redis is responding"
        return 0
    else
        log_error "Redis connection failed"
        return 1
    fi
}

# Check disk space
check_disk_space() {
    log_info "Checking disk space..."
    
    local disk_usage
    disk_usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        log_error "Disk usage critical: ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
        return 1
    elif [[ $disk_usage -gt $((DISK_THRESHOLD - 10)) ]]; then
        log_warning "Disk usage high: ${disk_usage}%"
        return 0
    else
        log_success "Disk usage normal: ${disk_usage}%"
        return 0
    fi
}

# Check log files for errors
check_logs() {
    log_info "Checking recent logs for errors..."
    
    local log_files=("$PROJECT_DIR/logs/health_system.log")
    local error_count=0
    
    for log_file in "${log_files[@]}"; do
        if [[ -f "$log_file" ]]; then
            # Check for errors in the last 5 minutes
            local recent_errors
            recent_errors=$(find "$log_file" -mmin -5 -exec grep -i "error\|exception\|critical" {} \; 2>/dev/null | wc -l)
            
            if [[ $recent_errors -gt 0 ]]; then
                log_warning "Found $recent_errors recent errors in $(basename "$log_file")"
                error_count=$((error_count + recent_errors))
            fi
        fi
    done
    
    if [[ $error_count -eq 0 ]]; then
        log_success "No recent errors found in logs"
        return 0
    else
        log_warning "Found $error_count recent errors in logs"
        return 1
    fi
}

# Send alert (placeholder for notification system)
send_alert() {
    local message="$1"
    local level="${2:-warning}"
    
    log_info "Sending $level alert: $message"
    
    # Here you would integrate with your notification system
    # Examples:
    # - Send email
    # - Post to Slack
    # - Send to monitoring system
    # - Write to external log system
    
    # For now, just log the alert
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT [$level]: $message" >> "${PROJECT_DIR}/logs/alerts.log"
}

# Generate health report
generate_report() {
    log_info "Generating health report..."
    
    local report_file="${PROJECT_DIR}/logs/health_report_$(date +%Y%m%d_%H%M%S).json"
    
    cat > "$report_file" << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "system": {
    "hostname": "$(hostname)",
    "uptime": "$(uptime -p 2>/dev/null || echo 'unknown')",
    "load_average": "$(uptime | awk -F'load average:' '{print $2}' | xargs)"
  },
  "docker": {
    "version": "$(docker --version 2>/dev/null || echo 'unknown')",
    "compose_version": "$(docker-compose --version 2>/dev/null || echo 'unknown')"
  },
  "application": {
    "health_url": "$HEALTH_URL",
    "metrics_url": "$METRICS_URL"
  },
  "checks_performed": [
    "service_status",
    "health_endpoint",
    "system_metrics",
    "database_connectivity",
    "redis_connectivity",
    "disk_space",
    "log_analysis"
  ]
}
EOF
    
    log_success "Health report generated: $report_file"
}

# Main monitoring function
run_monitoring() {
    log_info "Starting health monitoring..."
    
    local failed_checks=0
    local total_checks=7
    
    # Run all checks
    check_service_status || failed_checks=$((failed_checks + 1))
    check_health_endpoint || failed_checks=$((failed_checks + 1))
    check_system_metrics || failed_checks=$((failed_checks + 1))
    check_database || failed_checks=$((failed_checks + 1))
    check_redis || failed_checks=$((failed_checks + 1))
    check_disk_space || failed_checks=$((failed_checks + 1))
    check_logs || failed_checks=$((failed_checks + 1))
    
    # Generate report
    generate_report
    
    # Summary
    local passed_checks=$((total_checks - failed_checks))
    
    if [[ $failed_checks -eq 0 ]]; then
        log_success "All health checks passed ($passed_checks/$total_checks)"
        return 0
    elif [[ $failed_checks -le 2 ]]; then
        log_warning "Some health checks failed ($passed_checks/$total_checks)"
        send_alert "Health monitoring: $failed_checks/$total_checks checks failed" "warning"
        return 1
    else
        log_error "Critical: Multiple health checks failed ($passed_checks/$total_checks)"
        send_alert "Health monitoring: CRITICAL - $failed_checks/$total_checks checks failed" "critical"
        return 2
    fi
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND]

Commands:
    monitor     Run full health monitoring (default)
    status      Check service status only
    health      Check health endpoint only
    metrics     Check system metrics only
    database    Check database connectivity only
    redis       Check Redis connectivity only
    logs        Check logs for errors only
    report      Generate health report only

Options:
    -h, --help          Show this help message
    -v, --verbose       Verbose output
    -q, --quiet         Quiet output (errors only)
    --health-url URL    Override health check URL
    --metrics-url URL   Override metrics URL

Examples:
    $0                  # Run full monitoring
    $0 status           # Check service status only
    $0 health           # Check health endpoint only
    $0 --health-url http://soonmin.jclee.me/health
EOF
}

# Parse command line arguments
VERBOSE=false
QUIET=false
COMMAND="monitor"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -q|--quiet)
            QUIET=true
            shift
            ;;
        --health-url)
            HEALTH_URL="$2"
            shift 2
            ;;
        --metrics-url)
            METRICS_URL="$2"
            shift 2
            ;;
        monitor|status|health|metrics|database|redis|logs|report)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Adjust logging based on verbosity
if [[ "$QUIET" == "true" ]]; then
    # Redirect info and success to null
    exec 3>&1 4>&2
    exec 1>/dev/null 2>/dev/null
fi

# Main execution
main() {
    case "$COMMAND" in
        monitor)
            run_monitoring
            ;;
        status)
            check_service_status
            ;;
        health)
            check_health_endpoint
            ;;
        metrics)
            check_system_metrics
            ;;
        database)
            check_database
            ;;
        redis)
            check_redis
            ;;
        logs)
            check_logs
            ;;
        report)
            generate_report
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"