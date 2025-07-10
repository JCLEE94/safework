#!/bin/bash

# SafeWork Pro - Claude OAuth 1회 설정 스크립트
# 한국어 지원 및 SafeWork Pro 전용 설정

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 로깅 함수들
log_info() {
    echo -e "${CYAN}ℹ ${WHITE}$1${NC}"
}

log_success() {
    echo -e "${GREEN}✓ ${WHITE}$1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠ ${WHITE}$1${NC}"
}

log_error() {
    echo -e "${RED}✗ ${WHITE}$1${NC}"
}

log_step() {
    echo -e "${MAGENTA}${BOLD}▶ $1${NC}"
}

# TTY에서 입력 읽기
read_from_tty() {
    local prompt="$1"
    local input
    if [ -t 0 ]; then
        read -p "$prompt" input
    else
        printf "%s" "$prompt" >/dev/tty
        read input </dev/tty
    fi
    echo "$input"
}

# 헤더 표시
show_header() {
    clear
    echo -e "${CYAN}"
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║                    🏗️ SafeWork Pro Claude OAuth 설정 🏗️                ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝

  ███████╗ █████╗ ███████╗███████╗██╗    ██╗ ██████╗ ██████╗ ██╗  ██╗
  ██╔════╝██╔══██╗██╔════╝██╔════╝██║    ██║██╔═══██╗██╔══██╗██║ ██╔╝
  ███████╗███████║█████╗  █████╗  ██║ █╗ ██║██║   ██║██████╔╝█████╔╝ 
  ╚════██║██╔══██║██╔══╝  ██╔══╝  ██║███╗██║██║   ██║██╔══██╗██╔═██╗ 
  ███████║██║  ██║██║     ███████╗╚███╔███╔╝╚██████╔╝██║  ██║██║  ██╗
  ╚══════╝╚═╝  ╚═╝╚═╝     ╚══════╝ ╚══╝╚══╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝

  건설업 보건관리 시스템 - Claude AI 통합

EOF
    echo -e "${NC}"
}

show_header

log_step "SafeWork Pro Claude OAuth 설정 시작"
echo

# 1. GitHub CLI 확인
log_step "1단계: GitHub CLI 설치 확인"
if ! command -v gh &> /dev/null; then
    log_error "GitHub CLI (gh)가 설치되지 않았습니다"
    echo
    log_info "GitHub CLI 설치 방법:"
    echo "  • Ubuntu/Debian: sudo apt install gh"
    echo "  • CentOS/RHEL: sudo yum install gh"
    echo "  • macOS: brew install gh"
    echo "  • 또는 https://cli.github.com/ 에서 다운로드"
    exit 1
fi
log_success "GitHub CLI 설치 확인됨"

# 2. jq 확인
if ! command -v jq &> /dev/null; then
    log_warning "jq가 설치되지 않았습니다 - JSON 처리에 필요합니다"
    echo
    log_info "jq 설치 방법:"
    echo "  • Ubuntu/Debian: sudo apt install jq"
    echo "  • CentOS/RHEL: sudo yum install jq"
    echo "  • macOS: brew install jq"
    echo
    echo -e "${BOLD}jq를 설치한 후 다시 실행해주세요${NC}"
    exit 1
fi
log_success "jq 설치 확인됨"

# 3. GitHub 사용자명 확인
log_step "2단계: GitHub 사용자 인증 확인"
GITHUB_USERNAME=$(gh api user | jq -r '.login' 2>/dev/null)
if [ $? -ne 0 ] || [ "$GITHUB_USERNAME" = "null" ] || [ -z "$GITHUB_USERNAME" ]; then
    log_error "GitHub CLI 로그인이 필요합니다"
    echo
    log_info "다음 명령어로 GitHub에 로그인하세요:"
    echo -e "  ${CYAN}gh auth login${NC}"
    exit 1
fi
log_success "GitHub 사용자: $GITHUB_USERNAME"

# 4. 저장소 확인
log_step "3단계: SafeWork Pro 저장소 확인"
REPO_NAME="JCLEE94/safework"

if ! gh repo view "$REPO_NAME" &>/dev/null; then
    log_error "SafeWork Pro 저장소($REPO_NAME)에 접근할 수 없습니다"
    echo
    log_info "다음을 확인해주세요:"
    echo "  • 저장소가 존재하는지 확인"
    echo "  • 저장소에 대한 접근 권한이 있는지 확인"
    echo "  • GitHub CLI가 올바른 계정으로 로그인되어 있는지 확인"
    exit 1
fi
log_success "SafeWork Pro 저장소 접근 확인됨"

# 5. 기존 워크플로우 확인
log_step "4단계: OAuth 워크플로우 상태 확인"
if gh api repos/$REPO_NAME/contents/.github/workflows/claude-oauth-onetime.yml &>/dev/null; then
    log_success "OAuth 워크플로우가 이미 존재합니다"
    WORKFLOW_EXISTS=true
else
    log_warning "OAuth 워크플로우가 없습니다"
    WORKFLOW_EXISTS=false
fi

