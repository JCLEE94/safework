"""
데이터베이스 설정 및 연결
Database configuration and connection
"""

import logging

from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy Base 클래스"""

    pass


# 데이터베이스 엔진 및 세션
engine = None
async_engine = None  # For export
AsyncSessionLocal = None


async def init_db():
    """데이터베이스 초기화"""
    global engine, async_engine, AsyncSessionLocal

    import asyncio

    from .settings import get_settings

    settings = get_settings()

    # PostgreSQL URL을 AsyncPG 형식으로 변환
    database_url = settings.generate_database_url().replace(
        "postgresql://", "postgresql+asyncpg://"
    )

    engine = create_async_engine(
        database_url,
        echo=settings.debug,
        pool_size=20,
        max_overflow=0,
        pool_pre_ping=True,
    )
    async_engine = engine  # Export reference

    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # 모든 모델 임포트 (테이블 생성을 위해)
    from ..models import worker

    # 데이터베이스 연결 대기 및 재시도
    max_retries = 30
    retry_delay = 2

    for attempt in range(max_retries):
        try:
            # 연결 테스트
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("데이터베이스 초기화 완료")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"데이터베이스 연결 시도 {attempt + 1}/{max_retries} 실패: {e}"
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"데이터베이스 연결 최종 실패: {e}")
                logger.info("기존 테이블 사용")


async def get_db() -> AsyncSession:
    """데이터베이스 세션 의존성"""
    if AsyncSessionLocal is None:
        await init_db()

    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# Alias for compatibility with db_optimization
get_async_session = get_db


def get_db_engine():
    """동기 엔진 반환 (마이그레이션용)"""
    return engine
