#!/bin/bash

# Manual GitHub Secrets Configuration Commands
# Run these commands after setting up GitHub CLI authentication

echo "GitHub Secrets Manual Configuration"
echo "=================================="
echo
echo "First, ensure you're authenticated with GitHub CLI:"
echo "  gh auth login"
echo
echo "Then run these commands to set the secrets:"
echo

cat << 'EOF'
# Docker Hub Credentials (for pulling base images)
gh secret set DOCKERHUB_USERNAME --repo=qws941/health-management-system
gh secret set DOCKERHUB_TOKEN --repo=qws941/health-management-system

# Private Registry Credentials (registry.jclee.me)
gh secret set REGISTRY_USERNAME --repo=qws941/health-management-system
gh secret set REGISTRY_PASSWORD --repo=qws941/health-management-system

# Deployment Server Credentials
echo "192.168.50.215" | gh secret set DEPLOY_HOST --repo=qws941/health-management-system
echo "docker" | gh secret set DEPLOY_USER --repo=qws941/health-management-system
gh secret set DEPLOY_PASSWORD --repo=qws941/health-management-system
echo "1111" | gh secret set DEPLOY_PORT --repo=qws941/health-management-system

# Optional: Slack Webhook (if you want notifications)
# gh secret set SLACK_WEBHOOK --repo=qws941/health-management-system

# Verify secrets are set
gh secret list --repo=qws941/health-management-system
EOF

echo
echo "Alternative: Set secrets through GitHub Web UI"
echo "============================================="
echo
echo "1. Go to: https://github.com/qws941/health-management-system/settings/secrets/actions"
echo "2. Click 'New repository secret' for each:"
echo
echo "Required secrets:"
echo "  - DOCKERHUB_USERNAME: Your Docker Hub username"
echo "  - DOCKERHUB_TOKEN: Docker Hub access token (create at https://hub.docker.com/settings/security)"
echo "  - REGISTRY_USERNAME: Username for registry.jclee.me"
echo "  - REGISTRY_PASSWORD: Password for registry.jclee.me"
echo "  - DEPLOY_HOST: 192.168.50.215"
echo "  - DEPLOY_USER: docker"
echo "  - DEPLOY_PASSWORD: SSH password for deployment"
echo "  - DEPLOY_PORT: 1111"
echo
echo "Optional:"
echo "  - SLACK_WEBHOOK: Slack webhook URL for notifications"