"""
Smoke tests for quick CI/CD validation
These tests should complete within 30 seconds and verify core functionality
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

pytestmark = pytest.mark.smoke

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_health_endpoint(async_client: AsyncClient):
    """Test that health endpoint is accessible"""
    response = await async_client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert "version" in data

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_database_connection(async_session: AsyncSession):
    """Test that database is accessible"""
    result = await async_session.execute("SELECT 1")
    assert result.scalar() == 1

@pytest.mark.smoke
@pytest.mark.asyncio 
async def test_api_docs(async_client: AsyncClient):
    """Test that API documentation is accessible"""
    response = await async_client.get("/api/docs")
    assert response.status_code == 200

@pytest.mark.smoke
@pytest.mark.critical
@pytest.mark.asyncio
async def test_worker_api_basic(async_client: AsyncClient):
    """Test basic worker API functionality"""
    # Test list workers (should return empty list or existing workers)
    response = await async_client.get("/api/v1/workers/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

@pytest.mark.smoke
@pytest.mark.asyncio
async def test_cors_headers(async_client: AsyncClient):
    """Test that CORS headers are properly set"""
    response = await async_client.options(
        "/api/v1/workers/",
        headers={"Origin": "http://localhost:5173"}
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers