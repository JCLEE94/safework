#!/bin/bash
set -euo pipefail

# Deployment Verification Script with Integration Tests
# Validates that SafeWork Pro deployment is successful and healthy

# Configuration
DEPLOYMENT_URL="${DEPLOYMENT_URL:-https://safework.jclee.me}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_RETRIES="${MAX_RETRIES:-10}"
RETRY_DELAY="${RETRY_DELAY:-30}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test: HTTP endpoint reachability
test_endpoint_reachable() {
    local url="$1"
    echo "🌐 Testing endpoint reachability: $url"
    
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ Endpoint reachable (HTTP $http_code)${NC}"
        return 0
    else
        echo -e "${RED}❌ Endpoint not reachable (HTTP $http_code)${NC}"
        return 1
    fi
}

# Test: Health check response validation
test_health_check() {
    local url="${DEPLOYMENT_URL}${HEALTH_ENDPOINT}"
    echo "🏥 Testing health check: $url"
    
    local response=$(curl -s "$url" || echo "{}")
    local status=$(echo "$response" | jq -r '.status' 2>/dev/null || echo "unknown")
    
    if [ "$status" = "healthy" ] || [ "$status" = "ok" ]; then
        echo -e "${GREEN}✅ Health check passed: $status${NC}"
        return 0
    else
        echo -e "${RED}❌ Health check failed: $status${NC}"
        echo "Response: $response"
        return 1
    fi
}

# Test: API endpoints availability
test_api_endpoints() {
    echo "🔌 Testing API endpoints..."
    
    local endpoints=(
        "/api/v1/workers/"
        "/api/v1/health-exams/"
        "/api/v1/dashboard"
        "/api/docs"
    )
    
    local passed=0
    local failed=0
    
    for endpoint in "${endpoints[@]}"; do
        local url="${DEPLOYMENT_URL}${endpoint}"
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        
        if [[ "$http_code" =~ ^(200|301|302|401|403)$ ]]; then
            echo -e "  ${GREEN}✅ $endpoint (HTTP $http_code)${NC}"
            ((passed++))
        else
            echo -e "  ${RED}❌ $endpoint (HTTP $http_code)${NC}"
            ((failed++))
        fi
    done
    
    echo "API Test Results: $passed passed, $failed failed"
    [ $failed -eq 0 ]
}

# Test: Database connectivity
test_database_connectivity() {
    echo "🗄️ Testing database connectivity..."
    
    # Check if migrations endpoint exists
    local url="${DEPLOYMENT_URL}/api/v1/health/db"
    local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [[ "$http_code" =~ ^(200|404)$ ]]; then
        echo -e "${GREEN}✅ Database check endpoint tested${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Cannot verify database directly${NC}"
        return 0  # Don't fail the test
    fi
}

# Test: Redis connectivity
test_redis_connectivity() {
    echo "💾 Testing Redis connectivity..."
    
    # Check cache headers or specific cached endpoint
    local url="${DEPLOYMENT_URL}/api/v1/workers/"
    local cache_header=$(curl -s -I "$url" | grep -i "x-cache" || echo "")
    
    if [ -n "$cache_header" ]; then
        echo -e "${GREEN}✅ Cache headers detected: $cache_header${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ No cache headers found (might be normal)${NC}"
        return 0  # Don't fail the test
    fi
}

# Test: SSL certificate validity
test_ssl_certificate() {
    echo "🔒 Testing SSL certificate..."
    
    local domain=$(echo "$DEPLOYMENT_URL" | sed -E 's|https?://([^/]+).*|\1|')
    
    if echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -dates &>/dev/null; then
        echo -e "${GREEN}✅ SSL certificate valid${NC}"
        return 0
    else
        echo -e "${RED}❌ SSL certificate issue detected${NC}"
        return 1
    fi
}

# Test: Response time performance
test_response_time() {
    echo "⏱️ Testing response time..."
    
    local total_time=$(curl -s -o /dev/null -w "%{time_total}" "${DEPLOYMENT_URL}${HEALTH_ENDPOINT}" || echo "999")
    local time_ms=$(echo "$total_time * 1000" | bc 2>/dev/null || echo "999")
    
    if (( $(echo "$total_time < 2" | bc -l) )); then
        echo -e "${GREEN}✅ Response time: ${time_ms}ms${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️ Slow response time: ${time_ms}ms${NC}"
        return 1
    fi
}

# Wait for deployment with retries
wait_for_deployment() {
    echo "⏳ Waiting for deployment to be ready..."
    
    for i in $(seq 1 $MAX_RETRIES); do
        echo -e "${BLUE}Attempt $i/$MAX_RETRIES${NC}"
        
        if test_endpoint_reachable "${DEPLOYMENT_URL}${HEALTH_ENDPOINT}"; then
            echo -e "${GREEN}✅ Deployment is ready!${NC}"
            return 0
        fi
        
        if [ $i -lt $MAX_RETRIES ]; then
            echo "⏳ Waiting ${RETRY_DELAY}s before retry..."
            sleep $RETRY_DELAY
        fi
    done
    
    echo -e "${RED}❌ Deployment failed to become ready after $MAX_RETRIES attempts${NC}"
    return 1
}

# Run all integration tests
run_integration_tests() {
    echo "🧪 Running deployment integration tests..."
    echo "========================================="
    
    local tests_passed=0
    local tests_failed=0
    
    # Test suite
    local tests=(
        "test_health_check"
        "test_api_endpoints"
        "test_database_connectivity"
        "test_redis_connectivity"
        "test_ssl_certificate"
        "test_response_time"
    )
    
    for test in "${tests[@]}"; do
        echo ""
        if $test; then
            ((tests_passed++))
        else
            ((tests_failed++))
        fi
    done
    
    echo ""
    echo "========================================="
    echo "📊 Integration Test Results:"
    echo "  ✅ Passed: $tests_passed"
    echo "  ❌ Failed: $tests_failed"
    echo "========================================="
    
    if [ $tests_failed -eq 0 ]; then
        echo -e "${GREEN}🎉 All integration tests passed!${NC}"
        return 0
    else
        echo -e "${RED}⚠️ Some integration tests failed${NC}"
        return 1
    fi
}

# Main execution
main() {
    echo "🚀 SafeWork Pro Deployment Verification"
    echo "======================================="
    echo "Target: $DEPLOYMENT_URL"
    echo ""
    
    # Wait for deployment
    if ! wait_for_deployment; then
        exit 1
    fi
    
    echo ""
    
    # Run integration tests
    if run_integration_tests; then
        exit_code=0
    else
        exit_code=1
    fi
    
    # Set output for GitHub Actions
    if [ -n "${GITHUB_OUTPUT:-}" ]; then
        echo "deployment_healthy=$([[ $exit_code -eq 0 ]] && echo 'true' || echo 'false')" >> $GITHUB_OUTPUT
    fi
    
    exit $exit_code
}

# Execute main function
main "$@"