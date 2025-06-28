#!/bin/bash
set -e

echo "Starting SafeWork Pro All-in-One Container..."

# Function to wait for service
wait_for_service() {
    local service=$1
    local check_cmd=$2
    local max_attempts=30
    local attempt=0
    
    echo "Waiting for $service to be ready..."
    while [ $attempt -lt $max_attempts ]; do
        if eval "$check_cmd" >/dev/null 2>&1; then
            echo "$service is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        echo "Waiting for $service... (attempt $attempt/$max_attempts)"
        sleep 2
    done
    
    echo "ERROR: $service failed to start!"
    return 1
}

# Initialize PostgreSQL if needed
if [ ! -f "/var/lib/postgresql/data/PG_VERSION" ]; then
    echo "Initializing PostgreSQL..."
    su - postgres -c "initdb -D $PGDATA --encoding=UTF8 --locale=C.UTF-8"
fi

# Start PostgreSQL
echo "Starting PostgreSQL..."
su - postgres -c "pg_ctl -D $PGDATA -l /app/logs/postgres.log start"

# Wait for PostgreSQL
wait_for_service "PostgreSQL" "pg_isready -U postgres"

# Create database and user
echo "Setting up database..."
su - postgres -c "psql -c \"SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'\" | grep -q 1 || psql -c \"CREATE DATABASE $POSTGRES_DB;\""
su - postgres -c "psql -c \"SELECT 1 FROM pg_user WHERE usename = '$POSTGRES_USER'\" | grep -q 1 || psql -c \"CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';\""
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;\""

# Start Redis
echo "Starting Redis..."
redis-server /etc/redis/redis.conf --daemonize yes

# Wait for Redis
wait_for_service "Redis" "redis-cli ping"

# Start Python application
echo "Starting SafeWork Pro application on port 3001..."
cd /app
export PORT=3001
python3 main.py