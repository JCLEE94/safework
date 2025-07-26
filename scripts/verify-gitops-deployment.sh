#!/bin/bash
set -euo pipefail

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 로깅 함수
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 환경 변수
NAMESPACE="safework"
APP_NAME="safework"
NODEPORT="32301"
REGISTRY_URL="registry.jclee.me"
CHARTMUSEUM_URL="https://charts.jclee.me"
ARGOCD_URL="argo.jclee.me"

log_info "SafeWork Pro GitOps 배포 검증 시작"

# 검증 결과 수집
VERIFICATION_RESULTS=()

# 1. Kubernetes 리소스 확인
log_info "1. Kubernetes 리소스 상태 확인"
echo "----------------------------------------"

if kubectl get namespace ${NAMESPACE} > /dev/null 2>&1; then
  log_info "✅ 네임스페이스 ${NAMESPACE} 존재"
  VERIFICATION_RESULTS+=("✅ Namespace: OK")
else
  log_error "❌ 네임스페이스 ${NAMESPACE} 없음"
  VERIFICATION_RESULTS+=("❌ Namespace: FAIL")
fi

# Pod 상태 확인
echo ""
log_info "Pod 상태:"
if kubectl get pods -n ${NAMESPACE} -l app=${APP_NAME} 2>/dev/null; then
  POD_STATUS=$(kubectl get pods -n ${NAMESPACE} -l app=${APP_NAME} -o jsonpath='{.items[0].status.phase}' 2>/dev/null || echo "None")
  if [ "$POD_STATUS" = "Running" ]; then
    log_info "✅ Pod 실행 중"
    VERIFICATION_RESULTS+=("✅ Pod Status: Running")
  else
    log_warn "⚠ Pod 상태: $POD_STATUS"
    VERIFICATION_RESULTS+=("⚠ Pod Status: $POD_STATUS")
  fi
else
  log_error "❌ Pod 없음"
  VERIFICATION_RESULTS+=("❌ Pod: Not Found")
fi

# Service 상태 확인
echo ""
log_info "Service 상태:"
if kubectl get svc -n ${NAMESPACE} ${APP_NAME} 2>/dev/null; then
  SERVICE_NODEPORT=$(kubectl get svc -n ${NAMESPACE} ${APP_NAME} -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "None")
  if [ "$SERVICE_NODEPORT" = "$NODEPORT" ]; then
    log_info "✅ Service NodePort 올바름: $NODEPORT"
    VERIFICATION_RESULTS+=("✅ Service: OK ($NODEPORT)")
  else
    log_warn "⚠ Service NodePort 불일치: $SERVICE_NODEPORT (예상: $NODEPORT)"
    VERIFICATION_RESULTS+=("⚠ Service: Port Mismatch")
  fi
else
  log_error "❌ Service 없음"
  VERIFICATION_RESULTS+=("❌ Service: Not Found")
fi

# PVC 상태 확인
echo ""
log_info "PVC 상태:"
kubectl get pvc -n ${NAMESPACE} 2>/dev/null || log_warn "PVC 없음"

# 2. 애플리케이션 헬스체크
echo ""
log_info "2. 애플리케이션 헬스체크"
echo "----------------------------------------"

HEALTH_ENDPOINTS=(
  "https://safework.jclee.me/health"
  "http://localhost:${NODEPORT}/health"
)

for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
  echo ""
  log_info "헬스체크: $endpoint"
  if curl -f -s --connect-timeout 10 --max-time 30 "$endpoint" > /dev/null; then
    log_info "✅ $endpoint 응답 정상"
    VERIFICATION_RESULTS+=("✅ Health Check: $endpoint OK")
  else
    log_warn "⚠ $endpoint 응답 없음"
    VERIFICATION_RESULTS+=("⚠ Health Check: $endpoint FAIL")
  fi
done

# 3. Docker Registry 확인
echo ""
log_info "3. Docker Registry 이미지 확인"
echo "----------------------------------------"

log_info "최신 이미지 태그 확인 중..."
if LATEST_TAGS=$(curl -s ${REGISTRY_URL}/v2/${APP_NAME}/tags/list 2>/dev/null | jq -r '.tags[]?' 2>/dev/null | tail -5); then
  log_info "✅ Registry 접근 성공"
  log_info "최근 이미지 태그:"
  echo "$LATEST_TAGS" | sed 's/^/  - /'
  VERIFICATION_RESULTS+=("✅ Registry: OK")
else
  log_warn "⚠ Registry 접근 실패"
  VERIFICATION_RESULTS+=("⚠ Registry: FAIL")
fi

# 4. ChartMuseum 확인
echo ""
log_info "4. ChartMuseum Chart 확인"
echo "----------------------------------------"

