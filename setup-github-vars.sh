#!/bin/bash
set -e

echo "📝 Setting up GitHub Variables using API..."

# GitHub repository info
OWNER="JCLEE94"
REPO="safework"

# Variables to set
declare -A VARIABLES=(
    ["APP_NAME"]="safework"
    ["NAMESPACE"]="safework"
    ["REGISTRY_URL"]="registry.jclee.me"
    ["CHARTMUSEUM_URL"]="https://charts.jclee.me"
    ["ARGOCD_URL"]="https://argo.jclee.me"
)

# Function to create or update variable
set_variable() {
    local VAR_NAME=$1
    local VAR_VALUE=$2
    
    echo -n "Setting $VAR_NAME... "
    
    # Check if variable exists
    if gh api repos/$OWNER/$REPO/actions/variables/$VAR_NAME &>/dev/null; then
        # Update existing variable
        gh api repos/$OWNER/$REPO/actions/variables/$VAR_NAME \
            --method PATCH \
            -f name="$VAR_NAME" \
            -f value="$VAR_VALUE" &>/dev/null
        echo "✅ Updated"
    else
        # Create new variable
        gh api repos/$OWNER/$REPO/actions/variables \
            --method POST \
            -f name="$VAR_NAME" \
            -f value="$VAR_VALUE" &>/dev/null
        echo "✅ Created"
    fi
}

# Set all variables
for VAR_NAME in "${!VARIABLES[@]}"; do
    set_variable "$VAR_NAME" "${VARIABLES[$VAR_NAME]}"
done

echo ""
echo "✅ GitHub Variables 설정 완료!"
echo ""
echo "설정된 변수:"
for VAR_NAME in "${!VARIABLES[@]}"; do
    echo "  - $VAR_NAME: ${VARIABLES[$VAR_NAME]}"
done