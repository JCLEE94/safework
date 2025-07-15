#!/bin/bash

# SafeWork Production Environment Setup Script

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 SafeWork Production 환경변수 설정${NC}"
echo

# 프로덕션 URL 설정
export PRODUCTION_URL="https://safework.jclee.me"
export PRODUCTION_NODEPORT_URL="http://192.168.50.110:32301"

# 데이터베이스 설정
export DATABASE_HOST="${DATABASE_HOST:-postgres}"
export DATABASE_PORT="${DATABASE_PORT:-5432}"
export DATABASE_USER="${DATABASE_USER:-admin}"
export DATABASE_NAME="${DATABASE_NAME:-health_management}"

# Redis 설정
export REDIS_HOST="${REDIS_HOST:-redis}"
export REDIS_PORT="${REDIS_PORT:-6379}"

# JWT 설정
export JWT_SECRET="${JWT_SECRET:-$(openssl rand -base64 32)}"
export JWT_ALGORITHM="HS256"
export JWT_EXPIRATION_HOURS="24"

# 보안 키
export SECRET_KEY="${SECRET_KEY:-$(openssl rand -base64 32)}"

# Docker Registry
export DOCKER_REGISTRY="registry.jclee.me"
export REGISTRY_USERNAME="${REGISTRY_USERNAME}"
export REGISTRY_PASSWORD="${REGISTRY_PASSWORD}"

# ArgoCD 설정
export ARGOCD_SERVER="argo.jclee.me"
export ARGOCD_APP="safework"

# 환경변수 파일 생성
ENV_FILE=".env.production"

cat > $ENV_FILE << EOF
# SafeWork Production Environment Variables
# Generated on $(date)

# Application URLs
PRODUCTION_URL=$PRODUCTION_URL
PRODUCTION_NODEPORT_URL=$PRODUCTION_NODEPORT_URL

# Database Configuration
DATABASE_HOST=$DATABASE_HOST
DATABASE_PORT=$DATABASE_PORT
DATABASE_USER=$DATABASE_USER
DATABASE_PASSWORD=\${DATABASE_PASSWORD}
DATABASE_NAME=$DATABASE_NAME
DATABASE_URL=postgresql://\${DATABASE_USER}:\${DATABASE_PASSWORD}@\${DATABASE_HOST}:\${DATABASE_PORT}/\${DATABASE_NAME}

# Redis Configuration
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_PASSWORD=\${REDIS_PASSWORD}
REDIS_URL=redis://\${REDIS_HOST}:\${REDIS_PORT}/0

# JWT Configuration
JWT_SECRET=$JWT_SECRET
JWT_ALGORITHM=$JWT_ALGORITHM
JWT_EXPIRATION_HOURS=$JWT_EXPIRATION_HOURS

# Security
SECRET_KEY=$SECRET_KEY

# Docker Registry
DOCKER_REGISTRY=$DOCKER_REGISTRY
REGISTRY_USERNAME=$REGISTRY_USERNAME
REGISTRY_PASSWORD=\${REGISTRY_PASSWORD}

# ArgoCD
ARGOCD_SERVER=$ARGOCD_SERVER
ARGOCD_APP=$ARGOCD_APP
ARGOCD_TOKEN=\${ARGOCD_TOKEN}

# Environment
ENVIRONMENT=production
DISABLE_AUTH=false
EOF

echo -e "${GREEN}✅ 환경변수 파일이 생성되었습니다: $ENV_FILE${NC}"
echo
echo -e "${YELLOW}⚠️  다음 민감한 환경변수들은 직접 설정해야 합니다:${NC}"
echo "  - DATABASE_PASSWORD"
echo "  - REDIS_PASSWORD (선택사항)"
echo "  - REGISTRY_PASSWORD"
echo "  - ARGOCD_TOKEN"
echo
echo -e "${BLUE}📋 사용 방법:${NC}"
echo "  1. $ENV_FILE 파일을 편집하여 비밀번호 설정"
echo "  2. source $ENV_FILE"
echo "  3. GitHub Secrets에 추가 (CI/CD용)"
echo
echo -e "${BLUE}🌐 접속 URL:${NC}"
echo "  - 도메인: $PRODUCTION_URL"
echo "  - NodePort: $PRODUCTION_NODEPORT_URL"
echo "  - ArgoCD: https://$ARGOCD_SERVER"
echo

# Kubernetes Secret 생성 명령어 출력
echo -e "${BLUE}🔐 Kubernetes Secret 생성:${NC}"
echo "kubectl create secret generic safework-secrets -n safework \\"
echo "  --from-literal=DATABASE_PASSWORD=\${DATABASE_PASSWORD} \\"
echo "  --from-literal=REDIS_PASSWORD=\${REDIS_PASSWORD} \\"
echo "  --from-literal=JWT_SECRET=$JWT_SECRET \\"
echo "  --from-literal=SECRET_KEY=$SECRET_KEY \\"
echo "  --dry-run=client -o yaml | kubectl apply -f -"