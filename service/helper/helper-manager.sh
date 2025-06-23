#!/bin/bash
# Claude Service - Helper Manager (Inter-Session Assistance)
# Version: 1.0.0

set -euo pipefail

# Source common utilities
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SERVICE_ROOT}/utils/common.sh"

readonly HELPER_LOG="${LOG_DIR}/helper.log"
readonly HELP_CONTEXT_FILE="${KNOWLEDGE_DIR}/help_context.json"

# Initialize knowledge base
init_knowledge() {
    if [[ ! -f "$HELP_CONTEXT_FILE" ]]; then
        cat > "$HELP_CONTEXT_FILE" << 'EOF'
{
  "environment": {
    "project_type": "health_management_system",
    "stack": "FastAPI + React + PostgreSQL + Docker",
    "service_architecture": "Claude Service v1.0",
    "common_commands": {
      "service_control": "./service/core/service-manager.sh start|stop|status",
      "session_management": "./service/session/session-manager.sh create|list|stats",
      "notifications": "./service/notification/notification-manager.sh send|test",
      "docker_dev": "docker-compose up -d",
      "docker_logs": "docker logs health-management-system",
      "health_check": "curl http://localhost:3001/health"
    },
    "frequent_issues": {
      "port_conflict": "lsof -t -i:3000 | xargs kill -9",
      "docker_cleanup": "docker system prune -af",
      "permission_issues": "chmod +x service/*/*.sh",
      "build_failures": "npm install && npm run build"
    }
  },
  "deployment_templates": {
    "dockerfile": "Multi-stage with Python + Node.js support",
    "docker_compose": "PostgreSQL + Redis + App containers",
    "health_endpoints": "/health and /api/health",
    "environment_vars": "DATABASE_URL, REDIS_URL, TELEGRAM_CLAUDE_TOKEN"
  },
  "best_practices": [
    "Always use Docker for development",
    "Test health endpoints before deployment",
    "Update session tracking with helper system",
    "Use notification system for critical alerts",
    "Run cleanup commands regularly"
  ]
}
EOF
        log_info "Knowledge base initialized"
    fi
}

# Provide context to a session
context() {
    local session_name="${1:-}"
    local query="${2:-general}"
    
    if [[ -z "$session_name" ]]; then
        echo "Usage: $0 context <session_name> [query]"
        return 1
    fi
    
    log_info "Providing context to session: $session_name (query: $query)" | tee -a "$HELPER_LOG"
    
    init_knowledge
    
    echo "🤖 Claude Helper - Context for Session: $session_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Project overview
    echo "📦 Project Overview:"
    echo "  Type: SafeWork Pro (건설업 보건관리 시스템)"
    echo "  Stack: FastAPI + React + PostgreSQL + Docker"
    echo "  Architecture: Modular Claude Service v1.0"
    echo "  Current Dir: $PROJECT_ROOT"
    echo ""
    
    # Environment status
    echo "🌍 Environment Status:"
    echo "  Hostname: $(hostname)"
    echo "  Working Dir: $PROJECT_ROOT"
    echo "  Service Status: $(if "${SERVICE_ROOT}/core/service-manager.sh" status &>/dev/null; then echo "✅ Running"; else echo "❌ Stopped"; fi)"
    echo ""
    
    # Available tools
    echo "🛠️ Available Tools:"
    echo "  ✅ Docker: $(docker --version 2>/dev/null | cut -d' ' -f3 | tr -d ',' || echo "Not available")"
    echo "  ✅ Python: $(python3 --version 2>/dev/null | cut -d' ' -f2 || echo "Not available")"
    echo "  ✅ Node.js: $(node --version 2>/dev/null || echo "Not available")"
    echo "  ✅ Git: $(git --version 2>/dev/null | cut -d' ' -f3 || echo "Not available")"
    echo ""
    
    # Service modules
    echo "🔧 Claude Service Modules:"
    for module in core session notification helper utils; do
        local module_path="${SERVICE_ROOT}/${module}"
        if [[ -d "$module_path" ]]; then
            echo "  ✅ $module: Available at $module_path"
        else
            echo "  ❌ $module: Missing"
        fi
    done
    echo ""
    
    # Common commands based on query
    case "$query" in
        "deployment"|"deploy")
            echo "🚀 Deployment Commands:"
            echo "  ./deploy.sh health              # Full deployment"
            echo "  docker-compose up -d           # Start containers"
            echo "  docker logs health-app          # Check logs"
            echo "  curl http://localhost:3001/health # Health check"
            ;;
        "pdf"|"documents")
            echo "📄 PDF Document System:"
            echo "  Current forms: 4 Korean construction forms supported"
            echo "  PDF templates: document/ directory"
            echo "  Form handler: src/handlers/documents.py"
            echo "  Test endpoint: /api/v1/documents/fill-pdf/{form_name}"
            ;;
        "database"|"db")
            echo "🗄️ Database Commands:"
            echo "  python init_db.py              # Initialize database"
            echo "  docker exec -it postgres psql   # Access database"
            echo "  Check connection: DATABASE_URL in .env"
            ;;
        *)
            echo "🔄 Common Commands:"
            echo "  Service: ./service/core/service-manager.sh start"
            echo "  Session: ./service/session/session-manager.sh create $session_name"
            echo "  Notify:  ./service/notification/notification-manager.sh test"
            echo "  Docker:  docker-compose up -d"
            echo "  Health:  curl http://localhost:3001/health"
            ;;
    esac
    echo ""
    
    # Quick fixes
    echo "💡 Quick Fixes:"
    echo "  Port conflict: lsof -t -i:3000 | xargs kill -9"
    echo "  Docker cleanup: docker system prune -af"
    echo "  Permission fix: chmod +x service/*/*.sh"
    echo "  Build fix: npm install && npm run build"
    echo ""
    
    # Update session
    "${SERVICE_ROOT}/session/session-manager.sh" update "$session_name" "helper" "Context provided: $query" 2>/dev/null || true
    
    log_info "Context provided to session: $session_name"
}

