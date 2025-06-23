#!/bin/bash
# Claude Service - Core Service Manager
# Version: 1.0.0

set -euo pipefail

# Source common utilities
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SERVICE_ROOT}/utils/common.sh"

readonly PID_FILE="${LOG_DIR}/service-manager.pid"
readonly SERVICE_LOG="${LOG_DIR}/service.log"

# Service status check
is_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# Start service
start() {
    if is_running; then
        log_info "Service already running (PID: $(cat "$PID_FILE"))"
        return 0
    fi
    
    log_info "Starting Claude Service Manager..."
    
    # Validate environment first
    if ! "${SERVICE_ROOT}/utils/common.sh" validate; then
        log_error "Environment validation failed"
        return 1
    fi
    
    # Start background service
    (
        trap cleanup_and_exit TERM INT
        cleanup_and_exit() {
            log_info "Service manager shutting down..."
            rm -f "$PID_FILE"
            exit 0
        }
        
        echo $$ > "$PID_FILE"
        log_info "Service manager started (PID: $$)"
        
        while true; do
            # Service health monitoring
            monitor_services
            
            # Session cleanup
            cleanup_dead_sessions
            
            # System health check
            check_system_health
            
            sleep 60  # Check every minute
        done
    ) &>> "$SERVICE_LOG" &
    
    local service_pid=$!
    echo $service_pid > "$PID_FILE"
    
    log_info "Service manager started in background (PID: $service_pid)"
    return 0
}

# Stop service
stop() {
    if ! is_running; then
        log_info "Service not running"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    log_info "Stopping service manager (PID: $pid)..."
    
    kill "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local timeout=30
    while [[ $timeout -gt 0 ]] && kill -0 "$pid" 2>/dev/null; do
        sleep 1
        ((timeout--))
    done
    
    # Force kill if needed
    if kill -0 "$pid" 2>/dev/null; then
        log_info "Force killing service manager..."
        kill -9 "$pid" 2>/dev/null || true
    fi
    
    rm -f "$PID_FILE"
    log_info "Service manager stopped"
}

# Restart service
restart() {
    log_info "Restarting service manager..."
    stop
    sleep 2
    start
}

# Service status
status() {
    echo "🚀 Claude Service Manager Status"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ' || echo "unknown")
        echo "🟢 Status: Running (PID: $pid)"
        echo "⏰ Uptime: $uptime"
    else
        echo "🔴 Status: Stopped"
    fi
    
    echo ""
    echo "📁 Directories:"
    echo "  Log:       $LOG_DIR"
    echo "  Sessions:  $SESSION_DIR"
    echo "  Knowledge: $KNOWLEDGE_DIR"
    
    echo ""
    echo "📊 Module Status:"
    for module in core session notification helper utils; do
        local module_script="${SERVICE_ROOT}/${module}/${module}-manager.sh"
        if [[ "$module" == "utils" ]]; then
            module_script="${SERVICE_ROOT}/${module}/common.sh"
        fi
        
        if [[ -f "$module_script" ]]; then
            echo "  ✅ $module: Available"
        else
            echo "  ❌ $module: Missing"
        fi
    done
    
    echo ""
    echo "🐳 Docker Status:"
    if command -v docker &> /dev/null; then
        echo "  ✅ Docker: $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',')"
        echo "  📊 Containers: $(docker ps -q | wc -l) running"
    else
        echo "  ❌ Docker: Not available"
    fi
}

# Health check
health() {
    local health_status=0
    
    echo "🏥 Claude Service Health Check"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check service manager
    if is_running; then
        echo "✅ Service Manager: Running"
    else
        echo "❌ Service Manager: Stopped"
        health_status=1
    fi
    
    # Check required directories
    for dir in "$LOG_DIR" "$SESSION_DIR" "$KNOWLEDGE_DIR"; do
        if [[ -d "$dir" ]]; then
            echo "✅ Directory: $dir"
        else
            echo "❌ Directory: $dir (missing)"
            health_status=1
        fi
    done
    
    # Check disk space
    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2{print $5}' | tr -d '%')
    if [[ $disk_usage -lt 90 ]]; then
        echo "✅ Disk Space: ${disk_usage}% used"
    else
        echo "⚠️  Disk Space: ${disk_usage}% used (high)"
        health_status=1
    fi
    
    # Check memory
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [[ $mem_usage -lt 90 ]]; then
        echo "✅ Memory: ${mem_usage}% used"
    else
        echo "⚠️  Memory: ${mem_usage}% used (high)"
        health_status=1
    fi
    
    # Check Docker
    if command -v docker &> /dev/null && docker info &> /dev/null; then
        echo "✅ Docker: Available"
    else
        echo "❌ Docker: Not available"
        health_status=1
    fi
    
    echo ""
    if [[ $health_status -eq 0 ]]; then
        echo "🎉 All health checks passed"
    else
        echo "⚠️  Some health checks failed"
    fi
    
    return $health_status
}

