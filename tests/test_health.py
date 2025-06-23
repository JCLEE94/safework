"""
건설업 보건관리 시스템 테스트
Health management system tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import create_app

@pytest.fixture
def client():
    """테스트 클라이언트 픽스처"""
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    """헬스체크 엔드포인트 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "건설업 보건관리 시스템"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data
    assert "components" in data

def test_root_endpoint(client):
    """루트 엔드포인트 테스트"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "보건관리 시스템" in data["message"]

def test_dashboard_endpoint(client):
    """대시보드 데이터 엔드포인트 테스트"""
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 200
    
    data = response.json()
    
    # 필수 섹션 확인
    assert "workers" in data
    assert "health_exams" in data
    assert "work_environment" in data
    assert "education" in data
    assert "accidents" in data
    assert "chemicals" in data
    
    # 근로자 데이터 구조 확인
    workers = data["workers"]
    assert "total" in workers
    assert "active" in workers
    assert "on_leave" in workers
    assert "health_risk" in workers
    
    # 건강진단 데이터 구조 확인
    health_exams = data["health_exams"]
    assert "completed_this_month" in health_exams
    assert "pending" in health_exams
    assert "overdue" in health_exams
    assert "next_scheduled" in health_exams

def test_worker_statistics_data_types(client):
    """대시보드 데이터 타입 검증"""
    response = client.get("/api/v1/dashboard")
    data = response.json()
    
    # 숫자 타입 확인
    assert isinstance(data["workers"]["total"], int)
    assert isinstance(data["workers"]["active"], int)
    assert isinstance(data["education"]["completion_rate"], (int, float))
    
    # 문자열 타입 확인
    assert isinstance(data["work_environment"]["last_measurement"], str)
    assert isinstance(data["work_environment"]["next_due"], str)
    assert isinstance(data["accidents"]["severity_trend"], str)

def test_cors_headers(client):
    """CORS 헤더 테스트"""
    response = client.options("/health")
    # FastAPI의 CORSMiddleware가 적용되어 있는지 확인하기 위한 기본 테스트
    assert response.status_code in [200, 405]  # OPTIONS가 허용되거나 메서드 미지원

class TestHealthManagementIntegration:
    """보건관리 시스템 통합 테스트"""
    
    def test_system_ready(self, client):
        """시스템 준비 상태 테스트"""
        # 헬스체크가 성공하면 시스템이 준비된 것으로 간주
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["components"]["api"] == "running"
        assert data["components"]["database"] == "connected"
        assert data["components"]["frontend"] == "active"
    
    def test_api_endpoints_available(self, client):
        """주요 API 엔드포인트 가용성 테스트"""
        endpoints = [
            "/health",
            "/",
            "/api/v1/dashboard"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 200, f"엔드포인트 {endpoint} 실패"
    
    def test_data_consistency(self, client):
        """데이터 일관성 테스트"""
        response = client.get("/api/v1/dashboard")
        data = response.json()
        
        # 근로자 수 일관성 확인
        workers = data["workers"]
        total_workers = workers["total"]
        active_workers = workers["active"]
        on_leave = workers["on_leave"]
        
        # 논리적 일관성 확인
        assert active_workers + on_leave <= total_workers
        assert active_workers >= 0
        assert on_leave >= 0
        assert total_workers >= 0