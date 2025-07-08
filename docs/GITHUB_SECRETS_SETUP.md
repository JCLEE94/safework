# GitHub Secrets 설정 가이드

이 문서는 SafeWork Pro 프로젝트에 필요한 GitHub Secrets 설정 방법을 설명합니다.

## 필수 Secrets

### 1. Docker Registry 관련
- `REGISTRY_USERNAME`: Docker 레지스트리 사용자명
- `REGISTRY_PASSWORD`: Docker 레지스트리 비밀번호

### 2. ArgoCD 관련
- `ARGOCD_AUTH_TOKEN`: ArgoCD API 접근 토큰

### 3. Cloudflare Tunnel 관련 (신규)
- `CLOUDFLARE_TUNNEL_TOKEN`: Cloudflare Tunnel 연결 토큰

## Cloudflare Tunnel Token 설정 방법

### 1. GitHub Repository Settings로 이동
1. https://github.com/JCLEE94/safework 접속
2. Settings 탭 클릭
3. 왼쪽 메뉴에서 Secrets and variables > Actions 클릭

### 2. New repository secret 클릭

### 3. Secret 정보 입력
- **Name**: `CLOUDFLARE_TUNNEL_TOKEN`
- **Secret**: 제공받은 토큰 값 (eyJ로 시작하는 긴 문자열)
  ```
  eyJhIjoiYThkOWM2N2Y1ODZhY2RkMTVlZWJjYzY1Y2EzYWE1YmIiLCJ0IjoiOGVhNzg5MDYtMWEwNS00NGZiLWExYmItZTUxMjE3MmNiNWFiIiwicyI6Ill6RXlZVEUwWWpRdE1tVXlNUzAwWmpRMExXSTVaR0V0WkdNM09UY3pOV1ExT1RGbSJ9
  ```

### 4. Add secret 클릭

## 설정 확인

Secrets가 올바르게 설정되었는지 확인:
1. Actions 탭으로 이동
2. 최근 워크플로우 실행 확인
3. Secret 관련 단계가 정상적으로 실행되는지 확인

## 보안 주의사항

1. **토큰 보안**: Secret 값을 절대 공개 저장소나 로그에 노출하지 마세요
2. **권한 제한**: 필요한 최소한의 권한만 가진 토큰 사용
3. **정기 갱신**: 보안을 위해 토큰을 주기적으로 갱신
4. **접근 제어**: Repository secrets는 관리자만 접근 가능하도록 설정

## 문제 해결

### Secret이 인식되지 않는 경우
```yaml
# workflow 파일에서 올바른 이름으로 참조하는지 확인
env:
  CLOUDFLARE_TOKEN: ${{ secrets.CLOUDFLARE_TUNNEL_TOKEN }}
```

### 토큰이 유효하지 않은 경우
1. Cloudflare Zero Trust 대시보드에서 토큰 재생성
2. GitHub Secret 업데이트
3. 워크플로우 재실행

## 추가 리소스

- [GitHub Encrypted Secrets 문서](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Cloudflare Tunnel 문서](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [ArgoCD 인증 문서](https://argo-cd.readthedocs.io/en/stable/user-guide/security/)