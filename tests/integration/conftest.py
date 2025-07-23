"""
Integration test configuration and shared fixtures.

This module provides the foundation for all integration tests including:
- Database setup and teardown
- Authentication fixtures
- Test client configuration
- Shared test data
"""

import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any, Optional
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from redis.asyncio import Redis
import aiofiles

# Import SafeWork components
from src.app import create_app
from src.config.database import Base, get_db
from src.models import (
    Worker, User, HealthExam, HealthConsultation, WorkEnvironment,
    HealthEducation, ChemicalSubstance, AccidentReport
)
from src.config.settings import get_settings
from src.services.auth_service import AuthService
from src.services.cache import CacheService


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_settings():
    """Override settings for testing."""
    settings = get_settings()
    # Override with test-specific values
    test_values = {
        "environment": "test",
        "database_url": "sqlite+aiosqlite:///./test.db",
        "redis_url": "redis://localhost:6379/1",
        "jwt_secret": "test-jwt-secret-key",
        "upload_dir": Path(tempfile.mkdtemp()),
        "log_level": "DEBUG"
    }
    
    # Apply overrides
    for key, value in test_values.items():
        setattr(settings, key, value)
    
    return settings


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """Create test database engine."""
    engine = create_async_engine(
        test_settings.database_url,
        echo=True,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncSession:
    """Create database session for each test."""
    async with AsyncSession(test_engine) as session:
        try:
            yield session
        finally:
            await session.rollback()
            await session.close()


@pytest_asyncio.fixture
async def test_redis(test_settings) -> Redis:
    """Create Redis connection for testing."""
    redis = Redis.from_url(
        test_settings.redis_url,
        encoding="utf-8",
        decode_responses=True
    )
    
    # Clear test database
    await redis.flushdb()
    
    yield redis
    
    # Cleanup
    await redis.flushdb()
    await redis.close()


@pytest_asyncio.fixture
async def test_app(test_settings, db_session, test_redis):
    """Create test FastAPI application."""
    app = create_app()
    
    # Override dependencies for testing
    async def override_get_db():
        yield db_session
    
    async def override_get_redis():
        return test_redis
    
    app.dependency_overrides[get_db] = override_get_db
    
    return app


@pytest_asyncio.fixture
async def client(test_app) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client."""
    async with AsyncClient(app=test_app, base_url="http://testserver") as ac:
        yield ac


@pytest_asyncio.fixture
async def auth_service(db_session, test_settings) -> AuthService:
    """Create authentication service for testing."""
    return AuthService(db=db_session, settings=test_settings)


@pytest_asyncio.fixture
async def cache_service(test_redis) -> CacheService:
    """Create cache service for testing."""
    return CacheService(redis=test_redis)


# User and Authentication Fixtures

@pytest_asyncio.fixture
async def test_admin_user(db_session) -> User:
    """Create admin user for testing."""
    from tests.builders.user_builder import UserBuilder
    
    admin_user = await UserBuilder(db_session).create_admin_user(
        username="admin",
        email="admin@safework.test",
        password="admin123!"
    )
    return admin_user


@pytest_asyncio.fixture
async def test_manager_user(db_session) -> User:
    """Create manager user for testing."""
    from tests.builders.user_builder import UserBuilder
    
    manager_user = await UserBuilder(db_session).create_manager_user(
        username="manager",
        email="manager@safework.test",
        password="manager123!",
        department="건설부"
    )
    return manager_user


@pytest_asyncio.fixture
async def test_worker_user(db_session) -> User:
    """Create worker user for testing."""
    from tests.builders.user_builder import UserBuilder
    
    worker_user = await UserBuilder(db_session).create_worker_user(
        username="worker",
        email="worker@safework.test",
        password="worker123!",
        employee_number="EMP001"
    )
    return worker_user


@pytest_asyncio.fixture
async def admin_headers(auth_service, test_admin_user) -> Dict[str, str]:
    """Generate admin authentication headers."""
    token = await auth_service.create_access_token(
        user_id=test_admin_user.id,
        role=test_admin_user.role
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def manager_headers(auth_service, test_manager_user) -> Dict[str, str]:
    """Generate manager authentication headers."""
    token = await auth_service.create_access_token(
        user_id=test_manager_user.id,
        role=test_manager_user.role
    )
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def worker_headers(auth_service, test_worker_user) -> Dict[str, str]:
    """Generate worker authentication headers."""
    token = await auth_service.create_access_token(
        user_id=test_worker_user.id,
        role=test_worker_user.role
    )
    return {"Authorization": f"Bearer {token}"}


# Worker and Health Data Fixtures

@pytest_asyncio.fixture
async def test_worker(db_session) -> Worker:
    """Create test worker."""
    from tests.builders.worker_builder import WorkerBuilder
    
    worker = await WorkerBuilder(db_session).create(
        name="홍길동",
        employee_number="EMP001",
        department="건설부",
        position="안전관리자"
    )
    return worker


@pytest_asyncio.fixture
async def test_workers(db_session) -> list[Worker]:
    """Create multiple test workers."""
    from tests.builders.worker_builder import WorkerBuilder
    
    builder = WorkerBuilder(db_session)
    workers = []
    
    for i in range(5):
        worker = await builder.create(
            name=f"테스트직원{i+1}",
            employee_number=f"EMP{i+1:03d}",
            department="건설부" if i % 2 == 0 else "관리부",
            position="직원"
        )
        workers.append(worker)
    
    return workers


@pytest_asyncio.fixture
async def test_health_exam(db_session, test_worker) -> HealthExam:
    """Create test health examination."""
    from tests.builders.health_builder import HealthExamBuilder
    
    exam = await HealthExamBuilder(db_session).create(
        worker_id=test_worker.id,
        exam_type="일반건강진단",
        exam_date="2024-01-15"
    )
    return exam


@pytest_asyncio.fixture
async def test_work_environment(db_session) -> WorkEnvironment:
    """Create test work environment record."""
    from tests.builders.environment_builder import WorkEnvironmentBuilder
    
    environment = await WorkEnvironmentBuilder(db_session).create(
        location="현장A",
        measurement_type="소음측정",
        value=85.5,
        unit="dB",
        measured_date="2024-01-20"
    )
    return environment


@pytest_asyncio.fixture
async def test_chemical_substance(db_session) -> ChemicalSubstance:
    """Create test chemical substance."""
    from tests.builders.chemical_builder import ChemicalSubstanceBuilder
    
    chemical = await ChemicalSubstanceBuilder(db_session).create(
        name="아세톤",
        cas_number="67-64-1",
        hazard_class="인화성 액체",
        storage_location="창고A"
    )
    return chemical


# File and Document Fixtures

@pytest_asyncio.fixture
async def test_upload_dir(test_settings) -> Path:
    """Create temporary upload directory."""
    upload_dir = test_settings.upload_dir
    upload_dir.mkdir(exist_ok=True)
    
    yield upload_dir
    
    # Cleanup
    import shutil
    if upload_dir.exists():
        shutil.rmtree(upload_dir)


@pytest_asyncio.fixture
def test_pdf_file() -> bytes:
    """Create test PDF file content."""
    # Simple PDF content for testing
    return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
>>
endobj

xref
0 4
0000000000 65535 f 
0000000009 00000 n 
0000000074 00000 n 
0000000120 00000 n 
trailer
<<
/Size 4
/Root 1 0 R
>>
startxref
179
%%EOF"""


@pytest_asyncio.fixture
def test_image_file() -> bytes:
    """Create test image file content (1x1 PNG)."""
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d494844520000000100000001"
        "08060000001f15c4890000000a49444154789c6300010000"
        "05000106f6000000ffa26450ad0000000049454e44ae426082"
    )


