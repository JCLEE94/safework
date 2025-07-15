"""
Reusable Test Fixtures for Integration Testing
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import date, datetime
from typing import Any, AsyncGenerator, Dict, Optional

import redis.asyncio as redis
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)

from src.app import create_app
from src.config.database import get_db
from src.config.settings import get_settings
from src.models import Base, HealthExam, WorkEnvironment, Worker
from src.services.cache import CacheService

settings = get_settings()


class TestDatabase:
    """Test database fixture with transaction rollback"""

    def __init__(self):
        self.engine = None
        self.session_maker = None

    async def setup(self):
        """Initialize test database"""
        # Use in-memory SQLite for tests
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )

        # Create tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def teardown(self):
        """Clean up database"""
        if self.engine:
            await self.engine.dispose()

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a test database session with automatic commit for SQLite"""
        async with self.session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise


class TestClient:
    """Test HTTP client with authentication"""

    def __init__(self):
        self.app = None
        self.client = None
        self.auth_token = None

    async def setup(self, db: TestDatabase):
        """Initialize test client"""
        self.app = create_app()

        # Override database dependency
        async def override_get_db():
            async with db.get_session() as session:
                yield session

        self.app.dependency_overrides[get_db] = override_get_db

        # Create client
        transport = ASGITransport(app=self.app)
        self.client = AsyncClient(transport=transport, base_url="http://test")

        # Test environment is set via environment variable

    async def teardown(self):
        """Clean up client"""
        if self.client:
            await self.client.aclose()

    def set_auth(self, token: str):
        """Set authentication token"""
        self.auth_token = token
        self.client.headers["Authorization"] = f"Bearer {token}"

    async def get(self, url: str, **kwargs) -> Any:
        """GET request with auth"""
        return await self.client.get(url, **kwargs)

    async def post(self, url: str, **kwargs) -> Any:
        """POST request with auth"""
        return await self.client.post(url, **kwargs)

    async def put(self, url: str, **kwargs) -> Any:
        """PUT request with auth"""
        return await self.client.put(url, **kwargs)

    async def patch(self, url: str, **kwargs) -> Any:
        """PATCH request with auth"""
        return await self.client.patch(url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Any:
        """DELETE request with auth"""
        return await self.client.delete(url, **kwargs)


class TestCache:
    """Test Redis cache fixture"""

    def __init__(self):
        self.redis_client = None
        self.cache_service = None

    async def setup(self):
        """Initialize test cache"""
        # Use separate Redis DB for tests
        self.redis_client = await redis.from_url(
            "redis://localhost:6379/15",  # Test DB
            encoding="utf-8",
            decode_responses=True,
        )

        self.cache_service = CacheService()
        # Override the redis client for testing
        self.cache_service.redis_client = self.redis_client
        self.cache_service._connected = True

        # Clear test database
        await self.redis_client.flushdb()

    async def teardown(self):
        """Clean up cache"""
        if self.redis_client:
            await self.redis_client.flushdb()
            await self.redis_client.close()

    async def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        return await self.cache_service.get(key)

    async def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache"""
        await self.cache_service.set(key, value, ttl)

    async def delete(self, key: str):
        """Delete from cache"""
        await self.cache_service.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        return await self.redis_client.exists(key) > 0


class TestAuth:
    """Test authentication helper"""

    @staticmethod
    def create_test_token(user_id: int = 1, role: str = "admin") -> str:
        """Create a test JWT token"""
        # In test environment, we can use a simple token
        return f"test_token_{user_id}_{role}"

    @staticmethod
    def create_test_user(
        name: str = "테스트관리자", email: str = "admin@test.com", role: str = "admin"
    ) -> Dict[str, Any]:
        """Create test user data"""
        return {
            "id": 1,
            "name": name,
            "email": email,
            "role": role,
            "department": "안전관리팀",
            "is_active": True,
        }


# Test data creation helpers
async def create_test_worker(
    session: AsyncSession,
    name: str = "테스트근로자",
    employee_id: Optional[str] = None,
    **kwargs,
) -> Worker:
    """Create a test worker"""
    worker_data = {
        "name": name,
        "employee_id": employee_id or f"TEST_{datetime.now().timestamp()}",
        "birth_date": date(1990, 1, 1),
        "gender": "male",
        "phone": "010-1234-5678",
        "employment_type": "regular",
        "work_type": "construction",
        "department": "공무부",
        "hire_date": date.today(),
        **kwargs,
    }

    worker = Worker(**worker_data)
    session.add(worker)
    await session.commit()
    await session.refresh(worker)
    return worker


async def create_test_health_exam(
    session: AsyncSession, worker_id: int, exam_date: Optional[date] = None, **kwargs
) -> HealthExam:
    """Create a test health exam"""
    exam_data = {
        "worker_id": worker_id,
        "exam_date": exam_date or date.today(),
        "exam_type": "일반건강진단",
        "exam_agency": "테스트병원",
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "heart_rate": 72,
        "height": 175.5,
        "weight": 70.0,
        "vision_left": 1.0,
        "vision_right": 1.0,
        "hearing_left": "정상",
        "hearing_right": "정상",
        "overall_result": "정상",
        **kwargs,
    }

    exam = HealthExam(**exam_data)
    session.add(exam)
    await session.commit()
    await session.refresh(exam)
    return exam


async def create_test_environment_data(
    session: AsyncSession, measurement_date: Optional[date] = None, **kwargs
) -> WorkEnvironment:
    """Create test work environment data"""
    env_data = {
        "measurement_date": measurement_date or date.today(),
        "location": "A동 3층",
        "dust_concentration": 0.05,
        "noise_level": 75.5,
        "temperature": 22.5,
        "humidity": 55.0,
        "co_concentration": 5.0,
        "co2_concentration": 800.0,
        "illuminance": 500.0,
        "measured_by": "테스트측정자",
        **kwargs,
    }

    env = WorkEnvironment(**env_data)
    session.add(env)
    await session.commit()
    await session.refresh(env)
    return env


# Composite fixture for complete test setup
@asynccontextmanager
async def create_test_environment():
    """Create complete test environment with all fixtures"""
    db = TestDatabase()
    client = TestClient()
    cache = TestCache()

    try:
        # Setup
        await db.setup()
        await client.setup(db)
        await cache.setup()

        yield {"db": db, "client": client, "cache": cache, "auth": TestAuth()}

    finally:
        # Teardown
        await cache.teardown()
        await client.teardown()
        await db.teardown()
