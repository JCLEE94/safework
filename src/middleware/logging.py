"""
로깅 미들웨어
Logging middleware for request/response tracking
"""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..utils.logger import logger


class LoggingMiddleware(BaseHTTPMiddleware):
    """요청/응답 로깅 미들웨어"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # 요청 시작 시간
        start_time = time.time()

        # 요청 로깅
        logger.info(
            f"Request started: {request.method} {request.url.path}",
            request_id=request_id,
            method=request.method,
            endpoint=str(request.url.path),
            query_params=dict(request.query_params),
            client_ip=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent", ""),
        )

        try:
            # 요청 처리
            response = await call_next(request)

            # 응답 시간 계산
            duration_ms = (time.time() - start_time) * 1000

            # 응답 로깅
            logger.api_request(
                method=request.method,
                endpoint=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration_ms,
                request_id=request_id,
                response_size=response.headers.get("content-length", 0),
            )

            # 응답 헤더에 요청 ID 추가
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # 에러 시간 계산
            duration_ms = (time.time() - start_time) * 1000

            # 에러 로깅
            logger.error(
                f"Request failed: {request.method} {request.url.path}",
                error=e,
                request_id=request_id,
                method=request.method,
                endpoint=str(request.url.path),
                duration=duration_ms,
            )

            raise


class PerformanceMiddleware(BaseHTTPMiddleware):
    """성능 모니터링 미들웨어"""

    def __init__(self, app: ASGIApp, slow_request_threshold: float = 1000.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold  # ms

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)

        duration_ms = (time.time() - start_time) * 1000

        # 느린 요청 경고
        if duration_ms > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path}",
                endpoint=str(request.url.path),
                method=request.method,
                duration=duration_ms,
                threshold=self.slow_request_threshold,
                performance_warning=True,
            )

        # 성능 헤더 추가
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    """보안 이벤트 로깅 미들웨어"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.suspicious_patterns = [
            "SELECT",
            "UNION",
            "DROP",
            "DELETE",
            "INSERT",
            "UPDATE",  # SQL injection
            "<script",
            "javascript:",
            "onload=",
            "onerror=",  # XSS
            "../",
            "..\\",
            "/etc/passwd",
            "/proc/",  # Path traversal
        ]

    async def dispatch(self, request: Request, call_next):
        # 보안 검사
        await self._check_security_threats(request)

        response = await call_next(request)
        return response

    async def _check_security_threats(self, request: Request):
        """보안 위협 검사"""
        request_url = str(request.url)
        query_params = str(request.query_params)

        # URL과 쿼리 파라미터에서 의심스러운 패턴 검사
        for pattern in self.suspicious_patterns:
            if (
                pattern.lower() in request_url.lower()
                or pattern.lower() in query_params.lower()
            ):
                logger.security_event(
                    event_type="suspicious_request",
                    details={
                        "pattern": pattern,
                        "url": request_url,
                        "query_params": query_params,
                        "client_ip": request.client.host if request.client else None,
                        "user_agent": request.headers.get("user-agent", ""),
                    },
                    severity="warning",
                )
                break

        # 비정상적으로 긴 요청 URL 검사
        if len(request_url) > 2048:
            logger.security_event(
                event_type="long_url_request",
                details={
                    "url_length": len(request_url),
                    "url": (
                        request_url[:200] + "..."
                        if len(request_url) > 200
                        else request_url
                    ),
                    "client_ip": request.client.host if request.client else None,
                },
                severity="warning",
            )

        # 과도한 헤더 크기 검사
        total_header_size = sum(len(k) + len(v) for k, v in request.headers.items())
        if total_header_size > 8192:  # 8KB
            logger.security_event(
                event_type="large_headers",
                details={
                    "header_size": total_header_size,
                    "client_ip": request.client.host if request.client else None,
                    "headers_count": len(request.headers),
                },
                severity="warning",
            )
