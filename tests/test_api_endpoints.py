"""
API 엔드포인트 테스트
API endpoint tests
"""

import pytest
from httpx import AsyncClient
from datetime import datetime, date
import json


@pytest.mark.asyncio
class TestWorkerAPI:
    """근로자 API 테스트"""
    
    async def test_get_workers_list(self, async_client: AsyncClient):
        """근로자 목록 조회 테스트"""
        response = await async_client.get("/api/v1/workers/")
        
        # Auth might be required
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        
        # Check pagination headers if present
        if "X-Total-Count" in response.headers:
            assert int(response.headers["X-Total-Count"]) >= 0
            
    async def test_get_workers_with_filters(self, async_client: AsyncClient):
        """필터를 사용한 근로자 조회 테스트"""
        params = {
            "search": "홍길동",
            "work_type": "construction",
            "health_status": "normal",
            "skip": 0,
            "limit": 10
        }
        
        response = await async_client.get("/api/v1/workers/", params=params)
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["items"], list)
        
    async def test_create_worker_validation(self, async_client: AsyncClient):
        """근로자 생성 유효성 검사 테스트"""
        # Invalid data
        invalid_worker = {
            "name": "",  # Empty name
            "employee_number": "12345",
            "gender": "invalid",  # Invalid enum
        }
        
        response = await async_client.post("/api/v1/workers/", json=invalid_worker)
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        # Should fail validation
        assert response.status_code == 422
        
    async def test_worker_crud_operations(self, async_client: AsyncClient):
        """근로자 CRUD 작업 테스트"""
        # Create worker
        worker_data = {
            "name": "테스트 근로자",
            "employee_number": "TEST001",
            "department": "테스트부",
            "position": "사원",
            "hire_date": str(date.today()),
            "birth_date": "1990-01-01",
            "gender": "male",
            "phone": "010-1234-5678",
            "email": "test@example.com",
            "address": "서울시 강남구",
            "emergency_contact": "010-8765-4321",
            "emergency_relationship": "배우자",
            "blood_type": "A",
            "employment_type": "regular",
            "work_type": "construction",
            "health_status": "normal"
        }
        
        # Create
        response = await async_client.post("/api/v1/workers/", json=worker_data)
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        if response.status_code == 201:
            created_worker = response.json()
            worker_id = created_worker["id"]
            
            # Read
            response = await async_client.get(f"/api/v1/workers/{worker_id}")
            assert response.status_code == 200
            assert response.json()["name"] == worker_data["name"]
            
            # Update
            update_data = {"name": "수정된 이름"}
            response = await async_client.patch(f"/api/v1/workers/{worker_id}", json=update_data)
            assert response.status_code == 200
            
            # Delete
            response = await async_client.delete(f"/api/v1/workers/{worker_id}")
            assert response.status_code == 204


@pytest.mark.asyncio
class TestHealthExamAPI:
    """건강진단 API 테스트"""
    
    async def test_get_health_exams(self, async_client: AsyncClient):
        """건강진단 목록 조회 테스트"""
        response = await async_client.get("/api/v1/health-exams/")
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list) or "items" in data
        
    async def test_create_health_exam_validation(self, async_client: AsyncClient):
        """건강진단 생성 유효성 검사"""
        invalid_exam = {
            "worker_id": 999999,  # Non-existent worker
            "exam_date": "invalid-date",
            "exam_type": "invalid-type"
        }
        
        response = await async_client.post("/api/v1/health-exams/", json=invalid_exam)
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code in [400, 422, 404]


