#!/bin/bash
# SafeWork GitOps - ArgoCD Setup Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}SafeWork GitOps - ArgoCD Setup${NC}"
echo "================================="

# Check if ArgoCD is already installed
if kubectl get namespace argocd &> /dev/null; then
    echo -e "${YELLOW}ArgoCD namespace already exists, checking installation...${NC}"
    
    if kubectl get deployment argocd-server -n argocd &> /dev/null; then
        echo -e "${GREEN}ArgoCD is already installed and running${NC}"
        
        # Get ArgoCD admin password
        echo -e "${YELLOW}ArgoCD admin password:${NC}"
        kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
        echo ""
        
        # Check if Image Updater is installed
        if kubectl get deployment argocd-image-updater -n argocd &> /dev/null; then
            echo -e "${GREEN}ArgoCD Image Updater is already installed${NC}"
        else
            echo -e "${YELLOW}Installing ArgoCD Image Updater...${NC}"
            kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml
            echo "✓ ArgoCD Image Updater installed"
        fi
        
        exit 0
    fi
fi

echo -e "${YELLOW}Installing ArgoCD...${NC}"
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

echo -e "${YELLOW}Waiting for ArgoCD to be ready...${NC}"
kubectl wait --for=condition=available --timeout=300s deployment/argocd-server -n argocd

echo -e "${YELLOW}Installing ArgoCD Image Updater...${NC}"
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml

echo -e "${YELLOW}Configuring ArgoCD service...${NC}"
kubectl patch svc argocd-server -n argocd -p '{"spec": {"type": "LoadBalancer"}}'

echo -e "${YELLOW}Creating ArgoCD repository secret...${NC}"
kubectl create secret generic k8s-config-repo \
    --from-literal=type=git \
    --from-literal=url=https://github.com/JCLEE94/safework \
    --from-literal=username=not-used \
    --from-literal=password="${GITHUB_TOKEN:-replace-with-token}" \
    --namespace=argocd \
    --dry-run=client -o yaml | kubectl apply -f -

echo -e "${GREEN}ArgoCD setup completed successfully!${NC}"
echo ""
echo "ArgoCD UI: https://argo.jclee.me"
echo "Username: admin"
echo -e "${YELLOW}Password:${NC}"
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo ""
echo ""
echo "Next steps:"
echo "1. Access ArgoCD UI and change admin password"
echo "2. Create applications from k8s-config/argocd/applications/"
echo "3. Configure Image Updater for automated deployments"