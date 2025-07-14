# Kubernetes API Server 외부 DNS 설정 가이드

## 1. 도메인 선택 및 등록

### 추천 도메인 구조
```
# Option 1: API 전용 서브도메인 (추천)
k8s-api.your-domain.com

# Option 2: 짧은 서브도메인
k8s.your-domain.com

# Option 3: 명시적 이름
kubernetes.your-domain.com
```

### 예시: jclee.me 도메인 사용 시
- `k8s-api.jclee.me` (추천)
- `k8s.jclee.me`
- `kubernetes.jclee.me`

## 2. DNS 레코드 설정

### A. Cloudflare DNS 설정
```bash
# API 토큰으로 DNS 레코드 생성
curl -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer {api_token}" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "k8s-api",
    "content": "YOUR_KUBERNETES_MASTER_IP",
    "ttl": 300,
    "comment": "Kubernetes API Server"
  }'
```

### B. 일반 DNS 제공업체
```
Type: A
Name: k8s-api
Value: YOUR_KUBERNETES_MASTER_IP
TTL: 300 (5분)
```

## 3. Kubernetes Master IP 확인

### 현재 클러스터의 Master IP 찾기
```bash
# 방법 1: kubectl을 통해 확인
kubectl cluster-info

# 방법 2: API 서버 설정 확인
kubectl get endpoints kubernetes -n default

# 방법 3: 노드 정보에서 확인
kubectl get nodes -o wide

# 방법 4: 서비스 정보 확인
kubectl get svc kubernetes -n default
```

## 4. SSL 인증서 설정

### A. Kubernetes API 서버 인증서 업데이트
```bash
# 1. 현재 인증서 확인
openssl s_client -connect YOUR_K8S_IP:6443 -servername k8s-api.your-domain.com

# 2. API 서버 설정 업데이트 (kube-apiserver.yaml)
# /etc/kubernetes/manifests/kube-apiserver.yaml에 추가:
--tls-san-dns=k8s-api.your-domain.com
--tls-san-dns=k8s.your-domain.com
--tls-san-ip=YOUR_PUBLIC_IP
```

### B. Let's Encrypt 인증서 (선택사항)
```bash
# cert-manager 설치
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# ClusterIssuer 생성
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@domain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

## 5. 방화벽 설정

### 포트 6443 외부 접근 허용
```bash
# Ubuntu/Debian
sudo ufw allow 6443/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=6443/tcp
sudo firewall-cmd --reload

# 클라우드 보안 그룹에서도 6443 포트 허용 필요
```

## 6. 테스트 및 검증

### DNS 해석 테스트
```bash
# DNS 해석 확인
nslookup k8s-api.your-domain.com
dig k8s-api.your-domain.com

# API 서버 접근 테스트
curl -k https://k8s-api.your-domain.com:6443/version
```

### kubectl 연결 테스트
```bash
# 새로운 kubeconfig 생성
kubectl config set-cluster external-cluster \
  --server=https://k8s-api.your-domain.com:6443 \
  --certificate-authority=/path/to/ca.crt

kubectl config set-credentials your-user \
  --client-certificate=/path/to/client.crt \
  --client-key=/path/to/client.key

kubectl config set-context external-context \
  --cluster=external-cluster \
  --user=your-user

kubectl config use-context external-context

# 연결 테스트
kubectl get nodes
```

## 7. 보안 고려사항

### A. 접근 제어
```bash
# 특정 IP만 허용하도록 설정
sudo iptables -A INPUT -p tcp --dport 6443 -s YOUR_ALLOWED_IP -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 6443 -j DROP
```

### B. VPN 사용 (추천)
- API 서버는 민감한 리소스이므로 VPN을 통한 접근 권장
- Cloudflare Access 또는 Tailscale 같은 Zero Trust 솔루션 사용

### C. 모니터링
```bash
# API 서버 접근 로그 모니터링
kubectl logs -n kube-system kube-apiserver-master-node
```

## 다음 단계

1. 도메인 선택 후 DNS 레코드 생성
2. Kubernetes Master IP 확인
3. SSL 인증서 설정
4. ArgoCD 클러스터 설정 업데이트
5. 접근 테스트 및 검증