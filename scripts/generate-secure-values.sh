#!/bin/bash

# Generate secure random values for production configuration
# This script helps create secure passwords and secrets

set -e

echo "🔐 Generating Secure Values for Production Configuration"
echo "======================================================="
echo ""

# Function to generate random string
generate_random_string() {
    local length=$1
    openssl rand -base64 $length | tr -d "=+/" | cut -c1-$length
}

# Generate values
JWT_SECRET=$(generate_random_string 64)
API_KEY_SALT=$(generate_random_string 32)
POSTGRES_PASSWORD=$(generate_random_string 24)
REDIS_PASSWORD=$(generate_random_string 24)
SESSION_SECRET=$(generate_random_string 32)

echo "# Generated Secure Values"
echo "# Copy these to your .env.production file"
echo "# Generated at: $(date)"
echo ""
echo "# Database"
echo "POSTGRES_PASSWORD=$POSTGRES_PASSWORD"
echo ""
echo "# Redis"
echo "REDIS_PASSWORD=$REDIS_PASSWORD"
echo ""
echo "# JWT"
echo "JWT_SECRET=$JWT_SECRET"
echo ""
echo "# API"
echo "API_KEY_SALT=$API_KEY_SALT"
echo ""
echo "# Session (if needed)"
echo "SESSION_SECRET=$SESSION_SECRET"
echo ""
echo "# Database URL (update with your actual values)"
echo "DATABASE_URL=postgresql://admin:$POSTGRES_PASSWORD@postgres:5432/health_management"
echo ""
echo "# Redis URL (if using password)"
echo "REDIS_URL=redis://:$REDIS_PASSWORD@redis:6379/0"
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Save these values securely - they won't be shown again"
echo "2. Never commit these values to version control"
echo "3. Use different values for each environment (dev/staging/prod)"
echo "4. Consider using a secrets management system for production"