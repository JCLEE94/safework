#!/bin/bash
# SafeWork GitOps - Deploy Applications

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SafeWork GitOps - Deploy Applications${NC}"
echo "===================================="

# Check if ArgoCD CLI is installed
if ! command -v argocd &> /dev/null; then
    echo -e "${RED}Error: ArgoCD CLI is not installed${NC}"
    echo "Install it from: https://argo-cd.readthedocs.io/en/stable/cli_installation/"
    exit 1
fi

# Login to ArgoCD
echo -e "${YELLOW}Logging into ArgoCD...${NC}"
argocd login argo.jclee.me \
    --username admin \
    --password $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d) \
    --insecure

# Deploy App of Apps
echo -e "${YELLOW}Deploying App of Apps...${NC}"
kubectl apply -f ../k8s-config/argocd/applications/app-of-apps.yaml
echo "✓ App of Apps deployed"

# Deploy individual applications
echo -e "${YELLOW}Deploying individual applications...${NC}"
kubectl apply -f ../k8s-config/argocd/applications/safework-dev.yaml
kubectl apply -f ../k8s-config/argocd/applications/safework-staging.yaml
kubectl apply -f ../k8s-config/argocd/applications/safework-prod.yaml

echo "✓ All applications deployed"

# Wait for applications to sync
echo -e "${YELLOW}Waiting for applications to sync...${NC}"
sleep 10

# Check application status
echo -e "${YELLOW}Application status:${NC}"
argocd app list

echo -e "${GREEN}Applications deployed successfully!${NC}"
echo ""
echo "ArgoCD UI: https://argo.jclee.me"
echo ""
echo "Application URLs:"
echo "- Dev: http://k8s.jclee.me:30001"
echo "- Staging: http://k8s.jclee.me:30002"  
echo "- Production: https://safework.jclee.me"
echo ""
echo "Monitor deployment:"
echo "- argocd app get safework-dev"
echo "- argocd app get safework-staging"
echo "- argocd app get safework-prod"