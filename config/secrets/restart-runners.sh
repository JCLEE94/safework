#!/bin/bash
# GitHub Actions Runners 재시작 스크립트
# Repository 변경 후 러너 재연결

set -e

echo "🔄 GitHub Actions Runners 재시작 중..."

RUNNER_DIR="/home/jclee/actions-runners"

# 실행 중인 러너 정지
echo "🛑 기존 러너들 정지 중..."
pkill -f "Runner.Listener" 2>/dev/null || echo "실행 중인 러너 없음"

# 잠시 대기
sleep 5

# 각 러너 재시작
for i in {1..6}; do
    RUNNER_PATH="$RUNNER_DIR/runner-$i"
    
    if [ -d "$RUNNER_PATH" ]; then
        echo "🚀 Runner-$i 시작 중..."
        
        cd "$RUNNER_PATH"
        
        # 백그라운드에서 러너 시작
        nohup ./run.sh > runner.log 2>&1 &
        
        echo "✅ Runner-$i 시작됨 (PID: $!)"
        
        # 잠시 대기 (동시 시작으로 인한 충돌 방지)
        sleep 2
    else
        echo "⚠️  Runner-$i 디렉토리 없음: $RUNNER_PATH"
    fi
done

echo "⏳ 러너 연결 대기 중 (10초)..."
sleep 10

# 러너 상태 확인
echo "📊 러너 상태 확인:"
ps aux | grep -E "Runner.Listener" | grep -v grep | wc -l | xargs echo "실행 중인 러너:"

# GitHub에서 러너 상태 확인
echo "🌐 GitHub 러너 상태:"
gh api repos/JCLEE94/health/actions/runners --jq '.runners[] | "\(.name): \(.status)"' 2>/dev/null || echo "API 호출 실패"

echo "✅ 러너 재시작 완료!"
echo "💡 러너가 offline 상태라면 몇 분 기다린 후 다시 확인하세요."