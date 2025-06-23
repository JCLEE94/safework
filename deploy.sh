#!/bin/bash
# deploy.sh - Automated deployment script

set -e
PROJECT_NAME=${1:-health}
TZ=Asia/Seoul
BUILD_TIME=$(date +"%Y-%m-%d %H:%M:%S KST")

echo "🚀 Starting deployment for $PROJECT_NAME..."

# Build with timestamp
echo "📦 Building Docker image..."
docker build --build-arg BUILD_TIME="$BUILD_TIME" -t $PROJECT_NAME:latest .

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down --remove-orphans || true

# Start new containers
echo "🚀 Starting new containers..."
docker-compose up -d --force-recreate

sleep 10
echo "📋 Container status:"
docker-compose ps

echo "📄 Recent logs:"
docker-compose logs --tail=20

# Health check
echo "🔍 Verifying deployment..."
if curl -f http://192.168.50.215:3001/health; then
  echo "✅ Deployment successful!"
else
  echo "❌ Health check failed - deployment may have issues"
  exit 1
fi