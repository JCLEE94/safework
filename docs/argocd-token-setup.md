# ArgoCD API 토큰 설정 가이드

## 1. ArgoCD API 토큰 생성

### 방법 1: ArgoCD CLI 사용
```bash
# ArgoCD에 로그인
argocd login argo.jclee.me --username admin

# API 토큰 생성 (유효기간 설정 가능)
argocd account generate-token --account admin --id github-actions

# 또는 유효기간 지정 (예: 1년)
argocd account generate-token --account admin --id github-actions --expires-in 365d
```

### 방법 2: ArgoCD Web UI 사용
1. ArgoCD 웹 UI 접속: https://argo.jclee.me
2. 로그인 후 Settings → Accounts 메뉴로 이동
3. admin 계정 선택
4. "Generate New" 버튼 클릭
5. 토큰 이름 입력 (예: github-actions)
6. 생성된 토큰 복사 (한 번만 표시되므로 안전하게 보관)

### 방법 3: ArgoCD API 직접 호출
```bash
# 로그인하여 세션 토큰 획득
SESSION_TOKEN=$(curl -s -X POST https://argo.jclee.me/api/v1/session \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"YOUR_PASSWORD"}' | jq -r .token)

# API 토큰 생성
curl -s -X POST https://argo.jclee.me/api/v1/account/admin/token \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"github-actions","expiresIn":"365d"}' | jq -r .token
```

## 2. GitHub Secrets에 토큰 추가

### GitHub 웹 UI에서 설정
1. GitHub 저장소 페이지로 이동: https://github.com/JCLEE94/safework
2. Settings → Secrets and variables → Actions 클릭
3. "New repository secret" 버튼 클릭
4. 다음 정보 입력:
   - Name: `ARGOCD_AUTH_TOKEN`
   - Secret: (ArgoCD에서 생성한 토큰 붙여넣기)
5. "Add secret" 버튼 클릭

### GitHub CLI로 설정
```bash
# GitHub CLI가 설치되어 있어야 함
gh secret set ARGOCD_AUTH_TOKEN --body "YOUR_ARGOCD_TOKEN"
```

## 3. 토큰 권한 확인

생성된 토큰이 필요한 권한을 가지고 있는지 확인:

```bash
# 토큰으로 로그인 테스트
argocd login argo.jclee.me --auth-token YOUR_TOKEN --grpc-web --insecure

# 애플리케이션 목록 확인
argocd app list

# 특정 앱 상태 확인
argocd app get safework
```

## 4. CI/CD 파이프라인 확인

현재 워크플로우(.github/workflows/deploy.yml)는 이미 ArgoCD 토큰을 사용하도록 설정되어 있습니다:

```yaml
- name: Deploy via ArgoCD
  env:
    ARGOCD_AUTH_TOKEN: ${{ secrets.ARGOCD_AUTH_TOKEN }}
  run: |
    argocd login ${{ env.ARGOCD_SERVER }} \
      --auth-token ${{ env.ARGOCD_AUTH_TOKEN }} \
      --grpc-web \
      --insecure
```

## 5. 토큰 관리 베스트 프랙티스

1. **정기적 로테이션**: 보안을 위해 토큰을 정기적으로 교체
2. **최소 권한 원칙**: CI/CD에 필요한 최소한의 권한만 부여
3. **모니터링**: ArgoCD 감사 로그를 통해 토큰 사용 모니터링
4. **별도 계정 사용**: 가능하면 CI/CD 전용 서비스 계정 생성

## 6. 문제 해결

### 토큰 인증 실패
```bash
# ArgoCD 서버 상태 확인
curl https://argo.jclee.me/api/v1/version

# 토큰 유효성 확인
argocd account get-user-info --auth-token YOUR_TOKEN --server argo.jclee.me --grpc-web --insecure
```

### GitHub Actions에서 시크릿을 찾을 수 없음
- Repository secrets가 아닌 Organization secrets인지 확인
- 시크릿 이름의 오타 확인
- Environment protection rules 확인 (production environment 사용 시)

## 7. 추가 보안 설정

### ArgoCD RBAC 설정 (선택사항)
CI/CD 전용 계정을 만들고 필요한 권한만 부여:

```yaml
# argocd-cm ConfigMap에 추가
policy.csv: |
  p, role:ci-cd, applications, sync, safework/*, allow
  p, role:ci-cd, applications, get, safework/*, allow
  p, role:ci-cd, applications, action/*, safework/*, allow
  g, ci-cd-user, role:ci-cd
```

이 설정으로 CI/CD는 safework 애플리케이션만 관리할 수 있습니다.