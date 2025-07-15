"""
Optimized pytest configuration for faster test execution
"""

import asyncio
import os
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

# 환경 변수 설정
os.environ["ENVIRONMENT"] = "testing"
os.environ["JWT_SECRET"] = "test-secret-key"

# 데이터베이스 URL 설정
TEST_DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://admin:password@localhost:25432/health_management",
)

# 테스트용 엔진 생성 (연결 풀 최적화)
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # SQL 로깅 비활성화로 속도 향상
    pool_size=5,  # 연결 풀 크기 조정
    max_overflow=10,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300,  # 5분마다 연결 재사용
)

# 세션 팩토리
TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """데이터베이스 초기 설정 (세션당 한 번만)"""
    async with test_engine.begin() as conn:
        # 테스트용 스키마 생성
        from src.models import Base

        await conn.run_sync(Base.metadata.create_all)

    yield

    # 정리 작업
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """비동기 데이터베이스 세션 (함수 범위)"""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()  # 각 테스트 후 롤백


@pytest_asyncio.fixture(scope="function")
async def async_client(
    async_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """비동기 HTTP 클라이언트"""
    from src.app import create_app
    from src.models.database import get_db

    app = create_app()

    # 의존성 오버라이드
    async def override_get_db():
        yield async_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="session")
def event_loop():
    """이벤트 루프 최적화"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


# 테스트 데이터 캐싱
@pytest_asyncio.fixture(scope="session")
async def cached_test_data():
    """자주 사용되는 테스트 데이터 캐싱"""
    return {
        "worker": {
            "name": "테스트 작업자",
            "employee_number": "EMP001",
            "department": "건설부",
            "employment_type": "정규직",
        },
        "health_exam": {
            "exam_type": "일반건강진단",
            "exam_date": "2024-01-01",
            "result": "정상",
        },
    }


# 테스트 속도 향상을 위한 몽키패칭
@pytest.fixture(autouse=True)
def speed_up_tests(monkeypatch):
    """테스트 속도 향상을 위한 설정"""
    # 비밀번호 해싱 라운드 감소
    monkeypatch.setenv("BCRYPT_ROUNDS", "4")

    # 캐시 TTL 감소
    monkeypatch.setenv("CACHE_TTL", "1")

    # 재시도 횟수 감소
    monkeypatch.setenv("MAX_RETRIES", "1")
