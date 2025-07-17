#!/bin/bash
# SafeWork GitOps Environment Variables Template

# === 필수 인증 정보 ===
export K8S_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6Ikxobzc1NUhuUmV0S0pJQTkwN1F5dUZtcDdUeXlKRTdSX2t6NGo0ZWlmUUUifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJjbHVzdGVyLWFkbWluLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImNsdXN0ZXItYWRtaW4tc2EiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIzNWVmNDQxMS01NjRiLTQyNjItODM1Ni05YTI5YjE5NmQzNWQiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06Y2x1c3Rlci1hZG1pbi1zYSJ9.Fy3KcosO8gc_npEwxIjCi3d1bjEl6A8SsJ7NvAuiURkzhhpOiyV3MPjQ1-MjD6Len3OSP_OZMAnxlwONAoBHnUVXdhyAbEUk-TgKN9gwztaIiEboTf3AknhgSUJnZreGQKfipwOxZJ3gBzSVKbcaJ9zlDBDPwvrdNaEmvU9LNu5-pUgG0taAfJoWYFzZmBjH7LjioZdIqM1E5TjuIxVcPUOLh-CMF_5BdOk4s7eAvy3guBcXsvNHxCx8ZFuSOd4DwutU6YLrZ0f9sFol_w_oX3HNfpbwKmwoDoNNzYESnr66--QJLToI7RsLjMrgeWbwRkuFXGxyBt_oGyFn2bCfkA"
export REGISTRY_USER="admin"
export REGISTRY_PASS="bingogo1"
export SSH_USER="jclee"
export SSH_PASS="bingogo1"

# === 프로젝트 설정 ===
export GITHUB_ORG="JCLEE94"
export APP_NAME="safework"
export K8S_CLUSTER="https://k8s.jclee.me:443"
export REGISTRY_URL="registry.jclee.me"
export CHARTS_URL="https://charts.jclee.me"
export ARGOCD_URL="https://argo.jclee.me"

# === 데이터베이스 설정 ===
export DEV_DB_URL="postgresql://admin:dev-password@postgres-dev:5432/health_management"
export STAGE_DB_URL="postgresql://admin:staging-password@postgres-staging:5432/health_management"
export PROD_DB_URL="postgresql://admin:REPLACE_WITH_PROD_PASSWORD@postgres-prod:5432/health_management"

# === Redis 설정 ===
export DEV_REDIS_URL="redis://redis-dev:6379/0"
export STAGE_REDIS_URL="redis://redis-staging:6379/0"
export PROD_REDIS_URL="redis://redis-prod:6379/0"

# === JWT 시크릿 ===
export DEV_JWT_SECRET="dev-jwt-secret-key-change-in-production-32chars"
export STAGE_JWT_SECRET="staging-jwt-secret-key-32-characters-minimum"
export PROD_JWT_SECRET="REPLACE_WITH_PROD_JWT_SECRET_32_CHARS_MIN"

# === 기타 시크릿 ===
export DEV_SECRET_KEY="dev-secret-key-for-encryption-change-in-prod"
export STAGE_SECRET_KEY="staging-secret-key-for-encryption-32chars"
export PROD_SECRET_KEY="REPLACE_WITH_PROD_SECRET_KEY_32_CHARS"

# === GitHub 토큰 (선택사항) ===
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# === kubeconfig 설정 ===
export KUBECONFIG="$HOME/.kube/config-k8s-jclee"

echo "SafeWork GitOps environment variables loaded successfully!"
echo "Kubernetes cluster: $K8S_CLUSTER"
echo "Registry: $REGISTRY_URL"
echo "ArgoCD: $ARGOCD_URL"