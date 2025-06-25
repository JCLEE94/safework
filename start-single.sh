#!/bin/bash
set -e

echo "Starting SafeWork Pro Single Container..."

# Fix PostgreSQL permissions and initialize
echo "Fixing PostgreSQL permissions..."
chown -R postgres:postgres /var/lib/postgresql
chmod -R 755 /var/lib/postgresql
rm -rf /var/lib/postgresql/14/main/*
sudo -u postgres /usr/lib/postgresql/14/bin/initdb -D /var/lib/postgresql/14/main

# Start PostgreSQL
echo "Starting PostgreSQL..."
service postgresql start
sleep 3

# Setup database
echo "Setting up database..."
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = '$POSTGRES_DB'" | grep -q 1 || \
sudo -u postgres createdb $POSTGRES_DB

sudo -u postgres psql -c "SELECT 1 FROM pg_user WHERE usename = '$POSTGRES_USER'" | grep -q 1 || \
sudo -u postgres psql -c "CREATE USER $POSTGRES_USER WITH PASSWORD '$POSTGRES_PASSWORD';"

sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $POSTGRES_DB TO $POSTGRES_USER;"

# Start Redis
echo "Starting Redis..."
redis-server /etc/redis/redis.conf --daemonize yes
sleep 2

# Start application
echo "Starting SafeWork Pro application..."
cd /app
exec python3 main.py