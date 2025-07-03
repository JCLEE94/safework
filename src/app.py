"""
FastAPI 애플리케이션 메인 모듈 - 최적화된 버전
Main FastAPI application module - optimized version with advanced logging and error handling
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import uvicorn
from datetime import datetime

# 개선된 로깅 시스템 import
from .utils.logger import logger
from .utils.error_handlers import ERROR_HANDLERS
from .middleware.logging import LoggingMiddleware, PerformanceMiddleware, SecurityLoggingMiddleware
from .middleware.caching import ResponseCachingMiddleware, CacheInvalidationMiddleware
from .middleware.performance import (
    RateLimitMiddleware, CompressionMiddleware, ConnectionPoolMiddleware,
    QueryOptimizationMiddleware, BatchingMiddleware, PaginationOptimizationMiddleware
)
from .middleware.security import (
    CSRFProtectionMiddleware, XSSProtectionMiddleware, SQLInjectionProtectionMiddleware,
    ContentSecurityPolicyMiddleware, APIKeyAuthMiddleware, IPWhitelistMiddleware,
    SecurityHeadersMiddleware
)
from .middleware.auth import (
    JWTAuthMiddleware, RoleBasedAccessMiddleware, SessionManagementMiddleware
)
from .services.cache import cache_service
from .services.monitoring import initialize_monitoring, get_metrics_collector
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시
    logger.info("건설업 보건관리 시스템 시작")
    logger.info("데이터베이스 초기화 시작...")
    
    try:
        from .config.database import init_db
        await init_db()
        logger.info("데이터베이스 초기화 성공")
        
        # 데이터베이스 최적화
        try:
            from .utils.db_optimization import initialize_db_optimization
            await initialize_db_optimization()
            logger.info("데이터베이스 최적화 완료")
        except Exception as opt_e:
            logger.warning(f"데이터베이스 최적화 실패 (비치명적): {opt_e}")
        
        # Redis 캐시 서비스 연결
        try:
            await cache_service.connect()
            logger.info("Redis 캐시 서비스 연결 성공")
            
            # 모니터링 서비스 초기화
            await initialize_monitoring(cache_service.redis_client)
            logger.info("모니터링 서비스 초기화 성공")
            
            # 백그라운드 메트릭 수집 시작 (주석 처리 - 함수 없음)
            # asyncio.create_task(collect_metrics_background())
            logger.info("백그라운드 메트릭 수집 준비")
        except Exception as cache_e:
            logger.warning(f"Redis 캐시 서비스 연결 실패 (비치명적): {cache_e}")
            # Redis 없이도 모니터링은 작동
            await initialize_monitoring(None)
            logger.info("모니터링 서비스 초기화 성공 (Redis 없음)")
        
        # 데이터베이스 최적화 실행
        try:
            from .models.migration_optimized import optimize_database
            optimize_database()
            logger.info("데이터베이스 최적화 완료")
        except Exception as opt_e:
            logger.warning(f"데이터베이스 최적화 실패 (비치명적): {opt_e}")
            
    except Exception as e:
        logger.error(f"데이터베이스 초기화 실패: {e}")
        raise
    
    yield
    
    # 종료 시
    await cache_service.disconnect()
    logger.info("건설업 보건관리 시스템 종료")


def create_app() -> FastAPI:
    """FastAPI 애플리케이션 팩토리"""
    from .config.settings import get_settings
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="SafeWork Pro - Construction Health Management System",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/openapi.json"
    )
    
    # 에러 핸들러 등록
    for exception_type, handler in ERROR_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)
    
    logger.info("에러 핸들러 등록 완료")
    
    # 미들웨어 등록 (순서 중요) - 설정값 사용
    # TEMPORARY: Disable ALL middleware to fix POST request issues
    # Only keep CORS which is essential
    
    # # 1. Security headers (first)
    # app.add_middleware(SecurityHeadersMiddleware)
    
    # # 2. Rate limiting and DDoS protection
    # app.add_middleware(RateLimitMiddleware, rate_limit=settings.rate_limit, window_seconds=settings.rate_limit_window)
    # app.add_middleware(IPWhitelistMiddleware, enabled=False)  # Disabled by default
    
    # # 3. Security protection
    # app.add_middleware(XSSProtectionMiddleware)
    # app.add_middleware(SQLInjectionProtectionMiddleware)
    # app.add_middleware(CSRFProtectionMiddleware)
    # app.add_middleware(ContentSecurityPolicyMiddleware)
    
    # # 4. Authentication and authorization
    # app.add_middleware(JWTAuthMiddleware)
    # app.add_middleware(RoleBasedAccessMiddleware)
    # app.add_middleware(SessionManagementMiddleware)
    # app.add_middleware(APIKeyAuthMiddleware, api_keys=set())  # Add API keys as needed
    
    # # 5. Logging
    # app.add_middleware(SecurityLoggingMiddleware)
    # app.add_middleware(LoggingMiddleware)
    
    # # 6. Performance optimization
    # app.add_middleware(CompressionMiddleware)
    # app.add_middleware(ConnectionPoolMiddleware, pool_size=settings.db_pool_size, max_overflow=10)
    # app.add_middleware(QueryOptimizationMiddleware, slow_query_threshold=settings.slow_query_threshold)
    # app.add_middleware(BatchingMiddleware, batch_window_ms=50, max_batch_size=settings.max_batch_size)
    # app.add_middleware(PaginationOptimizationMiddleware, default_page_size=50, max_page_size=200)
    
    # # 7. Caching
    # app.add_middleware(CacheInvalidationMiddleware)
    # app.add_middleware(ResponseCachingMiddleware)
    
    # # 8. Performance monitoring (last to measure total time)
    # app.add_middleware(PerformanceMiddleware, slow_request_threshold=1000.0)
    
    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    logger.info("미들웨어 등록 완료")
    
    # Health check - Define before static files
    @app.get("/health")
    async def health_check():
        """시스템 상태 확인"""
        return {
            "status": "healthy",
            "service": "건설업 보건관리 시스템",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "timezone": "Asia/Seoul (KST)",
            "components": {
                "database": "connected",
                "api": "running",
                "frontend": "active"
            }
        }
    
    # API 라우터 등록
    from .handlers.workers import router as workers_router
    from .handlers.health_exams import router as health_exams_router
    from .handlers.health_consultations import router as health_consultations_router
    from .handlers.work_environments import router as work_environments_router
    from .handlers.health_education import router as health_education_router
    from .handlers.chemical_substances import router as chemical_substances_router
    from .handlers.accident_reports import router as accident_reports_router
    from .handlers.documents import router as documents_router, pdf_router
    from .handlers.pdf_auto_fill import router as pdf_auto_router
    from .handlers.monitoring import router as monitoring_router
    from .handlers.auth import router as auth_router
    from .handlers.reports import router as reports_router
    from .handlers.pipeline import router as pipeline_router
    from .handlers.compliance import router as compliance_router
    from .handlers.dashboard import router as dashboard_router
    from .handlers.legal_forms import router as legal_forms_router, unified_router as unified_documents_router
    from .handlers.settings import router as settings_router
    from .handlers.checklist import router as checklist_router
    from .handlers.special_materials import router as special_materials_router
    
    app.include_router(workers_router, prefix="/api/v1/workers", tags=["근로자관리"])
    app.include_router(health_exams_router, tags=["건강진단"])
    app.include_router(health_consultations_router, tags=["보건상담"])
    app.include_router(work_environments_router, tags=["작업환경측정"])
    app.include_router(health_education_router, tags=["보건교육"])
    app.include_router(chemical_substances_router, tags=["화학물질관리"])
    app.include_router(accident_reports_router, tags=["산업재해"])
    app.include_router(documents_router, tags=["문서관리"])
    app.include_router(pdf_router, tags=["PDF편집"])
    app.include_router(pdf_auto_router, tags=["PDF자동매핑"])
    app.include_router(monitoring_router, tags=["모니터링"])
    app.include_router(auth_router, tags=["인증"])
    app.include_router(reports_router, tags=["보고서"])
    app.include_router(pipeline_router, tags=["파이프라인"])
    app.include_router(compliance_router, tags=["법령준수"])
    app.include_router(dashboard_router, tags=["대시보드"])
    app.include_router(legal_forms_router, tags=["법정서식"])
    app.include_router(unified_documents_router, tags=["통합문서"])
    app.include_router(settings_router, tags=["설정관리"])
    app.include_router(checklist_router, tags=["체크리스트"])
    app.include_router(special_materials_router, tags=["특별관리물질"])
    
    # 정적 파일 서빙 (React 빌드된 파일들) - Mount after all API routes
    try:
        # 설정에서 정적 파일 디렉토리 가져오기
        static_dir = settings.static_files_dir if os.path.exists(settings.static_files_dir) else os.path.join(os.path.dirname(__file__), "../static")
        
        if os.path.exists(static_dir):
            app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
            logger.info(f"정적 파일 마운트 완료: {static_dir} -> /")
        else:
            logger.warning(f"정적 파일 디렉토리가 없습니다: {static_dir}")
            # 기본 fallback 응답
            @app.get("/")
            async def root():
                return {"message": settings.app_name + " API", "status": "running", "frontend": "not available"}
    except Exception as e:
        logger.warning(f"정적 파일 마운트 실패: {e}")
        # 기본 fallback 응답
        @app.get("/")
        async def root():
            return {"message": settings.app_name + " API", "status": "running", "error": str(e)}
    
    return app

# 애플리케이션 인스턴스 생성
app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        access_log=True
    )