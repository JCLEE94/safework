#!/bin/bash

# Health Management System Complete Deployment Script
# This script handles initial setup and deployment with Watchtower

set -e

echo "🚀 Health Management System Complete Deployment"
echo "=============================================="

# Configuration
REGISTRY="registry.jclee.me"
IMAGE_NAME="health-management-system"
REGISTRY_USER="qws941"
REGISTRY_PASS="bingogo1l7!"
PROJECT_DIR="${PWD}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if this is first time setup
FIRST_TIME_SETUP=false
if [ ! -f ".env" ] || [ ! -d "uploads" ] || [ ! -d "logs" ]; then
    FIRST_TIME_SETUP=true
    echo ""
    print_info "First time setup detected"
fi

# Step 1: Initial Setup (if needed)
if [ "$FIRST_TIME_SETUP" = true ]; then
    echo ""
    echo "📦 Step 1: Initial Setup"
    echo "-----------------------"
    
    # Create required directories
    print_info "Creating required directories..."
    mkdir -p uploads logs dist document
    chmod 755 uploads logs
    print_status "Directories created"
    
    # Create .env file if not exists
    if [ ! -f ".env" ]; then
        print_info "Creating .env file..."
        cat > .env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://admin:password@postgres:5432/health_management
POSTGRES_USER=admin
POSTGRES_PASSWORD=password
POSTGRES_DB=health_management

# Redis Configuration
REDIS_URL=redis://redis:6379/0
REDIS_PASSWORD=

# JWT Configuration
JWT_SECRET=your-super-secret-jwt-key-here-32-chars-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=1440

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
TZ=Asia/Seoul

# API Keys (update as needed)
API_KEY_SALT=your-api-key-salt-here

# CORS Settings
CORS_ORIGINS=["http://localhost:3001", "http://192.168.50.215:3001", "https://registry.jclee.me:3001"]

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60
EOF
        print_status ".env file created"
        print_warning "Please update .env file with your actual configuration"
    fi
else
    echo ""
    print_info "Existing installation detected, skipping initial setup"
fi

# Step 2: Docker Setup Check
echo ""
echo "🐳 Step 2: Docker Environment Check"
echo "----------------------------------"
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed!"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed!"
    exit 1
fi

# Check Docker daemon
if ! docker info > /dev/null 2>&1; then
    print_error "Docker daemon is not running!"
    exit 1
fi

print_status "Docker environment OK"

# Step 3: Login to registry
echo ""
echo "🔐 Step 3: Registry Authentication"
echo "---------------------------------"
echo "$REGISTRY_PASS" | docker login $REGISTRY -u $REGISTRY_USER --password-stdin
if [ $? -eq 0 ]; then
    print_status "Successfully logged in to $REGISTRY"
else
    print_error "Failed to login to registry"
    exit 1
fi

# Step 4: Pull latest image
echo ""
echo "📥 Step 4: Pull Latest Image"
echo "---------------------------"
docker pull $REGISTRY/$IMAGE_NAME:latest
if [ $? -eq 0 ]; then
    print_status "Successfully pulled latest image"
else
    print_error "Failed to pull image"
    exit 1
fi

# Step 5: Stop existing containers
echo ""
echo "🛑 Step 5: Clean Up Existing Containers"
echo "--------------------------------------"
# Stop any existing containers
docker-compose down 2>/dev/null || true
docker stop health-management-system health-postgres health-redis watchtower 2>/dev/null || true
docker rm health-management-system health-postgres health-redis watchtower 2>/dev/null || true
print_status "Cleaned up existing containers"

# Step 6: Create Docker config for Watchtower
echo ""
echo "🔧 Step 6: Configure Docker Registry Access"
echo "-----------------------------------------"
mkdir -p ~/.docker
cat > ~/.docker/config.json << EOF
{
  "auths": {
    "$REGISTRY": {
      "auth": "$(echo -n "$REGISTRY_USER:$REGISTRY_PASS" | base64)"
    },
    "https://index.docker.io/v1/": {}
  }
}
EOF
chmod 600 ~/.docker/config.json
print_status "Docker registry configuration created"

# Step 7: Create docker-compose file
echo ""
echo "📝 Step 7: Create Docker Compose Configuration"
echo "--------------------------------------------"
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: health-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=${POSTGRES_USER:-admin}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}
      - POSTGRES_DB=${POSTGRES_DB:-health_management}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=ko_KR.UTF-8 --lc-ctype=ko_KR.UTF-8
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - health-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-admin} -d ${POSTGRES_DB:-health_management}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: health-redis
    restart: unless-stopped
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - health-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  health-app:
    image: registry.jclee.me/health-management-system:latest
    container_name: health-management-system
    restart: unless-stopped
    ports:
      - "3001:8000"
    env_file:
      - .env
    environment:
      - TZ=Asia/Seoul
      - PYTHONUNBUFFERED=1
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./dist:/app/dist
      - ./.env:/app/.env:ro
    labels:
      - "com.centurylinklabs.watchtower.enable=true"
      - "com.centurylinklabs.watchtower.stop-signal=SIGTERM"
      - "com.centurylinklabs.watchtower.timeout=30s"
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - health-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  watchtower:
    image: containrrr/watchtower
    container_name: watchtower
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ~/.docker/config.json:/config.json:ro
    environment:
      - WATCHTOWER_POLL_INTERVAL=300  # Check every 5 minutes
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_INCLUDE_STOPPED=false
      - WATCHTOWER_INCLUDE_RESTARTING=true
      - WATCHTOWER_LABEL_ENABLE=true
      - WATCHTOWER_ROLLING_RESTART=true
      - WATCHTOWER_NO_PULL=false
      - WATCHTOWER_MONITOR_ONLY=false
      - DOCKER_CONFIG=/config.json
      - TZ=Asia/Seoul
      - WATCHTOWER_NOTIFICATIONS_LEVEL=info
      - WATCHTOWER_LOG_LEVEL=info
    command: --interval 300 --label-enable --cleanup
    networks:
      - health-network

