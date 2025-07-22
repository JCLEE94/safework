#!/bin/bash
# SafeWork Pro - Kubernetes Secrets Recreation Script
# This script recreates all necessary secrets for the SafeWork deployment

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="production"
REGISTRY_URL="registry.jclee.me"
REGISTRY_USER="admin"
REGISTRY_PASS="bingogo1"
CHARTMUSEUM_URL="https://charts.jclee.me"

echo -e "${BLUE}🔐 SafeWork Pro - Recreating Kubernetes Secrets${NC}"
echo "================================================="
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check cluster connectivity
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Cannot connect to Kubernetes cluster${NC}"
    echo "   Please check your kubeconfig and cluster connectivity"
    exit 1
fi

echo -e "${GREEN}✅ Connected to Kubernetes cluster${NC}"
echo ""

# Create namespace if it doesn't exist
echo -e "${BLUE}📁 Creating namespace: ${NAMESPACE}${NC}"
kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

# Function to create Docker registry secret
create_registry_secret() {
    local namespace="$1"
    local secret_name="$2"
    
    echo -e "${BLUE}🔐 Creating Docker registry secret: ${secret_name} in ${namespace}${NC}"
    
    kubectl create secret docker-registry "${secret_name}" \
        --docker-server="${REGISTRY_URL}" \
        --docker-username="${REGISTRY_USER}" \
        --docker-password="${REGISTRY_PASS}" \
        --namespace="${namespace}" \
        --dry-run=client -o yaml | kubectl apply -f -
        
    echo -e "${GREEN}✅ Registry secret created: ${secret_name}${NC}"
}

# Function to create application secrets
create_app_secrets() {
    local namespace="$1"
    
    echo -e "${BLUE}🔐 Creating application secrets in ${namespace}${NC}"
    
    # Generate strong secrets if they don't exist
    JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 32)}"
    SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 32)}"
    DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 16)}"
    
    kubectl create secret generic safework-secrets \
        --from-literal=jwt-secret="${JWT_SECRET}" \
        --from-literal=secret-key="${SECRET_KEY}" \
        --from-literal=database-password="${DB_PASSWORD}" \
        --namespace="${namespace}" \
        --dry-run=client -o yaml | kubectl apply -f -
        
    echo -e "${GREEN}✅ Application secrets created: safework-secrets${NC}"
    echo -e "${YELLOW}⚠️  Please store these secrets securely:${NC}"
    echo "   JWT_SECRET: ${JWT_SECRET}"
    echo "   SECRET_KEY: ${SECRET_KEY}" 
    echo "   DB_PASSWORD: ${DB_PASSWORD}"
}

# Function to create ChartMuseum auth secret for ArgoCD
create_chartmuseum_secret() {
    echo -e "${BLUE}🔐 Creating ChartMuseum auth secret for ArgoCD${NC}"
    
    kubectl create secret generic chartmuseum-auth \
        --from-literal=username="${REGISTRY_USER}" \
        --from-literal=password="${REGISTRY_PASS}" \
        --namespace=argocd \
        --dry-run=client -o yaml | kubectl apply -f -
        
    echo -e "${GREEN}✅ ChartMuseum auth secret created${NC}"
}

# Create all secrets
echo -e "${BLUE}🚀 Creating Docker registry secrets...${NC}"
create_registry_secret "production" "regcred"
create_registry_secret "argocd" "regcred"

echo ""
echo -e "${BLUE}🚀 Creating application secrets...${NC}"
create_app_secrets "production"

echo ""
echo -e "${BLUE}🚀 Creating ChartMuseum secrets...${NC}"
create_chartmuseum_secret

echo ""
echo -e "${GREEN}✅ All secrets created successfully!${NC}"
echo ""

# Verification
echo -e "${BLUE}🔍 Verifying created secrets...${NC}"
echo ""

# Check production secrets
echo "Production namespace secrets:"
kubectl get secrets -n production | grep -E "(regcred|safework-secrets)" || echo "No production secrets found"

echo ""
echo "ArgoCD namespace secrets:"
kubectl get secrets -n argocd | grep -E "(regcred|chartmuseum-auth)" || echo "No ArgoCD secrets found"

echo ""
echo -e "${GREEN}🎉 Secret recreation completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next steps:${NC}"
echo "1. Verify secrets are correctly created"
echo "2. Update ArgoCD application if needed"
echo "3. Restart deployments if necessary:"
echo "   kubectl rollout restart deployment/safework -n production"
echo ""
echo -e "${BLUE}🔗 Useful commands:${NC}"
echo "# Test registry access:"
echo "kubectl run test-pod --image=${REGISTRY_URL}/jclee94/safework:latest --rm -i --tty --restart=Never -n production"
echo ""
echo "# Check secret contents:"
echo "kubectl get secret safework-secrets -n production -o yaml"