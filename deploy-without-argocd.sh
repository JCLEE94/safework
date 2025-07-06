#!/bin/bash
# Direct deployment script bypassing ArgoCD

echo "🚀 직접 Kubernetes에 배포합니다..."

# Set namespace
NAMESPACE="safework"

# Create namespace if not exists
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Apply all resources directly
echo "📦 Applying resources..."
kubectl apply -f k8s/safework/secrets.yaml -n $NAMESPACE
kubectl apply -f k8s/safework/deployment.yaml -n $NAMESPACE  
kubectl apply -f k8s/safework/ingress.yaml -n $NAMESPACE

# Check rollout status
echo "⏳ Waiting for deployment..."
kubectl rollout status deployment/safework -n $NAMESPACE --timeout=300s

# Show status
echo "📊 Current status:"
kubectl get pods,svc,ingress -n $NAMESPACE

# Test health endpoint
echo "🔍 Testing health endpoint..."
sleep 10
curl -s https://safework.jclee.me/health | jq . || echo "Service not ready yet"

echo "✅ Direct deployment completed!"