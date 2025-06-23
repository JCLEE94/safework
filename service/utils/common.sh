#!/bin/bash
# Claude Service - Common Utilities
# Version: 1.0.0

set -euo pipefail

# Global configuration
if [[ -z "${SERVICE_ROOT:-}" ]]; then
    readonly SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi
if [[ -z "${PROJECT_ROOT:-}" ]]; then
    readonly PROJECT_ROOT="$(cd "${SERVICE_ROOT}/.." && pwd)"
fi
if [[ -z "${LOG_DIR:-}" ]]; then
    readonly LOG_DIR="${PROJECT_ROOT}/logs"
fi
if [[ -z "${SESSION_DIR:-}" ]]; then
    readonly SESSION_DIR="${PROJECT_ROOT}/sessions"
fi
if [[ -z "${KNOWLEDGE_DIR:-}" ]]; then
    readonly KNOWLEDGE_DIR="${PROJECT_ROOT}/knowledge"
fi

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "${LOG_DIR}/common.log"
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "${LOG_DIR}/common.log" >&2
}

log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $*" | tee -a "${LOG_DIR}/common.log"
}

# Environment validation
validate() {
    log_info "Validating Claude Service environment..."
    
    # Check required directories
    local required_dirs=("$LOG_DIR" "$SESSION_DIR" "$KNOWLEDGE_DIR")
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            log_error "Required directory missing: $dir"
            return 1
        fi
    done
    
    # Check Docker availability
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        return 1
    fi
    
    # Check Python availability
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 not found"
        return 1
    fi
    
    log_info "Environment validation passed"
    return 0
}

# Setup function
setup() {
    log_info "Setting up Claude Service architecture..."
    
    # Create required directories
    mkdir -p "$LOG_DIR" "$SESSION_DIR" "$KNOWLEDGE_DIR"
    mkdir -p "${PROJECT_ROOT}/tests"/{unit,integration}
    mkdir -p "${PROJECT_ROOT}/docker"
    mkdir -p "${PROJECT_ROOT}/scripts"
    
    # Initialize log files
    touch "${LOG_DIR}/common.log"
    touch "${LOG_DIR}/service.log"
    touch "${LOG_DIR}/session.log"
    touch "${LOG_DIR}/notification.log"
    touch "${LOG_DIR}/helper.log"
    
    # Create .env if not exists
    if [[ ! -f "${PROJECT_ROOT}/.env" ]]; then
        log_info "Creating .env template..."
        cat > "${PROJECT_ROOT}/.env" << 'EOF'
# Database
DATABASE_URL=postgresql://admin:password@localhost:5432/health_management

# Redis
REDIS_URL=redis://localhost:6379/0

# Application
DEBUG=false
LOG_LEVEL=INFO
TZ=Asia/Seoul

# Telegram (Add your token)
TELEGRAM_CLAUDE_TOKEN=

# Docker Registry
DOCKER_REGISTRY_URL=
DEPLOY_HOST=
DEPLOY_PORT=22
DEPLOY_USER=
EOF
    fi
    
    # Set proper permissions
    chmod 755 "${SERVICE_ROOT}"/*/
    chmod +x "${SERVICE_ROOT}"/*/*.sh 2>/dev/null || true
    
    log_info "Claude Service setup completed"
}

# Monitoring function
monitor() {
    log_info "Starting Claude Service monitoring..."
    
    while true; do
        # Check service health
        if pgrep -f "service-manager.sh" > /dev/null; then
            log_info "Service manager running"
        else
            log_error "Service manager not running"
        fi
        
        # Check disk space
        local disk_usage=$(df -h "${PROJECT_ROOT}" | awk 'NR==2{print $5}' | tr -d '%')
        if [[ $disk_usage -gt 90 ]]; then
            log_error "Disk usage high: ${disk_usage}%"
        fi
        
        # Check memory usage
        local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        if [[ $mem_usage -gt 90 ]]; then
            log_error "Memory usage high: ${mem_usage}%"
        fi
        
        sleep 300  # Monitor every 5 minutes
    done
}

# Cleanup function
cleanup() {
    local days=${1:-7}
    log_info "Cleaning up files older than $days days..."
    
    # Clean old logs
    find "$LOG_DIR" -name "*.log" -mtime +$days -delete 2>/dev/null || true
    
    # Clean old sessions
    find "$SESSION_DIR" -name "*.json" -mtime +$days -delete 2>/dev/null || true
    
    # Clean Docker
    docker system prune -f --volumes 2>/dev/null || true
    
    log_info "Cleanup completed"
}

# Backup function
backup() {
    local backup_path=${1:-"${PROJECT_ROOT}/backup"}
    log_info "Creating backup at $backup_path..."
    
    mkdir -p "$backup_path"
    
    # Backup configuration
    cp "${PROJECT_ROOT}/.env" "$backup_path/" 2>/dev/null || true
    cp "${PROJECT_ROOT}/CLAUDE.md" "$backup_path/" 2>/dev/null || true
    
    # Backup sessions and knowledge
    cp -r "$SESSION_DIR" "$backup_path/" 2>/dev/null || true
    cp -r "$KNOWLEDGE_DIR" "$backup_path/" 2>/dev/null || true
    
    # Backup logs (last 7 days)
    find "$LOG_DIR" -name "*.log" -mtime -7 -exec cp {} "$backup_path/" \; 2>/dev/null || true
    
    log_info "Backup completed at $backup_path"
}

# Restore function
restore() {
    local backup_path=${1:-"${PROJECT_ROOT}/backup"}
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup path not found: $backup_path"
        return 1
    fi
    
    log_info "Restoring from backup at $backup_path..."
    
    # Restore configuration
    cp "$backup_path/.env" "$PROJECT_ROOT/" 2>/dev/null || true
    cp "$backup_path/CLAUDE.md" "$PROJECT_ROOT/" 2>/dev/null || true
    
    # Restore sessions and knowledge
    cp -r "$backup_path/sessions" "$PROJECT_ROOT/" 2>/dev/null || true
    cp -r "$backup_path/knowledge" "$PROJECT_ROOT/" 2>/dev/null || true
    
    log_info "Restore completed"
}

# Main function
main() {
    case "${1:-}" in
        "validate")
            validate
            ;;
        "setup")
            setup
            ;;
        "monitor")
            monitor
            ;;
        "cleanup")
            cleanup "${2:-7}"
            ;;
        "backup")
            backup "${2:-}"
            ;;
        "restore")
            restore "${2:-}"
            ;;
        *)
            echo "Usage: $0 {validate|setup|monitor|cleanup|backup|restore}"
            echo ""
            echo "Commands:"
            echo "  validate         - Validate environment"
            echo "  setup           - Setup Claude Service architecture"
            echo "  monitor         - Start monitoring (background recommended)"
            echo "  cleanup [days]  - Clean files older than N days (default: 7)"
            echo "  backup [path]   - Backup configuration and data"
            echo "  restore [path]  - Restore from backup"
            exit 1
            ;;
    esac
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi