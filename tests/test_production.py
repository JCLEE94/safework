"""
운영서버 통합 테스트
Production server integration tests
"""
import pytest
import httpx
import json

import os

PRODUCTION_URL = os.getenv("PRODUCTION_URL", "http://soonmin.jclee.me")

class TestProductionServer:
    """운영서버 통합 테스트"""
    
    async def test_health_check(self):
        """헬스체크 테스트"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCTION_URL}/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "건설업 보건관리 시스템" in data["service"]
    
    async def test_api_documentation_access(self):
        """API 문서 접근 테스트"""
        async with httpx.AsyncClient() as client:
            # OpenAPI JSON
            response = await client.get(f"{PRODUCTION_URL}/openapi.json")
            assert response.status_code == 200
            assert "openapi" in response.json()
    
    async def test_pdf_forms_list(self):
        """PDF 양식 목록 조회"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{PRODUCTION_URL}/api/v1/documents/pdf-forms")
            assert response.status_code == 200
            data = response.json()
            assert "forms" in data
            assert len(data["forms"]) == 4
            
            # 양식 이름 확인
            form_ids = [form["id"] for form in data["forms"]]
            assert "유소견자_관리대장" in form_ids
            assert "MSDS_관리대장" in form_ids
            assert "건강관리_상담방문_일지" in form_ids
            assert "특별관리물질_취급일지" in form_ids
    
    async def test_worker_api_endpoints(self):
        """근로자 관리 API 엔드포인트"""
        async with httpx.AsyncClient() as client:
            # 근로자 목록 조회
            response = await client.get(f"{PRODUCTION_URL}/api/v1/workers/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert isinstance(data["total"], int)
    
    async def test_all_module_endpoints(self):
        """모든 모듈 엔드포인트 테스트"""
        endpoints = [
            "/api/v1/health-exams/",
            "/api/v1/work-environments/",
            "/api/v1/chemical-substances/",
            "/api/v1/health-education/",
            "/api/v1/accident-reports/"
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                response = await client.get(f"{PRODUCTION_URL}{endpoint}")
                assert response.status_code == 200
                data = response.json()
                assert "items" in data
                assert "total" in data
                print(f"✅ {endpoint}: total={data['total']}")
    
    async def test_pdf_generation_api(self):
        """PDF 생성 API 테스트"""
        async with httpx.AsyncClient() as client:
            # PDF 테스트 엔드포인트
            response = await client.post(f"{PRODUCTION_URL}/api/v1/documents/test-pdf")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            assert data["document_api"] == "enabled"
    
    async def test_cors_configuration(self):
        """CORS 설정 테스트"""
        async with httpx.AsyncClient() as client:
            response = await client.options(
                f"{PRODUCTION_URL}/api/v1/workers/",
                headers={
                    "Origin": os.getenv("FRONTEND_URL", "http://localhost:3000"),
                    "Access-Control-Request-Method": "GET"
                }
            )
            assert response.status_code == 200
            headers = response.headers
            assert headers.get("access-control-allow-origin") == "*"
            assert "GET" in headers.get("access-control-allow-methods", "")
    
    async def test_static_file_serving(self):
        """정적 파일 서빙 테스트"""
        async with httpx.AsyncClient() as client:
            # 메인 페이지 접근
            response = await client.get(PRODUCTION_URL)
            assert response.status_code == 200
            # React 앱이 정상적으로 로드되는지 확인
            assert response.headers.get("content-type", "").startswith("text/html")
    
    async def test_api_response_times(self):
        """API 응답 시간 테스트"""
        import time
        
        endpoints = [
            "/health",
            "/api/v1/workers/",
            "/api/v1/documents/pdf-forms"
        ]
        
        async with httpx.AsyncClient() as client:
            for endpoint in endpoints:
                start_time = time.time()
                response = await client.get(f"{PRODUCTION_URL}{endpoint}")
                elapsed_time = time.time() - start_time
                
                assert response.status_code == 200
                assert elapsed_time < 2.0  # 2초 이내 응답
                print(f"⚡ {endpoint}: {elapsed_time:.3f}초")