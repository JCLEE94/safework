#!/bin/bash
set -euo pipefail

# Claude Code OAuth Status Check with Tests
# This script verifies OAuth authentication for Claude Code

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test: Check OAuth status
test_oauth_status() {
    echo "🔐 Checking Claude Code OAuth status..."
    
    if ! command -v claude &> /dev/null; then
        echo -e "${RED}❌ Claude Code not installed${NC}"
        return 2
    fi
    
    if claude auth status &>/dev/null; then
        echo -e "${GREEN}✅ OAuth authenticated${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ OAuth authentication required${NC}"
        return 1
    fi
}

# Test: Verify API access
test_api_access() {
    echo "🔍 Testing Claude API access..."
    
    # Simple API test (adjust based on actual Claude CLI capabilities)
    if claude --version &>/dev/null; then
        echo -e "${GREEN}✅ Claude CLI responsive${NC}"
        return 0
    else
        echo -e "${RED}❌ Claude CLI not responding${NC}"
        return 1
    fi
}

# Test: Check token expiration (if applicable)
test_token_validity() {
    echo "🕐 Checking token validity..."
    
    # This is a placeholder - adjust based on actual Claude CLI token management
    # For now, we'll assume if auth status passes, token is valid
    if claude auth status &>/dev/null; then
        echo -e "${GREEN}✅ Authentication token valid${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Token may be expired or invalid${NC}"
        return 1
    fi
}

# Handle OAuth setup failure
handle_oauth_failure() {
    echo -e "${RED}❌ Claude Code OAuth Setup Required${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "⚠️ OAuth authentication is not configured"
    echo ""
    echo "To fix this on the self-hosted runner:"
    echo "1. SSH into the runner machine"
    echo "2. Run: claude auth login"
    echo "3. Follow the authentication prompts"
    echo "4. Re-run this workflow"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Self-test runner
run_tests() {
    echo "🧪 Running OAuth validation tests..."
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: OAuth status
    if test_oauth_status; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    # Test 2: API access
    if test_api_access; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    # Test 3: Token validity
    if test_token_validity; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo "📊 Test Results: $tests_passed passed, $tests_failed failed"
    
    if [ $tests_failed -eq 0 ]; then
        echo -e "${GREEN}✅ All OAuth tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ OAuth tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo "🔐 Claude Code OAuth Validation"
    echo "==============================="
    
    # Check if Claude is installed first
    if ! command -v claude &> /dev/null; then
        echo -e "${RED}❌ Claude Code not installed${NC}"
        echo "Please run install-claude.sh first"
        exit 2
    fi
    
    # Run OAuth tests
    if run_tests; then
        echo -e "${GREEN}✅ OAuth validation successful${NC}"
        oauth_ready=true
    else
        handle_oauth_failure
        oauth_ready=false
        exit_code=1
    fi
    
    # Set output for GitHub Actions
    if [ -n "${GITHUB_OUTPUT:-}" ]; then
        echo "oauth_ready=$oauth_ready" >> $GITHUB_OUTPUT
    fi
    
    # Exit with appropriate code
    exit ${exit_code:-0}
}

# Execute main function
main "$@"