@pytest_asyncio.fixture
def test_document_file() -> bytes:
    """Create test document file content."""
    return b"Test document content for SafeWork Pro testing."


# WebSocket Testing Fixtures

@pytest_asyncio.fixture
async def websocket_client(client):
    """Create WebSocket test client."""
    # Note: This will be implemented when we add WebSocket tests
    # For now, return the HTTP client
    return client


# Performance and Load Testing Fixtures

@pytest_asyncio.fixture
def performance_config() -> Dict[str, Any]:
    """Configuration for performance tests."""
    return {
        "concurrent_users": 10,
        "requests_per_second": 100,
        "test_duration_seconds": 30,
        "acceptable_response_time_ms": 200,
        "acceptable_error_rate": 0.01
    }


# Database Transaction Fixtures

@pytest_asyncio.fixture
async def db_transaction(db_session):
    """Create database transaction that can be rolled back."""
    transaction = await db_session.begin()
    try:
        yield db_session
    finally:
        await transaction.rollback()


@pytest_asyncio.fixture
async def clean_db(db_session):
    """Clean database after each test."""
    yield db_session
    
    # Clean up all tables in reverse order (to handle foreign keys)
    tables = [
        "accident_reports",
        "chemical_substances", 
        "health_education",
        "work_environments",
        "health_consultations",
        "health_exams",
        "workers",
        "users"
    ]
    
    for table in tables:
        await db_session.execute(f"DELETE FROM {table}")
    
    await db_session.commit()


# Mock External Services

@pytest_asyncio.fixture
def mock_email_service():
    """Mock email service for testing notifications."""
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []
        
        async def send_email(self, to: str, subject: str, body: str):
            self.sent_emails.append({
                "to": to,
                "subject": subject,
                "body": body
            })
            return True
        
        def get_sent_emails(self):
            return self.sent_emails
        
        def clear_sent_emails(self):
            self.sent_emails = []
    
    return MockEmailService()


@pytest_asyncio.fixture
def mock_sms_service():
    """Mock SMS service for testing notifications."""
    class MockSMSService:
        def __init__(self):
            self.sent_messages = []
        
        async def send_sms(self, to: str, message: str):
            self.sent_messages.append({
                "to": to,
                "message": message
            })
            return True
        
        def get_sent_messages(self):
            return self.sent_messages
        
        def clear_sent_messages(self):
            self.sent_messages = []
    
    return MockSMSService()


# Error Testing Fixtures

@pytest_asyncio.fixture
def db_connection_error():
    """Simulate database connection error."""
    from sqlalchemy.exc import OperationalError
    return OperationalError("Connection failed", None, None)


@pytest_asyncio.fixture
def redis_connection_error():
    """Simulate Redis connection error."""
    from redis.exceptions import ConnectionError
    return ConnectionError("Redis connection failed")


# Test Data Cleanup

@pytest.fixture(autouse=True)
async def cleanup_test_data(test_upload_dir):
    """Automatically cleanup test data after each test."""
    yield
    
    # Clean up any test files created during the test
    if test_upload_dir.exists():
        for file_path in test_upload_dir.iterdir():
            if file_path.is_file():
                file_path.unlink()


# Test Markers

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "websocket: marks tests that use WebSocket connections"
    )
    config.addinivalue_line(
        "markers", "file_upload: marks tests that involve file uploads"
    )
    config.addinivalue_line(
        "markers", "performance: marks performance/load tests"
    )
    config.addinivalue_line(
        "markers", "security: marks security-focused tests"
    )


# Test Configuration

@pytest.fixture(scope="session")
def test_config():
    """Test configuration settings."""
    return {
        "base_url": "http://testserver",
        "timeout": 30,
        "max_retries": 3,
        "retry_delay": 0.1
    }