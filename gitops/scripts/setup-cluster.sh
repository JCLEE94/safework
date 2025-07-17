#!/bin/bash
# SafeWork GitOps - Cluster Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SafeWork GitOps - Cluster Setup${NC}"
echo "================================="

# Check if kubectl is configured
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}Error: kubectl is not configured or cluster is not accessible${NC}"
    exit 1
fi

# Set environment variables
export REGISTRY_URL=${REGISTRY_URL:-registry.jclee.me}
export REGISTRY_USER=${REGISTRY_USER:-admin}
export REGISTRY_PASS=${REGISTRY_PASS:-bingogo1}

echo -e "${YELLOW}Creating namespaces...${NC}"
for ns in argocd dev staging production monitoring; do
    kubectl create namespace $ns --dry-run=client -o yaml | kubectl apply -f -
    echo "✓ Namespace: $ns"
done

echo -e "${YELLOW}Creating Harbor registry secrets...${NC}"
for ns in argocd dev staging production; do
    kubectl create secret docker-registry harbor-registry \
        --docker-server=${REGISTRY_URL} \
        --docker-username=${REGISTRY_USER} \
        --docker-password=${REGISTRY_PASS} \
        --namespace=$ns \
        --dry-run=client -o yaml | kubectl apply -f -
    echo "✓ Harbor secret in namespace: $ns"
done

echo -e "${YELLOW}Creating default service accounts...${NC}"
for ns in dev staging production; do
    kubectl patch serviceaccount default -n $ns -p '{"imagePullSecrets": [{"name": "harbor-registry"}]}'
    echo "✓ Service account patched in namespace: $ns"
done

echo -e "${GREEN}Cluster setup completed successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Run ./setup-argocd.sh to configure ArgoCD"
echo "2. Run ./create-secrets.sh to create application secrets"
echo "3. Deploy applications via ArgoCD UI"