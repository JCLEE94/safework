# Cloudflare Access를 사용한 Docker Registry 인증

## 개요
Cloudflare Access를 통해 보호된 Docker Registry 사용 방법

## 설정 방법

### 1. Cloudflare Access Token 획득
1. https://registry.jclee.me 접속
2. Cloudflare Access 로그인
3. 브라우저 개발자 도구 (F12) → Application → Cookies
4. `CF_Authorization` 쿠키 값 복사

### 2. 환경 변수 설정

```bash
# 로컬 환경
export CF_ACCESS_TOKEN="eyJhbGciOiJSUzI1NiI..."

# GitHub Actions Secret 설정
gh secret set CF_ACCESS_TOKEN --body "eyJhbGciOiJSUzI1NiI..."
```

### 3. Kubernetes Secret 생성

```bash
# 스크립트 사용
export CF_ACCESS_TOKEN="your-token-here"
./scripts/create-registry-secret.sh

# 또는 수동으로
kubectl create secret docker-registry regcred-cf \
  --docker-server=registry.jclee.me \
  --docker-username=_token \
  --docker-password="$CF_ACCESS_TOKEN" \
  -n safework
```

### 4. Deployment 업데이트

```yaml
spec:
  imagePullSecrets:
  - name: regcred-cf  # Cloudflare Access 토큰 사용
```

## Docker CLI에서 사용

```bash
# 로그인
echo "$CF_ACCESS_TOKEN" | docker login registry.jclee.me -u _token --password-stdin

# 이미지 푸시
docker tag myapp:latest registry.jclee.me/myapp:latest
docker push registry.jclee.me/myapp:latest
```

## 토큰 갱신
- Cloudflare Access 토큰은 기본적으로 24시간 유효
- 만료 전에 갱신 필요
- 자동 갱신 스크립트는 별도 구현 필요

## 장점
1. 사용자별 인증 관리
2. IP 제한 없이 어디서나 접근 가능
3. Cloudflare의 보안 기능 활용
4. 감사 로그 자동 생성

## 문제 해결

### 401 Unauthorized
- 토큰 만료 확인
- 토큰 형식 확인 (전체 JWT 토큰 필요)

### 413 Request Entity Too Large
- Cloudflare 프록시 설정 확인
- 직접 IP 사용 고려