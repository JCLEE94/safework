#!/bin/bash
# Claude Service - Notification Manager
# Version: 1.0.0

set -euo pipefail

# Source common utilities
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SERVICE_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SERVICE_ROOT}/utils/common.sh"

readonly NOTIFICATION_LOG="${LOG_DIR}/notification.log"

# Load environment variables
if [[ -f "${PROJECT_ROOT}/.env" ]]; then
    source "${PROJECT_ROOT}/.env"
fi

# Severity levels with emojis
get_severity_emoji() {
    case "${1:-INFO}" in
        "CRITICAL") echo "🚨🔥" ;;
        "ERROR")    echo "❌" ;;
        "WARNING")  echo "⚠️" ;;
        "INFO")     echo "ℹ️" ;;
        "SUCCESS")  echo "✅" ;;
        "DEBUG")    echo "🐛" ;;
        *)          echo "📝" ;;
    esac
}

# Send notification
send() {
    local message="$1"
    local severity="${2:-INFO}"
    local session_name="${3:-}"
    
    local emoji=$(get_severity_emoji "$severity")
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local project_name=$(basename "$PROJECT_ROOT")
    local hostname=$(hostname)
    
    # Log notification
    log_info "Sending notification: [$severity] $message" | tee -a "$NOTIFICATION_LOG"
    
    # Update session if provided
    if [[ -n "$session_name" ]]; then
        "${SERVICE_ROOT}/session/session-manager.sh" update "$session_name" "notification" "$message" 2>/dev/null || true
    fi
    
    # Send to Telegram if token is available
    if [[ -n "${TELEGRAM_CLAUDE_TOKEN:-}" ]]; then
        send_telegram "$message" "$severity"
    else
        log_info "Telegram token not configured, notification logged only"
    fi
    
    # Send to system log
    logger -t "claude-notify" "[$severity] $message"
    
    return 0
}

# Send Telegram notification
send_telegram() {
    local message="$1"
    local severity="${2:-INFO}"
    
    if [[ -z "${TELEGRAM_CLAUDE_TOKEN:-}" ]]; then
        log_error "TELEGRAM_CLAUDE_TOKEN not set"
        return 1
    fi
    
    local emoji=$(get_severity_emoji "$severity")
    local project_name=$(basename "$PROJECT_ROOT")
    local hostname=$(hostname)
    local timestamp=$(date '+%H:%M:%S')
    
    local full_message="${emoji} *${severity}*
${message}

🚀 ${project_name} | 🖥️ ${hostname} | 🕐 ${timestamp}"
    
    # Send via Python for better error handling
    python3 << EOF
import requests
import os
import json
import sys

token = os.environ.get('TELEGRAM_CLAUDE_TOKEN', '')
if not token:
    print('ERROR: TELEGRAM_CLAUDE_TOKEN not set', file=sys.stderr)
    sys.exit(1)

message = '''$full_message'''

try:
    # Get chat ID from recent updates
    updates_url = f'https://api.telegram.org/bot{token}/getUpdates'
    updates_resp = requests.get(updates_url, timeout=10)
    updates_data = updates_resp.json()
    
    if updates_data.get('ok') and updates_data.get('result'):
        # Use most recent chat ID
        latest_update = updates_data['result'][-1]
        chat_id = latest_update['message']['chat']['id']
        
        # Send message
        send_url = f'https://api.telegram.org/bot{token}/sendMessage'
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown',
            'disable_notification': False
        }
        
        response = requests.post(send_url, data=data, timeout=10)
        if response.json().get('ok'):
            print('✅ Telegram notification sent successfully')
        else:
            print(f'❌ Telegram send failed: {response.text}', file=sys.stderr)
            sys.exit(1)
    else:
        print('⚠️ Please start a conversation with the bot first (/start)', file=sys.stderr)
        sys.exit(1)
        
except Exception as e:
    print(f'❌ Telegram API error: {e}', file=sys.stderr)
    sys.exit(1)
EOF
    
    if [[ $? -eq 0 ]]; then
        log_info "Telegram notification sent successfully"
    else
        log_error "Failed to send Telegram notification"
        return 1
    fi
}

# Test notification system
test() {
    echo "🧪 Testing Claude Notification System"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Test configuration
    if [[ -n "${TELEGRAM_CLAUDE_TOKEN:-}" ]]; then
        echo "✅ Telegram token configured"
    else
        echo "❌ Telegram token not configured"
        echo "   Add TELEGRAM_CLAUDE_TOKEN to .env file"
        return 1
    fi
    
    # Test notification levels
    echo ""
    echo "📤 Testing notification levels..."
    
    local test_levels=("INFO" "SUCCESS" "WARNING" "ERROR")
    for level in "${test_levels[@]}"; do
        echo "  Testing $level level..."
        send "Test notification - $level level" "$level" "test-session"
        sleep 1
    done
    
    echo ""
    echo "🎉 Notification test completed!"
    echo "Check your Telegram bot for test messages."
}

