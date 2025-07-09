#!/bin/bash
# Cloudflare Access를 사용하는 레지스트리 시크릿 생성 스크립트

# 환경 변수 확인
if [ -z "$CF_ACCESS_TOKEN" ]; then
    echo "❌ CF_ACCESS_TOKEN 환경 변수가 설정되지 않았습니다."
    echo "export CF_ACCESS_TOKEN='your-cloudflare-access-token'"
    exit 1
fi

# Docker config 생성
DOCKER_CONFIG_JSON=$(cat <<EOF
{
    "auths": {
        "registry.jclee.me": {
            "auth": "$(echo -n "_token:${CF_ACCESS_TOKEN}" | base64 -w 0)"
        }
    }
}
EOF
)

# Base64 인코딩
ENCODED_CONFIG=$(echo -n "$DOCKER_CONFIG_JSON" | base64 -w 0)

# Kubernetes Secret YAML 생성
cat <<EOF > k8s/safework/regcred-cf-generated.yaml
apiVersion: v1
kind: Secret
metadata:
  name: regcred-cf
  namespace: safework
type: kubernetes.io/dockerconfigjson
data:
  .dockerconfigjson: $ENCODED_CONFIG
EOF

echo "✅ Secret YAML 파일이 생성되었습니다: k8s/safework/regcred-cf-generated.yaml"

# 적용 여부 확인
read -p "Kubernetes에 적용하시겠습니까? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    kubectl apply -f k8s/safework/regcred-cf-generated.yaml
    echo "✅ Secret이 적용되었습니다."
fi