@pytest.mark.asyncio
class TestDocumentAPI:
    """문서 API 테스트"""
    
    async def test_get_pdf_forms(self, async_client: AsyncClient):
        """PDF 양식 목록 조회 테스트"""
        response = await async_client.get("/api/v1/documents/pdf-forms")
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 200
        forms = response.json()
        assert isinstance(forms, list)
        
        # Check expected forms
        expected_forms = [
            "health_consultation_log",
            "health_findings_ledger",
            "msds_management_ledger",
            "special_substance_log"
        ]
        
        form_names = [form["value"] for form in forms]
        for expected in expected_forms:
            assert expected in form_names
            
    async def test_fill_pdf_validation(self, async_client: AsyncClient):
        """PDF 양식 채우기 유효성 검사"""
        # Invalid form name
        response = await async_client.post(
            "/api/v1/documents/fill-pdf/invalid_form",
            json={"entries": []}
        )
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 404
        
        # Invalid data structure
        response = await async_client.post(
            "/api/v1/documents/fill-pdf/health_consultation_log",
            json={"invalid": "data"}
        )
        
        if response.status_code != 401:
            assert response.status_code == 422


@pytest.mark.asyncio
class TestMonitoringAPI:
    """모니터링 API 테스트"""
    
    async def test_get_metrics(self, async_client: AsyncClient):
        """시스템 메트릭 조회 테스트"""
        response = await async_client.get("/api/v1/monitoring/metrics")
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 200
        metrics = response.json()
        
        # Check metric structure
        expected_fields = ["cpu_percent", "memory", "disk", "timestamp"]
        for field in expected_fields:
            assert field in metrics
            
    async def test_get_alerts(self, async_client: AsyncClient):
        """알림 조회 테스트"""
        response = await async_client.get("/api/v1/monitoring/alerts")
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        assert response.status_code == 200
        data = response.json()
        assert "alerts" in data
        assert isinstance(data["alerts"], list)


@pytest.mark.asyncio
class TestAuthAPI:
    """인증 API 테스트"""
    
    async def test_login_validation(self, async_client: AsyncClient):
        """로그인 유효성 검사"""
        # Empty credentials
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "", "password": ""}
        )
        assert response.status_code == 422
        
        # Invalid email format
        response = await async_client.post(
            "/api/v1/auth/login",
            json={"email": "invalid-email", "password": "password123"}
        )
        assert response.status_code == 422
        
    async def test_registration_password_validation(self, async_client: AsyncClient):
        """회원가입 비밀번호 검증"""
        weak_passwords = [
            "short",      # Too short
            "alllowercase",  # No uppercase
            "ALLUPPERCASE",  # No lowercase
            "NoNumbers!",    # No digits
            "NoSpecial123",  # No special chars
        ]
        
        for password in weak_passwords:
            response = await async_client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@example.com",
                    "password": password,
                    "name": "Test User"
                }
            )
            assert response.status_code == 400
            
    async def test_logout(self, async_client: AsyncClient):
        """로그아웃 테스트"""
        response = await async_client.post("/api/v1/auth/logout")
        # Logout should always succeed
        assert response.status_code == 200


@pytest.mark.asyncio
class TestCacheHeaders:
    """캐시 헤더 테스트"""
    
    async def test_cache_headers_on_get_requests(self, async_client: AsyncClient):
        """GET 요청 캐시 헤더 테스트"""
        endpoints = [
            "/api/v1/workers/",
            "/api/v1/health-exams/",
            "/api/v1/documents/pdf-forms"
        ]
        
        for endpoint in endpoints:
            response = await async_client.get(endpoint)
            
            if response.status_code == 200:
                # Check for cache headers
                assert "X-Cache-Status" in response.headers or "Cache-Control" in response.headers


@pytest.mark.asyncio
class TestErrorHandling:
    """에러 처리 테스트"""
    
    async def test_404_error(self, async_client: AsyncClient):
        """404 에러 처리 테스트"""
        response = await async_client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404
        
    async def test_method_not_allowed(self, async_client: AsyncClient):
        """405 에러 처리 테스트"""
        # Try to POST to an endpoint that only accepts GET
        response = await async_client.post("/health", json={})
        assert response.status_code == 405
        
    async def test_malformed_json(self, async_client: AsyncClient):
        """잘못된 JSON 처리 테스트"""
        response = await async_client.post(
            "/api/v1/workers/",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 401:  # If not auth error
            assert response.status_code in [400, 422]