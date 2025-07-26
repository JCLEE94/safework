#!/bin/bash

# SafeWork Frontend V2 Deployment Script
# This script builds and deploys the new frontend to Kubernetes

set -e

echo "========================================="
echo "SafeWork Frontend V2 Deployment"
echo "========================================="

# Configuration
REGISTRY="registry.jclee.me"
IMAGE_NAME="safework-frontend-v2"
NAMESPACE="safework"
OLD_FRONTEND_DEPLOYMENT="safework-frontend"

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.."
FRONTEND_DIR="$PROJECT_ROOT/safework-frontend-v2"
K8S_DIR="$PROJECT_ROOT/k8s/safework-frontend-v2"

# Generate build tag
BUILD_TAG="v2-$(date +%Y%m%d)-$(git rev-parse --short HEAD 2>/dev/null || echo 'local')"
echo "Build tag: $BUILD_TAG"

# Step 1: Build Docker image
echo ""
echo "Step 1: Building Docker image..."
cd "$FRONTEND_DIR"

docker build -t "$REGISTRY/$IMAGE_NAME:$BUILD_TAG" .
docker tag "$REGISTRY/$IMAGE_NAME:$BUILD_TAG" "$REGISTRY/$IMAGE_NAME:latest"

# Step 2: Push to registry
echo ""
echo "Step 2: Pushing to registry..."
docker push "$REGISTRY/$IMAGE_NAME:$BUILD_TAG"
docker push "$REGISTRY/$IMAGE_NAME:latest"

# Step 3: Update Kubernetes manifests
echo ""
echo "Step 3: Updating Kubernetes manifests..."
cd "$K8S_DIR"
kustomize edit set image "$REGISTRY/$IMAGE_NAME=$REGISTRY/$IMAGE_NAME:$BUILD_TAG"

# Step 4: Apply to Kubernetes
echo ""
echo "Step 4: Applying to Kubernetes..."
kubectl apply -k .

# Step 5: Wait for rollout
echo ""
echo "Step 5: Waiting for rollout to complete..."
kubectl rollout status deployment/safework-frontend-v2 -n $NAMESPACE --timeout=300s

# Step 6: Verify deployment
echo ""
echo "Step 6: Verifying deployment..."
kubectl get pods -n $NAMESPACE -l app=safework-frontend-v2
echo ""
kubectl get ingress -n $NAMESPACE safework-frontend-v2

# Step 7: Health check
echo ""
echo "Step 7: Performing health check..."
sleep 10
HEALTH_URL="https://safework-v2.jclee.me"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Health check passed! Frontend is accessible at $HEALTH_URL"
else
    echo "⚠️  Health check failed with status: $HTTP_STATUS"
    echo "Please check the deployment logs:"
    echo "kubectl logs -n $NAMESPACE -l app=safework-frontend-v2"
fi

# Step 8: Cleanup old frontend (optional)
echo ""
echo "Step 8: Old frontend cleanup"
echo "Current old frontend status:"
kubectl get deployment -n $NAMESPACE $OLD_FRONTEND_DEPLOYMENT 2>/dev/null || echo "Old frontend not found"

read -p "Do you want to delete the old frontend deployment? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting old frontend deployment..."
    kubectl delete deployment $OLD_FRONTEND_DEPLOYMENT -n $NAMESPACE 2>/dev/null || echo "Old deployment not found"
    kubectl delete service $OLD_FRONTEND_DEPLOYMENT -n $NAMESPACE 2>/dev/null || echo "Old service not found"
    kubectl delete ingress $OLD_FRONTEND_DEPLOYMENT -n $NAMESPACE 2>/dev/null || echo "Old ingress not found"
    echo "✅ Old frontend deleted"
else
    echo "Keeping old frontend deployment"
fi

echo ""
echo "========================================="
echo "Deployment Summary:"
echo "- Image: $REGISTRY/$IMAGE_NAME:$BUILD_TAG"
echo "- URL: https://safework-v2.jclee.me"
echo "- Status: $([ "$HTTP_STATUS" = "200" ] && echo "✅ Running" || echo "⚠️  Check required")"
echo "========================================="