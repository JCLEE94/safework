"""
캐싱 미들웨어
Caching middleware for API response caching
"""

import hashlib
import json
from typing import Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ..services.cache import CacheTTL, cache_service
from ..utils.logger import logger


class ResponseCachingMiddleware(BaseHTTPMiddleware):
    """API 응답 캐싱 미들웨어"""

    def __init__(self, app: ASGIApp, cache_paths: Optional[list] = None):
        super().__init__(app)
        # 캐싱할 경로 패턴
        self.cache_paths = cache_paths or [
            "/api/v1/dashboard",
            "/api/v1/workers/statistics",
            "/api/v1/health-exams/statistics",
            "/api/v1/work-environments/statistics",
            "/api/v1/chemical-substances/statistics",
            "/api/v1/accident-reports/statistics",
        ]
        # 캐싱하지 않을 메서드
        self.non_cacheable_methods = {"POST", "PUT", "PATCH", "DELETE"}

    def _should_cache(self, request: Request) -> bool:
        """요청이 캐싱 대상인지 확인"""
        # GET 요청만 캐싱
        if request.method in self.non_cacheable_methods:
            return False

        # 설정된 경로만 캐싱
        path = str(request.url.path)
        return any(cache_path in path for cache_path in self.cache_paths)

    def _generate_cache_key(self, request: Request) -> str:
        """요청 기반 캐시 키 생성"""
        # URL path + query parameters로 키 생성
        path = str(request.url.path)
        query_params = str(request.query_params)

        # 사용자별 캐싱을 위해 user_id도 포함 (나중에 인증 구현 시)
        user_id = getattr(request.state, "user_id", "anonymous")

        cache_data = f"{path}:{query_params}:{user_id}"
        cache_hash = hashlib.md5(cache_data.encode()).hexdigest()[:12]

        return f"health_cache:response:{cache_hash}"

    def _get_cache_ttl(self, path: str) -> int:
        """경로별 캐시 TTL 반환"""
        if "dashboard" in path:
            return CacheTTL.DASHBOARD
        elif "statistics" in path:
            return CacheTTL.STATISTICS
        elif "workers" in path:
            return CacheTTL.WORKER_INFO
        elif "health-exams" in path:
            return CacheTTL.HEALTH_EXAM
        else:
            return CacheTTL.STATISTICS  # 기본값

    async def dispatch(self, request: Request, call_next):
        # 캐싱 대상이 아니면 그대로 처리
        if not self._should_cache(request):
            return await call_next(request)

        # 캐시 키 생성
        cache_key = self._generate_cache_key(request)

        try:
            # 캐시에서 조회
            cached_response = await cache_service.get(cache_key)
            if cached_response:
                logger.debug(f"API 응답 캐시 적중: {request.url.path}")

                # 캐시된 응답 반환
                return Response(
                    content=json.dumps(cached_response["content"], ensure_ascii=False),
                    status_code=cached_response["status_code"],
                    headers={
                        "content-type": "application/json; charset=utf-8",
                        "x-cache": "HIT",
                        "x-cache-key": cache_key[-8:],  # 캐시 키 마지막 8자리만 노출
                    },
                )

        except Exception as e:
            logger.warning(f"캐시 조회 중 오류: {e}")

        # 원본 요청 처리
        response = await call_next(request)

        # 응답 캐싱 (성공적인 응답만)
        if response.status_code == 200:
            try:
                # 응답 본문 읽기
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk

                # JSON 파싱 가능한 응답만 캐싱
                try:
                    response_data = json.loads(response_body.decode())

                    # 캐시 데이터 구성
                    cache_data = {
                        "content": response_data,
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    }

                    # 캐시 저장
                    ttl = self._get_cache_ttl(str(request.url.path))
                    await cache_service.set(cache_key, cache_data, ttl)

                    logger.debug(
                        f"API 응답 캐시 저장: {request.url.path}, TTL: {ttl}초"
                    )

                    # 캐시 헤더 추가
                    response.headers["x-cache"] = "MISS"
                    response.headers["x-cache-ttl"] = str(ttl)

                except json.JSONDecodeError:
                    # JSON이 아닌 응답은 캐싱하지 않음
                    pass

                # 새로운 응답 생성 (body가 이미 읽혔으므로)
                return Response(
                    content=response_body,
                    status_code=response.status_code,
                    headers=response.headers,
                    media_type=response.media_type,
                )

            except Exception as e:
                logger.warning(f"응답 캐싱 중 오류: {e}")

        return response


class CacheInvalidationMiddleware(BaseHTTPMiddleware):
    """캐시 무효화 미들웨어"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        # 모델별 무효화 패턴
        self.invalidation_patterns = {
            "workers": ["worker", "dashboard", "statistics"],
            "health-exams": ["health_exam", "dashboard", "statistics"],
            "work-environments": ["work_env", "dashboard", "statistics"],
            "chemical-substances": ["chemical", "dashboard", "statistics"],
            "accident-reports": ["accident", "dashboard", "statistics"],
        }

    def _should_invalidate(self, request: Request) -> bool:
        """캐시 무효화가 필요한 요청인지 확인"""
        # 데이터 변경 메서드만 무효화 대상
        return request.method in {"POST", "PUT", "PATCH", "DELETE"}

    def _get_invalidation_patterns(self, path: str) -> list:
        """경로별 무효화 패턴 반환"""
        patterns = []

        for resource, cache_patterns in self.invalidation_patterns.items():
            if resource in path:
                patterns.extend(cache_patterns)
                break

        # 공통 패턴 추가
        patterns.extend(["response", "dashboard"])

        return patterns

    async def dispatch(self, request: Request, call_next):
        # 원본 요청 처리
        response = await call_next(request)

        # 성공적인 데이터 변경 요청 후 캐시 무효화
        if self._should_invalidate(request) and 200 <= response.status_code < 300:

            try:
                patterns = self._get_invalidation_patterns(str(request.url.path))

                for pattern in patterns:
                    deleted_count = await cache_service.delete_pattern(
                        f"health_cache:{pattern}*"
                    )
                    if deleted_count > 0:
                        logger.info(
                            f"캐시 무효화: {pattern} 패턴, 삭제된 키: {deleted_count}개"
                        )

            except Exception as e:
                logger.warning(f"캐시 무효화 중 오류: {e}")

        return response