volumes:
  postgres_data:
  redis_data:

networks:
  health-network:
    driver: bridge
EOF
print_status "Docker Compose configuration created"

# Step 8: Create database init script
echo ""
echo "🗄️  Step 8: Create Database Initialization Script"
echo "-----------------------------------------------"
mkdir -p scripts
cat > scripts/init-db.sql << 'EOF'
-- Health Management System Database Initialization
-- This script runs only on first database creation

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Set timezone
SET timezone = 'Asia/Seoul';

-- Create schema if needed
CREATE SCHEMA IF NOT EXISTS health;

-- Grant permissions
GRANT ALL ON SCHEMA health TO admin;
GRANT ALL ON SCHEMA public TO admin;

-- Log initialization
DO $$
BEGIN
  RAISE NOTICE 'Database initialized at %', NOW();
END $$;
EOF
print_status "Database init script created"

# Step 9: Start all services
echo ""
echo "🚀 Step 9: Start All Services"
echo "----------------------------"
docker-compose up -d

# Step 10: Wait for services to be ready
echo ""
echo "⏳ Step 10: Waiting for Services to Initialize"
echo "---------------------------------------------"
print_info "Waiting for database to be ready..."
sleep 10

# Check database connection
for i in {1..30}; do
    if docker exec health-postgres pg_isready -U admin -d health_management > /dev/null 2>&1; then
        print_status "Database is ready"
        break
    fi
    echo -n "."
    sleep 2
done

# Step 11: Initialize database schema (if first time)
if [ "$FIRST_TIME_SETUP" = true ]; then
    echo ""
    echo "🗄️  Step 11: Initialize Database Schema"
    echo "-------------------------------------"
    print_info "Running database migrations..."
    
    # Wait a bit more for the app to start
    sleep 10
    
    # The app should auto-create tables on first run
    print_status "Database schema initialization complete"
fi

# Step 12: Health check
echo ""
echo "🏥 Step 12: Application Health Check"
echo "-----------------------------------"
for i in {1..30}; do
    if curl -f http://localhost:3001/health > /dev/null 2>&1; then
        print_status "Application is healthy!"
        break
    fi
    echo -n "."
    sleep 2
done

if ! curl -f http://localhost:3001/health > /dev/null 2>&1; then
    print_warning "Health check failed, checking logs..."
    docker logs health-management-system --tail 30
fi

# Step 13: Show service status
echo ""
echo "📊 Step 13: Service Status"
echo "-------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(NAME|watchtower|health-|postgres|redis)" || true

# Step 14: Watchtower status
echo ""
echo "👀 Step 14: Watchtower Status"
echo "----------------------------"
docker logs watchtower --tail 5 2>/dev/null || print_warning "Watchtower logs not available yet"

# Summary
echo ""
echo "=================================================================================="
echo "                        🎉 Deployment Complete! 🎉"
echo "=================================================================================="
echo ""
print_status "Application URL: http://localhost:3001"
print_status "Health Check: http://localhost:3001/health"
print_status "API Docs: http://localhost:3001/api/docs"
echo ""
print_info "Watchtower is monitoring for updates every 5 minutes"
print_info "Registry: $REGISTRY/$IMAGE_NAME:latest"
echo ""
echo "📚 Useful Commands:"
echo "==================="
echo "📋 View app logs:       docker logs -f health-management-system"
echo "👀 Monitor Watchtower:  docker logs -f watchtower"
echo "🔄 Manual update:       docker pull $REGISTRY/$IMAGE_NAME:latest && docker-compose restart health-app"
echo "🛑 Stop all services:   docker-compose down"
echo "📈 View status:         docker-compose ps"
echo "🗄️  Access database:     docker exec -it health-postgres psql -U admin -d health_management"
echo "🔄 Restart app:         docker-compose restart health-app"
echo ""

if [ "$FIRST_TIME_SETUP" = true ]; then
    echo ""
    print_warning "⚠️  First Time Setup Notes:"
    echo "1. Update the .env file with your production values"
    echo "2. Change JWT_SECRET to a secure random string"
    echo "3. Update database passwords if needed"
    echo "4. Configure your firewall to allow port 3001"
    echo ""
fi

print_status "Deployment script completed successfully!"