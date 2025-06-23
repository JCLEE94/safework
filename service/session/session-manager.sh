#!/bin/bash
# Claude Service - Session Manager
# Version: 1.0.0

set -euo pipefail

# Source common utilities
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SERVICE_ROOT}/utils/common.sh"

readonly SESSION_LOG="${LOG_DIR}/session.log"

# Session utilities
generate_session_id() {
    echo "${1:-session}-$(date '+%Y%m%d-%H%M%S')-$$"
}

get_session_file() {
    local session_name="$1"
    echo "${SESSION_DIR}/${session_name}.json"
}

session_exists() {
    local session_name="$1"
    [[ -f "$(get_session_file "$session_name")" ]]
}

# Create new session
create() {
    local session_name="${1:-$(generate_session_id)}"
    local project_name="${2:-$(basename "$PROJECT_ROOT")}"
    
    if session_exists "$session_name"; then
        log_error "Session already exists: $session_name"
        return 1
    fi
    
    log_info "Creating session: $session_name"
    
    local session_file=$(get_session_file "$session_name")
    local timestamp=$(date -Iseconds)
    
    cat > "$session_file" << EOF
{
  "session_id": "$session_name",
  "project": "$project_name",
  "created_at": "$timestamp",
  "last_activity": "$timestamp",
  "status": "active",
  "stats": {
    "commands_executed": 0,
    "notifications_sent": 0,
    "errors_handled": 0,
    "uptime_seconds": 0
  },
  "context": {
    "working_directory": "$PROJECT_ROOT",
    "environment": "$(uname -s)",
    "hostname": "$(hostname)",
    "tools_available": {
      "docker": $(command -v docker &>/dev/null && echo "true" || echo "false"),
      "python": $(command -v python3 &>/dev/null && echo "true" || echo "false"),
      "node": $(command -v node &>/dev/null && echo "true" || echo "false"),
      "git": $(command -v git &>/dev/null && echo "true" || echo "false")
    }
  },
  "activity_log": []
}
EOF
    
    log_info "Session created: $session_name" | tee -a "$SESSION_LOG"
    echo "$session_name"
}

