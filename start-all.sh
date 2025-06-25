#!/bin/bash
set -e

echo "Starting SafeWork Pro All-in-One Container..."

# Start PostgreSQL service
service postgresql start
sleep 5

# Create database and user if they don't exist
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
sudo -u postgres createdb $POSTGRES_DB

sudo -u postgres psql -c "SELECT 1 FROM pg_user WHERE usename = '$POSTGRES_USER'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;"

# Start Redis
service redis-server start
sleep 2

# Start Python application
echo "Starting SafeWork Pro application on port 3001..."
cd /app
export PORT=3001
python3 main.py