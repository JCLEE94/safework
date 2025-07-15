#!/bin/bash

# SafeWork GitOps ArgoCD 설정 스크립트

set -e

NAMESPACE="argocd"
ARGOCD_SERVER="argo.jclee.me"

echo "🚀 SafeWork GitOps ArgoCD 설정 시작..."

# 1. 기존 애플리케이션 정리
echo "1. 기존 애플리케이션 정리..."
kubectl get application -n $NAMESPACE safework -o name 2>/dev/null | xargs -r kubectl delete -n $NAMESPACE || echo "기존 safework 애플리케이션 없음"

# 2. ArgoCD 프로젝트 생성
echo "2. ArgoCD 프로젝트 생성..."
kubectl apply -f k8s/argocd/project-safework.yaml

# 3. 새로운 GitOps 애플리케이션 생성
echo "3. 새로운 GitOps 애플리케이션 생성..."
kubectl apply -f k8s/argocd/application-gitops.yaml

# 4. 권한 설정
echo "4. RBAC 설정..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: argocd-application-controller
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: argocd-application-controller
rules:
  - apiGroups: [""]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["apps"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["networking.k8s.io"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["rbac.authorization.k8s.io"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["batch"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["policy"]
    resources: ["*"]
    verbs: ["*"]
  - apiGroups: ["autoscaling"]
    resources: ["*"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: argocd-application-controller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: argocd-application-controller
subjects:
  - kind: ServiceAccount
    name: argocd-application-controller
    namespace: $NAMESPACE
EOF

# 5. 네임스페이스 확인 및 생성
echo "5. 네임스페이스 확인..."
kubectl get namespace safework || kubectl create namespace safework

# 6. ArgoCD 애플리케이션 상태 확인
echo "6. ArgoCD 애플리케이션 상태 확인..."
kubectl get application -n $NAMESPACE safework-gitops -o yaml

# 7. 초기 동기화
echo "7. 초기 동기화..."
kubectl patch application safework-gitops -n $NAMESPACE --type merge --patch='{"operation":{"sync":{"syncStrategy":{"hook":{"syncPolicy":"Background"}}}}}'

echo "✅ ArgoCD 설정 완료!"
echo "📊 ArgoCD 대시보드: https://$ARGOCD_SERVER/applications/safework-gitops"
echo "🔄 동기화 상태 확인: kubectl get application -n $NAMESPACE safework-gitops"
echo "📋 애플리케이션 로그: kubectl logs -n $NAMESPACE deployment/argocd-application-controller"