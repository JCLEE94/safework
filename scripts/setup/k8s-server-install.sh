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

