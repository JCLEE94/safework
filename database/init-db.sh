#!/bin/bash
set -e

echo "🗄️ PostgreSQL 데이터베이스 초기화 중..."

# PostgreSQL 초기화
if [ ! -f /var/lib/postgresql/data/PG_VERSION ]; then
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/data"
    echo "host all all 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf
    echo "listen_addresses = '*'" >> /var/lib/postgresql/data/postgresql.conf
fi

# PostgreSQL 시작
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/data start"

# 데이터베이스 및 사용자 생성
echo "👤 데이터베이스 사용자 생성 중..."
su - postgres -c "psql -c \"CREATE USER admin WITH PASSWORD 'safework123';\"" || true
su - postgres -c "psql -c \"CREATE DATABASE health_management OWNER admin;\"" || true
su - postgres -c "psql -c \"GRANT ALL PRIVILEGES ON DATABASE health_management TO admin;\"" || true

echo "✅ PostgreSQL 초기화 완료"