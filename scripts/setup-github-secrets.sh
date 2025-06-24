#!/bin/bash

# GitHub Secrets Setup Script for SafeWork Pro
# This script helps configure GitHub repository secrets for CI/CD

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== GitHub Secrets Setup for SafeWork Pro ===${NC}"
echo

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}Error: GitHub CLI (gh) is not installed.${NC}"
    echo "Please install it from: https://cli.github.com/"
    exit 1
fi

# Check if authenticated
if ! gh auth status &> /dev/null; then
    echo -e "${YELLOW}GitHub CLI is not authenticated. Running 'gh auth login'...${NC}"
    gh auth login
fi

# Get repository info
REPO_OWNER="qws941"
REPO_NAME="health-management-system"

echo -e "${YELLOW}Setting up secrets for: ${REPO_OWNER}/${REPO_NAME}${NC}"
echo

# Function to set secret
set_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    echo -e "${YELLOW}Setting ${secret_name}...${NC}"
    echo -e "Description: ${description}"
    
    if [ -z "$secret_value" ]; then
        echo -n "Enter value for ${secret_name}: "
        read -s secret_value
        echo
    fi
    
    echo "$secret_value" | gh secret set "$secret_name" --repo="${REPO_OWNER}/${REPO_NAME}"
    echo -e "${GREEN}✓ ${secret_name} set successfully${NC}\n"
}

# Required secrets
echo -e "${GREEN}=== Required Secrets ===${NC}\n"

# Docker Hub credentials
echo -e "${YELLOW}1. Docker Hub Credentials${NC}"
echo "These are needed to pull base images during build."
set_secret "DOCKERHUB_USERNAME" "" "Your Docker Hub username"
set_secret "DOCKERHUB_TOKEN" "" "Docker Hub access token (not password)"

# Private Registry credentials
echo -e "${YELLOW}2. Private Registry Credentials${NC}"
echo "For pushing/pulling from registry.jclee.me"
set_secret "REGISTRY_USERNAME" "" "Private registry username"
set_secret "REGISTRY_PASSWORD" "" "Private registry password"

# Deployment credentials
echo -e "${YELLOW}3. Deployment Server Credentials${NC}"
echo "SSH access to production server (192.168.50.215)"
set_secret "DEPLOY_HOST" "192.168.50.215" "Production server hostname"
set_secret "DEPLOY_USER" "docker" "SSH username"
set_secret "DEPLOY_PASSWORD" "" "SSH password"
set_secret "DEPLOY_PORT" "1111" "SSH port"

# Optional secrets
echo -e "${GREEN}=== Optional Secrets ===${NC}\n"

echo -e "${YELLOW}4. Monitoring & Notifications (Optional)${NC}"
echo -n "Do you want to configure Slack webhook? (y/N): "
read -r configure_slack

if [[ "$configure_slack" =~ ^[Yy]$ ]]; then
    set_secret "SLACK_WEBHOOK" "" "Slack webhook URL for notifications"
fi

echo
echo -e "${GREEN}=== Verification ===${NC}"
echo "Listing configured secrets:"
gh secret list --repo="${REPO_OWNER}/${REPO_NAME}"

echo
echo -e "${GREEN}✓ GitHub secrets setup complete!${NC}"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Commit and push your changes"
echo "2. GitHub Actions will automatically trigger on push to main/develop"
echo "3. Monitor the Actions tab in your repository"
echo
echo -e "${YELLOW}To manually trigger deployment:${NC}"
echo "git push origin main"