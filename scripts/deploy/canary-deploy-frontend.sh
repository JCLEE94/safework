#!/bin/bash

# SafeWork Frontend Canary Deployment Script
# This script performs a canary deployment of the new frontend

set -e

echo "========================================="
echo "SafeWork Frontend Canary Deployment"
echo "========================================="

# Configuration
REGISTRY="registry.jclee.me"
IMAGE_NAME="safework-frontend-v2"
NAMESPACE="safework"
OLD_FRONTEND="safework-frontend"
NEW_FRONTEND="safework-frontend-v2"

# Get current traffic split
CURRENT_V1_WEIGHT=100
CURRENT_V2_WEIGHT=0

echo "Current traffic split:"
echo "- V1 (old): $CURRENT_V1_WEIGHT%"
echo "- V2 (new): $CURRENT_V2_WEIGHT%"
echo ""

# Step 1: Deploy V2 alongside V1
echo "Step 1: Ensuring V2 is deployed..."
./deploy-frontend-v2.sh

# Step 2: Create canary VirtualService for traffic splitting
echo ""
echo "Step 2: Creating canary traffic split configuration..."

cat > /tmp/canary-virtualservice.yaml <<EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: safework-frontend-canary
  namespace: $NAMESPACE
spec:
  hosts:
  - safework.jclee.me
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: $NEW_FRONTEND
        port:
          number: 80
  - route:
    - destination:
        host: $OLD_FRONTEND
        port:
          number: 80
      weight: 90
    - destination:
        host: $NEW_FRONTEND
        port:
          number: 80
      weight: 10
EOF

# Step 3: Apply canary configuration
echo ""
echo "Step 3: Applying canary configuration (10% to new version)..."
kubectl apply -f /tmp/canary-virtualservice.yaml

# Step 4: Monitor metrics
echo ""
echo "Step 4: Monitoring canary deployment..."
echo "Waiting 2 minutes to collect metrics..."
sleep 120

# Check error rates
echo ""
echo "Checking error rates..."
kubectl logs -n $NAMESPACE -l app=$NEW_FRONTEND --tail=100 | grep -i error || echo "No errors found in V2"

# Step 5: Progressive rollout
echo ""
read -p "Increase traffic to V2 to 50%? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > /tmp/canary-virtualservice-50.yaml <<EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: safework-frontend-canary
  namespace: $NAMESPACE
spec:
  hosts:
  - safework.jclee.me
  http:
  - route:
    - destination:
        host: $OLD_FRONTEND
        port:
          number: 80
      weight: 50
    - destination:
        host: $NEW_FRONTEND
        port:
          number: 80
      weight: 50
EOF
    kubectl apply -f /tmp/canary-virtualservice-50.yaml
    echo "✅ Traffic split updated to 50/50"
    
    echo "Monitoring for 2 minutes..."
    sleep 120
    
    read -p "Complete rollout to 100% V2? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Update ingress to point to V2
        kubectl patch ingress safework -n $NAMESPACE --type='json' \
          -p='[{"op": "replace", "path": "/spec/rules/0/http/paths/0/backend/service/name", "value":"'$NEW_FRONTEND'"}]'
        
        # Remove VirtualService
        kubectl delete virtualservice safework-frontend-canary -n $NAMESPACE 2>/dev/null || true
        
        echo "✅ Rollout complete! 100% traffic now going to V2"
        
        # Optional: Delete old deployment
        read -p "Delete old V1 deployment? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            kubectl delete deployment $OLD_FRONTEND -n $NAMESPACE
            kubectl delete service $OLD_FRONTEND -n $NAMESPACE
            echo "✅ Old V1 deployment deleted"
        fi
    fi
fi

# Cleanup
rm -f /tmp/canary-virtualservice*.yaml

echo ""
echo "========================================="
echo "Canary Deployment Complete"
echo "========================================="