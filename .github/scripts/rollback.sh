#!/bin/bash
# Rollback script for failed deployments

APP_NAME="${1:-safework}"
NAMESPACE="${2:-default}"
HEALTH_URL="${3:-https://safework.jclee.me/health}"

echo "🔄 Starting rollback procedure for $APP_NAME"

# Get current deployment info
CURRENT_IMAGE=$(kubectl get deployment $APP_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)

if [ -z "$CURRENT_IMAGE" ]; then
    echo "❌ Failed to get current image"
    exit 1
fi

echo "📸 Current image: $CURRENT_IMAGE"

# Get previous revision
PREVIOUS_REVISION=$(kubectl rollout history deployment/$APP_NAME -n $NAMESPACE | tail -2 | head -1 | awk '{print $1}')

if [ -z "$PREVIOUS_REVISION" ]; then
    echo "❌ No previous revision found"
    exit 1
fi

echo "⏮️  Rolling back to revision: $PREVIOUS_REVISION"

# Perform rollback
if kubectl rollout undo deployment/$APP_NAME -n $NAMESPACE --to-revision=$PREVIOUS_REVISION; then
    echo "✅ Rollback command executed"
    
    # Wait for rollout to complete
    echo "⏳ Waiting for rollout to complete..."
    kubectl rollout status deployment/$APP_NAME -n $NAMESPACE --timeout=300s
    
    # Verify health after rollback
    echo "🏥 Verifying application health..."
    sleep 30
    
    if curl -f "$HEALTH_URL"; then
        echo "✅ Rollback successful - application is healthy!"
        exit 0
    else
        echo "⚠️  Rollback completed but health check failed"
        exit 1
    fi
else
    echo "❌ Rollback command failed"
    exit 1
fi