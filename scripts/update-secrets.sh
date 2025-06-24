#!/bin/bash

# Update GitHub Secrets with Real Values
# Run this script after getting your actual credentials

echo "🔐 Updating GitHub Secrets with Real Credentials"
echo "================================================"
echo
echo "Current placeholder secrets are already set. Update them with real values:"
echo

echo "1. Docker Hub Token (create at https://hub.docker.com/settings/security):"
echo "   gh secret set DOCKERHUB_TOKEN --repo=qws941/health-management-system"
echo "   Current: dckr_pat_placeholder_token_here"
echo

echo "2. Registry Username (for registry.jclee.me):"
echo "   gh secret set REGISTRY_USERNAME --repo=qws941/health-management-system"
echo "   Current: registry_user_placeholder"
echo

echo "3. Registry Password (for registry.jclee.me):"
echo "   gh secret set REGISTRY_PASSWORD --repo=qws941/health-management-system"
echo "   Current: registry_password_placeholder"
echo

echo "4. SSH Password (for deployment server):"
echo "   gh secret set DEPLOY_PASSWORD --repo=qws941/health-management-system"
echo "   Current: ssh_password_placeholder"
echo

echo "✅ Already configured with correct values:"
echo "   - DOCKERHUB_USERNAME: qws941"
echo "   - DEPLOY_HOST: 192.168.50.215"
echo "   - DEPLOY_USER: docker"
echo "   - DEPLOY_PORT: 1111"
echo

echo "To verify all secrets:"
echo "   gh secret list --repo=qws941/health-management-system"
echo

echo "Once real credentials are set, GitHub Actions will work on push to main!"