#!/bin/bash
# SafeWork Pro 수동 빌드 및 배포 스크립트
# GitHub Actions 빌링 문제 해결을 위한 로컬 빌드

set -e

# 변수 설정
REGISTRY="registry.jclee.me"
IMAGE_NAME="safework"
DATE=$(date +%Y%m%d)
SHORT_SHA=$(git rev-parse --short HEAD)
TAG="manual-${DATE}-${SHORT_SHA}"

echo "🔨 SafeWork Pro 수동 빌드 시작"
echo "Registry: ${REGISTRY}"
echo "Image: ${IMAGE_NAME}"
echo "Tag: ${TAG}"
echo "----------------------------------------"

# 1. 프론트엔드 빌드 (최소한)
echo "📱 프론트엔드 준비 중..."
mkdir -p frontend/dist
cat > frontend/dist/index.html << EOF
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SafeWork Pro - 건설업 보건관리 시스템</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            text-align: center; 
            padding: 50px; 
            background: #f8fafc;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #2563eb; margin-bottom: 10px; }
        .subtitle { color: #64748b; margin-bottom: 30px; }
        .status { 
            background: #10b981; 
            color: white; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0;
            font-weight: bold;
        }
        .info { 
            background: #f1f5f9; 
            padding: 15px; 
            border-radius: 5px; 
            margin: 20px 0;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        .nav {
            margin-top: 30px;
        }
        .nav a {
            display: inline-block;
            background: #3b82f6;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 0 10px;
        }
        .nav a:hover {
            background: #2563eb;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>SafeWork Pro</h1>
        <p class="subtitle">건설업 보건관리 시스템</p>
        
        <div class="status">
            ✅ 시스템 운영 중 - Build: ${TAG}
        </div>
        
        <div class="info">
            <strong>빌드 정보:</strong><br>
            태그: ${TAG}<br>
            커밋: ${SHORT_SHA}<br>
            빌드 시간: $(date +'%Y-%m-%d %H:%M:%S KST')
        </div>
        
        <div class="nav">
            <a href="/api/docs">API 문서</a>
            <a href="/api/v1/health">헬스체크</a>
            <a href="/api/v1/workers/">근로자 관리</a>
        </div>
        
        <p style="margin-top: 30px; color: #64748b; font-size: 14px;">
            Korean Occupational Safety and Health Management System
        </p>
    </div>
</body>
</html>
EOF

echo "✅ 프론트엔드 준비 완료"

# 2. Docker 이미지 빌드
echo "🐳 Docker 이미지 빌드 중..."
docker build -f deployment/Dockerfile -t ${REGISTRY}/${IMAGE_NAME}:${TAG} .
docker tag ${REGISTRY}/${IMAGE_NAME}:${TAG} ${REGISTRY}/${IMAGE_NAME}:latest

echo "✅ Docker 이미지 빌드 완료"

# 3. 이미지 정보 출력
echo "📊 빌드된 이미지:"
docker images | grep ${IMAGE_NAME} | head -5

# 4. 로컬 배포 (선택사항)
echo ""
echo "🚀 로컬 배포 옵션:"
echo "1. 현재 컨테이너 중지 및 새 이미지로 재시작:"
echo "   docker-compose down && docker-compose up -d"
echo ""
echo "2. 레지스트리에 푸시 (인증 필요):"
echo "   docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}"
echo "   docker push ${REGISTRY}/${IMAGE_NAME}:latest"
echo ""
echo "3. Kubernetes 배포 업데이트:"
echo "   kubectl set image deployment/safework safework=${REGISTRY}/${IMAGE_NAME}:${TAG} -n safework"
echo ""

# 5. 현재 실행 중인 컨테이너 확인
echo "📋 현재 SafeWork 컨테이너 상태:"
docker ps | grep safework || echo "SafeWork 컨테이너가 실행 중이지 않습니다"

echo ""
echo "🎉 수동 빌드 완료!"
echo "이미지: ${REGISTRY}/${IMAGE_NAME}:${TAG}"