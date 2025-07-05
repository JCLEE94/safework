#!/bin/bash
set -euo pipefail

# Claude Code Installation Script with Tests
# This script handles Claude Code CLI installation for CI/CD pipeline

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test: Check if Claude is already installed
test_claude_exists() {
    if command -v claude &> /dev/null; then
        echo -e "${GREEN}✅ Claude Code CLI found: $(which claude)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Claude Code CLI not found${NC}"
        return 1
    fi
}

# Test: Verify Claude version
test_claude_version() {
    if command -v claude &> /dev/null; then
        local version=$(claude --version 2>/dev/null || echo "Unknown")
        echo -e "${GREEN}✅ Claude version: $version${NC}"
        return 0
    else
        echo -e "${RED}❌ Cannot check Claude version${NC}"
        return 1
    fi
}

# Install Claude via npm
install_claude_npm() {
    echo "🔧 Installing Claude Code via npm..."
    if command -v npm &> /dev/null; then
        npm install -g @anthropic/claude-code || {
            echo -e "${RED}❌ npm installation failed${NC}"
            return 1
        }
    else
        echo -e "${RED}❌ npm not available${NC}"
        return 1
    fi
}

# Install Claude via direct download
install_claude_direct() {
    echo "🔧 Installing Claude Code via direct download..."
    curl -fsSL https://claude.ai/install.sh | bash || {
        echo -e "${RED}❌ Direct installation failed${NC}"
        return 1
    }
}

# Main installation function
install_claude() {
    echo "📦 Starting Claude Code installation..."
    
    # Try npm first
    if install_claude_npm; then
        echo -e "${GREEN}✅ Claude installed via npm${NC}"
        return 0
    fi
    
    # Fallback to direct download
    if install_claude_direct; then
        echo -e "${GREEN}✅ Claude installed via direct download${NC}"
        return 0
    fi
    
    echo -e "${RED}❌ All installation methods failed${NC}"
    return 1
}

# Self-test function
run_tests() {
    echo "🧪 Running Claude installation tests..."
    local tests_passed=0
    local tests_failed=0
    
    # Test 1: Claude existence
    if test_claude_exists; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    # Test 2: Claude version check
    if test_claude_version; then
        ((tests_passed++))
    else
        ((tests_failed++))
    fi
    
    echo "📊 Test Results: $tests_passed passed, $tests_failed failed"
    
    if [ $tests_failed -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        return 0
    else
        echo -e "${RED}❌ Some tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo "🔍 Claude Code Installation Check"
    echo "=================================="
    
    # Check if already installed
    if test_claude_exists; then
        echo "✅ Claude Code already installed"
        
        # Check for updates
        if command -v npm &> /dev/null; then
            echo "🔄 Checking for updates..."
            npm outdated -g @anthropic/claude-code || true
        fi
    else
        # Install Claude
        if install_claude; then
            echo "✅ Installation successful"
        else
            echo "❌ Installation failed"
            echo "📋 Manual installation required: ./setup-claude-code-runner.sh"
            exit 1
        fi
    fi
    
    # Run tests
    run_tests
    
    # Set output for GitHub Actions
    if [ -n "${GITHUB_OUTPUT:-}" ]; then
        if command -v claude &> /dev/null; then
            echo "claude_available=true" >> $GITHUB_OUTPUT
        else
            echo "claude_available=false" >> $GITHUB_OUTPUT
        fi
    fi
}

# Execute main function
main "$@"