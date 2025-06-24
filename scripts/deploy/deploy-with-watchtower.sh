#!/bin/bash

# Health Management System Deployment Script with Watchtower
# This script deploys the application and sets up Watchtower for automatic updates

set -e

echo "🚀 Health Management System Deployment with Watchtower"
echo "======================================================"

# Configuration
REGISTRY="registry.jclee.me"
IMAGE_NAME="health-management-system"
REGISTRY_USER="qws941"
REGISTRY_PASS="bingogo1l7!"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   print_warning "Running as root user"
fi

# Step 1: Login to registry
echo ""
echo "🔐 Step 1: Registry Authentication"
echo "---------------------------------"
echo "$REGISTRY_PASS" | docker login $REGISTRY -u $REGISTRY_USER --password-stdin
if [ $? -eq 0 ]; then
    print_status "Successfully logged in to $REGISTRY"
else
    print_error "Failed to login to registry"
    exit 1
fi

# Step 2: Pull latest image
echo ""
echo "📥 Step 2: Pull Latest Image"
echo "---------------------------"
docker pull $REGISTRY/$IMAGE_NAME:latest
if [ $? -eq 0 ]; then
    print_status "Successfully pulled latest image"
else
    print_error "Failed to pull image"
    exit 1
fi

# Step 3: Stop existing containers
echo ""
echo "🛑 Step 3: Stop Existing Containers"
echo "----------------------------------"
if [ -f docker-compose.prod.yml ]; then
    docker-compose -f docker-compose.prod.yml down || true
fi
if [ -f docker-compose.watchtower.yml ]; then
    docker-compose -f docker-compose.watchtower.yml down || true
fi
docker stop health-management-system 2>/dev/null || true
docker stop watchtower 2>/dev/null || true
print_status "Stopped existing containers"

# Step 4: Create Docker config for Watchtower
echo ""
echo "🔧 Step 4: Configure Docker Registry Access"
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

# Step 5: Start application with Watchtower
echo ""
echo "🚀 Step 5: Start Application with Watchtower"
echo "------------------------------------------"

# Create combined docker-compose with Watchtower
cat > docker-compose.deploy.yml << 'EOF'
version: '3.8'

services:
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

  health-app:
    image: registry.jclee.me/health-management-system:latest
    container_name: health-management-system
    restart: unless-stopped
    ports:
      - "3001:8000"
    environment:
      - DATABASE_URL=postgresql://admin:password@postgres:5432/health_management
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET:-your-super-secret-jwt-key-here-32-chars-long}
      - DEBUG=false
      - LOG_LEVEL=INFO
      - TZ=Asia/Seoul
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./dist:/app/dist
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

  postgres:
    image: postgres:15
    container_name: health-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=admin
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=health_management
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=ko_KR.UTF-8 --lc-ctype=ko_KR.UTF-8
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - health-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d health_management"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: health-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
    networks:
      - health-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:

networks:
  health-network:
    driver: bridge
EOF

# Start all services
docker-compose -f docker-compose.deploy.yml up -d

# Step 6: Wait for services to be ready
echo ""
echo "⏳ Step 6: Waiting for Services to Start"
echo "---------------------------------------"
sleep 10

# Check if services are running
echo ""
echo "🔍 Checking Service Status:"
echo "--------------------------"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(watchtower|health-|postgres|redis)"

# Step 7: Health check
echo ""
echo "🏥 Step 7: Application Health Check"
echo "----------------------------------"
sleep 5
if curl -f http://localhost:3001/health > /dev/null 2>&1; then
    print_status "Application is healthy!"
else
    print_warning "Health check failed, checking logs..."
    docker logs health-management-system --tail 20
fi

# Step 8: Watchtower status
echo ""
echo "👀 Step 8: Watchtower Status"
echo "---------------------------"
docker logs watchtower --tail 10

# Summary
echo ""
echo "📊 Deployment Summary"
echo "===================="
print_status "Application: http://localhost:3001"
print_status "Watchtower: Monitoring for updates every 5 minutes"
print_status "Registry: $REGISTRY/$IMAGE_NAME:latest"
echo ""
echo "Useful Commands:"
echo "---------------"
echo "📋 View logs:           docker logs -f health-management-system"
echo "👀 Monitor Watchtower:  docker logs -f watchtower"
echo "🔄 Manual update:       docker pull $REGISTRY/$IMAGE_NAME:latest && docker-compose -f docker-compose.deploy.yml up -d"
echo "🛑 Stop all:           docker-compose -f docker-compose.deploy.yml down"
echo "📈 View status:        docker ps"
echo ""
print_status "Deployment completed successfully!"