# 6. GitHub Secrets 확인
log_step "5단계: GitHub Secrets 상태 확인"
SECRET_STATUS=""
set +e
gh secret list --repo "$REPO_NAME" | grep -q "CLAUDE_ACCESS_TOKEN"
ACCESS_TOKEN_EXISTS=$?
gh secret list --repo "$REPO_NAME" | grep -q "CLAUDE_REFRESH_TOKEN"
REFRESH_TOKEN_EXISTS=$?
gh secret list --repo "$REPO_NAME" | grep -q "CLAUDE_EXPIRES_AT"
EXPIRES_AT_EXISTS=$?
set -e

if [ $ACCESS_TOKEN_EXISTS -eq 0 ] && [ $REFRESH_TOKEN_EXISTS -eq 0 ] && [ $EXPIRES_AT_EXISTS -eq 0 ]; then
    log_success "모든 Claude OAuth Secrets가 존재합니다"
    SECRETS_EXIST=true
    
    # 만료 시간 확인 (가능한 경우)
    echo
    log_info "기존 토큰 상태:"
    echo "  ✅ CLAUDE_ACCESS_TOKEN"
    echo "  ✅ CLAUDE_REFRESH_TOKEN"
    echo "  ✅ CLAUDE_EXPIRES_AT"
else
    log_warning "Claude OAuth Secrets가 설정되지 않았습니다"
    SECRETS_EXIST=false
fi

# 7. 설정 상태 요약 및 다음 단계 안내
echo
log_step "설정 상태 요약"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

if [ "$WORKFLOW_EXISTS" = true ] && [ "$SECRETS_EXIST" = true ]; then
    echo -e "${GREEN}${BOLD}🎉 Claude OAuth가 이미 설정되어 있습니다!${NC}"
    echo
    echo -e "${BOLD}✅ 사용 가능한 기능:${NC}"
    echo "  • @claude 멘션으로 AI 도움 요청"
    echo "  • 자동 코드 리뷰 및 분석"
    echo "  • 한국 법규 컴플라이언스 검토"
    echo "  • 보안 취약점 스캔"
    echo
    echo -e "${BOLD}🚀 사용 방법:${NC}"
    echo "  1. Issue나 PR에서 '@claude 도움이 필요해요' 멘션"
    echo "  2. 자동으로 AI 분석 결과 제공"
    echo "  3. 필요시 추가 질문이나 요청 가능"
    echo
    echo -e "${CYAN}💡 팁: Claude가 응답하지 않으면 토큰이 만료되었을 수 있습니다.${NC}"
    echo -e "   이 경우 OAuth 워크플로우를 다시 실행하여 토큰을 갱신하세요.${NC}"

elif [ "$WORKFLOW_EXISTS" = true ] && [ "$SECRETS_EXIST" = false ]; then
    echo -e "${YELLOW}${BOLD}🔧 OAuth 인증만 필요합니다${NC}"
    echo
    echo -e "${BOLD}📋 다음 단계:${NC}"
    echo
    echo "1️⃣ ${BOLD}OAuth 워크플로우 실행 (1단계):${NC}"
    echo "   • https://github.com/$REPO_NAME/actions/workflows/claude-oauth-onetime.yml"
    echo "   • 'Run workflow' 클릭 → 'Run workflow' 실행 (코드는 비워두세요)"
    echo
    echo "2️⃣ ${BOLD}Claude 로그인:${NC}"
    echo "   • 워크플로우 로그에서 제공되는 로그인 URL 클릭"
    echo "   • Claude 계정으로 로그인"
    echo "   • 인증 코드 복사"
    echo
    echo "3️⃣ ${BOLD}토큰 저장 (2단계):${NC}"
    echo "   • 같은 워크플로우를 다시 실행"
    echo "   • 'code' 필드에 복사한 인증 코드 입력"
    echo "   • 'Run workflow' 클릭"
    echo
    echo "4️⃣ ${BOLD}완료 확인:${NC}"
    echo "   • 워크플로우가 성공하면 설정 완료!"
    echo "   • 이제 @claude 멘션을 사용할 수 있습니다"

else
    echo -e "${RED}${BOLD}⚠️ 초기 설정이 필요합니다${NC}"
    echo
    echo -e "${BOLD}🔧 필요한 작업:${NC}"
    echo
    if [ "$WORKFLOW_EXISTS" = false ]; then
        echo "❌ OAuth 워크플로우 파일이 없습니다"
        echo "   → 최신 코드를 pull하거나 수동으로 워크플로우를 추가하세요"
        echo
    fi
    
    echo -e "${BOLD}💡 권장 해결 방법:${NC}"
    echo "1. 최신 코드 동기화:"
    echo "   git pull origin main"
    echo
    echo "2. 워크플로우 파일 확인:"
    echo "   ls -la .github/workflows/claude-*"
    echo
    echo "3. 누락된 파일이 있다면 다음 명령어로 다시 실행:"
    echo "   ./setup-claude-oauth.sh"
fi

echo
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# 8. 추가 도움말
echo -e "${BOLD}📚 추가 정보:${NC}"
echo "  • 공식 문서: https://github.com/grll/claude-code-action"
echo "  • SafeWork Pro 저장소: https://github.com/$REPO_NAME"
echo "  • 문제 발생 시: GitHub Issues에 문의"
echo

log_success "SafeWork Pro Claude OAuth 설정 가이드 완료!"
echo
echo -e "${CYAN}질문이나 문제가 있으시면 언제든지 문의해주세요! 🤖${NC}"