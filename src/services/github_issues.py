"""
GitHub Issues 자동 생성 서비스
Automatic GitHub Issues creation service for error reporting
"""

import asyncio
import json
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Any
import hashlib
import aiohttp
from pydantic import BaseModel
from src.config.settings import get_settings

settings = get_settings()

class ErrorReport(BaseModel):
    """에러 리포트 모델"""
    title: str
    error_type: str
    error_message: str
    stack_trace: str
    timestamp: datetime
    user_id: Optional[str] = None
    request_path: Optional[str] = None
    request_method: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    environment: str = "production"
    severity: str = "error"  # error, warning, critical
    component: str = "backend"  # backend, frontend, database, etc.

class GitHubIssuesService:
    """GitHub Issues 자동 생성 서비스"""
    
    def __init__(self):
        self.github_token = settings.github_token
        self.repo_owner = settings.github_repo_owner or "JCLEE94"
        self.repo_name = settings.github_repo_name or "safework"
        self.api_base = "https://api.github.com"
        self.issue_cache = {}  # 중복 이슈 방지 캐시
        
    def _generate_issue_hash(self, error_report: ErrorReport) -> str:
        """에러 해시 생성 (중복 방지용)"""
        content = f"{error_report.error_type}:{error_report.error_message}:{error_report.request_path}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _format_issue_title(self, error_report: ErrorReport) -> str:
        """이슈 제목 포맷팅"""
        severity_emoji = {
            "critical": "🚨",
            "error": "❌", 
            "warning": "⚠️"
        }
        
        component_emoji = {
            "backend": "🔧",
            "frontend": "🖥️", 
            "database": "🗄️",
            "api": "🔌"
        }
        
        emoji = severity_emoji.get(error_report.severity, "❌")
        comp_emoji = component_emoji.get(error_report.component, "🔧")
        
        return f"{emoji} [{error_report.component.upper()}] {error_report.error_type}: {error_report.title}"
    
    def _format_issue_body(self, error_report: ErrorReport) -> str:
        """이슈 본문 포맷팅"""
        body = f"""## 🐛 에러 리포트 / Error Report

### 📋 기본 정보 / Basic Information
- **발생 시간 / Timestamp**: {error_report.timestamp.strftime('%Y-%m-%d %H:%M:%S')} KST
- **심각도 / Severity**: `{error_report.severity.upper()}`
- **컴포넌트 / Component**: `{error_report.component}`
- **환경 / Environment**: `{error_report.environment}`

### 🔍 에러 상세 / Error Details
**에러 타입 / Error Type**: `{error_report.error_type}`

**에러 메시지 / Error Message**:
```
{error_report.error_message}
```

### 📍 요청 정보 / Request Information
"""
        
        if error_report.request_path:
            body += f"- **경로 / Path**: `{error_report.request_path}`\n"
        if error_report.request_method:
            body += f"- **메소드 / Method**: `{error_report.request_method}`\n"
        if error_report.user_id:
            body += f"- **사용자 / User**: `{error_report.user_id}`\n"
        if error_report.ip_address:
            body += f"- **IP 주소 / IP Address**: `{error_report.ip_address}`\n"
        if error_report.user_agent:
            body += f"- **User Agent**: `{error_report.user_agent}`\n"
            
        body += f"""
### 📚 스택 트레이스 / Stack Trace
```python
{error_report.stack_trace}
```

### 🔧 해결 방법 / Resolution
- [ ] 에러 원인 분석
- [ ] 수정 사항 구현
- [ ] 테스트 수행
- [ ] 배포 및 확인

---
🤖 **자동 생성된 이슈** / Auto-generated issue by SafeWork Pro Error Reporter
"""
        return body
    
    def _get_issue_labels(self, error_report: ErrorReport) -> List[str]:
        """이슈 라벨 생성"""
        labels = ["bug", "auto-generated"]
        
        # 심각도별 라벨
        severity_labels = {
            "critical": "priority:critical",
            "error": "priority:high", 
            "warning": "priority:medium"
        }
        if error_report.severity in severity_labels:
            labels.append(severity_labels[error_report.severity])
        
        # 컴포넌트별 라벨
        component_labels = {
            "backend": "backend",
            "frontend": "frontend",
            "database": "database",
            "api": "api"
        }
        if error_report.component in component_labels:
            labels.append(component_labels[error_report.component])
            
        # 환경별 라벨
        if error_report.environment:
            labels.append(f"env:{error_report.environment}")
            
        return labels
    
    async def create_github_issue(self, error_report: ErrorReport) -> Optional[Dict]:
        """GitHub 이슈 생성"""
        if not self.github_token:
            print("GitHub token이 설정되지 않았습니다. 이슈 생성을 건너뜁니다.")
            return None
            
        # 중복 체크
        issue_hash = self._generate_issue_hash(error_report)
        if issue_hash in self.issue_cache:
            print(f"중복 이슈 감지: {issue_hash}")
            return None
            
        issue_data = {
            "title": self._format_issue_title(error_report),
            "body": self._format_issue_body(error_report),
            "labels": self._get_issue_labels(error_report)
        }
        
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=issue_data, headers=headers) as response:
                    if response.status == 201:
                        result = await response.json()
                        self.issue_cache[issue_hash] = result["number"]
                        print(f"GitHub 이슈 생성 완료: #{result['number']} - {result['html_url']}")
                        return result
                    else:
                        error_text = await response.text()
                        print(f"GitHub 이슈 생성 실패: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            print(f"GitHub API 호출 중 오류: {str(e)}")
            return None
    
    async def report_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict]:
        """에러 리포트 생성 및 GitHub 이슈 생성"""
        
        # 기본 컨텍스트 설정
        if context is None:
            context = {}
            
        # 에러 정보 추출
        error_type = type(error).__name__
        error_message = str(error)
        stack_trace = traceback.format_exc()
        
        # 에러 리포트 생성
        error_report = ErrorReport(
            title=error_message[:100] + "..." if len(error_message) > 100 else error_message,
            error_type=error_type,
            error_message=error_message,
            stack_trace=stack_trace,
            timestamp=datetime.now(),
            user_id=context.get("user_id"),
            request_path=context.get("path"),
            request_method=context.get("method"),
            user_agent=context.get("user_agent"),
            ip_address=context.get("client_ip"),
            environment=context.get("environment", "production"),
            severity=context.get("severity", "error"),
            component=context.get("component", "backend")
        )
        
        # GitHub 이슈 생성
        return await self.create_github_issue(error_report)
    
    async def report_frontend_error(
        self,
        error_data: Dict[str, Any]
    ) -> Optional[Dict]:
        """프론트엔드 에러 리포트"""
        
        error_report = ErrorReport(
            title=error_data.get("message", "Frontend Error")[:100],
            error_type=error_data.get("name", "JavaScriptError"),
            error_message=error_data.get("message", "Unknown error"),
            stack_trace=error_data.get("stack", "No stack trace available"),
            timestamp=datetime.now(),
            user_id=error_data.get("userId"),
            request_path=error_data.get("url"),
            request_method="GET",
            user_agent=error_data.get("userAgent"),
            ip_address=error_data.get("clientIp"),
            environment=error_data.get("environment", "production"),
            severity=error_data.get("severity", "error"),
            component="frontend"
        )
        
        return await self.create_github_issue(error_report)

# 싱글톤 인스턴스
github_issues_service = GitHubIssuesService()