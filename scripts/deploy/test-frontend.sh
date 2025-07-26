#!/bin/bash

# SafeWork Frontend V2 Testing Script
# This script runs tests against the deployed frontend

set -e

echo "========================================="
echo "SafeWork Frontend V2 Testing"
echo "========================================="

# Configuration
FRONTEND_URL="${FRONTEND_URL:-https://safework-v2.jclee.me}"
API_URL="${API_URL:-https://safework.jclee.me/api/v1}"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results
PASSED=0
FAILED=0

# Function to run a test
run_test() {
    local test_name="$1"
    local test_command="$2"
    local expected_result="$3"
    
    echo -n "Testing: $test_name... "
    
    if eval "$test_command"; then
        echo -e "${GREEN}✅ PASSED${NC}"
        ((PASSED++))
    else
        echo -e "${RED}❌ FAILED${NC}"
        echo "  Expected: $expected_result"
        ((FAILED++))
    fi
}

# Function to check HTTP status
check_http_status() {
    local url="$1"
    local expected_status="$2"
    local actual_status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    [ "$actual_status" = "$expected_status" ]
}

# Function to check page contains text
check_page_contains() {
    local url="$1"
    local text="$2"
    curl -s "$url" | grep -q "$text"
}

echo "Frontend URL: $FRONTEND_URL"
echo "API URL: $API_URL"
echo ""

# Test 1: Frontend is accessible
run_test "Frontend accessibility" \
    "check_http_status '$FRONTEND_URL' 200" \
    "HTTP 200 OK"

# Test 2: Static assets are served
run_test "Static assets (JS)" \
    "curl -s '$FRONTEND_URL' | grep -q '<script'" \
    "JavaScript files loaded"

run_test "Static assets (CSS)" \
    "curl -s '$FRONTEND_URL' | grep -q '<link.*css'" \
    "CSS files loaded"

# Test 3: React app is loaded
run_test "React app initialization" \
    "curl -s '$FRONTEND_URL' | grep -q 'id=\"root\"'" \
    "React root element present"

# Test 4: Routes are accessible
ROUTES=(
    "/dashboard"
    "/workers"
    "/health-exams"
    "/accidents"
    "/educations"
    "/documents"
    "/compliance"
)

for route in "${ROUTES[@]}"; do
    run_test "Route: $route" \
        "check_http_status '${FRONTEND_URL}${route}' 200" \
        "Route accessible"
done

# Test 5: API proxy is working
run_test "API proxy configuration" \
    "check_http_status '${FRONTEND_URL}/api/v1/health' 200" \
    "API proxy forwards requests"

# Test 6: Security headers
echo ""
echo "Security Headers Test:"
HEADERS=$(curl -s -I "$FRONTEND_URL")

security_headers=(
    "X-Frame-Options"
    "X-Content-Type-Options"
    "X-XSS-Protection"
)

for header in "${security_headers[@]}"; do
    if echo "$HEADERS" | grep -q "$header"; then
        echo -e "  ${GREEN}✅${NC} $header present"
        ((PASSED++))
    else
        echo -e "  ${RED}❌${NC} $header missing"
        ((FAILED++))
    fi
done

# Test 7: Performance checks
echo ""
echo "Performance Tests:"

# Check gzip compression
if curl -s -H "Accept-Encoding: gzip" -I "$FRONTEND_URL" | grep -q "Content-Encoding: gzip"; then
    echo -e "  ${GREEN}✅${NC} Gzip compression enabled"
    ((PASSED++))
else
    echo -e "  ${RED}❌${NC} Gzip compression not enabled"
    ((FAILED++))
fi

# Check cache headers for static assets
STATIC_ASSET=$(curl -s "$FRONTEND_URL" | grep -o 'src="[^"]*\.js"' | head -1 | cut -d'"' -f2)
if [ ! -z "$STATIC_ASSET" ]; then
    CACHE_HEADER=$(curl -s -I "${FRONTEND_URL}${STATIC_ASSET}" | grep -i "cache-control")
    if echo "$CACHE_HEADER" | grep -q "max-age"; then
        echo -e "  ${GREEN}✅${NC} Static asset caching enabled"
        ((PASSED++))
    else
        echo -e "  ${RED}❌${NC} Static asset caching not configured"
        ((FAILED++))
    fi
fi

# Test 8: Mobile responsiveness
echo ""
echo "Mobile Responsiveness Test:"
MOBILE_UA="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15"
if curl -s -H "User-Agent: $MOBILE_UA" "$FRONTEND_URL" | grep -q "viewport"; then
    echo -e "  ${GREEN}✅${NC} Viewport meta tag present"
    ((PASSED++))
else
    echo -e "  ${RED}❌${NC} Viewport meta tag missing"
    ((FAILED++))
fi

# Test 9: Error handling
run_test "404 page handling" \
    "check_http_status '${FRONTEND_URL}/non-existent-page' 200" \
    "React Router handles 404"

# Test 10: WebSocket support (if applicable)
echo ""
echo "Checking WebSocket support..."
if curl -s -I "$FRONTEND_URL" | grep -q "Upgrade: websocket"; then
    echo -e "  ${GREEN}✅${NC} WebSocket upgrade supported"
    ((PASSED++))
else
    echo -e "  ${YELLOW}⚠️${NC} WebSocket not configured (may be normal)"
fi

# Summary
echo ""
echo "========================================="
echo "Test Summary:"
echo "  ${GREEN}Passed: $PASSED${NC}"
echo "  ${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! ✅${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the results above.${NC}"
    exit 1
fi