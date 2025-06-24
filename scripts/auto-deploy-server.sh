#!/bin/bash

# 서버에 설치할 자동 배포 스크립트
# registry.jclee.me와 같은 서버에서 실행

echo "📦 Registry Auto-Deploy Monitor"
echo "=============================="

PROJECT_NAME="health-management-system"
REGISTRY="localhost:5000"  # 로컬 registry
DEPLOY_PATH="~/app/health"

# Registry 이미지 변경 감지 및 자동 배포
watch_and_deploy() {
    while true; do
        echo "🔍 Checking for new image..."
        
        # 새 이미지가 있는지 확인
        LATEST_IMAGE=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.CreatedAt}}" | grep "$PROJECT_NAME:latest" | head -1)
        
        if [ -n "$LATEST_IMAGE" ]; then
            echo "📥 New image found: $LATEST_IMAGE"
            
            cd $DEPLOY_PATH
            
            # 자동 배포
            echo "🚀 Auto-deploying..."
            docker-compose pull
            docker-compose up -d --force-recreate
            
            # 헬스체크
            sleep 10
            if curl -f http://localhost:3001/health; then
                echo "✅ Auto-deployment successful!"
            else
                echo "❌ Auto-deployment failed!"
                docker-compose logs --tail=50 health-app
            fi
        fi
        
        # 1분마다 체크
        sleep 60
    done
}

case "$1" in
    start)
        echo "Starting auto-deploy monitor..."
        watch_and_deploy &
        echo $! > /tmp/auto-deploy.pid
        echo "Monitor started (PID: $(cat /tmp/auto-deploy.pid))"
        ;;
    stop)
        if [ -f /tmp/auto-deploy.pid ]; then
            kill $(cat /tmp/auto-deploy.pid)
            rm /tmp/auto-deploy.pid
            echo "Monitor stopped"
        fi
        ;;
    status)
        if [ -f /tmp/auto-deploy.pid ] && kill -0 $(cat /tmp/auto-deploy.pid) 2>/dev/null; then
            echo "Monitor is running (PID: $(cat /tmp/auto-deploy.pid))"
        else
            echo "Monitor is not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|status}"
        exit 1
        ;;
esac