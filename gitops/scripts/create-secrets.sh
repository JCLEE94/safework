#!/bin/bash
# SafeWork GitOps - Create Application Secrets

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SafeWork GitOps - Create Application Secrets${NC}"
echo "============================================="

# Function to create secrets for each environment
create_env_secrets() {
    local env=$1
    local namespace=$2
    
    echo -e "${YELLOW}Creating secrets for $env environment...${NC}"
    
    # Check if .env.secret file exists
    local env_file="../k8s-config/overlays/$env/.env.secret"
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: $env_file not found${NC}"
        return 1
    fi
    
    # Create secret from .env file
    kubectl create secret generic safework-secret \
        --from-env-file="$env_file" \
        --namespace=$namespace \
        --dry-run=client -o yaml | kubectl apply -f -
    
    echo "✓ Created safework-secret in namespace: $namespace"
}

# Create secrets for all environments
create_env_secrets "dev" "dev"
create_env_secrets "staging" "staging"
create_env_secrets "prod" "production"

echo -e "${YELLOW}Creating additional secrets...${NC}"

# Create TLS secrets if certificates are available
if [ -f "certs/tls.crt" ] && [ -f "certs/tls.key" ]; then
    for ns in dev staging production; do
        kubectl create secret tls safework-tls \
            --cert=certs/tls.crt \
            --key=certs/tls.key \
            --namespace=$ns \
            --dry-run=client -o yaml | kubectl apply -f -
        echo "✓ Created TLS secret in namespace: $ns"
    done
fi

echo -e "${GREEN}All secrets created successfully!${NC}"
echo ""
echo "Secrets summary:"
echo "- safework-secret: Application configuration secrets"
echo "- harbor-registry: Container registry authentication"
echo "- safework-tls: TLS certificates (if available)"
echo ""
echo "Next steps:"
echo "1. Verify secrets: kubectl get secrets -n <namespace>"
echo "2. Deploy applications via ArgoCD"
echo "3. Monitor application health"