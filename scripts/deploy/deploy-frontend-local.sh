#!/bin/bash

# SafeWork Frontend V2 Local Deployment Script
# This script builds and deploys the new frontend to Kubernetes using local images

set -e

echo "========================================="
echo "SafeWork Frontend V2 Local Deployment"
echo "========================================="

# Configuration
REGISTRY="registry.jclee.me"
IMAGE_NAME="safework-frontend-v2"
NAMESPACE="safework"
OLD_FRONTEND_DEPLOYMENT="safework"

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
echo "✅ Image built successfully"

# Step 2: Update deployment to use local image
echo ""
echo "Step 2: Updating Kubernetes deployment..."
cd "$K8S_DIR"

# Create a temporary deployment file with imagePullPolicy set to Never for local images
cat > deployment-local.yaml <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: safework-frontend-v2
  namespace: $NAMESPACE
spec:
  replicas: 2
  selector:
    matchLabels:
      app: safework-frontend-v2
  template:
    metadata:
      labels:
        app: safework-frontend-v2
    spec:
      containers:
      - name: frontend
        image: $REGISTRY/$IMAGE_NAME:$BUILD_TAG
        imagePullPolicy: Never
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
        env:
        - name: NODE_ENV
          value: production
EOF

# Step 3: Apply to Kubernetes
echo ""
echo "Step 3: Applying to Kubernetes..."
kubectl apply -f deployment-local.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# Step 4: Wait for rollout
echo ""
echo "Step 4: Waiting for rollout to complete..."
kubectl rollout status deployment/safework-frontend-v2 -n $NAMESPACE --timeout=300s

# Step 5: Verify deployment
echo ""
echo "Step 5: Verifying deployment..."
kubectl get pods -n $NAMESPACE -l app=safework-frontend-v2
echo ""
kubectl get ingress -n $NAMESPACE safework-frontend-v2

# Step 6: Health check
echo ""
echo "Step 6: Performing health check..."
sleep 10
HEALTH_URL="https://safework-v2.jclee.me"
LOCAL_URL="http://localhost:8080"

# Try port-forward for local testing
echo "Setting up port-forward for local testing..."
kubectl port-forward -n $NAMESPACE svc/safework-frontend-v2 8080:80 &
PORT_FORWARD_PID=$!
sleep 5

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$LOCAL_URL" || echo "000")
kill $PORT_FORWARD_PID 2>/dev/null || true

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Local health check passed!"
    echo "Note: External URL $HEALTH_URL may take a few minutes to be accessible"
else
    echo "⚠️  Health check failed with status: $HTTP_STATUS"
    echo "Please check the deployment logs:"
    echo "kubectl logs -n $NAMESPACE -l app=safework-frontend-v2"
fi

# Step 7: Cleanup old frontend (optional)
echo ""
echo "Step 7: Old system cleanup"
echo "Current old system status:"
kubectl get deployment -n $NAMESPACE $OLD_FRONTEND_DEPLOYMENT 2>/dev/null || echo "Old system not found"

read -p "Do you want to delete the old system deployment? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Deleting old system..."
    kubectl delete deployment $OLD_FRONTEND_DEPLOYMENT -n $NAMESPACE 2>/dev/null || echo "Old deployment not found"
    kubectl delete service $OLD_FRONTEND_DEPLOYMENT -n $NAMESPACE 2>/dev/null || echo "Old service not found"
    kubectl delete configmap safework-config -n $NAMESPACE 2>/dev/null || echo "Old configmap not found"
    echo "✅ Old system deleted"
else
    echo "Keeping old system deployment"
fi

# Cleanup
rm -f deployment-local.yaml

echo ""
echo "========================================="
echo "Deployment Summary:"
echo "- Image: $REGISTRY/$IMAGE_NAME:$BUILD_TAG (local)"
echo "- Internal URL: http://safework-frontend-v2.$NAMESPACE.svc.cluster.local"
echo "- External URL: https://safework-v2.jclee.me"
echo "- Status: $([ "$HTTP_STATUS" = "200" ] && echo "✅ Running" || echo "⚠️  Check required")"
echo ""
echo "To test locally:"
echo "kubectl port-forward -n $NAMESPACE svc/safework-frontend-v2 8080:80"
echo "Then visit: http://localhost:8080"
echo "========================================="