#!/bin/bash
# SafeWork Pro - Production Environment Setup Script
# This script sets up the complete production environment

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="production"
APP_NAME="safework"
REGISTRY_URL="registry.jclee.me"
CHARTMUSEUM_URL="https://charts.jclee.me"
ARGOCD_URL="https://argo.jclee.me"

echo -e "${PURPLE}🚀 SafeWork Pro - Production Environment Setup${NC}"
echo "=============================================="
echo ""

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check required tools
    local tools=("kubectl" "helm" "docker" "curl")
    for tool in "${tools[@]}"; do
        if command -v "$tool" &> /dev/null; then
            echo -e "${GREEN}✅ $tool is installed${NC}"
        else
            echo -e "${RED}❌ $tool is not installed${NC}"
            exit 1
        fi
    done
    
    # Check cluster connectivity
    if kubectl cluster-info &> /dev/null; then
        echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
        kubectl cluster-info | head -1
    else
        echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
        exit 1
    fi
    
    echo ""
}

# Function to setup namespaces
setup_namespaces() {
    echo -e "${BLUE}📁 Setting up namespaces...${NC}"
    
    local namespaces=("production" "staging" "monitoring")
    
    for ns in "${namespaces[@]}"; do
        echo "Creating namespace: $ns"
        kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
    done
    
    echo -e "${GREEN}✅ Namespaces created successfully${NC}"
    echo ""
}

# Function to setup secrets
setup_secrets() {
    echo -e "${BLUE}🔐 Setting up secrets...${NC}"
    
    # Run the secrets recreation script
    if [ -f "scripts/recreate-secrets.sh" ]; then
        bash scripts/recreate-secrets.sh
    else
        echo -e "${YELLOW}⚠️  Secrets script not found. Creating basic secrets...${NC}"
        
        # Create basic registry secret
        kubectl create secret docker-registry regcred \
            --docker-server="$REGISTRY_URL" \
            --docker-username="admin" \
            --docker-password="bingogo1" \
            --namespace="$NAMESPACE" \
            --dry-run=client -o yaml | kubectl apply -f -
    fi
    
    echo ""
}

# Function to setup Helm repositories
setup_helm_repos() {
    echo -e "${BLUE}📦 Setting up Helm repositories...${NC}"
    
    # Add ChartMuseum repository
    if helm repo list | grep -q "jclee"; then
        echo "Helm repository already exists, updating..."
        helm repo update
    else
        echo "Adding ChartMuseum repository..."
        helm repo add jclee "$CHARTMUSEUM_URL" \
            --username admin \
            --password bingogo1
        helm repo update
    fi
    
    echo -e "${GREEN}✅ Helm repositories configured${NC}"
    echo ""
}

# Function to deploy application
deploy_application() {
    echo -e "${BLUE}🚀 Deploying SafeWork application...${NC}"
    
    # Check if ArgoCD application exists
    if kubectl get application "$APP_NAME-prod" -n argocd &> /dev/null; then
        echo "ArgoCD application already exists, syncing..."
        # Apply the latest application configuration
        kubectl apply -f k8s/argocd/application-optimized.yaml
    else
        echo "Creating ArgoCD application..."
        kubectl apply -f k8s/argocd/application-optimized.yaml
    fi
    
    echo -e "${GREEN}✅ Application deployment initiated${NC}"
    echo ""
}

# Function to verify deployment
verify_deployment() {
    echo -e "${BLUE}🔍 Verifying deployment...${NC}"
    
    # Wait for ArgoCD application to sync
    echo "Waiting for ArgoCD application to sync..."
    sleep 30
    
    # Check application status
    echo "Checking application status..."
    if kubectl get application "$APP_NAME-prod" -n argocd -o jsonpath='{.status.sync.status}' | grep -q "Synced"; then
        echo -e "${GREEN}✅ Application is synced${NC}"
    else
        echo -e "${YELLOW}⚠️  Application sync in progress...${NC}"
    fi
    
    # Check pod status
    echo "Checking pods in production namespace..."
    kubectl get pods -n "$NAMESPACE" | grep "$APP_NAME" || echo "No application pods found yet"
    
    # Check service status
    echo "Checking services..."
    kubectl get services -n "$NAMESPACE" | grep "$APP_NAME" || echo "No application services found yet"
    
    echo ""
}

# Function to display summary
display_summary() {
    echo -e "${PURPLE}📊 Production Setup Summary${NC}"
    echo "=========================="
    echo ""
    echo -e "${GREEN}✅ Environment setup completed!${NC}"
    echo ""
    echo -e "${BLUE}🔗 Important URLs:${NC}"
    echo "   🌐 Production: https://$APP_NAME.jclee.me"
    echo "   🚀 ArgoCD: $ARGOCD_URL"
    echo "   📦 Registry: https://$REGISTRY_URL"
    echo "   📈 Charts: $CHARTMUSEUM_URL"
    echo ""
    echo -e "${BLUE}🔧 Useful commands:${NC}"
    echo "   # Check application status"
    echo "   kubectl get application $APP_NAME-prod -n argocd"
    echo ""
    echo "   # Check pods"
    echo "   kubectl get pods -n $NAMESPACE"
    echo ""
    echo "   # Check logs"
    echo "   kubectl logs -f deployment/$APP_NAME -n $NAMESPACE"
    echo ""
    echo "   # Force ArgoCD sync"
    echo "   kubectl patch application $APP_NAME-prod -n argocd -p '{\"operation\":{\"sync\":{}}}' --type merge"
    echo ""
    echo "   # Restart deployment"
    echo "   kubectl rollout restart deployment/$APP_NAME -n $NAMESPACE"
    echo ""
    echo -e "${BLUE}📋 Next steps:${NC}"
    echo "1. Monitor ArgoCD application sync status"
    echo "2. Verify application health at production URL"
    echo "3. Configure monitoring and alerting"
    echo "4. Set up backup procedures"
    echo ""
}

# Main execution
main() {
    echo -e "${BLUE}Starting production setup...${NC}"
    echo ""
    
    check_prerequisites
    setup_namespaces
    setup_secrets
    setup_helm_repos
    deploy_application
    verify_deployment
    display_summary
    
    echo -e "${GREEN}🎉 Production setup completed successfully!${NC}"
}

# Run main function
main "$@"