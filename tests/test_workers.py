"""
근로자 API 테스트
Tests for Workers API
"""
import pytest
from httpx import AsyncClient
from src.app import create_app

async def test_create_worker():
    """근로자 생성 테스트"""
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        worker_data = {
            "name": "테스트근로자",
            "employee_id": "TEST001",
            "employment_type": "정규직",
            "work_type": "건설"
        }
        
        response = await client.post("/api/v1/workers/", json=worker_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "테스트근로자"
        assert data["employee_id"] == "TEST001"

async def test_get_workers():
    """근로자 목록 조회 테스트"""
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/workers/")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

async def test_health_check():
    """헬스체크 테스트"""
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

async def test_pdf_forms():
    """PDF 양식 목록 테스트"""
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/documents/pdf-forms")
        assert response.status_code == 200
        data = response.json()
        assert "forms" in data
        assert len(data["forms"]) > 0

async def test_pdf_test_endpoint():
    """PDF 테스트 엔드포인트"""
    app = create_app()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/documents/test-pdf")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"