# Show dashboard
dashboard() {
    echo "📱 Notification Dashboard"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📅 $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    
    # Configuration status
    echo "⚙️ Configuration:"
    if [[ -n "${TELEGRAM_CLAUDE_TOKEN:-}" ]]; then
        echo "  ✅ Telegram: Configured"
    else
        echo "  ❌ Telegram: Not configured"
    fi
    echo ""
    
    # Recent notifications
    echo "📋 Recent Notifications (last 10):"
    if [[ -f "$NOTIFICATION_LOG" ]]; then
        tail -10 "$NOTIFICATION_LOG" | while read -r line; do
            echo "  $line"
        done
    else
        echo "  📭 No notifications logged yet"
    fi
    echo ""
    
    # Statistics
    if [[ -f "$NOTIFICATION_LOG" ]]; then
        local total_notifications=$(wc -l < "$NOTIFICATION_LOG")
        local today_notifications=$(grep "$(date '+%Y-%m-%d')" "$NOTIFICATION_LOG" | wc -l)
        
        echo "📊 Statistics:"
        echo "  Total notifications: $total_notifications"
        echo "  Today's notifications: $today_notifications"
        
        # Count by severity
        echo ""
        echo "📈 By Severity (today):"
        for level in CRITICAL ERROR WARNING INFO SUCCESS DEBUG; do
            local count=$(grep "$(date '+%Y-%m-%d')" "$NOTIFICATION_LOG" | grep -c "\[$level\]" || echo "0")
            local emoji=$(get_severity_emoji "$level")
            if [[ $count -gt 0 ]]; then
                echo "  $emoji $level: $count"
            fi
        done
    fi
}

# Broadcast to all active sessions
broadcast() {
    local message="$1"
    local severity="${2:-INFO}"
    
    log_info "Broadcasting message: $message"
    
    # Send to all active sessions
    if [[ -d "$SESSION_DIR" ]]; then
        for session_file in "$SESSION_DIR"/*.json; do
            if [[ -f "$session_file" ]]; then
                local session_name=$(basename "$session_file" .json)
                send "$message" "$severity" "$session_name"
            fi
        done
    fi
    
    # Also send without session tracking
    send "[BROADCAST] $message" "$severity"
}

# Cleanup old logs
cleanup() {
    local days="${1:-30}"
    log_info "Cleaning up notification logs older than $days days..."
    
    if [[ -f "$NOTIFICATION_LOG" ]]; then
        # Keep only recent lines (last 1000 lines or within date range)
        local temp_log="${NOTIFICATION_LOG}.tmp"
        local cutoff_date=$(date -d "$days days ago" '+%Y-%m-%d')
        
        awk -v cutoff="$cutoff_date" '$0 ~ cutoff {found=1} found {print}' "$NOTIFICATION_LOG" > "$temp_log"
        
        # If temp file is significantly smaller, use it
        if [[ -s "$temp_log" ]]; then
            mv "$temp_log" "$NOTIFICATION_LOG"
            log_info "Notification log cleaned up"
        else
            rm -f "$temp_log"
            log_info "No old entries to clean up"
        fi
    fi
}

# Setup Telegram bot
setup_telegram() {
    echo "📱 Telegram Bot Setup"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "1. Create a Telegram bot:"
    echo "   - Message @BotFather on Telegram"
    echo "   - Send: /newbot"
    echo "   - Follow instructions to create your bot"
    echo "   - Copy the bot token"
    echo ""
    echo "2. Add token to .env file:"
    echo "   TELEGRAM_CLAUDE_TOKEN=your_bot_token_here"
    echo ""
    echo "3. Start conversation with your bot:"
    echo "   - Find your bot in Telegram"
    echo "   - Send: /start"
    echo ""
    echo "4. Test the setup:"
    echo "   ./service/notification/notification-manager.sh test"
    echo ""
    
    if [[ -n "${TELEGRAM_CLAUDE_TOKEN:-}" ]]; then
        echo "✅ Token is already configured in .env"
        echo "Test with: ./service/notification/notification-manager.sh test"
    else
        echo "❌ Token not found in .env"
        echo "Please add TELEGRAM_CLAUDE_TOKEN to your .env file"
    fi
}

# Main function
main() {
    case "${1:-}" in
        "send")
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 send <message> [severity] [session]"
                exit 1
            fi
            send "$2" "${3:-INFO}" "${4:-}"
            ;;
        "test")
            test
            ;;
        "dashboard")
            dashboard
            ;;
        "broadcast")
            if [[ -z "${2:-}" ]]; then
                echo "Usage: $0 broadcast <message> [severity]"
                exit 1
            fi
            broadcast "$2" "${3:-INFO}"
            ;;
        "cleanup")
            cleanup "${2:-30}"
            ;;
        "setup")
            setup_telegram
            ;;
        "help"|"")
            echo "Usage: $0 {send|test|dashboard|broadcast|cleanup|setup}"
            echo ""
            echo "Commands:"
            echo "  send <msg> [severity] [session]  - Send notification"
            echo "  test                            - Test notification system"
            echo "  dashboard                       - Show notification dashboard"
            echo "  broadcast <msg> [severity]      - Broadcast to all sessions"
            echo "  cleanup [days]                  - Clean logs older than N days"
            echo "  setup                          - Setup Telegram bot"
            echo ""
            echo "Severity levels: CRITICAL, ERROR, WARNING, INFO, SUCCESS, DEBUG"
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