#!/bin/bash
# Fix GitHub Actions Self-hosted Runner Permission Issues

echo "🔧 GitHub Actions Self-hosted Runner 권한 문제 해결 스크립트"
echo "=================================================="

# Runner 작업 디렉토리 찾기
RUNNER_WORK_DIR="/home/jclee/github_runner/github-runners/runner-*/_work"

echo "1. Runner 작업 디렉토리 권한 수정 중..."
for dir in $RUNNER_WORK_DIR; do
    if [ -d "$dir" ]; then
        echo "   - $dir 권한 수정"
        sudo chown -R $USER:$USER "$dir"
        sudo chmod -R 755 "$dir"
    fi
done

echo "2. SafeWork 프로젝트 디렉토리 권한 수정 중..."
SAFEWORK_DIRS="/home/jclee/github_runner/github-runners/runner-*/_work/safework"
for dir in $SAFEWORK_DIRS; do
    if [ -d "$dir" ]; then
        echo "   - $dir 완전 삭제"
        sudo rm -rf "$dir"
    fi
done

echo "3. Docker 권한 확인..."
if groups $USER | grep -q docker; then
    echo "   ✅ Docker 그룹에 속해있음"
else
    echo "   ❌ Docker 그룹에 추가 필요"
    sudo usermod -aG docker $USER
    echo "   ✅ Docker 그룹에 추가됨 (재로그인 필요)"
fi

echo "4. Runner 서비스 재시작..."
# Runner 서비스 재시작 (systemd service 이름은 환경에 따라 다를 수 있음)
for i in {1..4}; do
    SERVICE_NAME="actions.runner.JCLEE94-safework.runner-$i"
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "   - $SERVICE_NAME 재시작 중..."
        sudo systemctl restart $SERVICE_NAME
    fi
done

echo ""
echo "✅ 권한 문제 해결 완료!"
echo ""
echo "권장사항:"
echo "1. 이 스크립트를 정기적으로 실행하거나 CI/CD 실패 시 실행"
echo "2. Self-hosted runner 대신 Docker 컨테이너 기반 워크플로우 사용 권장"
echo "3. 또는 GitHub-hosted runner 사용 고려"