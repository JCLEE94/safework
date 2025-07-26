#!/bin/bash

# SafeWork Frontend V2 Direct Deployment Script
# Deploys using the existing safework deployment as base

set -e

echo "========================================="
echo "SafeWork Frontend V2 Direct Deployment"
echo "========================================="

# Configuration
NAMESPACE="safework"
OLD_DEPLOYMENT="safework"
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
FRONTEND_DIR="$PROJECT_ROOT/safework-frontend-v2"

# Step 1: Build frontend
echo "Step 1: Building frontend..."
cd "$FRONTEND_DIR"
npm run build

# Step 2: Copy built files to existing container
echo ""
echo "Step 2: Updating existing deployment with new frontend..."

# Get a running pod
POD=$(kubectl get pod -n $NAMESPACE -l app=safework -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")

if [ -z "$POD" ]; then
    echo "❌ No running safework pod found"
    exit 1
fi

echo "Using pod: $POD"

# Create a temporary directory in the pod
kubectl exec -n $NAMESPACE $POD -- mkdir -p /tmp/new-frontend

# Copy the built files
echo "Copying built files..."
cd "$FRONTEND_DIR/dist"
tar czf - . | kubectl exec -n $NAMESPACE -i $POD -- tar xzf - -C /tmp/new-frontend

# Backup old frontend and replace with new
echo "Replacing frontend files..."
kubectl exec -n $NAMESPACE $POD -- bash -c "
    # Backup old frontend
    if [ -d /usr/share/nginx/html ]; then
        mv /usr/share/nginx/html /usr/share/nginx/html.backup-$(date +%Y%m%d-%H%M%S)
    fi
    
    # Move new frontend
    mv /tmp/new-frontend /usr/share/nginx/html
    
    # Reload nginx
    nginx -s reload || true
"

echo "✅ Frontend updated successfully"

# Step 3: Test the deployment
echo ""
echo "Step 3: Testing deployment..."
sleep 5

# Port forward for testing
kubectl port-forward -n $NAMESPACE $POD 8080:3001 &
PF_PID=$!
sleep 3

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8080" || echo "000")
kill $PF_PID 2>/dev/null || true

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Deployment successful!"
else
    echo "⚠️  Deployment verification failed (status: $HTTP_STATUS)"
fi

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "- URL: https://safework.jclee.me"
echo "- The new frontend V2 is now live"
echo "========================================="