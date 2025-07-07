"""
Redis 캐싱 서비스
Redis caching service for health management system
"""

import json
import hashlib
from typing import Any, Optional, Union, Callable, Dict
from functools import wraps
import asyncio
import redis.asyncio as redis
from datetime import timedelta

from ..config.settings import get_settings
from ..utils.logger import logger


class CacheService:
    """Redis 캐싱 서비스 클래스"""
    
    def __init__(self):
        self.settings = get_settings()
        self.redis_client: Optional[redis.Redis] = None
        self._connected = False
    
    async def connect(self):
        """Redis 연결 설정"""
        try:
            self.redis_client = redis.from_url(
                self.settings.generate_redis_url(),
                encoding="utf-8",
                decode_responses=True
            )
            # 연결 테스트
            await self.redis_client.ping()
            self._connected = True
            logger.info("Redis 캐시 서비스 연결 성공")
        except Exception as e:
            logger.error(f"Redis 연결 실패: {e}")
            self._connected = False
            raise
    
    async def disconnect(self):
        """Redis 연결 해제"""
        if self.redis_client:
            await self.redis_client.close()
            self._connected = False
            logger.info("Redis 캐시 서비스 연결 해제")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """캐시 키 생성"""
        # 함수 인자를 포함한 고유 키 생성
        key_data = f"{prefix}:{args}:{kwargs}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:8]
        return f"health_cache:{prefix}:{key_hash}"
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        if not self._connected:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                logger.debug(f"캐시 적중: {key}")
                return json.loads(data)
        except Exception as e:
            logger.warning(f"캐시 조회 실패: {key}, 에러: {e}")
        
        return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 데이터 저장"""
        if not self._connected:
            return False
        
        try:
            data = json.dumps(value, ensure_ascii=False, default=str)
            await self.redis_client.setex(
                key, 
                ttl or 3600,  # 기본 1시간
                data
            )
            logger.debug(f"캐시 저장: {key}, TTL: {ttl}초")
            return True
        except Exception as e:
            logger.warning(f"캐시 저장 실패: {key}, 에러: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """캐시에서 데이터 삭제"""
        if not self._connected:
            return False
        
        try:
            result = await self.redis_client.delete(key)
            if result:
                logger.debug(f"캐시 삭제: {key}")
            return bool(result)
        except Exception as e:
            logger.warning(f"캐시 삭제 실패: {key}, 에러: {e}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """패턴 매칭으로 캐시 삭제"""
        if not self._connected:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                result = await self.redis_client.delete(*keys)
                logger.info(f"패턴 캐시 삭제: {pattern}, 삭제된 키 수: {result}")
                return result
        except Exception as e:
            logger.warning(f"패턴 캐시 삭제 실패: {pattern}, 에러: {e}")
        
        return 0
    
    async def exists(self, key: str) -> bool:
        """캐시 키 존재 여부 확인"""
        if not self._connected:
            return False
        
        try:
            return bool(await self.redis_client.exists(key))
        except Exception as e:
            logger.warning(f"캐시 존재 확인 실패: {key}, 에러: {e}")
            return False


# 글로벌 캐시 서비스 인스턴스
cache_service = CacheService()


async def get_cache_service() -> CacheService:
    """FastAPI 의존성 주입용 캐시 서비스 팩토리"""
    if not cache_service._connected:
        await cache_service.connect()
    return cache_service


# 캐시 TTL 상수
class CacheTTL:
    """캐시 TTL 설정"""
    STATISTICS = 3600        # 통계 데이터: 1시간
    WORKER_INFO = 1800       # 근로자 정보: 30분
    PDF_RESULT = 86400       # PDF 생성 결과: 24시간
    DASHBOARD = 1800         # 대시보드 데이터: 30분
    HEALTH_EXAM = 7200       # 건강검진 데이터: 2시간
    SESSION = 86400          # 세션 데이터: 24시간


def cache_result(prefix: str, ttl: int = CacheTTL.STATISTICS):
    """
    함수 결과 캐싱 데코레이터
    
    Args:
        prefix: 캐시 키 접두사
        ttl: 캐시 TTL (초)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = cache_service._generate_key(prefix, *args, **kwargs)
            
            # 캐시에서 조회
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 함수 실행
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # 결과 캐싱
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


def cache_query(model_name: str, ttl: int = CacheTTL.WORKER_INFO):
    """
    데이터베이스 쿼리 결과 캐싱 데코레이터
    
    Args:
        model_name: 모델명 (캐시 키 구성에 사용)
        ttl: 캐시 TTL (초)
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 캐시 키 생성
            cache_key = cache_service._generate_key(f"query:{model_name}", *args, **kwargs)
            
            # 캐시에서 조회
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # 쿼리 실행
            result = await func(*args, **kwargs)
            
            # 결과 캐싱 (None이 아닌 경우만)
            if result is not None:
                await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


async def invalidate_cache_pattern(pattern: str):
    """캐시 무효화 함수"""
    return await cache_service.delete_pattern(f"health_cache:{pattern}*")


# 모델별 캐시 무효화 함수들
async def invalidate_worker_cache(worker_id: Optional[int] = None):
    """근로자 관련 캐시 무효화"""
    patterns = ["query:Worker", "worker_stats", "dashboard"]
    if worker_id:
        patterns.append(f"worker:{worker_id}")
    
    for pattern in patterns:
        await invalidate_cache_pattern(pattern)


async def invalidate_health_exam_cache(worker_id: Optional[int] = None):
    """건강검진 관련 캐시 무효화"""
    patterns = ["query:HealthExam", "health_stats", "dashboard"]
    if worker_id:
        patterns.append(f"health_exam:worker:{worker_id}")
    
    for pattern in patterns:
        await invalidate_cache_pattern(pattern)


async def invalidate_dashboard_cache():
    """대시보드 관련 캐시 무효화"""
    await invalidate_cache_pattern("dashboard")
    await invalidate_cache_pattern("statistics")


# 세션 관리 함수들
async def set_session(session_id: str, data: Dict[str, Any], ttl: int = CacheTTL.SESSION):
    """세션 데이터 저장"""
    key = f"health_cache:session:{session_id}"
    return await cache_service.set(key, data, ttl)


async def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    """세션 데이터 조회"""
    key = f"health_cache:session:{session_id}"
    return await cache_service.get(key)


async def delete_session(session_id: str):
    """세션 데이터 삭제"""
    key = f"health_cache:session:{session_id}"
    return await cache_service.delete(key)


# PDF 캐싱 함수들
async def cache_pdf_result(form_id: str, data_hash: str, pdf_data: bytes, ttl: int = CacheTTL.PDF_RESULT):
    """PDF 생성 결과 캐싱"""
    key = f"health_cache:pdf:{form_id}:{data_hash}"
    # PDF 데이터를 base64로 인코딩하여 저장
    import base64
    pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')
    return await cache_service.set(key, pdf_base64, ttl)


async def get_cached_pdf(form_id: str, data_hash: str) -> Optional[bytes]:
    """캐시된 PDF 조회"""
    key = f"health_cache:pdf:{form_id}:{data_hash}"
    pdf_base64 = await cache_service.get(key)
    if pdf_base64:
        import base64
        return base64.b64decode(pdf_base64.encode('utf-8'))
    return None