# SafeWork Pro - Claude OAuth 1회 인증 가이드

## 🚀 개요

SafeWork Pro에서 Claude AI를 활용하여 다음과 같은 기능을 사용할 수 있습니다:

- **자동 코드 리뷰**: PR과 Issue에서 @claude 멘션으로 AI 분석
- **보안 컴플라이언스**: 한국 산업안전보건법/개인정보보호법 준수 검토  
- **의료 데이터 보안**: 민감정보 처리 방식 검증
- **실시간 도움**: 개발 중 AI 어시스턴트 활용

## 🔐 1회 OAuth 인증 설정

### 준비 사항

- **GitHub CLI** 설치 및 로그인 (`gh auth login`)
- **jq** 설치 (JSON 처리용)
- **SafeWork Pro 저장소** 접근 권한

### 자동 설정 (권장)

```bash
# 설정 스크립트 실행
./setup-claude-oauth.sh

# 또는 직접 다운로드하여 실행
curl -fsSL https://raw.githubusercontent.com/JCLEE94/safework/main/setup-claude-oauth.sh | bash
```

### 수동 설정

#### 1단계: OAuth 인증 시작

1. [OAuth 워크플로우](https://github.com/JCLEE94/safework/actions/workflows/claude-oauth-onetime.yml) 실행
2. **"Run workflow"** 클릭 → **"Run workflow"** 실행 (코드는 비워두세요)
3. 워크플로우 로그에서 **로그인 URL 확인**

#### 2단계: Claude 로그인

1. 제공된 URL로 이동: `https://claude.ai/oauth/login`
2. Claude 계정으로 로그인
3. **인증 코드 복사** (10분 이내 사용해야 함)

#### 3단계: 토큰 저장

1. [OAuth 워크플로우](https://github.com/JCLEE94/safework/actions/workflows/claude-oauth-onetime.yml)를 다시 실행
2. **"code"** 필드에 복사한 인증 코드 입력
3. **"Run workflow"** 클릭
4. 성공 메시지 확인

## 🤖 사용 방법

### @claude 멘션 사용

#### Issue에서 사용
```
@claude 이 버그를 어떻게 해결해야 할까요?

현재 PostgreSQL 연결 에러가 발생하고 있습니다:
- 에러 메시지: connection timeout
- 발생 위치: src/models/database.py:45
- 환경: Docker 개발 환경
```

#### PR에서 사용
```
@claude 이 코드 변경사항을 리뷰해주세요

특히 다음 부분을 중점적으로 봐주세요:
- 보안 취약점 여부
- 한국 개인정보보호법 준수
- 성능 최적화 가능 여부
```

#### 특정 파일 분석 요청
```
@claude src/handlers/workers.py 파일의 보안을 점검해주세요

- SQL Injection 취약점
- 입력 검증 로직
- 권한 체크 메커니즘
```

### 사용 가능한 액션

#### 1. Simple Action (기본)
- **파일**: `.github/workflows/claude-simple-action.yml`
- **기능**: @claude 멘션 시 기본 AI 분석
- **특징**: 빠른 응답, 간단한 질문에 적합

#### 2. Official Action (고급)
- **파일**: `.github/workflows/claude-official-action.yml`
- **기능**: Anthropic 공식 액션 사용
- **특징**: 고급 분석, MCP 도구 활용

#### 3. Integrated Pipeline (전문)
- **파일**: `.github/workflows/main-integrated.yml`
- **기능**: CI/CD와 통합된 종합 분석
- **특징**: 보안 스캔, 법규 준수, 성능 최적화

## 🔧 고급 설정

### 토큰 갱신

토큰이 만료되었을 때:

```bash
# 1. 기존 토큰 초기화
gh workflow run claude-oauth-onetime.yml -f reset_auth=true

# 2. 새 토큰 설정 (위의 1-3단계 반복)
```

### 권한 설정

현재는 **JCLEE94** 사용자만 @claude 멘션을 사용할 수 있습니다.
다른 사용자를 추가하려면 워크플로우 파일에서 조건을 수정하세요:

```yaml
# claude-simple-action.yml에서
if: |
  ... && github.actor == 'JCLEE94'
  
# 다음으로 변경
if: |
  ... && (github.actor == 'JCLEE94' || github.actor == 'OTHER_USER')
```

### 커스텀 프롬프트

시스템 프롬프트를 수정하여 Claude의 응답을 조정할 수 있습니다:

```yaml
system_prompt: |
  SafeWork Pro는 한국 건설업 보건관리 시스템입니다.
  
  추가 요구사항:
  - 모든 응답은 한국어로 작성
  - 코드 예시는 주석도 한국어로
  - 법적 조언이 아닌 기술적 가이드만 제공
  - 보안 이슈는 즉시 GitHub Issue로 생성
```

## 🔍 트러블슈팅

### 일반적인 문제

#### 1. Claude가 응답하지 않음
```bash
# 토큰 상태 확인
gh secret list --repo JCLEE94/safework | grep CLAUDE

# 토큰 갱신
gh workflow run claude-oauth-onetime.yml
```

#### 2. 권한 오류
```
Error: GitHub user not authorized
```
**해결**: 워크플로우 파일에서 `github.actor` 조건 확인

#### 3. 워크플로우 실행 실패
```bash
# 워크플로우 로그 확인
gh run list --limit 5
gh run view [RUN_ID] --log-failed
```

#### 4. 인증 코드 만료
```
Error: Authorization code expired
```
**해결**: 새로운 인증 코드 발급받아 재시도

### 로그 분석

#### OAuth 설정 로그
```bash
# OAuth 워크플로우 로그 확인
gh run list --workflow=claude-oauth-onetime.yml
gh run view [RUN_ID] --log
```

#### Claude Action 로그
```bash
# Claude 액션 로그 확인  
gh run list --workflow=claude-simple-action.yml
gh run view [RUN_ID] --log
```

### 수동 토큰 설정

API를 통한 수동 설정 (최후 수단):

```bash
# 토큰 직접 설정
gh secret set CLAUDE_ACCESS_TOKEN --body "YOUR_ACCESS_TOKEN" --repo JCLEE94/safework
gh secret set CLAUDE_REFRESH_TOKEN --body "YOUR_REFRESH_TOKEN" --repo JCLEE94/safework  
gh secret set CLAUDE_EXPIRES_AT --body "1735689600" --repo JCLEE94/safework
```

## 📚 참고 자료

### 관련 문서
- [grll/claude-code-action](https://github.com/grll/claude-code-action) - 기본 액션
- [Claude OAuth 가이드](https://docs.anthropic.com/oauth) - 공식 문서
- [GitHub Actions Secrets](https://docs.github.com/actions/security-guides/encrypted-secrets) - 시크릿 관리

### SafeWork Pro 특화 설정
- **CLAUDE.md**: 프로젝트별 Claude 지침
- **한국 법규 데이터베이스**: 산업안전보건법, 개인정보보호법
- **의료 데이터 처리**: HIPAA 유사 한국 기준 적용

### 보안 고려사항
- OAuth 토큰은 암호화되어 GitHub Secrets에 저장
- 토큰 자동 갱신으로 보안 유지
- 사용자별 권한 제어로 남용 방지
- 모든 AI 요청은 로그로 추적 가능

## 🎯 다음 단계

1. **기본 사용법 익히기**: 간단한 @claude 멘션으로 시작
2. **고급 기능 활용**: MCP 도구, 보안 스캔 등
3. **팀 전체 확산**: 다른 개발자들에게 가이드 공유
4. **커스터마이징**: 프로젝트별 요구사항에 맞게 조정

---

**💡 팁**: Claude는 한국의 건설업 보건관리 도메인에 특화되어 있습니다. 
관련 법규나 의료 데이터 처리에 대한 질문도 자유롭게 해보세요!

**🔒 보안**: 민감한 정보(API 키, 비밀번호 등)는 절대 Claude와 공유하지 마세요.
필요시 GitHub Secrets을 통해 안전하게 관리하세요.