#!/bin/bash
# Direct deployment script without ArgoCD

echo "🚀 Starting direct deployment to Kubernetes..."

# Set context
KUBECONFIG_PATH="/home/jclee/.kube/config"
export KUBECONFIG=$KUBECONFIG_PATH

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl is not installed"
    exit 1
fi

# Delete existing resources
echo "🗑️  Cleaning up existing resources..."
kubectl delete deployment safework -n safework --ignore-not-found=true
kubectl delete service safework -n safework --ignore-not-found=true
kubectl delete ingress safework-ingress -n safework --ignore-not-found=true

# Wait for cleanup
sleep 5

# Apply new resources
echo "📦 Applying new resources..."
kubectl apply -f k8s/safework/namespace.yaml
kubectl apply -f k8s/safework/secrets.yaml
kubectl apply -f k8s/safework/deployment.yaml
kubectl apply -f k8s/safework/ingress.yaml

# Check deployment status
echo "📊 Checking deployment status..."
kubectl rollout status deployment/safework -n safework --timeout=300s

# Show pods
echo "🔍 Current pods:"
kubectl get pods -n safework

# Show services
echo "🌐 Current services:"
kubectl get svc -n safework

echo "✅ Direct deployment completed!"