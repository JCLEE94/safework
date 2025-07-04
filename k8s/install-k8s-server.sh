#!/bin/bash

# SafeWork K8s 클러스터 서버 설치 스크립트
# 대상 서버: 192.168.50.110

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 서버 정보
SERVER_HOST="192.168.50.110"
SERVER_USER="root"  # 또는 ubuntu

log "SafeWork K8s 클러스터 서버 설치 시작 (${SERVER_HOST})"

# 1. 서버 연결 테스트
log "서버 연결 테스트 중..."
if ping -c 1 ${SERVER_HOST} &> /dev/null; then
    success "서버 연결 확인됨"
else
    error "서버 연결 실패"
    exit 1
fi

# 2. K8s 설치 스크립트 생성
log "K8s 설치 스크립트 생성 중..."
cat > k8s-server-install.sh << 'EOF'
#!/bin/bash

set -e

echo "=== SafeWork K8s 클러스터 설치 시작 ==="

# 시스템 업데이트
echo "시스템 업데이트 중..."
apt-get update -y
apt-get upgrade -y

# Docker 설치
echo "Docker 설치 중..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl enable docker
    systemctl start docker
    usermod -aG docker root
    usermod -aG docker ubuntu 2>/dev/null || true
fi

# containerd 설정
echo "containerd 설정 중..."
cat > /etc/modules-load.d/containerd.conf << EOL
overlay
br_netfilter
EOL

modprobe overlay
modprobe br_netfilter

cat > /etc/sysctl.d/99-kubernetes-cri.conf << EOL
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOL

sysctl --system

# kubeadm, kubelet, kubectl 설치
echo "Kubernetes 도구 설치 중..."
apt-get install -y apt-transport-https ca-certificates curl gpg

curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.28/deb/Release.key | gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.28/deb/ /' | tee /etc/apt/sources.list.d/kubernetes.list

apt-get update -y
apt-get install -y kubelet kubeadm kubectl
apt-mark hold kubelet kubeadm kubectl

systemctl enable kubelet

# swap 비활성화
echo "swap 비활성화 중..."
swapoff -a
sed -i '/swap/d' /etc/fstab

# 클러스터 초기화
echo "K8s 클러스터 초기화 중..."
kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=192.168.50.110

# kubectl 설정
mkdir -p /root/.kube
cp -i /etc/kubernetes/admin.conf /root/.kube/config
chown root:root /root/.kube/config

# ubuntu 사용자용 설정
if id "ubuntu" &>/dev/null; then
    mkdir -p /home/ubuntu/.kube
    cp -i /etc/kubernetes/admin.conf /home/ubuntu/.kube/config
    chown ubuntu:ubuntu /home/ubuntu/.kube/config
fi

# 네트워크 플러그인 (Flannel) 설치
echo "네트워크 플러그인 설치 중..."
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# 단일 노드 클러스터 설정 (마스터 노드에서 Pod 실행 허용)
kubectl taint nodes --all node-role.kubernetes.io/control-plane-

# NGINX Ingress Controller 설치
echo "NGINX Ingress Controller 설치 중..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.8.2/deploy/static/provider/baremetal/deploy.yaml

# MetalLB 설치 (LoadBalancer 지원)
echo "MetalLB 설치 중..."
kubectl apply -f https://raw.githubusercontent.com/metallb/metallb/v0.13.12/config/manifests/metallb-native.yaml

# MetalLB 설정
cat > metallb-config.yaml << EOL
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: first-pool
  namespace: metallb-system
spec:
  addresses:
  - 192.168.50.200-192.168.50.250
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: example
  namespace: metallb-system
spec:
  ipAddressPools:
  - first-pool
EOL

# MetalLB가 준비될 때까지 대기
echo "MetalLB 준비 대기 중..."
kubectl wait --namespace metallb-system --for=condition=ready pod --selector=app=metallb --timeout=300s

kubectl apply -f metallb-config.yaml

# 클러스터 상태 확인
echo "클러스터 상태 확인 중..."
kubectl get nodes
kubectl get pods --all-namespaces

echo "=== K8s 클러스터 설치 완료 ==="
echo "클러스터 IP: 192.168.50.110:6443"
echo "Ingress Controller: NodePort 방식"
echo "LoadBalancer: MetalLB (192.168.50.200-250)"

# kubeconfig 백업
cp /root/.kube/config /root/kubeconfig-backup
echo "kubeconfig 파일이 /root/kubeconfig-backup에 백업되었습니다"

EOF

chmod +x k8s-server-install.sh

# 3. 서버에 스크립트 전송
log "서버에 설치 스크립트 전송 중..."
if command -v scp &> /dev/null; then
    scp -o StrictHostKeyChecking=no k8s-server-install.sh ${SERVER_USER}@${SERVER_HOST}:/tmp/ || {
        warning "SCP 전송 실패, SSH 키 설정이 필요할 수 있습니다"
        echo "수동으로 다음 명령어를 실행하세요:"
        echo "scp k8s-server-install.sh ${SERVER_USER}@${SERVER_HOST}:/tmp/"
        exit 1
    }
else
    error "scp 명령어를 찾을 수 없습니다"
    exit 1
fi

# 4. 서버에서 K8s 설치 실행
log "서버에서 K8s 설치 실행 중..."
if command -v ssh &> /dev/null; then
    ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_HOST} "sudo bash /tmp/k8s-server-install.sh" || {
        warning "SSH 실행 실패"
        echo "수동으로 다음 명령어를 실행하세요:"
        echo "ssh ${SERVER_USER}@${SERVER_HOST}"
        echo "sudo bash /tmp/k8s-server-install.sh"
        exit 1
    }
else
    error "ssh 명령어를 찾을 수 없습니다"
    exit 1
fi

# 5. kubeconfig 가져오기
log "kubeconfig 파일 가져오는 중..."
scp -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_HOST}:/root/kubeconfig-backup ./kubeconfig-server || {
    warning "kubeconfig 가져오기 실패"
}

# 6. 로컬 kubectl 설정
if [ -f "./kubeconfig-server" ]; then
    log "로컬 kubectl 설정 중..."
    mkdir -p ~/.kube
    cp ./kubeconfig-server ~/.kube/config-server
    
    # 서버 IP로 수정
    sed -i "s/https:\/\/.*:6443/https:\/\/${SERVER_HOST}:6443/g" ~/.kube/config-server
    
    echo "로컬에서 서버 클러스터에 연결하려면:"
    echo "export KUBECONFIG=~/.kube/config-server"
    echo "kubectl get nodes"
fi

# 7. 정리
rm -f k8s-server-install.sh

success "SafeWork K8s 클러스터 설치 완료!"
echo ""
echo "=== 클러스터 정보 ==="
echo "마스터 노드: ${SERVER_HOST}:6443"
echo "네트워크: Flannel (10.244.0.0/16)"
echo "Ingress: NGINX Controller"
echo "LoadBalancer: MetalLB (192.168.50.200-250)"
echo ""
echo "=== 다음 단계 ==="
echo "1. export KUBECONFIG=~/.kube/config-server"
echo "2. kubectl get nodes"
echo "3. kubectl apply -f k8s/"
echo ""
echo "=== GitHub Secrets 설정 ==="
echo "KUBECONFIG: $(cat ~/.kube/config-server | base64 -w 0)"