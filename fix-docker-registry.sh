#!/bin/bash

# Fix Docker Registry Push Issues

echo "Fixing Docker registry configuration..."

# 1. Update docker-compose on server to use HTTP explicitly
cat > /tmp/docker-compose-registry.yml << 'EOF'
version: '3.8'

services:
  registry:
    image: registry:2
    container_name: docker-registry
    restart: always
    ports:
      - '1234:5000'
    environment:
      REGISTRY_STORAGE_FILESYSTEM_ROOTDIRECTORY: /var/lib/registry
      REGISTRY_HTTP_ADDR: 0.0.0.0:5000
      REGISTRY_STORAGE_DELETE_ENABLED: 'true'
      # Add explicit HTTP configuration
      REGISTRY_HTTP_TLS_CERTIFICATE: ''
      REGISTRY_HTTP_TLS_KEY: ''
    volumes:
      - /volume1/app/registry/data:/var/lib/registry
    networks:
      - registry-network

networks:
  registry-network:
    driver: bridge
EOF

# 2. Deploy updated configuration
echo "Deploying updated registry configuration..."
scp -P 1111 /tmp/docker-compose-registry.yml docker@192.168.50.215:/volume1/app/registry/docker-compose.yml

# 3. Restart registry with new configuration
echo "Restarting registry..."
ssh -p 1111 docker@192.168.50.215 "cd /volume1/app/registry && /usr/local/bin/docker-compose down && /usr/local/bin/docker-compose up -d"

# 4. Wait for registry to be ready
echo "Waiting for registry to be ready..."
sleep 5

# 5. Test registry
echo "Testing registry..."
curl -s http://192.168.50.215:1234/v2/ | jq .

# 6. Try push again
echo "Retrying push..."
docker push 192.168.50.215:1234/health:latest