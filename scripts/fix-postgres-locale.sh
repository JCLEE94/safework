#!/bin/bash

# PostgreSQL Locale Fix Script
# This script fixes the ko_KR.UTF-8 locale issue

echo "🔧 Fixing PostgreSQL locale issue..."

# Stop existing containers
docker-compose down

# Remove old postgres data (backup first if needed!)
if [ -d "postgres_data" ] || [ -d "/var/services/homes/docker/app/health/postgres_data" ]; then
    echo "⚠️  WARNING: This will remove existing PostgreSQL data!"
    echo "Press Ctrl+C to cancel, or Enter to continue..."
    read
    
    # Backup existing data
    BACKUP_DIR="postgres_backup_$(date +%Y%m%d_%H%M%S)"
    if [ -d "postgres_data" ]; then
        mv postgres_data "$BACKUP_DIR"
        echo "✅ Backed up existing data to $BACKUP_DIR"
    fi
    
    if [ -d "/var/services/homes/docker/app/health/postgres_data" ]; then
        sudo mv /var/services/homes/docker/app/health/postgres_data "/var/services/homes/docker/app/health/$BACKUP_DIR"
        echo "✅ Backed up existing data to /var/services/homes/docker/app/health/$BACKUP_DIR"
    fi
fi

# Create a Dockerfile for PostgreSQL with Korean locale support
cat > Dockerfile.postgres << 'EOF'
FROM postgres:15

# Install locales package
RUN apt-get update && apt-get install -y locales

# Generate Korean locale
RUN localedef -i ko_KR -c -f UTF-8 -A /usr/share/locale/locale.alias ko_KR.UTF-8

# Set locale environment variables
ENV LANG ko_KR.UTF-8
ENV LANGUAGE ko_KR:ko
ENV LC_ALL ko_KR.UTF-8

# Clean up
RUN apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

# Build custom PostgreSQL image
echo "🔨 Building custom PostgreSQL image with Korean locale..."
docker build -f Dockerfile.postgres -t postgres:15-ko .

# Update docker-compose to use custom image
if [ -f "docker-compose.yml" ]; then
    sed -i 's|image: postgres:15.*|image: postgres:15-ko|g' docker-compose.yml
    echo "✅ Updated docker-compose.yml"
fi

if [ -f "/var/services/homes/docker/app/health/docker-compose.yml" ]; then
    sed -i 's|image: postgres:15.*|image: postgres:15-ko|g' /var/services/homes/docker/app/health/docker-compose.yml
    echo "✅ Updated production docker-compose.yml"
fi

echo "✅ PostgreSQL locale fix complete!"
echo ""
echo "You can now run:"
echo "  docker-compose up -d"
echo ""
echo "Or use the Korean locale in POSTGRES_INITDB_ARGS:"
echo "  POSTGRES_INITDB_ARGS='--encoding=UTF-8 --lc-collate=ko_KR.UTF-8 --lc-ctype=ko_KR.UTF-8'"