#!/bin/bash

# SafeWork GitHub Secrets 설정 가이드 템플릿
# 사용법: 환경변수를 설정한 후 ./setup-github-secrets.template.sh 실행

set -e

echo "🔐 SafeWork GitHub Secrets 설정 가이드"
echo "====================================="

# 환경변수 확인
if [ -z "$ARGO_HOST" ] || [ -z "$ARGO_ADMIN" ] || [ -z "$ARGO_PASSWORD" ]; then
    echo "❌ 필수 환경변수가 설정되지 않았습니다."
    echo ""
    echo "다음 환경변수를 설정하세요:"
    echo "export ARGO_HOST='https://argo.jclee.me'"
    echo "export ARGO_ADMIN='admin'"
    echo "export ARGO_PASSWORD='your-password'"
    echo ""
    echo "또는 .env 파일에 설정:"
    cat << 'EOF'
ARGO_HOST=https://argo.jclee.me
ARGO_ADMIN=admin
ARGO_PASSWORD=your-password
EOF
    exit 1
fi

# ArgoCD API 토큰 발급
echo "🎫 ArgoCD API 토큰 발급 중..."
ARGO_TOKEN=$(curl -s -k "$ARGO_HOST/api/v1/session" \
  -d "{\"username\":\"$ARGO_ADMIN\",\"password\":\"$ARGO_PASSWORD\"}" \
  -H "Content-Type: application/json" | jq -r '.token')

if [ "$ARGO_TOKEN" != "null" ] && [ -n "$ARGO_TOKEN" ]; then
  echo "✅ ArgoCD 토큰 발급 성공"
else
  echo "❌ ArgoCD 토큰 발급 실패"
  exit 1
fi

echo ""
echo "📋 다음 GitHub Secrets을 설정하세요:"
echo "======================================"
echo ""
echo "Repository: JCLEE94/safework"
echo "Settings → Secrets and variables → Actions → New repository secret"
echo ""

# 필수 시크릿 목록
cat << EOF
🔑 REQUIRED SECRETS:

1. ANTHROPIC_API_KEY
   Value: [Claude API 키를 입력하세요]
   
2. ARGO_HOST
   Value: $ARGO_HOST
   
3. ARGO_TOKEN  
   Value: $ARGO_TOKEN
   
4. REGISTRY_USERNAME
   Value: [Docker Registry 사용자명]
   
5. REGISTRY_PASSWORD
   Value: [Docker Registry 비밀번호]
   
6. BRAVE_API_KEY
   Value: [Brave Search API 키]
   
7. GITHUB_TOKEN
   Value: [GitHub Personal Access Token - 자동 생성됨]

📝 설정 방법:
1. https://github.com/JCLEE94/safework/settings/secrets/actions 접속
2. "New repository secret" 클릭
3. 위의 Name과 Value를 각각 입력
4. "Add secret" 클릭하여 저장

🚀 설정 완료 후 새로운 커밋을 푸시하면 CI/CD 파이프라인이 자동 실행됩니다!
EOF

echo ""
echo "🔧 ArgoCD 애플리케이션 현재 상태:"
echo "================================"

# ArgoCD 애플리케이션 상태 확인
curl -s -k "$ARGO_HOST/api/v1/applications/safework" \
  -H "Authorization: Bearer $ARGO_TOKEN" | jq -r '
{
  "애플리케이션": .metadata.name,
  "동기화 상태": .status.sync.status,
  "헬스 상태": .status.health.status,
  "Git 저장소": .spec.source.repoURL,
  "브랜치": .spec.source.targetRevision,
  "경로": .spec.source.path,
  "자동 동기화": (.spec.syncPolicy.automated != null)
}' 2>/dev/null || echo "❌ 상태 조회 실패"

echo ""
echo "🌐 ArgoCD 웹 인터페이스:"
echo "URL: $ARGO_HOST"
echo "Username: 환경변수로 설정된 값 사용"
echo ""
echo "✅ 설정 스크립트 완료!"