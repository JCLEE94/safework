"""
에러 리포팅 미들웨어
Error reporting middleware for automatic GitHub issue creation
"""

import asyncio
import traceback
from datetime import datetime
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from src.services.github_issues import github_issues_service
import logging

logger = logging.getLogger(__name__)

class ErrorReportingMiddleware:
    """자동 에러 리포팅 미들웨어"""
    
    def __init__(self, app, enabled: bool = True):
        self.app = app
        self.enabled = enabled
        
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        try:
            # 정상 요청 처리
            response = await call_next(request)
            return response
            
        except Exception as error:
            # 에러 발생 시 리포팅
            if self.enabled:
                # 백그라운드에서 GitHub 이슈 생성 (블로킹 방지)
                asyncio.create_task(self._report_error_async(error, request))
            
            # 사용자에게는 일반적인 에러 응답 반환
            logger.error(f"Unhandled error: {str(error)}\n{traceback.format_exc()}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "내부 서버 오류가 발생했습니다. 개발팀에 자동으로 리포트되었습니다.",
                    "error_id": str(hash(str(error)))[:8],
                    "timestamp": datetime.now().isoformat()
                }
            )
    
    async def _report_error_async(self, error: Exception, request: Request):
        """비동기 에러 리포팅"""
        try:
            # 요청 컨텍스트 정보 수집
            context = {
                "path": str(request.url.path),
                "method": request.method,
                "user_agent": request.headers.get("user-agent"),
                "client_ip": self._get_client_ip(request),
                "environment": "production",
                "component": "backend",
                "severity": self._determine_severity(error)
            }
            
            # 사용자 정보 추출 (가능한 경우)
            try:
                if hasattr(request.state, "user_id"):
                    context["user_id"] = str(request.state.user_id)
            except:
                pass
            
            # GitHub 이슈 생성
            await github_issues_service.report_error(error, context)
            
        except Exception as reporting_error:
            # 리포팅 자체에서 에러가 발생한 경우 로그만 남김
            logger.error(f"Error reporting failed: {str(reporting_error)}")
    
    def _get_client_ip(self, request: Request) -> str:
        """클라이언트 IP 추출"""
        # 프록시를 통한 접근인 경우 실제 IP 추출
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
            
        return request.client.host if request.client else "unknown"
    
    def _determine_severity(self, error: Exception) -> str:
        """에러 심각도 결정"""
        # 특정 에러 타입에 따른 심각도 분류
        critical_errors = [
            "DatabaseError", 
            "ConnectionError", 
            "SecurityError",
            "AuthenticationError"
        ]
        
        warning_errors = [
            "ValidationError",
            "HTTPException", 
            "FileNotFoundError"
        ]
        
        error_name = type(error).__name__
        
        if error_name in critical_errors:
            return "critical"
        elif error_name in warning_errors:
            return "warning"
        else:
            return "error"

def add_error_reporting_middleware(app, enabled: bool = True):
    """에러 리포팅 미들웨어 추가"""
    app.middleware("http")(ErrorReportingMiddleware(app, enabled))
    logger.info(f"Error reporting middleware {'enabled' if enabled else 'disabled'}")