#!/bin/bash

# SafeWork Pro Health Management System - Deployment Script
# Supports both local and CI/CD deployments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
APP_NAME="health-management-system"
DOCKER_COMPOSE_FILE="docker-compose.yml"
PRODUCTION_HOST="${PRODUCTION_HOST:-soonmin.jclee.me}"
PRODUCTION_PORT="${PRODUCTION_PORT:-3001}"
PRODUCTION_USER="${PRODUCTION_USER:-docker}"
SSH_PORT="${PRODUCTION_SSH_PORT:-1111}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage function
usage() {
    cat << EOF
Usage: $0 [OPTIONS] [COMMAND]

Commands:
    local       Deploy locally using Docker Compose
    production  Deploy to production server
    staging     Deploy to staging environment
    test        Run deployment tests
    rollback    Rollback to previous version

Options:
    -h, --help          Show this help message
    -v, --version       Show version information
    -c, --cleanup       Cleanup before deployment
    -f, --force         Force deployment without confirmation
    --no-cache          Build without cache
    --skip-tests        Skip running tests
    --dry-run           Show what would be done without executing

Examples:
    $0 local --cleanup
    $0 production --force
    $0 staging --no-cache
    $0 test
EOF
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Run tests
run_tests() {
    if [[ "${SKIP_TESTS:-false}" == "true" ]]; then
        log_warning "Skipping tests as requested"
        return 0
    fi
    
    log_info "Running tests..."
    
    # Create logs directory for tests
    mkdir -p "${PROJECT_DIR}/logs"
    
    # Run Python tests
    if [[ -f "${PROJECT_DIR}/requirements.txt" ]]; then
        log_info "Running Python tests..."
        cd "$PROJECT_DIR"
        
        # Install test dependencies if not in CI
        if [[ "${CI:-false}" != "true" ]]; then
            pip install -q pytest pytest-asyncio httpx pytest-cov || {
                log_warning "Could not install test dependencies, skipping Python tests"
                return 0
            }
        fi
        
        # Run tests with coverage
        python -m pytest tests/ -v --tb=short || {
            log_error "Python tests failed"
            return 1
        }
    fi
    
    # Run frontend tests if package.json exists
    if [[ -f "${PROJECT_DIR}/package.json" ]]; then
        log_info "Running frontend tests..."
        cd "$PROJECT_DIR"
        
        if [[ "${CI:-false}" != "true" ]]; then
            npm ci --silent || {
                log_warning "Could not install npm dependencies, skipping frontend tests"
                return 0
            }
        fi
        
        # Run frontend tests if test script exists
        if npm run test --dry-run &>/dev/null; then
            npm run test || {
                log_error "Frontend tests failed"
                return 1
            }
        fi
    fi
    
    log_success "All tests passed"
}

# Build application
build_app() {
    log_info "Building application..."
    
    cd "$PROJECT_DIR"
    
    # Build frontend if package.json exists
    if [[ -f "package.json" ]]; then
        log_info "Building frontend..."
        npm ci --silent
        npm run build
        log_success "Frontend build completed"
    fi
    
    # Build Docker image
    local cache_flag=""
    if [[ "${NO_CACHE:-false}" == "true" ]]; then
        cache_flag="--no-cache"
    fi
    
    log_info "Building Docker image..."
    docker build $cache_flag -t "$APP_NAME:latest" . || {
        log_error "Docker build failed"
        exit 1
    }
    
    log_success "Docker image built successfully"
}

# Deploy locally
deploy_local() {
    log_info "Deploying locally..."
    
    cd "$PROJECT_DIR"
    
    # Cleanup if requested
    if [[ "${CLEANUP:-false}" == "true" ]]; then
        log_info "Cleaning up existing containers..."
        docker-compose down --remove-orphans --volumes || true
        docker system prune -f || true
    fi
    
    # Start services
    log_info "Starting services..."
    docker-compose up -d --build
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 10
    
    # Health check
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s "http://localhost:${PRODUCTION_PORT}/health" &>/dev/null; then
            log_success "Local deployment successful!"
            log_info "Application available at: http://localhost:${PRODUCTION_PORT}"
            log_info "API documentation: http://localhost:${PRODUCTION_PORT}/api/docs"
            return 0
        fi
        
        log_info "Waiting for health check... (attempt $attempt/$max_attempts)"
        sleep 2
        ((attempt++))
    done
    
    log_error "Health check failed after $max_attempts attempts"
    docker-compose logs --tail=50
    exit 1
}

# Deploy to production
deploy_production() {
    log_info "Deploying to production server: $PRODUCTION_HOST"
    
    # Confirmation prompt unless forced
    if [[ "${FORCE:-false}" != "true" ]]; then
        read -p "Are you sure you want to deploy to production? (y/N): " confirm
        if [[ $confirm != [yY] ]]; then
            log_info "Deployment cancelled"
            exit 0
        fi
    fi
    
    # Check if we can connect to production server
    log_info "Checking connection to production server..."
    if ! ssh -p "$SSH_PORT" -o ConnectTimeout=10 -o BatchMode=yes "$PRODUCTION_USER@$PRODUCTION_HOST" exit &>/dev/null; then
        log_error "Cannot connect to production server $PRODUCTION_HOST"
        log_info "Please ensure SSH access is configured"
        exit 1
    fi
    
    # Create deployment archive
    log_info "Creating deployment package..."
    local deploy_archive="safework-pro-$(date +%Y%m%d-%H%M%S).tar.gz"
    
    tar -czf "/tmp/$deploy_archive" \
        --exclude='.git' \
        --exclude='node_modules' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.pytest_cache' \
        --exclude='coverage*' \
        --exclude='.env*' \
        --exclude='logs/*' \
        --exclude='uploads/*' \
        -C "$PROJECT_DIR" .
    
    # Upload to production server
    log_info "Uploading deployment package..."
    scp -P "$SSH_PORT" "/tmp/$deploy_archive" "$PRODUCTION_USER@$PRODUCTION_HOST:/tmp/"
    
    # Deploy on production server
    log_info "Executing deployment on production server..."
    ssh -p "$SSH_PORT" "$PRODUCTION_USER@$PRODUCTION_HOST" << EOF
        set -euo pipefail
        
        # Backup current deployment
        if [[ -d ~/app/health ]]; then
            echo "Creating backup..."
            cp -r ~/app/health ~/app/health-backup-\$(date +%Y%m%d-%H%M%S)
            
            # Keep only last 5 backups
            ls -dt ~/app/health-backup-* | tail -n +6 | xargs rm -rf
        fi
        
        # Extract new deployment
        echo "Extracting deployment package..."
        mkdir -p ~/app/health
        cd ~/app/health
        tar -xzf "/tmp/$deploy_archive"
        
        # Create necessary directories
        mkdir -p logs uploads
        chmod 755 logs uploads
        
        # Update environment file if template exists
        if [[ -f .env.example ]] && [[ ! -f .env ]]; then
            echo "Creating .env from template..."
            cp .env.example .env
        fi
        
        # Build and restart services
        echo "Building and restarting services..."
        /usr/local/bin/docker-compose down || true
        /usr/local/bin/docker-compose up -d --build
        
        # Cleanup
        rm -f "/tmp/$deploy_archive"
        
        echo "Waiting for services to be ready..."
        sleep 15
        
        # Health check
        if curl -s http://localhost:${PRODUCTION_PORT}/health > /dev/null; then
            echo "✅ Production deployment successful!"
            echo "🌐 Application: http://${PRODUCTION_HOST}:${PRODUCTION_PORT}"
            echo "📚 API docs: http://${PRODUCTION_HOST}:${PRODUCTION_PORT}/api/docs"
        else
            echo "❌ Health check failed!"
            echo "📋 Checking logs:"
            /usr/local/bin/docker-compose logs --tail=20
            exit 1
        fi
EOF
    
    # Cleanup local archive
    rm -f "/tmp/$deploy_archive"
    
    log_success "Production deployment completed successfully!"
}

# Deploy to staging
deploy_staging() {
    log_info "Deploying to staging environment..."
    # Similar to production but with staging-specific configurations
    log_warning "Staging deployment not yet implemented"
    exit 1
}

# Rollback deployment
rollback_deployment() {
    log_info "Rolling back deployment..."
    
    ssh -p "$SSH_PORT" "$PRODUCTION_USER@$PRODUCTION_HOST" << 'EOF'
        set -euo pipefail
        
        # Find latest backup
        latest_backup=$(ls -dt ~/app/health-backup-* 2>/dev/null | head -n 1 || echo "")
        
        if [[ -z "$latest_backup" ]]; then
            echo "❌ No backup found for rollback"
            exit 1
        fi
        
        echo "Rolling back to: $latest_backup"
        
        # Stop current services
        cd ~/app/health
        /usr/local/bin/docker-compose down || true
        
        # Backup current (failed) deployment
        if [[ -d ~/app/health ]]; then
            mv ~/app/health ~/app/health-failed-$(date +%Y%m%d-%H%M%S)
        fi
        
        # Restore from backup
        mv "$latest_backup" ~/app/health
        
        # Restart services
        cd ~/app/health
        /usr/local/bin/docker-compose up -d
        
        sleep 10
        
        # Health check
        if curl -s http://localhost:3001/health > /dev/null; then
            echo "✅ Rollback successful!"
        else
            echo "❌ Rollback health check failed!"
            /usr/local/bin/docker-compose logs --tail=20
            exit 1
        fi
EOF
    
    log_success "Rollback completed successfully!"
}

# Parse command line arguments
CLEANUP=false
FORCE=false
NO_CACHE=false
SKIP_TESTS=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -v|--version)
            echo "SafeWork Pro Deployment Script v1.0.0"
            exit 0
            ;;
        -c|--cleanup)
            CLEANUP=true
            shift
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        --no-cache)
            NO_CACHE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        local|production|staging|test|rollback)
            COMMAND="$1"
            shift
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Set default command if none provided
COMMAND="${COMMAND:-local}"

# Export variables for use in functions
export CLEANUP FORCE NO_CACHE SKIP_TESTS DRY_RUN

# Main execution
main() {
    log_info "SafeWork Pro Health Management System - Deployment Script"
    log_info "Command: $COMMAND"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warning "DRY RUN MODE - No actual changes will be made"
    fi
    
    # Check prerequisites for all commands except help
    if [[ "$COMMAND" != "help" ]]; then
        check_prerequisites
    fi
    
    case "$COMMAND" in
        local)
            if [[ "$DRY_RUN" != "true" ]]; then
                run_tests
                build_app
                deploy_local
            else
                log_info "Would run tests, build app, and deploy locally"
            fi
            ;;
        production)
            if [[ "$DRY_RUN" != "true" ]]; then
                run_tests
                build_app
                deploy_production
            else
                log_info "Would run tests, build app, and deploy to production"
            fi
            ;;
        staging)
            if [[ "$DRY_RUN" != "true" ]]; then
                run_tests
                build_app
                deploy_staging
            else
                log_info "Would run tests, build app, and deploy to staging"
            fi
            ;;
        test)
            run_tests
            ;;
        rollback)
            if [[ "$DRY_RUN" != "true" ]]; then
                rollback_deployment
            else
                log_info "Would rollback deployment"
            fi
            ;;
        *)
            log_error "Unknown command: $COMMAND"
            usage
            exit 1
            ;;
    esac
}

# Run main function
main "$@"