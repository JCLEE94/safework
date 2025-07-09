#!/bin/bash

# Setup Cloudflare Service Tokens for SafeWork Pro
# This script helps create and configure service tokens for different services

set -e

echo "🔐 Cloudflare Service Token Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_requirements() {
    echo -e "${BLUE}Checking requirements...${NC}"
    
    if ! command -v kubectl &> /dev/null; then
        echo -e "${RED}❌ kubectl is not installed${NC}"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        echo -e "${RED}❌ jq is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Requirements met${NC}"
}

# Function to create service tokens in Cloudflare
create_service_tokens() {
    echo -e "\n${BLUE}Service Token Creation Guide${NC}"
    echo -e "${YELLOW}Please create the following service tokens in Cloudflare Zero Trust:${NC}"
    echo "1. Go to https://one.dash.cloudflare.com/"
    echo "2. Navigate to Access → Service Tokens"
    echo "3. Create tokens for each service:"
    echo ""
    echo "   📋 Required Service Tokens:"
    echo "   - safework-api          (API access authentication)"
    echo "   - safework-registry     (Docker registry access)"
    echo "   - safework-cicd         (CI/CD pipeline authentication)"
    echo "   - safework-monitoring   (Monitoring and health checks)"
    echo ""
    echo "4. For each token, copy the Client ID and Client Secret"
    echo ""
    
    read -p "Have you created all service tokens? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Please create the service tokens first, then run this script again.${NC}"
        exit 0
    fi
}

# Function to collect service token credentials
collect_credentials() {
    echo -e "\n${BLUE}Collecting Service Token Credentials${NC}"
    
    # Team Domain
    read -p "Enter your Cloudflare Team Domain (e.g., mycompany): " CLOUDFLARE_TEAM_DOMAIN
    
    # API Service Token
    echo -e "\n${YELLOW}📋 API Service Token (safework-api):${NC}"
    read -p "Client ID: " CF_SERVICE_TOKEN_API_CLIENT_ID
    read -s -p "Client Secret: " CF_SERVICE_TOKEN_API_CLIENT_SECRET
    echo
    
    # Registry Service Token
    echo -e "\n${YELLOW}📋 Registry Service Token (safework-registry):${NC}"
    read -p "Client ID: " CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID
    read -s -p "Client Secret: " CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET
    echo
    
    # CI/CD Service Token
    echo -e "\n${YELLOW}📋 CI/CD Service Token (safework-cicd):${NC}"
    read -p "Client ID: " CF_SERVICE_TOKEN_CICD_CLIENT_ID
    read -s -p "Client Secret: " CF_SERVICE_TOKEN_CICD_CLIENT_SECRET
    echo
    
    # Monitoring Service Token
    echo -e "\n${YELLOW}📋 Monitoring Service Token (safework-monitoring):${NC}"
    read -p "Client ID: " CF_SERVICE_TOKEN_MONITORING_CLIENT_ID
    read -s -p "Client Secret: " CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET
    echo
}

# Function to validate credentials
validate_credentials() {
    echo -e "\n${BLUE}Validating credentials...${NC}"
    
    # Basic validation
    if [[ -z "$CLOUDFLARE_TEAM_DOMAIN" ]]; then
        echo -e "${RED}❌ Team domain is required${NC}"
        exit 1
    fi
    
    if [[ -z "$CF_SERVICE_TOKEN_API_CLIENT_ID" || -z "$CF_SERVICE_TOKEN_API_CLIENT_SECRET" ]]; then
        echo -e "${RED}❌ API service token credentials are required${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Credentials validated${NC}"
}