# List sessions
list() {
    echo "🗂️ Claude Sessions"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [[ ! -d "$SESSION_DIR" ]] || [[ -z "$(ls -A "$SESSION_DIR" 2>/dev/null)" ]]; then
        echo "📭 No sessions found"
        return 0
    fi
    
    echo "🆔 Session ID                | 📦 Project     | 📊 Commands | 📱 Notifications | 🕐 Status"
    echo "─────────────────────────────┼────────────────┼─────────────┼──────────────────┼──────────"
    
    for session_file in "$SESSION_DIR"/*.json; do
        if [[ -f "$session_file" ]]; then
            local session_data=$(cat "$session_file")
            local session_id=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null || echo "unknown")
            local project=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['project'])" 2>/dev/null || echo "unknown")
            local commands=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['commands_executed'])" 2>/dev/null || echo "0")
            local notifications=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['notifications_sent'])" 2>/dev/null || echo "0")
            local status=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
            
            printf "%-30s │ %-14s │ %-11s │ %-16s │ %s\n" \
                "${session_id:0:30}" \
                "${project:0:14}" \
                "$commands" \
                "$notifications" \
                "$status"
        fi
    done
}

# Show session statistics
stats() {
    local session_name="$1"
    
    if ! session_exists "$session_name"; then
        log_error "Session not found: $session_name"
        return 1
    fi
    
    local session_file=$(get_session_file "$session_name")
    local session_data=$(cat "$session_file")
    
    echo "📊 Session Statistics: $session_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Basic info
    local project=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['project'])" 2>/dev/null || echo "unknown")
    local created_at=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['created_at'])" 2>/dev/null || echo "unknown")
    local status=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
    
    echo "📦 Project: $project"
    echo "🕐 Created: $created_at"
    echo "📊 Status: $status"
    echo ""
    
    # Statistics
    local commands=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['commands_executed'])" 2>/dev/null || echo "0")
    local notifications=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['notifications_sent'])" 2>/dev/null || echo "0")
    local errors=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['errors_handled'])" 2>/dev/null || echo "0")
    local uptime=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['uptime_seconds'])" 2>/dev/null || echo "0")
    
    echo "📈 Activity Statistics:"
    echo "  Commands executed: $commands"
    echo "  Notifications sent: $notifications"
    echo "  Errors handled: $errors"
    echo "  Uptime: ${uptime}s"
    echo ""
    
    # Context info
    local working_dir=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['context']['working_directory'])" 2>/dev/null || echo "unknown")
    local hostname=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['context']['hostname'])" 2>/dev/null || echo "unknown")
    
    echo "🌍 Environment:"
    echo "  Working directory: $working_dir"
    echo "  Hostname: $hostname"
    echo ""
    
    # Tools availability
    echo "🛠️ Tools Available:"
    local tools_available=$(echo "$session_data" | python3 -c "
import sys, json
tools = json.load(sys.stdin)['context']['tools_available']
for tool, available in tools.items():
    status = '✅' if available else '❌'
    print(f'  {status} {tool}')
" 2>/dev/null || echo "  ❓ Unable to parse tools")
    echo "$tools_available"
}

# Update session activity
update_activity() {
    local session_name="$1"
    local activity_type="$2"
    local description="${3:-$activity_type}"
    
    if ! session_exists "$session_name"; then
        log_error "Session not found: $session_name"
        return 1
    fi
    
    local session_file=$(get_session_file "$session_name")
    local timestamp=$(date -Iseconds)
    
    # Update session with Python (safer JSON manipulation)
    python3 << EOF
import json
import sys
from datetime import datetime

session_file = "$session_file"
activity_type = "$activity_type"
description = "$description"
timestamp = "$timestamp"

try:
    with open(session_file, 'r') as f:
        session_data = json.load(f)
    
    # Update last activity
    session_data['last_activity'] = timestamp
    
    # Update stats
    if activity_type == 'command':
        session_data['stats']['commands_executed'] += 1
    elif activity_type == 'notification':
        session_data['stats']['notifications_sent'] += 1
    elif activity_type == 'error':
        session_data['stats']['errors_handled'] += 1
    
    # Add to activity log (keep last 50 entries)
    if 'activity_log' not in session_data:
        session_data['activity_log'] = []
    
    session_data['activity_log'].append({
        'timestamp': timestamp,
        'type': activity_type,
        'description': description
    })
    
    # Keep only last 50 activities
    session_data['activity_log'] = session_data['activity_log'][-50:]
    
    # Save updated session
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print(f"Updated session {session_data['session_id']}: {activity_type}")
    
except Exception as e:
    print(f"Error updating session: {e}", file=sys.stderr)
    sys.exit(1)
EOF
}

# Analytics overview
analytics() {
    echo "📊 Session Analytics"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if [[ ! -d "$SESSION_DIR" ]] || [[ -z "$(ls -A "$SESSION_DIR" 2>/dev/null)" ]]; then
        echo "📭 No session data available"
        return 0
    fi
    
    local total_sessions=0
    local total_commands=0
    local total_notifications=0
    local total_errors=0
    local active_sessions=0
    
    for session_file in "$SESSION_DIR"/*.json; do
        if [[ -f "$session_file" ]]; then
            ((total_sessions++))
            
            local session_data=$(cat "$session_file")
            local commands=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['commands_executed'])" 2>/dev/null || echo "0")
            local notifications=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['notifications_sent'])" 2>/dev/null || echo "0")
            local errors=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['stats']['errors_handled'])" 2>/dev/null || echo "0")
            local status=$(echo "$session_data" | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null || echo "unknown")
            
            total_commands=$((total_commands + commands))
            total_notifications=$((total_notifications + notifications))
            total_errors=$((total_errors + errors))
            
            if [[ "$status" == "active" ]]; then
                ((active_sessions++))
            fi
        fi
    done
    
    echo "📈 Overall Statistics:"
    echo "  Total sessions: $total_sessions"
    echo "  Active sessions: $active_sessions"
    echo "  Total commands: $total_commands"
    echo "  Total notifications: $total_notifications"
    echo "  Total errors handled: $total_errors"
    
    if [[ $total_sessions -gt 0 ]]; then
        echo ""
        echo "📊 Averages per session:"
        echo "  Commands: $((total_commands / total_sessions))"
        echo "  Notifications: $((total_notifications / total_sessions))"
        echo "  Errors: $((total_errors / total_sessions))"
    fi
}

# Cleanup old sessions
cleanup() {
    local days="${1:-7}"
    log_info "Cleaning up sessions older than $days days..."
    
    local cleaned=0
    for session_file in "$SESSION_DIR"/*.json; do
        if [[ -f "$session_file" ]] && [[ $(find "$session_file" -mtime +$days) ]]; then
            local session_name=$(basename "$session_file" .json)
            log_info "Removing old session: $session_name"
            rm -f "$session_file"
            ((cleaned++))
        fi
    done
    
    log_info "Cleaned up $cleaned old sessions" | tee -a "$SESSION_LOG"
}

# Main function
main() {
    case "${1:-}" in
        "create")
            create "${2:-}" "${3:-}"
            ;;
        "list")
            list
            ;;
        "stats")
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 stats <session_name>"
                exit 1
            fi
            stats "$2"
            ;;
        "update")
            if [[ -z "${2:-}" ]] || [[ -z "${3:-}" ]]; then
                echo "Usage: $0 update <session_name> <activity_type> [description]"
                exit 1
            fi
            update_activity "$2" "$3" "${4:-}"
            ;;
        "analytics")
            analytics
            ;;
        "cleanup")
            cleanup "${2:-7}"
            ;;
        "help"|"")
            echo "Usage: $0 {create|list|stats|update|analytics|cleanup}"
            echo ""
            echo "Commands:"
            echo "  create [name] [project]        - Create new session"
            echo "  list                          - List all sessions"
            echo "  stats <session_name>          - Show session statistics"
            echo "  update <session> <type> [desc] - Update session activity"
            echo "  analytics                     - Show analytics overview"
            echo "  cleanup [days]               - Clean sessions older than N days"
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