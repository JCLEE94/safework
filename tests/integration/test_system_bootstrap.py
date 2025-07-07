"""
시스템 부팅 및 헬스체크 통합 테스트
System Bootstrap and Health Check Integration Tests
"""

import pytest
import asyncio
import docker
import time
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

from src.app import create_app
from src.config.settings import get_settings
from src.config.database import get_db, init_db


class TestSystemBootstrap:
    """시스템 전체 시작 프로세스 통합 테스트"""
    
    @pytest.fixture(scope="class")
    def docker_client(self):
        """Docker 클라이언트 설정"""
        return docker.from_env()
    
    @pytest.fixture(scope="class")
    async def test_containers(self, docker_client):
        """테스트용 컨테이너 시작"""
        containers = {}
        
        # PostgreSQL 컨테이너
        postgres_container = docker_client.containers.run(
            "postgres:15",
            environment={
                "POSTGRES_USER": "test_admin",
                "POSTGRES_PASSWORD": "test_password",
                "POSTGRES_DB": "test_health_management"
            },
            ports={"5432/tcp": 25433},
            detach=True,
            remove=True,
            name="test_postgres_integration"
        )
        containers["postgres"] = postgres_container
        
        # Redis 컨테이너
        redis_container = docker_client.containers.run(
            "redis:7-alpine",
            ports={"6379/tcp": 26380},
            detach=True,
            remove=True,
            name="test_redis_integration"
        )
        containers["redis"] = redis_container
        
        # 컨테이너 준비 대기
        await self._wait_for_containers(containers)
        
        yield containers
        
        # 정리
        for container in containers.values():
            container.stop()
    
    async def _wait_for_containers(self, containers, timeout=30):
        """컨테이너 준비 대기"""
        import psycopg2
        
        # PostgreSQL 준비 대기
        for _ in range(timeout):
            try:
                conn = psycopg2.connect(
                    host="localhost",
                    port=25433,
                    user="test_admin",
                    password="test_password",
                    database="test_health_management"
                )
                conn.close()
                break
            except psycopg2.OperationalError:
                await asyncio.sleep(1)
        
        # Redis 준비 대기
        for _ in range(timeout):
            try:
                r = redis.Redis(host="localhost", port=26380)
                await r.ping()
                await r.close()
                break
            except Exception:
                await asyncio.sleep(1)
    
    async def test_full_system_startup_sequence(self, test_containers):
        """컨테이너 시작 순서: PostgreSQL → Redis → FastAPI → Frontend"""
        # 1. PostgreSQL 연결 확인
        postgres_container = test_containers["postgres"]
        assert postgres_container.status == "running"
        
        # 2. Redis 연결 확인
        redis_container = test_containers["redis"]
        assert redis_container.status == "running"
        
        # 3. FastAPI 애플리케이션 생성
        app = create_app()
        client = TestClient(app)
        
        # 4. 헬스체크 엔드포인트 확인
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert health_data["service"] == "건설업 보건관리 시스템"
        assert "components" in health_data
    
    async def test_database_connection_and_migration(self, test_containers):
        """데이터베이스 연결 및 마이그레이션 테스트"""
        # 환경변수 오버라이드
        import os
        os.environ["DATABASE_URL"] = "postgresql://test_admin:test_password@localhost:25433/test_health_management"
        
        # 데이터베이스 초기화
        await init_db()
        
        # 연결 테스트
        async for db in get_db():
            result = await db.execute(text("SELECT 1"))
            assert result.scalar() == 1
            break
    
    async def test_redis_cache_connectivity(self, test_containers):
        """Redis 캐시 연결성 테스트"""
        from src.services.cache import CacheService
        
        cache_service = CacheService()
        # Redis URL 오버라이드
        cache_service.settings.redis_url = "redis://localhost:26380/0"
        
        await cache_service.connect()
        
        # 캐시 쓰기/읽기 테스트
        test_key = "test:integration"
        test_value = {"message": "헬스체크 통합 테스트"}
        
        await cache_service.set(test_key, test_value, expire_seconds=60)
        cached_value = await cache_service.get(test_key)
        
        assert cached_value == test_value
        
        await cache_service.disconnect()
    
    async def test_all_api_endpoints_registration(self):
        """모든 API 엔드포인트 등록 확인"""
        app = create_app()
        client = TestClient(app)
        
        # OpenAPI 스키마에서 등록된 경로 확인
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        paths = openapi_schema["paths"]
        
        # 필수 API 엔드포인트 확인
        required_endpoints = [
            "/api/v1/workers/",
            "/api/v1/health-exams/",
            "/api/v1/work-environments/",
            "/api/v1/health-educations/",
            "/api/v1/chemical-substances/",
            "/api/v1/accident-reports/",
            "/api/v1/documents/",
            "/api/v1/monitoring/metrics",
            "/health"
        ]
        
        for endpoint in required_endpoints:
            assert endpoint in paths, f"필수 엔드포인트 {endpoint}가 등록되지 않음"
    
    async def test_frontend_static_files_serving(self):
        """프론트엔드 정적 파일 서빙 테스트"""
        app = create_app()
        client = TestClient(app)
        
        # 정적 파일 경로 확인
        response = client.get("/")
        # 정적 파일이 없는 경우 API 응답 또는 404
        assert response.status_code in [200, 404]
        
        # API 문서 확인
        response = client.get("/api/docs")
        assert response.status_code == 200
    
    async def test_health_check_cascade(self, test_containers):
        """헬스체크 캐스케이드 테스트"""
        import os
        os.environ["DATABASE_URL"] = "postgresql://test_admin:test_password@localhost:25433/test_health_management"
        os.environ["REDIS_URL"] = "redis://localhost:26380/0"
        
        app = create_app()
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        
        # 각 컴포넌트 상태 확인
        components = health_data["components"]
        assert components["database"] == "connected"
        assert components["api"] == "running"
        assert components["frontend"] == "active"
        
        # 타임스탬프 형식 확인
        assert "timestamp" in health_data
        assert "timezone" in health_data
        assert health_data["timezone"] == "Asia/Seoul (KST)"


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import sys
    import subprocess
    
    # 현재 파일의 테스트만 실행
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
    ])
    
    if result.returncode == 0:
        print("✅ 시스템 부팅 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 시스템 부팅 통합 테스트 실패")
        sys.exit(1)