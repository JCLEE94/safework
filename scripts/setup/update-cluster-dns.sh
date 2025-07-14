#!/bin/bash

# SafeWork - Update ArgoCD Cluster to External DNS
# Usage: ./update-cluster-dns.sh <new-cluster-url>

set -e

NEW_CLUSTER_URL=${1:-"https://k8s.jclee.me:6443"}
CLUSTER_NAME="jclee-k8s"

echo "🔧 Updating ArgoCD cluster configuration..."
echo "New Cluster URL: $NEW_CLUSTER_URL"

# Step 1: Add new cluster with external DNS
echo "📡 Adding new cluster configuration..."
argocd cluster add $CLUSTER_NAME \
  --grpc-web \
  --name $CLUSTER_NAME \
  --cluster-endpoint $NEW_CLUSTER_URL \
  --upsert \
  --yes

# Step 2: Verify new cluster
echo "✅ Verifying new cluster..."
argocd cluster list --grpc-web

# Step 3: Update application configurations
echo "📝 Updating application manifests..."

# Update safework application
sed -i "s|server: https://kubernetes.default.svc|server: $NEW_CLUSTER_URL|g" k8s/argocd/application.yaml
sed -i "s|server: https://kubernetes.default.svc|server: $NEW_CLUSTER_URL|g" k8s/argocd/application-*.yaml

# Update any other applications
find k8s/ -name "*.yaml" -exec grep -l "https://kubernetes.default.svc" {} \; | \
  xargs sed -i "s|https://kubernetes.default.svc|$NEW_CLUSTER_URL|g"

echo "📋 Updated files:"
grep -r "$NEW_CLUSTER_URL" k8s/ --include="*.yaml" | cut -d: -f1 | sort | uniq

# Step 4: Apply updated configurations
echo "🚀 Applying updated configurations..."
argocd app delete safework --grpc-web --yes || true
sleep 5
argocd app create --grpc-web -f k8s/argocd/application.yaml

echo "✅ Cluster DNS update completed!"
echo "🔗 New Cluster URL: $NEW_CLUSTER_URL"
echo "📊 ArgoCD Dashboard: https://argo.jclee.me/applications/safework"