# Function to create Kubernetes secret
create_kubernetes_secret() {
    echo -e "\n${BLUE}Creating Kubernetes Secret...${NC}"
    
    # Check if namespace exists
    if ! kubectl get namespace safework &> /dev/null; then
        echo -e "${YELLOW}Creating namespace 'safework'...${NC}"
        kubectl create namespace safework
    fi
    
    # Delete existing secret if it exists
    if kubectl get secret cloudflare-service-tokens -n safework &> /dev/null; then
        echo -e "${YELLOW}Deleting existing secret...${NC}"
        kubectl delete secret cloudflare-service-tokens -n safework
    fi
    
    # Create new secret
    kubectl create secret generic cloudflare-service-tokens -n safework \
        --from-literal=CLOUDFLARE_TEAM_DOMAIN="$CLOUDFLARE_TEAM_DOMAIN" \
        --from-literal=CF_SERVICE_TOKEN_API_CLIENT_ID="$CF_SERVICE_TOKEN_API_CLIENT_ID" \
        --from-literal=CF_SERVICE_TOKEN_API_CLIENT_SECRET="$CF_SERVICE_TOKEN_API_CLIENT_SECRET" \
        --from-literal=CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID="$CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID" \
        --from-literal=CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET="$CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET" \
        --from-literal=CF_SERVICE_TOKEN_CICD_CLIENT_ID="$CF_SERVICE_TOKEN_CICD_CLIENT_ID" \
        --from-literal=CF_SERVICE_TOKEN_CICD_CLIENT_SECRET="$CF_SERVICE_TOKEN_CICD_CLIENT_SECRET" \
        --from-literal=CF_SERVICE_TOKEN_MONITORING_CLIENT_ID="$CF_SERVICE_TOKEN_MONITORING_CLIENT_ID" \
        --from-literal=CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET="$CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET" \
        --from-literal=ENABLE_SERVICE_TOKEN_VALIDATION="true" \
        --from-literal=ENABLE_SERVICE_TOKEN_RATE_LIMITING="true" \
        --from-literal=ENABLE_SERVICE_TOKEN_AUDIT="true" \
        --from-literal=SERVICE_TOKEN_CACHE_TTL="300" \
        --from-literal=SERVICE_TOKEN_RATE_LIMIT_WINDOW="3600" \
        --from-literal=SERVICE_TOKEN_API_RATE_LIMIT="1000" \
        --from-literal=SERVICE_TOKEN_REGISTRY_RATE_LIMIT="500" \
        --from-literal=SERVICE_TOKEN_CICD_RATE_LIMIT="100" \
        --from-literal=SERVICE_TOKEN_MONITORING_RATE_LIMIT="2000"
    
    # Add labels to the secret
    kubectl label secret cloudflare-service-tokens -n safework \
        app=safework \
        component=authentication \
        security=service-tokens
    
    echo -e "${GREEN}✅ Kubernetes secret created successfully${NC}"
}

