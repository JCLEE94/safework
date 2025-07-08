# Cloudflare Tunnel을 통한 SafeWork 배포 가이드

이 문서는 SafeWork 애플리케이션을 Cloudflare Tunnel을 통해 안전하게 노출하는 방법을 설명합니다.

## 개요

Cloudflare Tunnel을 사용하면:
- 공용 IP나 포트 개방 없이 애플리케이션을 인터넷에 노출
- DDoS 보호 및 WAF 자동 적용
- SSL/TLS 자동 관리
- Zero Trust 액세스 정책 적용 가능

## 사전 요구사항

1. Cloudflare 계정 및 도메인
2. Kubernetes 클러스터
3. kubectl 및 ArgoCD 설치
4. Cloudflare Zero Trust 대시보드 접근 권한

## 배포 단계

### 1. Cloudflare Tunnel 생성

1. [Cloudflare Zero Trust 대시보드](https://one.dash.cloudflare.com/) 접속
2. **Networks** > **Tunnels** > **Create a tunnel** 클릭
3. **Cloudflared** 선택 후 터널 이름 입력 (예: `safework-tunnel`)
4. 토큰 복사 (eyJ로 시작하는 긴 문자열)

### 2. Kubernetes Secret 적용

```bash
# 네임스페이스가 없다면 생성
kubectl create namespace safework

# Secret 적용 (토큰이 이미 base64로 인코딩되어 있음)
kubectl apply -f k8s/cloudflare/tunnel-secret.yaml
```

### 3. Cloudflare Tunnel 배포

#### 옵션 A: 직접 배포
```bash
# Cloudflare Tunnel 배포
kubectl apply -f k8s/cloudflare/cloudflared-deployment.yaml
kubectl apply -f k8s/cloudflare/tunnel-config.yaml

# SafeWork 서비스를 ClusterIP로 변경
kubectl apply -f k8s/cloudflare/safework-service-clusterip.yaml
```

#### 옵션 B: Kustomize 사용
```bash
# Cloudflare Tunnel과 함께 SafeWork 배포
kubectl apply -k k8s/safework-with-cloudflare/
```

#### 옵션 C: ArgoCD 사용
```bash
# ArgoCD Application 생성
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: safework-cloudflare
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/JCLEE94/safework
    targetRevision: main
    path: k8s/safework-with-cloudflare
  destination:
    server: https://kubernetes.default.svc
    namespace: safework
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
    - CreateNamespace=true
EOF
```

### 4. Cloudflare 대시보드에서 라우팅 설정

1. Cloudflare Zero Trust 대시보드로 이동
2. **Networks** > **Tunnels** > 생성한 터널 선택
3. **Configure** 탭에서 **Public Hostname** 추가:
   - **Subdomain**: `safework` (또는 원하는 서브도메인)
   - **Domain**: `jclee.me` (귀하의 도메인)
   - **Path**: `/*`
   - **Service**: 
     - Type: `HTTP`
     - URL: `safework.safework.svc.cluster.local:3001`

### 5. 배포 확인

```bash
# Pod 상태 확인
kubectl get pods -n safework

# cloudflared 로그 확인
kubectl logs -n safework -l app=cloudflared

# 연결 상태 확인
kubectl exec -n safework deployment/cloudflared -- cloudflared tunnel info
```

### 6. 접속 테스트

브라우저에서 `https://safework.jclee.me` 접속하여 확인

## 문제 해결

### cloudflared Pod이 시작되지 않는 경우
```bash
# Secret 확인
kubectl get secret cloudflare-tunnel-token -n safework -o yaml

# Pod 이벤트 확인
kubectl describe pod -n safework -l app=cloudflared
```

### 터널이 연결되지 않는 경우
```bash
# cloudflared 로그 상세 확인
kubectl logs -n safework -l app=cloudflared --tail=100

# 네트워크 정책 확인
kubectl get networkpolicies -n safework
```

### 애플리케이션에 접근할 수 없는 경우
```bash
# Service 확인
kubectl get svc -n safework

# DNS 해결 테스트
kubectl exec -n safework deployment/cloudflared -- nslookup safework.safework.svc.cluster.local
```

## 보안 강화 (선택사항)

### 1. Access Policy 설정
Cloudflare Zero Trust 대시보드에서:
1. **Access** > **Applications** > **Add an application**
2. Self-hosted 선택
3. 애플리케이션 도메인 입력
4. 정책 설정 (예: 특정 이메일 도메인만 허용)

### 2. WAF 규칙 적용
1. Cloudflare 대시보드 > **Security** > **WAF**
2. Custom rules 생성
3. Rate limiting 설정

### 3. 추가 보안 헤더
```yaml
# cloudflared deployment에 환경 변수 추가
env:
- name: TUNNEL_ORIGIN_SERVER_NAME
  value: "safework.jclee.me"
- name: TUNNEL_NO_TLS_VERIFY
  value: "false"
```

## 모니터링

### Cloudflare 대시보드
- **Analytics** > **Tunnel Analytics**에서 트래픽 모니터링
- **Logs** > **Instant Logs**에서 실시간 로그 확인

### Kubernetes
```bash
# 메트릭 확인 (Prometheus metrics)
kubectl port-forward -n safework deployment/cloudflared 2000:2000
curl http://localhost:2000/metrics
```

## 업데이트 및 유지보수

### cloudflared 이미지 업데이트
```bash
kubectl set image -n safework deployment/cloudflared cloudflared=cloudflare/cloudflared:latest
```

### 터널 토큰 갱신
1. 새 토큰 생성
2. Secret 업데이트
3. Pod 재시작

## 주의사항

1. **토큰 보안**: `tunnel-secret.yaml` 파일을 Git에 커밋하지 마세요
2. **고가용성**: cloudflared deployment의 replica를 2개 이상 유지
3. **리소스 제한**: 프로덕션 환경에서는 적절한 리소스 limits 설정
4. **백업 계획**: Cloudflare 장애 시 대체 접근 방법 준비

## 참고 문서

- [Cloudflare Tunnel 공식 문서](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [Kubernetes 배포 가이드](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/deployment-guides/kubernetes/)
- [Zero Trust 정책 설정](https://developers.cloudflare.com/cloudflare-one/policies/access/)