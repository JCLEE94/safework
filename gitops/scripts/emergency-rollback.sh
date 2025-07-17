#!/bin/bash
# SafeWork GitOps - Emergency Rollback Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}SafeWork GitOps - Emergency Rollback${NC}"
echo "===================================="

# Function to show usage
show_usage() {
    echo "Usage: $0 <environment> [revision]"
    echo "Environments: dev, staging, prod"
    echo "Revision: specific revision number (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 prod                 # Rollback to previous version"
    echo "  $0 staging 5            # Rollback to specific revision"
    echo "  $0 dev                  # Rollback dev environment"
}

# Check arguments
if [ $# -lt 1 ]; then
    show_usage
    exit 1
fi

ENVIRONMENT=$1
REVISION=${2:-""}

# Validate environment
case $ENVIRONMENT in
    dev|staging|prod)
        APP_NAME="safework-$ENVIRONMENT"
        ;;
    *)
        echo -e "${RED}Error: Invalid environment. Use: dev, staging, or prod${NC}"
        exit 1
        ;;
esac

# Check if ArgoCD CLI is installed
if ! command -v argocd &> /dev/null; then
    echo -e "${RED}Error: ArgoCD CLI is not installed${NC}"
    exit 1
fi

# Login to ArgoCD
echo -e "${YELLOW}Logging into ArgoCD...${NC}"
argocd login argo.jclee.me \
    --username admin \
    --password $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d) \
    --insecure

# Show current application status
echo -e "${YELLOW}Current application status:${NC}"
argocd app get $APP_NAME

# Show revision history
echo -e "${YELLOW}Revision history:${NC}"
argocd app history $APP_NAME

# Confirm rollback
echo -e "${RED}WARNING: This will rollback the $ENVIRONMENT environment!${NC}"
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled."
    exit 0
fi

# Perform rollback
if [ -n "$REVISION" ]; then
    echo -e "${YELLOW}Rolling back to revision $REVISION...${NC}"
    argocd app rollback $APP_NAME $REVISION
else
    echo -e "${YELLOW}Rolling back to previous version...${NC}"
    argocd app rollback $APP_NAME
fi

# Force sync to ensure rollback is applied
echo -e "${YELLOW}Force syncing application...${NC}"
argocd app sync $APP_NAME --force --prune

# Wait for rollback to complete
echo -e "${YELLOW}Waiting for rollback to complete...${NC}"
sleep 10

# Check final status
echo -e "${YELLOW}Final application status:${NC}"
argocd app get $APP_NAME

echo -e "${GREEN}Emergency rollback completed!${NC}"
echo ""
echo "Next steps:"
echo "1. Verify application is working correctly"
echo "2. Check logs: kubectl logs -n <namespace> -l app=safework"
echo "3. Monitor application health"
echo "4. Investigate root cause of the issue"