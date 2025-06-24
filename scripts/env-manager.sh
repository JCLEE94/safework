#!/bin/bash

# Environment Configuration Manager
# Helps manage environment files and configurations

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to print colored output
print_menu() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}    Environment Configuration Manager${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
    echo "1) Generate secure values"
    echo "2) Create production .env from template"
    echo "3) Validate environment configuration"
    echo "4) Show current configuration (masked)"
    echo "5) Export GitHub Actions variables"
    echo "6) Setup systemd environment file"
    echo "7) Backup current configuration"
    echo "8) Exit"
    echo ""
}

# Generate secure values
generate_secure_values() {
    echo -e "${GREEN}Generating secure values...${NC}"
    ./scripts/generate-secure-values.sh
}

# Create production env from template
create_production_env() {
    if [ -f ".env.production.example" ]; then
        if [ -f ".env.production" ]; then
            echo -e "${YELLOW}Warning: .env.production already exists!${NC}"
            read -p "Overwrite? (y/N): " confirm
            if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
                return
            fi
        fi
        cp .env.production.example .env.production
        echo -e "${GREEN}Created .env.production from template${NC}"
        echo -e "${YELLOW}Please update with your actual values${NC}"
    else
        echo -e "${RED}Error: .env.production.example not found${NC}"
    fi
}

# Validate environment configuration
validate_env() {
    echo -e "${BLUE}Validating environment configuration...${NC}"
    
    local env_file="${1:-.env}"
    local errors=0
    
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: $env_file not found${NC}"
        return 1
    fi
    
    # Check required variables
    local required_vars=(
        "POSTGRES_USER"
        "POSTGRES_PASSWORD"
        "POSTGRES_DB"
        "JWT_SECRET"
        "DATABASE_URL"
    )
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" "$env_file"; then
            echo -e "${RED}Missing required variable: $var${NC}"
            ((errors++))
        else
            value=$(grep "^$var=" "$env_file" | cut -d'=' -f2-)
            if [[ -z "$value" || "$value" == "change-this"* || "$value" == "your-"* ]]; then
                echo -e "${YELLOW}Warning: $var appears to have a placeholder value${NC}"
            fi
        fi
    done
    
    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✓ All required variables are present${NC}"
    else
        echo -e "${RED}✗ Found $errors missing variables${NC}"
    fi
}

# Show current configuration (masked)
show_config() {
    local env_file="${1:-.env}"
    
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: $env_file not found${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Current configuration (sensitive values masked):${NC}"
    echo ""
    
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        
        # Mask sensitive values
        if [[ "$key" =~ (PASSWORD|SECRET|TOKEN|KEY) ]]; then
            if [[ -n "$value" && ! "$value" =~ ^(change-this|your-) ]]; then
                value="****${value: -4}"
            fi
        fi
        
        echo "$key=$value"
    done < "$env_file"
}

# Export GitHub Actions variables
export_github_vars() {
    echo -e "${BLUE}GitHub Actions Repository Variables:${NC}"
    echo ""
    echo "Set these in your GitHub repository settings:"
    echo "Settings → Secrets and variables → Actions → Variables"
    echo ""
    echo "DOCKER_REGISTRY=registry.jclee.me"
    echo "DOCKER_IMAGE_NAME=health-management-system"
    echo ""
    echo -e "${BLUE}GitHub Actions Secrets:${NC}"
    echo "Set these in your GitHub repository settings:"
    echo "Settings → Secrets and variables → Actions → Secrets"
    echo ""
    echo "DOCKERHUB_USERNAME=<your-dockerhub-username>"
    echo "DOCKERHUB_TOKEN=<your-dockerhub-token>"
    echo "REGISTRY_USERNAME=<your-registry-username>"
    echo "REGISTRY_PASSWORD=<your-registry-password>"
}

# Setup systemd environment file
setup_systemd_env() {
    local systemd_env="/etc/sysconfig/health-management"
    
    echo -e "${BLUE}Creating systemd environment file...${NC}"
    
    if [ ! -f ".env.production" ]; then
        echo -e "${RED}Error: .env.production not found${NC}"
        echo "Please create it first using option 2"
        return 1
    fi
    
    # Create systemd environment file
    cat > health-management.env << 'EOF'
# Systemd Environment File for Health Management System
# Place this in /etc/sysconfig/health-management
EOF
    
    # Convert .env to systemd format
    grep -v '^#' .env.production | grep -v '^$' >> health-management.env
    
    echo -e "${GREEN}Created health-management.env${NC}"
    echo "To install:"
    echo "  sudo mkdir -p /etc/sysconfig"
    echo "  sudo cp health-management.env /etc/sysconfig/health-management"
    echo "  sudo chmod 600 /etc/sysconfig/health-management"
}

# Backup current configuration
backup_config() {
    local backup_dir="config-backups"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    
    mkdir -p "$backup_dir"
    
    local files_to_backup=(
        ".env"
        ".env.production"
        ".env.deploy"
        "docker-compose.yml"
        "docker-compose.production.yml"
    )
    
    local backed_up=0
    for file in "${files_to_backup[@]}"; do
        if [ -f "$file" ]; then
            cp "$file" "$backup_dir/${file}.${timestamp}"
            ((backed_up++))
        fi
    done
    
    if [ $backed_up -gt 0 ]; then
        echo -e "${GREEN}Backed up $backed_up files to $backup_dir/*.$timestamp${NC}"
    else
        echo -e "${YELLOW}No configuration files found to backup${NC}"
    fi
}

# Main loop
while true; do
    print_menu
    read -p "Select option: " choice
    echo ""
    
    case $choice in
        1) generate_secure_values ;;
        2) create_production_env ;;
        3) validate_env ;;
        4) show_config ;;
        5) export_github_vars ;;
        6) setup_systemd_env ;;
        7) backup_config ;;
        8) echo "Exiting..."; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done