log_info "Chart 버전 확인 중..."
if CHART_VERSIONS=$(curl -s -u admin:bingogo1 ${CHARTMUSEUM_URL}/api/charts/${APP_NAME} 2>/dev/null | jq -r '.[].version' 2>/dev/null | head -5); then
  log_info "✅ ChartMuseum 접근 성공"
  log_info "최근 Chart 버전:"
  echo "$CHART_VERSIONS" | sed 's/^/  - /'
  VERIFICATION_RESULTS+=("✅ ChartMuseum: OK")
else
  log_warn "⚠ ChartMuseum 접근 실패"
  VERIFICATION_RESULTS+=("⚠ ChartMuseum: FAIL")
fi

# 5. ArgoCD 애플리케이션 확인
echo ""
log_info "5. ArgoCD 애플리케이션 상태 확인"
echo "----------------------------------------"

if command -v argocd &> /dev/null; then
  # ArgoCD 로그인 시도
  if argocd login ${ARGOCD_URL} --username admin --password bingogo1 --insecure --grpc-web 2>/dev/null; then
    log_info "✅ ArgoCD 로그인 성공"
    
    # 애플리케이션 상태 확인
    if APP_STATUS=$(argocd app get safework-gitops --grpc-web -o json 2>/dev/null | jq -r '.status.sync.status' 2>/dev/null); then
      log_info "✅ ArgoCD 애플리케이션 상태: $APP_STATUS"
      VERIFICATION_RESULTS+=("✅ ArgoCD: $APP_STATUS")
      
      # 상세 정보 출력
      log_info "ArgoCD 애플리케이션 정보:"
      argocd app get safework-gitops --grpc-web 2>/dev/null | grep -E "(Health Status|Sync Status|Last Sync)" || true
    else
      log_warn "⚠ ArgoCD 애플리케이션 정보 조회 실패"
      VERIFICATION_RESULTS+=("⚠ ArgoCD: App Not Found")
    fi
  else
    log_warn "⚠ ArgoCD 로그인 실패"
    VERIFICATION_RESULTS+=("⚠ ArgoCD: Login Failed")
  fi
else
  log_warn "⚠ ArgoCD CLI 없음"
  VERIFICATION_RESULTS+=("⚠ ArgoCD: CLI Not Installed")
fi

# 6. 로그 확인
echo ""
log_info "6. 애플리케이션 로그 확인"
echo "----------------------------------------"

log_info "최근 애플리케이션 로그 (최근 20줄):"
kubectl logs -n ${NAMESPACE} -l app=${APP_NAME} --tail=20 2>/dev/null || log_warn "로그 조회 실패"

# 7. 검증 결과 요약
echo ""
echo "========================================"
log_info "🔍 GitOps 배포 검증 결과 요약"
echo "========================================"

for result in "${VERIFICATION_RESULTS[@]}"; do
  echo "  $result"
done

# 전체 결과 판정
SUCCESS_COUNT=$(printf '%s\n' "${VERIFICATION_RESULTS[@]}" | grep -c "✅" || echo "0")
WARNING_COUNT=$(printf '%s\n' "${VERIFICATION_RESULTS[@]}" | grep -c "⚠" || echo "0")
FAILURE_COUNT=$(printf '%s\n' "${VERIFICATION_RESULTS[@]}" | grep -c "❌" || echo "0")

echo ""
echo "📊 검증 통계:"
echo "  - 성공: ${SUCCESS_COUNT}개"
echo "  - 경고: ${WARNING_COUNT}개"
echo "  - 실패: ${FAILURE_COUNT}개"

echo ""
if [ "$FAILURE_COUNT" -eq 0 ] && [ "$SUCCESS_COUNT" -gt 0 ]; then
  log_info "🎉 GitOps 배포 검증 성공!"
  echo ""
  echo "🌐 접속 정보:"
  echo "  - 메인 사이트: https://safework.jclee.me"
  echo "  - NodePort: http://your-cluster:${NODEPORT}"
  echo "  - ArgoCD: https://${ARGOCD_URL}/applications/safework-gitops"
  echo ""
  echo "📋 관리 명령어:"
  echo "  - Pod 상태: kubectl get pods -n ${NAMESPACE}"
  echo "  - 로그 확인: kubectl logs -n ${NAMESPACE} -l app=${APP_NAME} -f"
  echo "  - ArgoCD 동기화: argocd app sync safework-gitops --grpc-web"
  exit 0
else
  log_error "❌ GitOps 배포에 문제가 있습니다."
  echo ""
  echo "🔧 문제 해결 단계:"
  echo "  1. kubectl get pods -n ${NAMESPACE} -o wide"
  echo "  2. kubectl describe pod -n ${NAMESPACE} -l app=${APP_NAME}"
  echo "  3. kubectl logs -n ${NAMESPACE} -l app=${APP_NAME}"
  echo "  4. argocd app get safework-gitops --grpc-web"
  exit 1
fi