# Assist with deployment
assist_deploy() {
    local session_name="${1:-}"
    
    if [[ -z "$session_name" ]]; then
        echo "Usage: $0 assist-deploy <session_name>"
        return 1
    fi
    
    log_info "Assisting deployment for session: $session_name" | tee -a "$HELPER_LOG"
    
    echo "🚀 Claude Helper - Deployment Assistance"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    local files_created=0
    
    # Check and create missing files
    echo "📋 Checking deployment files..."
    
    # 1. Check docker-compose.yml
    if [[ ! -f "${PROJECT_ROOT}/docker-compose.yml" ]]; then
        echo "  ❌ docker-compose.yml missing - creating basic template"
        cat > "${PROJECT_ROOT}/docker-compose.yml" << 'EOF'
version: '3.8'
services:
  health-app:
    build: .
    ports:
      - "3001:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./dist:/app/dist
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: health_management
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

volumes:
  postgres_data:
EOF
        ((files_created++))
    else
        echo "  ✅ docker-compose.yml exists"
    fi
    
    # 2. Check Dockerfile
    if [[ ! -f "${PROJECT_ROOT}/Dockerfile" ]]; then
        echo "  ❌ Dockerfile missing - creating optimized template"
        cat > "${PROJECT_ROOT}/Dockerfile" << 'EOF'
# Multi-stage build for FastAPI + React
FROM node:18-alpine AS frontend
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM python:3.11-alpine AS backend
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    postgresql-dev \
    curl

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY --from=frontend /app/dist ./dist

# Create non-root user
RUN adduser -D -s /bin/sh app
RUN chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["python", "main.py"]
EOF
        ((files_created++))
    else
        echo "  ✅ Dockerfile exists"
    fi
    
    # 3. Check deploy script
    if [[ ! -f "${PROJECT_ROOT}/deploy.sh" ]]; then
        echo "  ❌ deploy.sh missing - creating deployment script"
        cat > "${PROJECT_ROOT}/deploy.sh" << 'EOF'
#!/bin/bash
set -e

PROJECT_NAME=${1:-health}
VERSION=$(date +%Y%m%d-%H%M%S)

echo "🚀 Deploying $PROJECT_NAME (version: $VERSION)"

# Build and test
echo "🧪 Testing..."
docker-compose -f docker-compose.yml build
docker-compose up -d

# Health check
echo "🏥 Health check..."
sleep 10
curl -f http://localhost:3001/health

echo "✅ Deployment successful!"
EOF
        chmod +x "${PROJECT_ROOT}/deploy.sh"
        ((files_created++))
    else
        echo "  ✅ deploy.sh exists"
    fi
    
    # 4. Check health endpoint
    echo ""
    echo "🏥 Checking health endpoints..."
    if curl -f http://localhost:3001/health &>/dev/null; then
        echo "  ✅ Health endpoint responding"
    else
        echo "  ⚠️  Health endpoint not responding (service may be stopped)"
    fi
    
    # 5. Environment check
    echo ""
    echo "🌍 Environment check..."
    if [[ -f "${PROJECT_ROOT}/.env" ]]; then
        echo "  ✅ .env file exists"
        if grep -q "DATABASE_URL" "${PROJECT_ROOT}/.env"; then
            echo "  ✅ DATABASE_URL configured"
        else
            echo "  ⚠️  DATABASE_URL missing in .env"
        fi
    else
        echo "  ❌ .env file missing"
    fi
    
    # Summary
    echo ""
    echo "📊 Deployment Assistance Summary:"
    echo "  Files created: $files_created"
    echo "  Ready for deployment: $(if [[ $files_created -eq 0 ]]; then echo "✅ Yes"; else echo "⚠️  Check new files"; fi)"
    echo ""
    
    # Next steps
    echo "🎯 Next Steps:"
    echo "  1. Review created files"
    echo "  2. Update .env with correct values"
    echo "  3. Run: ./deploy.sh health"
    echo "  4. Test: curl http://localhost:3001/health"
    echo ""
    
    # Update session
    "${SERVICE_ROOT}/session/session-manager.sh" update "$session_name" "helper" "Deployment assistance: $files_created files created" 2>/dev/null || true
    
    # Send notification
    "${SERVICE_ROOT}/notification/notification-manager.sh" send "Deployment assistance completed for $session_name ($files_created files created)" "SUCCESS" "$session_name" 2>/dev/null || true
    
    log_info "Deployment assistance completed for session: $session_name"
}

