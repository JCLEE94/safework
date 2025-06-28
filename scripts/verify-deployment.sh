#!/bin/bash

# SafeWork Pro Deployment Verification Script
# This script verifies that a deployment is healthy and functioning

set -euo pipefail

# Configuration
PRODUCTION_URL="${PRODUCTION_URL:-http://192.168.50.215:3001}"
MAX_ATTEMPTS="${MAX_ATTEMPTS:-30}"
WAIT_INTERVAL="${WAIT_INTERVAL:-10}"
EXPECTED_BUILD_TIME="${EXPECTED_BUILD_TIME:-}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to check if service is healthy
check_health() {
    local url="$1/health"
    local response
    local http_code
    
    response=$(curl -s -w "\n%{http_code}" "$url" 2>/dev/null || echo -e "\n000")
    http_code=$(echo "$response" | tail -n1)
    
    if [ "$http_code" = "200" ]; then
        local body=$(echo "$response" | head -n-1)
        local status=$(echo "$body" | jq -r '.status // "unknown"' 2>/dev/null || echo "unknown")
        local build_time=$(echo "$body" | jq -r '.build_time // ""' 2>/dev/null || echo "")
        
        if [ "$status" = "healthy" ]; then
            success "Health check passed (HTTP $http_code, status: $status)"
            if [ -n "$build_time" ]; then
                log "Build time: $build_time"
                
                # If expected build time is provided, verify it matches
                if [ -n "$EXPECTED_BUILD_TIME" ] && [ "$build_time" != "$EXPECTED_BUILD_TIME" ]; then
                    warning "Build time mismatch: expected '$EXPECTED_BUILD_TIME', got '$build_time'"
                    return 2  # Indicates old deployment
                fi
            fi
            return 0
        else
            warning "Service responding but unhealthy (status: $status)"
            return 1
        fi
    else
        error "Health check failed (HTTP $http_code)"
        return 1
    fi
}

# Function to test critical endpoints
test_endpoints() {
    local base_url="$1"
    
    log "Testing critical endpoints..."
    
    local endpoints=(
        "/health"
        "/api/docs"
        "/api/v1/workers/"
        "/api/v1/monitoring/metrics"
        "/api/v1/companies/"
        "/api/v1/health-checkups/"
    )
    
    local success_count=0
    local total_endpoints=${#endpoints[@]}
    
    for endpoint in "${endpoints[@]}"; do
        local url="$base_url$endpoint"
        local http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
        
        case $http_code in
            200)
                success "$endpoint: HTTP $http_code"
                ((success_count++))
                ;;
            401|403)
                success "$endpoint: HTTP $http_code (auth required - expected)"
                ((success_count++))
                ;;
            *)
                error "$endpoint: HTTP $http_code"
                ;;
        esac
    done
    
    log "Endpoint test results: $success_count/$total_endpoints passed"
    
    if [ $success_count -eq $total_endpoints ]; then
        success "All critical endpoints are responding correctly"
        return 0
    else
        error "Some endpoints failed - deployment may have issues"
        return 1
    fi
}

# Function to test performance
test_performance() {
    local url="$1/health"
    
    log "Testing response time..."
    
    local total_time=0
    local test_count=3
    
    for i in $(seq 1 $test_count); do
        local time=$(curl -o /dev/null -s -w '%{time_total}' "$url" 2>/dev/null || echo "0")
        total_time=$(echo "$total_time + $time" | bc -l)
        log "Test $i: ${time}s"
    done
    
    local avg_time=$(echo "scale=3; $total_time / $test_count" | bc -l)
    local avg_time_ms=$(echo "$avg_time * 1000" | bc -l)
    
    log "Average response time: ${avg_time_ms}ms"
    
    if (( $(echo "$avg_time_ms > 5000" | bc -l) )); then
        error "Slow response time: ${avg_time_ms}ms (threshold: 5000ms)"
        return 1
    elif (( $(echo "$avg_time_ms > 2000" | bc -l) )); then
        warning "Moderate response time: ${avg_time_ms}ms"
        return 0
    else
        success "Good response time: ${avg_time_ms}ms"
        return 0
    fi
}

# Function to check database connectivity
test_database() {
    local base_url="$1"
    local url="$base_url/api/v1/monitoring/metrics"
    
    log "Testing database connectivity..."
    
    local response=$(curl -s "$url" 2>/dev/null || echo "")
    
    if echo "$response" | grep -q "database_connections\|db_pool"; then
        success "Database connectivity confirmed"
        return 0
    else
        warning "Could not verify database connectivity"
        return 1
    fi
}

# Main verification function
verify_deployment() {
    log "🚀 Starting deployment verification for $PRODUCTION_URL"
    
    local attempt=1
    local verification_passed=false
    
    while [ $attempt -le $MAX_ATTEMPTS ]; do
        log "🔍 Verification attempt $attempt/$MAX_ATTEMPTS"
        
        # Check basic health
        local health_result
        check_health "$PRODUCTION_URL"
        health_result=$?
        
        if [ $health_result -eq 0 ]; then
            log "✅ Basic health check passed"
            
            # Run comprehensive tests
            if test_endpoints "$PRODUCTION_URL" && \
               test_performance "$PRODUCTION_URL" && \
               test_database "$PRODUCTION_URL"; then
                verification_passed=true
                break
            else
                warning "Some tests failed, retrying..."
            fi
        elif [ $health_result -eq 2 ]; then
            warning "Old deployment detected, waiting for new version..."
        else
            warning "Health check failed, waiting..."
        fi
        
        if [ $attempt -eq $MAX_ATTEMPTS ]; then
            error "Deployment verification failed after $MAX_ATTEMPTS attempts"
            return 1
        fi
        
        log "⏳ Waiting ${WAIT_INTERVAL}s before next attempt..."
        sleep $WAIT_INTERVAL
        ((attempt++))
    done
    
    if [ "$verification_passed" = true ]; then
        success "🎉 Deployment verification completed successfully!"
        return 0
    else
        error "💥 Deployment verification failed!"
        return 1
    fi
}

# Script execution
main() {
    if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
        cat << EOF
SafeWork Pro Deployment Verification Script

Usage: $0 [OPTIONS]

Environment Variables:
  PRODUCTION_URL     Target URL to verify (default: http://192.168.50.215:3001)
  MAX_ATTEMPTS       Maximum verification attempts (default: 30)
  WAIT_INTERVAL      Seconds between attempts (default: 10)
  EXPECTED_BUILD_TIME Expected build timestamp for new deployment verification

Examples:
  # Basic verification
  $0
  
  # Custom URL and timeout
  PRODUCTION_URL=http://localhost:3001 MAX_ATTEMPTS=10 $0
  
  # Verify specific build
  EXPECTED_BUILD_TIME="2024-01-01T12:00:00Z" $0

Exit Codes:
  0 - Verification successful
  1 - Verification failed
  2 - Invalid arguments
EOF
        return 0
    fi
    
    # Validate URL
    if ! curl -s --head "$PRODUCTION_URL" >/dev/null 2>&1; then
        error "Cannot reach $PRODUCTION_URL - check URL and network connectivity"
        return 2
    fi
    
    # Run verification
    verify_deployment
}

# Check if script is being sourced or executed
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    main "$@"
fi