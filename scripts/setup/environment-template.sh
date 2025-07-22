#!/bin/bash
# SafeWork Pro CI/CD Environment Variables Setup Template
# This script sets up all required environment variables for CI/CD pipeline

set -euo pipefail

echo "🚀 SafeWork Pro CI/CD Environment Setup"
echo "========================================"

# === 필수 인증 정보 ===
export K8S_TOKEN="eyJhbGciOiJSUzI1NiIsImtpZCI6Ikxobzd5NUhuUmV0S0pJQTkwN1F5dUZtcDdUeXlKRTdSX2t6NGo0ZWlmUUUifQ.eyJpc3MiOiJrdWJlcm5ldGVzL3NlcnZpY2VhY2NvdW50Iiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9uYW1lc3BhY2UiOiJrdWJlLXN5c3RlbSIsImt1YmVybmV0ZXMuaW8vc2VydmljZWFjY291bnQvc2VjcmV0Lm5hbWUiOiJjbHVzdGVyLWFkbWluLXRva2VuIiwia3ViZXJuZXRlcy5pby9zZXJ2aWNlYWNjb3VudC9zZXJ2aWNlLWFjY291bnQubmFtZSI6ImNsdXN0ZXItYWRtaW4tc2EiLCJrdWJlcm5ldGVzLmlvL3NlcnZpY2VhY2NvdW50L3NlcnZpY2UtYWNjb3VudC51aWQiOiIzNWVmNDQxMS01NjRiLTQyNjItODM1Ni05YTI5YjE5NmQzNWQiLCJzdWIiOiJzeXN0ZW06c2VydmljZWFjY291bnQ6a3ViZS1zeXN0ZW06Y2x1c3Rlci1hZG1pbi1zYSJ9.Fy3KcosO8gc_npEwxIjCi3d1bjEl6A8SsJ7NvAuiURkzhhpOiyV3MPjQ1-MjD6Len3OSP_OZMAnxlwONAoBHnUVXdhyAbEUk-TgKN9gwztaIiEboTf3AknhgSUJnZreGQKfipwOxZJ3gBzSVKbcaJ9zlDBDPwvrdNaEmvU9LNu5-pUgG0taAfJoWYFzZmBjH7LjioZdIqM1E5TjuIxVcPUOLh-CMF_5BdOk4s7eAvy3guBcXsvNHxCx8ZFuSOd4DwutU6YLrZ0f9sFol_w_oX3HNfpbwKmwoDoNNzYESnr66--QJLToI7RsLjMrgeWbwRkuFXGxyBt_oGyFn2bCfkA"

# === Docker Registry 인증 ===
export REGISTRY_URL="registry.jclee.me"
export REGISTRY_USER="admin"
export REGISTRY_PASS="bingogo1"
export REGISTRY_AUTH="YWRtaW46YmluZ29nbzE="

# === ChartMuseum 인증 ===
export CHARTS_URL="https://charts.jclee.me"
export HELM_REPO_USERNAME="admin"
export HELM_REPO_PASSWORD="bingogo1"
export CHARTMUSEUM_AUTH="Authorization: Basic YWRtaW46YmluZ29nbzE="

# === 프로젝트 설정 ===
export GITHUB_ORG="JCLEE94"
export APP_NAME="safework"
export K8S_CLUSTER="https://k8s.jclee.me:443"
export ARGOCD_URL="https://argo.jclee.me"

# === Application Configuration ===
export DATABASE_URL="postgresql://admin:password@postgres-service:5432/health_management"
export REDIS_URL="redis://redis-service:6379/0"
export JWT_SECRET="safework-jwt-secret-production-2025"
export SECRET_KEY="safework-app-secret-key-production"
export ENVIRONMENT="production"

echo "✅ Environment variables set successfully"
echo ""
echo "🔧 Required GitHub Secrets:"
echo "- REGISTRY_USERNAME: admin"
echo "- REGISTRY_PASSWORD: bingogo1"
echo "- CHARTMUSEUM_USERNAME: admin"  
echo "- CHARTMUSEUM_PASSWORD: bingogo1"
echo "- K8S_TOKEN: [Kubernetes service account token]"
echo ""
echo "🔧 Required GitHub Variables:"
echo "- REGISTRY_URL: registry.jclee.me"
echo "- CHARTMUSEUM_URL: https://charts.jclee.me"
echo "- GITHUB_ORG: JCLEE94"
echo "- APP_NAME: safework"
echo "- K8S_CLUSTER: https://k8s.jclee.me:443"
echo "- ARGOCD_URL: https://argo.jclee.me"