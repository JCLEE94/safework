#!/bin/bash
set -e

echo "🚀 Starting SafeWork Pro application..."

# 환경 변수 기본값 설정
export PORT=${PORT:-3001}
export ENVIRONMENT=${ENVIRONMENT:-production}
export PYTHONPATH=${PYTHONPATH:-/app}

# 데이터베이스 마이그레이션 실행
echo "📊 Running database migrations..."
if [ "$ENVIRONMENT" != "production" ] || [ "${SKIP_MIGRATIONS:-false}" != "true" ]; then
    python -m alembic upgrade head || echo "⚠️ Migration failed, continuing..."
else
    echo "⏭️ Skipping migrations in production"
fi

# Nginx 설정 확인
echo "🌐 Checking Nginx configuration..."
nginx -t || echo "⚠️ Nginx config test failed"

# supervisord로 서비스 시작
echo "🎯 Starting services with supervisord..."
exec supervisord -c /etc/supervisor/conf.d/supervisord.conf