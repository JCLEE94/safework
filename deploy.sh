#!/bin/bash

# 배포 스크립트 - Private Registry를 통한 프로덕션 배포
# Usage: ./deploy.sh [environment]
# environment: dev, staging, prod (default: prod)

set -e

# Configuration
PROJECT_NAME="health-management-system"
REGISTRY="registry.jclee.me"
REMOTE_HOST="192.168.50.215"
REMOTE_PORT="1111"
REMOTE_USER="docker"
REMOTE_PATH="~/app/health"
ENVIRONMENT="${1:-prod}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Build timestamp (KST)
BUILD_TIME=$(TZ=Asia/Seoul date +"%Y-%m-%d %H:%M:%S KST")
BUILD_TAG="${ENVIRONMENT}-$(date +%Y%m%d-%H%M%S)"

echo -e "${BLUE}🚀 Starting deployment for $PROJECT_NAME ($ENVIRONMENT)${NC}"
echo -e "Build Time: $BUILD_TIME"
echo

# Step 1: Run tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
pytest tests/ -v --tb=short || {
    echo -e "${RED}❌ Tests failed! Aborting deployment.${NC}"
    exit 1
}
echo -e "${GREEN}✓ Tests passed${NC}\n"

# Step 2: Build frontend
echo -e "${YELLOW}📦 Building frontend...${NC}"
npm run build || {
    echo -e "${RED}❌ Frontend build failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Frontend built${NC}\n"

# Step 3: Build Docker image
echo -e "${YELLOW}🐳 Building Docker image...${NC}"
docker build \
    --build-arg BUILD_TIME="$BUILD_TIME" \
    --no-cache \
    -t $REGISTRY/$PROJECT_NAME:$BUILD_TAG \
    -t $REGISTRY/$PROJECT_NAME:latest \
    . || {
    echo -e "${RED}❌ Docker build failed!${NC}"
    exit 1
}
echo -e "${GREEN}✓ Docker image built${NC}\n"

# Step 4: Test the image locally
echo -e "${YELLOW}🔍 Testing Docker image...${NC}"
docker run --rm -d --name test-$PROJECT_NAME \
    -p 8001:8000 \
    $REGISTRY/$PROJECT_NAME:latest
sleep 5

if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    docker stop test-$PROJECT_NAME > /dev/null
else
    echo -e "${RED}❌ Health check failed!${NC}"
    docker stop test-$PROJECT_NAME > /dev/null 2>&1
    exit 1
fi
echo

# Step 5: Push to registry
echo -e "${YELLOW}📤 Pushing to registry...${NC}"
docker push $REGISTRY/$PROJECT_NAME:$BUILD_TAG || {
    echo -e "${RED}❌ Registry push failed!${NC}"
    exit 1
}
docker push $REGISTRY/$PROJECT_NAME:latest
echo -e "${GREEN}✓ Pushed to registry${NC}\n"

# Step 6: Deploy to remote server
echo -e "${YELLOW}🚀 Deploying to remote server...${NC}"

# Copy docker-compose.prod.yml
scp -P $REMOTE_PORT docker-compose.prod.yml $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/docker-compose.yml

# Copy .env if exists
if [ -f .env.production ]; then
    scp -P $REMOTE_PORT .env.production $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/.env
fi

# Deploy on remote
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST << EOF
    set -e
    cd $REMOTE_PATH
    
    # Pull latest image
    docker pull $REGISTRY/$PROJECT_NAME:latest
    
    # Backup current deployment
    docker tag $REGISTRY/$PROJECT_NAME:latest $REGISTRY/$PROJECT_NAME:backup-\$(date +%Y%m%d-%H%M%S) 2>/dev/null || true
    
    # Update and restart
    /usr/local/bin/docker-compose pull
    /usr/local/bin/docker-compose up -d
    
    # Wait for health check
    echo "Waiting for application to be healthy..."
    sleep 10
    
    # Verify deployment
    if curl -f http://localhost:3001/health > /dev/null 2>&1; then
        echo "✓ Deployment successful!"
        /usr/local/bin/docker-compose logs --tail=20 health-app
    else
        echo "❌ Deployment verification failed!"
        /usr/local/bin/docker-compose logs --tail=50 health-app
        exit 1
    fi
EOF

echo
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${BLUE}📊 Application Info:${NC}"
echo -e "  • Environment: $ENVIRONMENT"
echo -e "  • Version: $BUILD_TAG"
echo -e "  • URL: http://$REMOTE_HOST:3001"
echo -e "  • API Docs: http://$REMOTE_HOST:3001/api/docs"
echo -e "  • Health: http://$REMOTE_HOST:3001/health"
echo -e "  • Build Time: $BUILD_TIME"

# Show recent logs
echo
echo -e "${YELLOW}📋 Recent logs:${NC}"
ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "cd $REMOTE_PATH && /usr/local/bin/docker-compose logs --tail=10 health-app | grep -E 'INFO|WARNING|ERROR' || true"