# Function to create GitHub secrets
create_github_secrets() {
    echo -e "\n${BLUE}Creating GitHub Secrets...${NC}"
    
    if ! command -v gh &> /dev/null; then
        echo -e "${YELLOW}⚠️  GitHub CLI not installed, skipping GitHub secrets creation${NC}"
        echo "To manually create GitHub secrets, run:"
        echo "gh secret set CF_SERVICE_TOKEN_API_CLIENT_ID --body \"$CF_SERVICE_TOKEN_API_CLIENT_ID\""
        echo "gh secret set CF_SERVICE_TOKEN_API_CLIENT_SECRET --body \"$CF_SERVICE_TOKEN_API_CLIENT_SECRET\""
        echo "gh secret set CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID --body \"$CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID\""
        echo "gh secret set CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET --body \"$CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET\""
        echo "gh secret set CF_SERVICE_TOKEN_CICD_CLIENT_ID --body \"$CF_SERVICE_TOKEN_CICD_CLIENT_ID\""
        echo "gh secret set CF_SERVICE_TOKEN_CICD_CLIENT_SECRET --body \"$CF_SERVICE_TOKEN_CICD_CLIENT_SECRET\""
        echo "gh secret set CF_SERVICE_TOKEN_MONITORING_CLIENT_ID --body \"$CF_SERVICE_TOKEN_MONITORING_CLIENT_ID\""
        echo "gh secret set CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET --body \"$CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET\""
        echo "gh secret set CLOUDFLARE_TEAM_DOMAIN --body \"$CLOUDFLARE_TEAM_DOMAIN\""
        return
    fi
    
    read -p "Create GitHub secrets? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        gh secret set CF_SERVICE_TOKEN_API_CLIENT_ID --body "$CF_SERVICE_TOKEN_API_CLIENT_ID"
        gh secret set CF_SERVICE_TOKEN_API_CLIENT_SECRET --body "$CF_SERVICE_TOKEN_API_CLIENT_SECRET"
        gh secret set CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID --body "$CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID"
        gh secret set CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET --body "$CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET"
        gh secret set CF_SERVICE_TOKEN_CICD_CLIENT_ID --body "$CF_SERVICE_TOKEN_CICD_CLIENT_ID"
        gh secret set CF_SERVICE_TOKEN_CICD_CLIENT_SECRET --body "$CF_SERVICE_TOKEN_CICD_CLIENT_SECRET"
        gh secret set CF_SERVICE_TOKEN_MONITORING_CLIENT_ID --body "$CF_SERVICE_TOKEN_MONITORING_CLIENT_ID"
        gh secret set CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET --body "$CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET"
        gh secret set CLOUDFLARE_TEAM_DOMAIN --body "$CLOUDFLARE_TEAM_DOMAIN"
        
        echo -e "${GREEN}✅ GitHub secrets created successfully${NC}"
    fi
}

# Function to test service token validation
test_service_token() {
    echo -e "\n${BLUE}Testing Service Token Validation...${NC}"
    
    # Get service ClusterIP
    SERVICE_IP=$(kubectl get svc safework -n safework -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
    
    if [[ -z "$SERVICE_IP" ]]; then
        echo -e "${YELLOW}⚠️  SafeWork service not found, skipping validation test${NC}"
        return
    fi
    
    # Test API service token
    echo "Testing API service token..."
    kubectl run service-token-test --image=curlimages/curl:latest --rm -i --restart=Never -- \
        curl -s -H "CF-Access-Client-Id: $CF_SERVICE_TOKEN_API_CLIENT_ID" \
        -H "CF-Access-Client-Secret: $CF_SERVICE_TOKEN_API_CLIENT_SECRET" \
        "http://$SERVICE_IP:3001/health" || echo "Test failed (this is expected if service is not running)"
    
    echo -e "${GREEN}✅ Service token test completed${NC}"
}

# Function to display summary
display_summary() {
    echo -e "\n${GREEN}🎉 Service Token Setup Complete!${NC}"
    echo "==============================="
    echo ""
    echo "✅ Created service tokens for:"
    echo "   - API access"
    echo "   - Registry access"
    echo "   - CI/CD pipeline"
    echo "   - Monitoring"
    echo ""
    echo "✅ Kubernetes secret created: cloudflare-service-tokens"
    echo "✅ Service token validation enabled"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Update your deployment to use the service tokens"
    echo "2. Restart your SafeWork Pro deployment"
    echo "3. Test API endpoints with service tokens"
    echo ""
    echo -e "${YELLOW}Important reminders:${NC}"
    echo "- Service tokens should be rotated every 3-6 months"
    echo "- Monitor token usage and audit logs"
    echo "- Keep token secrets secure and never commit to version control"
    echo ""
    echo "For documentation, see: docs/CLOUDFLARE_SERVICE_TOKENS_IMPLEMENTATION.md"
}

# Main execution
main() {
    echo -e "${BLUE}Starting Cloudflare Service Token Setup...${NC}"
    
    check_requirements
    create_service_tokens
    collect_credentials
    validate_credentials
    create_kubernetes_secret
    create_github_secrets
    test_service_token
    display_summary
    
    echo -e "\n${GREEN}Setup completed successfully! 🚀${NC}"
}

# Run main function
main "$@"