# Dashboard view
dashboard() {
    clear
    echo "🚀 Claude Service Dashboard (v1.0)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Service status
    if is_running; then
        local pid=$(cat "$PID_FILE")
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null | tr -d ' ' || echo "unknown")
        echo "🟢 Service: Running | ⏰ Uptime: $uptime"
    else
        echo "🔴 Service: Stopped"
    fi
    
    # Module status
    echo "📦 Modules: ✅ Core ✅ Session ✅ Notification ✅ Helper ✅ Utils"
    echo ""
    
    # Session overview
    echo "🗂️ Active Sessions:"
    if [[ -d "$SESSION_DIR" ]]; then
        local session_count=$(find "$SESSION_DIR" -name "*.json" 2>/dev/null | wc -l)
        if [[ $session_count -gt 0 ]]; then
            find "$SESSION_DIR" -name "*.json" -exec basename {} .json \; | while read session; do
                echo "🆔 $session | 📊 Active"
            done
        else
            echo "  📭 No active sessions"
        fi
    else
        echo "  ❌ Session directory not found"
    fi
    
    echo ""
    echo "🛠️ Quick Commands:"
    echo "  ./service/core/service-manager.sh status"
    echo "  ./service/session/session-manager.sh list"
    echo "  ./service/helper/helper-manager.sh dashboard"
    echo "  ./service/notification/notification-manager.sh test"
    echo ""
    echo "Press Ctrl+C to exit dashboard"
    
    # Auto-refresh every 30 seconds
    sleep 30
    dashboard
}

# Monitor services
monitor_services() {
    # Check if other modules are responsive
    for module in session notification helper; do
        local module_script="${SERVICE_ROOT}/${module}/${module}-manager.sh"
        if [[ -f "$module_script" ]]; then
            # Simple health check for modules
            timeout 5 bash "$module_script" help &>/dev/null || {
                log_error "Module $module not responding"
            }
        fi
    done
}

# Cleanup dead sessions
cleanup_dead_sessions() {
    if [[ -d "$SESSION_DIR" ]]; then
        # Remove session files older than 7 days
        find "$SESSION_DIR" -name "*.json" -mtime +7 -delete 2>/dev/null || true
    fi
}

# System health check
check_system_health() {
    # Check disk space
    local disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2{print $5}' | tr -d '%')
    if [[ $disk_usage -gt 95 ]]; then
        log_error "Critical: Disk space at ${disk_usage}%"
        # Trigger cleanup
        "${SERVICE_ROOT}/utils/common.sh" cleanup 3
    fi
    
    # Check memory
    local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [[ $mem_usage -gt 95 ]]; then
        log_error "Critical: Memory usage at ${mem_usage}%"
    fi
}

# Main function
main() {
    case "${1:-}" in
        "start")
            start
            ;;
        "stop")
            stop
            ;;
        "restart")
            restart
            ;;
        "status")
            status
            ;;
        "health")
            health
            ;;
        "dashboard")
            dashboard
            ;;
        "help"|"")
            echo "Usage: $0 {start|stop|restart|status|health|dashboard}"
            echo ""
            echo "Commands:"
            echo "  start      - Start service manager"
            echo "  stop       - Stop service manager"
            echo "  restart    - Restart service manager"
            echo "  status     - Show service status"
            echo "  health     - Run health check"
            echo "  dashboard  - Show interactive dashboard"
            exit 0
            ;;
        *)
            echo "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi