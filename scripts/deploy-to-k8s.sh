#!/bin/bash
# SafeWork Pro K8s 배포 스크립트
# GitHub Actions 없이 직접 배포

set -e

echo "🚀 SafeWork Pro K8s 배포 시작"
echo "================================"

# 변수 설정
REGISTRY="registry.jclee.me"
IMAGE_NAME="safework"
NAMESPACE="safework"
DATE=$(date +%Y%m%d)
TIME=$(date +%H%M%S)
TAG="deploy-${DATE}-${TIME}"

# 1. Docker 이미지 태그
echo "📦 Docker 이미지 준비..."
# 현재 실행 중인 safework 컨테이너의 이미지 사용
CURRENT_IMAGE=$(docker ps --filter "name=safework" --format "{{.Image}}" | head -1)
if [ -z "$CURRENT_IMAGE" ]; then
    echo "❌ 실행 중인 SafeWork 컨테이너를 찾을 수 없습니다"
    exit 1
fi

echo "현재 이미지: ${CURRENT_IMAGE}"
docker tag ${CURRENT_IMAGE} ${REGISTRY}/${IMAGE_NAME}:${TAG}
docker tag ${CURRENT_IMAGE} ${REGISTRY}/${IMAGE_NAME}:latest

# 2. 레지스트리 푸시 (옵션)
echo ""
read -p "레지스트리에 푸시하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🔄 레지스트리에 푸시 중..."
    docker push ${REGISTRY}/${IMAGE_NAME}:${TAG}
    docker push ${REGISTRY}/${IMAGE_NAME}:latest
    echo "✅ 레지스트리 푸시 완료"
fi

# 3. K8s 배포 업데이트
echo ""
echo "📝 K8s 배포 업데이트..."
# deployment.yaml 수정
sed -i.bak "s|image: .*|image: ${REGISTRY}/${IMAGE_NAME}:${TAG}|g" k8s/safework/deployment.yaml
sed -i.bak "s|imagePullPolicy: Never|imagePullPolicy: Always|g" k8s/safework/deployment.yaml

# 4. K8s 적용
echo "🔧 K8s 리소스 적용..."
kubectl apply -f k8s/safework/deployment.yaml
kubectl apply -f k8s/safework/service.yaml
kubectl apply -f k8s/safework/ingress.yaml

# 5. 배포 상태 확인
echo ""
echo "⏳ 배포 상태 확인 중..."
kubectl rollout status deployment/safework -n ${NAMESPACE} --timeout=300s || true

# 6. 포드 상태
echo ""
echo "📊 포드 상태:"
kubectl get pods -n ${NAMESPACE} -l app=safework

# 7. 서비스 확인
echo ""
echo "🔗 서비스 상태:"
kubectl get svc -n ${NAMESPACE} | grep safework

# 8. 접근 정보
echo ""
echo "✅ 배포 완료!"
echo "================================"
echo "접근 방법:"
echo "- NodePort: http://192.168.50.110:32301"
echo "- Ingress: https://safework.jclee.me"
echo "- 로컬 Docker: http://192.168.50.100:3001"
echo ""
echo "상태 확인:"
echo "kubectl logs -f deployment/safework -n ${NAMESPACE}"
echo "kubectl describe pod -l app=safework -n ${NAMESPACE}"