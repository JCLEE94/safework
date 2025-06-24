#!/bin/bash

# Watchtower Setup Script for Health Management System
# This script sets up Watchtower to automatically update containers from registry.jclee.me

set -e

echo "🚀 Setting up Watchtower for automatic deployment..."

# Create Docker config for registry authentication (if needed)
mkdir -p ~/.docker

# Since the registry doesn't require auth, create minimal config
cat > ~/.docker/config.json << EOF
{
  "auths": {
    "https://index.docker.io/v1/": {}
  }
}
EOF

echo "✅ Docker config created"

# Stop existing Watchtower if running
docker stop watchtower 2>/dev/null || true
docker rm watchtower 2>/dev/null || true

# Start Watchtower with docker-compose
echo "🔄 Starting Watchtower..."
docker-compose -f docker-compose.watchtower.yml up -d watchtower

# Wait for Watchtower to start
sleep 5

# Check Watchtower logs
echo "📋 Watchtower logs:"
docker logs watchtower --tail 20

echo "✅ Watchtower setup complete!"
echo ""
echo "Watchtower will now:"
echo "- Check for new images every 30 seconds"
echo "- Automatically update containers with label 'com.centurylinklabs.watchtower.enable=true'"
echo "- Clean up old images after updates"
echo ""
echo "To monitor Watchtower:"
echo "  docker logs -f watchtower"
echo ""
echo "To stop Watchtower:"
echo "  docker-compose -f docker-compose.watchtower.yml down"