# Auto-assist (analyze and help automatically)
auto_assist() {
    local session_name="${1:-}"
    
    if [[ -z "$session_name" ]]; then
        echo "Usage: $0 auto-assist <session_name>"
        return 1
    fi
    
    log_info "Auto-assisting session: $session_name" | tee -a "$HELPER_LOG"
    
    echo "🤖 Claude Helper - Auto Assistance for: $session_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Analyze current situation
    echo "🔍 Analyzing current situation..."
    
    # Check if service is running
    if ! "${SERVICE_ROOT}/core/service-manager.sh" status &>/dev/null; then
        echo "  ⚠️  Service not running - starting service"
        "${SERVICE_ROOT}/core/service-manager.sh" start
    fi
    
    # Check for common issues
    local issues_found=0
    
    # 1. Port conflicts
    if lsof -ti:3000 &>/dev/null; then
        echo "  ⚠️  Port 3000 conflict detected"
        echo "     Fix: lsof -t -i:3000 | xargs kill -9"
        ((issues_found++))
    fi
    
    # 2. Docker issues
    if ! docker info &>/dev/null; then
        echo "  ❌ Docker not available"
        ((issues_found++))
    fi
    
    # 3. Missing directories
    for dir in logs uploads dist; do
        if [[ ! -d "${PROJECT_ROOT}/$dir" ]]; then
            echo "  ⚠️  Missing directory: $dir - creating"
            mkdir -p "${PROJECT_ROOT}/$dir"
            ((issues_found++))
        fi
    done
    
    # 4. Permission issues
    if [[ ! -x "${SERVICE_ROOT}/core/service-manager.sh" ]]; then
        echo "  ⚠️  Permission issues detected - fixing"
        chmod +x "${SERVICE_ROOT}"/*/*.sh
        ((issues_found++))
    fi
    
    # Provide recommendations
    echo ""
    echo "💡 Recommendations:"
    if [[ $issues_found -eq 0 ]]; then
        echo "  ✅ No issues detected - system looks healthy"
        echo "  🚀 Ready for development or deployment"
    else
        echo "  🔧 $issues_found issues detected and addressed"
        echo "  🔄 Consider running health check: ./service/core/service-manager.sh health"
    fi
    
    # Update session
    "${SERVICE_ROOT}/session/session-manager.sh" update "$session_name" "helper" "Auto-assistance: $issues_found issues addressed" 2>/dev/null || true
    
    log_info "Auto-assistance completed for session: $session_name ($issues_found issues)"
}

# Share knowledge between sessions
share_knowledge() {
    local from_session="$1"
    local to_session="$2"
    
    if [[ -z "$from_session" ]] || [[ -z "$to_session" ]]; then
        echo "Usage: $0 share-knowledge <from_session> <to_session>"
        return 1
    fi
    
    log_info "Sharing knowledge from $from_session to $to_session" | tee -a "$HELPER_LOG"
    
    echo "📚 Claude Helper - Knowledge Transfer"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "From: $from_session → To: $to_session"
    echo ""
    
    # Check if source session exists
    local from_file="${SESSION_DIR}/${from_session}.json"
    if [[ ! -f "$from_file" ]]; then
        echo "❌ Source session not found: $from_session"
        return 1
    fi
    
    # Extract knowledge from source session
    echo "📖 Extracting knowledge from $from_session..."
    
    # Get session statistics
    local commands_executed=$(python3 -c "
import json
with open('$from_file') as f:
    data = json.load(f)
    print(data['stats']['commands_executed'])
" 2>/dev/null || echo "0")
    
    local successful_activities=$(python3 -c "
import json
with open('$from_file') as f:
    data = json.load(f)
    activities = data.get('activity_log', [])
    successful = [a for a in activities if 'error' not in a['description'].lower()]
    for activity in successful[-5:]:  # Last 5 successful activities
        print(f\"  ✅ {activity['type']}: {activity['description']}\")
" 2>/dev/null || echo "  📭 No activity log available")
    
    echo "📊 Source session stats:"
    echo "  Commands executed: $commands_executed"
    echo "  Recent successful activities:"
    echo "$successful_activities"
    echo ""
    
    # Transfer knowledge to target session
    echo "📤 Transferring knowledge to $to_session..."
    
    # Update target session with knowledge
    "${SERVICE_ROOT}/session/session-manager.sh" update "$to_session" "helper" "Knowledge transfer from $from_session: $commands_executed commands experience" 2>/dev/null || true
    
    # Provide context to target session
    context "$to_session" "knowledge-transfer"
    
    echo "✅ Knowledge transfer completed successfully!"
    
    log_info "Knowledge transfer completed: $from_session → $to_session"
}

# Helper dashboard
dashboard() {
    echo "🤖 Claude Helper Dashboard"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Helper statistics
    if [[ -f "$HELPER_LOG" ]]; then
        local total_assists=$(wc -l < "$HELPER_LOG")
        local today_assists=$(grep "$(date '+%Y-%m-%d')" "$HELPER_LOG" | wc -l)
        
        echo "📊 Helper Statistics:"
        echo "  Total assists: $total_assists"
        echo "  Today's assists: $today_assists"
        echo ""
    fi
    
    # Knowledge base status
    echo "📚 Knowledge Base:"
    if [[ -f "$HELP_CONTEXT_FILE" ]]; then
        echo "  ✅ Context file: Available"
        local kb_size=$(wc -c < "$HELP_CONTEXT_FILE")
        echo "  📏 Size: ${kb_size} bytes"
    else
        echo "  ❌ Context file: Missing (will be created on first use)"
    fi
    echo ""
    
    # Active sessions that might need help
    echo "🆘 Sessions Needing Assistance:"
    if [[ -d "$SESSION_DIR" ]]; then
        local help_needed=0
        for session_file in "$SESSION_DIR"/*.json; do
            if [[ -f "$session_file" ]]; then
                local session_name=$(basename "$session_file" .json)
                local errors=$(python3 -c "
import json
with open('$session_file') as f:
    data = json.load(f)
    print(data['stats']['errors_handled'])
" 2>/dev/null || echo "0")
                
                if [[ $errors -gt 0 ]]; then
                    echo "  ⚠️  $session_name: $errors errors"
                    ((help_needed++))
                fi
            fi
        done
        
        if [[ $help_needed -eq 0 ]]; then
            echo "  ✅ All sessions appear healthy"
        fi
    else
        echo "  📭 No sessions directory found"
    fi
    echo ""
    
    # Quick helper commands
    echo "🛠️ Quick Helper Commands:"
    echo "  ./service/helper/helper-manager.sh context <session>"
    echo "  ./service/helper/helper-manager.sh assist-deploy <session>"
    echo "  ./service/helper/helper-manager.sh auto-assist <session>"
    echo "  ./service/helper/helper-manager.sh share-knowledge <from> <to>"
}

# Main function
main() {
    case "${1:-}" in
        "context")
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 context <session_name> [query]"
                exit 1
            fi
            context "$2" "${3:-general}"
            ;;
        "assist-deploy")
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 assist-deploy <session_name>"
                exit 1
            fi
            assist_deploy "$2"
            ;;
        "auto-assist")
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 auto-assist <session_name>"
                exit 1
            fi
            auto_assist "$2"
            ;;
        "share-knowledge")
            if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]]; then
                echo "Usage: $0 share-knowledge <from_session> <to_session>"
                exit 1
            fi
            share_knowledge "$2" "$3"
            ;;
        "dashboard")
            dashboard
            ;;
        "help"|"")
            echo "Usage: $0 {context|assist-deploy|auto-assist|share-knowledge|dashboard}"
            echo ""
            echo "Commands:"
            echo "  context <session> [query]      - Provide context to session"
            echo "  assist-deploy <session>        - Help with deployment setup"
            echo "  auto-assist <session>          - Analyze and auto-help"
            echo "  share-knowledge <from> <to>    - Transfer knowledge between sessions"
            echo "  dashboard                      - Show helper dashboard"
            echo ""
            echo "Queries for context:"
            echo "  general, deployment, pdf, database"
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