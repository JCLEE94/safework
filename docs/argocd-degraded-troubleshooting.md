# ArgoCD Degraded 상태 트러블슈팅 가이드

## Degraded 상태의 일반적인 원인

### 1. Health Check 실패
- **원인**: `/health` 엔드포인트가 응답하지 않음
- **확인 방법**:
  ```bash
  kubectl describe pod -l app=safework
  kubectl logs -l app=safework --tail=100
  ```

### 2. 리소스 부족
- **메모리/CPU 한계 초과**
- **확인 방법**:
  ```bash
  kubectl top pod -l app=safework
  kubectl describe node
  ```

### 3. 이미지 Pull 실패
- **Registry 인증 문제**
- **확인 방법**:
  ```bash
  kubectl describe pod -l app=safework | grep -A 10 Events
  kubectl get secret regcred -o yaml
  ```

### 4. 환경변수/시크릿 문제
- **필수 환경변수 누락**
- **확인 방법**:
  ```bash
  kubectl get secret safework-secrets -o yaml
  kubectl exec -it <pod-name> -- env | grep -E "(DATABASE|REDIS|JWT)"
  ```

## 즉시 확인할 사항

### 1. Pod 상태 확인
```bash
# Pod 목록 및 상태
kubectl get pods -n safework -l app=safework

# Pod 상세 정보
kubectl describe pod -n safework -l app=safework

# 최근 이벤트
kubectl get events -n safework --sort-by='.lastTimestamp' | tail -20
```

### 2. 로그 확인
```bash
# 애플리케이션 로그
kubectl logs -n safework -l app=safework --tail=100

# 이전 Pod 로그 (재시작된 경우)
kubectl logs -n safework -l app=safework --tail=100 --previous
```

### 3. 리소스 사용량 확인
```bash
# Pod 리소스 사용량
kubectl top pod -n safework -l app=safework

# Node 리소스 상태
kubectl top nodes
```

### 4. Health Check 테스트
```bash
# Pod 내부에서 health check
kubectl exec -n safework -it <pod-name> -- curl http://localhost:3001/health

# Service 경유 테스트
kubectl run test-curl --image=curlimages/curl --rm -it -- curl http://safework-service.safework:3001/health
```

## 일반적인 해결 방법

### 1. Pod 재시작
```bash
kubectl rollout restart deployment/safework -n safework
```

### 2. 리소스 한계 증가
```yaml
# deployment.yaml 수정
resources:
  requests:
    memory: "1Gi"    # 512Mi -> 1Gi
    cpu: "500m"      # 200m -> 500m
  limits:
    memory: "3Gi"    # 2Gi -> 3Gi
    cpu: "2000m"     # 1000m -> 2000m
```

### 3. Health Check 타이밍 조정
```yaml
livenessProbe:
  initialDelaySeconds: 120  # 90 -> 120
  periodSeconds: 30
  timeoutSeconds: 15        # 10 -> 15
  failureThreshold: 5       # 3 -> 5
```

### 4. 이미지 최신화
```bash
# ArgoCD에서 수동 동기화
argocd app sync safework --force

# 또는 kubectl로 직접
kubectl set image deployment/safework safework=registry.jclee.me/safework:latest -n safework
```

## 디버깅 스크립트

```bash
#!/bin/bash
# debug-safework.sh

echo "=== SafeWork 애플리케이션 디버깅 ==="

echo -e "\n1. Pod 상태:"
kubectl get pods -n safework -l app=safework -o wide

echo -e "\n2. 최근 이벤트:"
kubectl get events -n safework --field-selector involvedObject.name=safework --sort-by='.lastTimestamp' | tail -10

echo -e "\n3. Pod 로그 (에러만):"
kubectl logs -n safework -l app=safework --tail=50 | grep -E "(ERROR|CRITICAL|Failed|Exception)"

echo -e "\n4. 리소스 사용량:"
kubectl top pod -n safework -l app=safework

echo -e "\n5. Health Check 상태:"
POD_NAME=$(kubectl get pods -n safework -l app=safework -o jsonpath='{.items[0].metadata.name}')
kubectl exec -n safework $POD_NAME -- wget -qO- http://localhost:3001/health || echo "Health check failed"

echo -e "\n6. 환경변수 확인:"
kubectl exec -n safework $POD_NAME -- env | grep -E "(DATABASE_URL|REDIS_URL|JWT_SECRET)" | wc -l
echo "환경변수 개수: $(kubectl exec -n safework $POD_NAME -- env | grep -E "(DATABASE_URL|REDIS_URL|JWT_SECRET)" | wc -l)/3"
```

## ArgoCD 관련 확인사항

### 1. Sync 상태 확인
```bash
argocd app get safework --grpc-web
```

### 2. 리소스 Diff 확인
```bash
argocd app diff safework
```

### 3. 수동 Sync (필요시)
```bash
argocd app sync safework --prune --force
```

## 예상 원인 (SafeWork 특정)

1. **데이터베이스 연결 실패**
   - PostgreSQL 서비스 확인
   - DATABASE_URL 환경변수 확인

2. **Redis 연결 실패**
   - Redis 서비스 확인
   - REDIS_URL 환경변수 확인

3. **초기화 지연**
   - 데이터베이스 마이그레이션 시간
   - 대용량 정적 파일 로딩

4. **메모리 부족**
   - Python + PostgreSQL + Redis 동시 실행
   - 최소 1GB 메모리 필요

## 즉시 조치 사항

1. **로그 확인**:
   ```bash
   kubectl logs -n safework -l app=safework --tail=200
   ```

2. **이벤트 확인**:
   ```bash
   kubectl describe pod -n safework -l app=safework
   ```

3. **필요시 재시작**:
   ```bash
   kubectl rollout restart deployment/safework -n safework
   ```

이 가이드를 참고하여 Degraded 상태의 원인을 파악하고 해결하시기 바랍니다.