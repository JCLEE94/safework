#!/bin/bash
set -e

echo "SafeWork Pro - 볼륨 디렉토리 설정 스크립트"
echo "============================================"

# 기본 디렉토리 경로
BASE_DIR="/opt/safework"
UPLOAD_DIR="$BASE_DIR/uploads"
LOGS_DIR="$BASE_DIR/logs"
POSTGRES_DIR="$BASE_DIR/postgres"
REDIS_DIR="$BASE_DIR/redis"

# 디렉토리 생성 함수
create_directory() {
    local dir_path=$1
    local description=$2
    
    echo "📁 $description 디렉토리 생성: $dir_path"
    
    if [ ! -d "$dir_path" ]; then
        sudo mkdir -p "$dir_path"
        echo "   ✅ 디렉토리 생성 완료"
    else
        echo "   ℹ️  디렉토리가 이미 존재합니다"
    fi
    
    # 권한 설정 (Docker 컨테이너에서 읽기/쓰기 가능)
    sudo chown -R 1000:1000 "$dir_path"
    sudo chmod -R 755 "$dir_path"
    echo "   🔒 권한 설정 완료 (1000:1000, 755)"
}

# 메인 기본 디렉토리 생성
echo "🚀 SafeWork Pro 기본 디렉토리 구조 생성 시작..."
sudo mkdir -p "$BASE_DIR"

# 각 서비스별 디렉토리 생성
create_directory "$UPLOAD_DIR" "업로드 파일"
create_directory "$LOGS_DIR" "로그 파일"
create_directory "$POSTGRES_DIR" "PostgreSQL 데이터"
create_directory "$REDIS_DIR" "Redis 데이터"

# 백업 디렉토리 생성
BACKUP_DIR="$BASE_DIR/backups"
create_directory "$BACKUP_DIR" "백업 파일"

# 설정 파일 디렉토리 생성
CONFIG_DIR="$BASE_DIR/config"
create_directory "$CONFIG_DIR" "설정 파일"

# .gitkeep 파일 생성 (빈 디렉토리 유지)
for dir in "$UPLOAD_DIR" "$LOGS_DIR" "$BACKUP_DIR" "$CONFIG_DIR"; do
    touch "$dir/.gitkeep"
done

# 디렉토리 구조 확인
echo ""
echo "📋 생성된 디렉토리 구조:"
echo "==============================="
sudo tree "$BASE_DIR" 2>/dev/null || sudo find "$BASE_DIR" -type d | sed 's|[^/]*/|- |g'

# 디스크 사용량 확인
echo ""
echo "💾 디스크 사용량:"
echo "================"
df -h "$BASE_DIR"

# 권한 확인
echo ""
echo "🔐 권한 확인:"
echo "============"
ls -la "$BASE_DIR"

echo ""
echo "✅ SafeWork Pro 볼륨 디렉토리 설정 완료!"
echo ""
echo "📝 다음 단계:"
echo "1. docker-compose -f docker-compose.final.yml up -d"
echo "2. docker logs safework-single"
echo "3. curl http://localhost:3001/health"
echo ""
echo "🗂️  볼륨 경로:"
echo "- 업로드: $UPLOAD_DIR"
echo "- 로그:   $LOGS_DIR" 
echo "- DB:     $POSTGRES_DIR"
echo "- Cache:  $REDIS_DIR"
echo "- 백업:   $BACKUP_DIR"