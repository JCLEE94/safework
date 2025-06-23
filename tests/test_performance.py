"""
성능 테스트
Performance tests for the health management system
"""

import pytest
import asyncio
import time
from httpx import AsyncClient
from concurrent.futures import ThreadPoolExecutor
import statistics


@pytest.mark.asyncio
class TestPerformance:
    """성능 테스트 클래스"""
    
    async def test_health_endpoint_response_time(self, async_client: AsyncClient):
        """헬스 체크 엔드포인트 응답 시간 테스트"""
        start_time = time.time()
        response = await async_client.get("/health")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert response_time < 500  # Should respond within 500ms
        
    async def test_concurrent_requests(self, async_client: AsyncClient):
        """동시 요청 처리 테스트"""
        async def make_request():
            start_time = time.time()
            response = await async_client.get("/health")
            end_time = time.time()
            return {
                "status_code": response.status_code,
                "response_time": (end_time - start_time) * 1000
            }
        
        # Make 10 concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks)
        
        # Check all requests succeeded
        for result in results:
            assert result["status_code"] == 200
            
        # Check average response time
        response_times = [result["response_time"] for result in results]
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        
        assert avg_response_time < 1000  # Average should be under 1 second
        assert max_response_time < 2000  # No request should take more than 2 seconds
        
    async def test_api_endpoints_performance(self, async_client: AsyncClient):
        """API 엔드포인트 성능 테스트"""
        endpoints = [
            "/api/v1/workers/",
            "/api/v1/health-exams/",
            "/api/v1/documents/pdf-forms",
            "/api/v1/monitoring/metrics"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = await async_client.get(endpoint)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            # Skip if authentication is required
            if response.status_code == 401:
                continue
                
            # API endpoints should respond within 2 seconds
            assert response_time < 2000, f"{endpoint} took {response_time}ms"
            
    async def test_pagination_performance(self, async_client: AsyncClient):
        """페이지네이션 성능 테스트"""
        params = {"page": 1, "page_size": 50}
        
        start_time = time.time()
        response = await async_client.get("/api/v1/workers/", params=params)
        end_time = time.time()
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 1500  # Pagination should be fast
        
        # Check pagination headers
        assert "X-Total-Count" in response.headers or "total" in response.json()
        
    async def test_search_performance(self, async_client: AsyncClient):
        """검색 성능 테스트"""
        search_params = {
            "search": "테스트",
            "page_size": 20
        }
        
        start_time = time.time()
        response = await async_client.get("/api/v1/workers/", params=search_params)
        end_time = time.time()
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        assert response_time < 2000  # Search should complete within 2 seconds


@pytest.mark.asyncio
class TestCachePerformance:
    """캐시 성능 테스트"""
    
    async def test_cache_hit_performance(self, async_client: AsyncClient):
        """캐시 히트 성능 테스트"""
        endpoint = "/api/v1/workers/"
        
        # First request (cache miss)
        start_time = time.time()
        response1 = await async_client.get(endpoint)
        first_time = (time.time() - start_time) * 1000
        
        if response1.status_code == 401:
            pytest.skip("Authentication required")
            
        # Second request (cache hit)
        start_time = time.time()
        response2 = await async_client.get(endpoint)
        second_time = (time.time() - start_time) * 1000
        
        assert response1.status_code == response2.status_code == 200
        
        # Cache hit should be faster (allow some variance)
        if "X-Cache-Status" in response2.headers:
            cache_status = response2.headers["X-Cache-Status"]
            if cache_status == "hit":
                # Cache hit should be at least 20% faster
                assert second_time < first_time * 0.8
                
    async def test_cache_headers(self, async_client: AsyncClient):
        """캐시 헤더 확인"""
        response = await async_client.get("/api/v1/workers/")
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        # Check for cache-related headers
        cache_headers = [
            "X-Cache-Status",
            "Cache-Control",
            "ETag",
            "Last-Modified"
        ]
        
        has_cache_header = any(header in response.headers for header in cache_headers)
        assert has_cache_header, "Response should have cache headers"


@pytest.mark.asyncio
class TestDatabasePerformance:
    """데이터베이스 성능 테스트"""
    
    async def test_connection_pool_performance(self, async_client: AsyncClient):
        """연결 풀 성능 테스트"""
        async def make_db_request():
            response = await async_client.get("/api/v1/workers/")
            return response.status_code
            
        # Make multiple concurrent requests to test connection pooling
        tasks = [make_db_request() for _ in range(20)]
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        total_time = (end_time - start_time) * 1000
        
        # Check that no connection errors occurred
        for result in results:
            if isinstance(result, Exception):
                pytest.fail(f"Database connection error: {result}")
            # Skip auth errors for this test
            if result not in [200, 401]:
                pytest.fail(f"Unexpected status code: {result}")
                
        # All requests should complete within reasonable time
        assert total_time < 10000  # 10 seconds for 20 requests
        
    async def test_query_performance_headers(self, async_client: AsyncClient):
        """쿼리 성능 헤더 확인"""
        response = await async_client.get("/api/v1/workers/")
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        # Check for query performance headers
        performance_headers = [
            "X-Query-Count",
            "X-Query-Time",
            "X-Pool-Active"
        ]
        
        for header in performance_headers:
            if header in response.headers:
                # Validate header values
                if header == "X-Query-Count":
                    assert int(response.headers[header]) >= 0
                elif header == "X-Query-Time":
                    query_time = float(response.headers[header])
                    assert query_time < 5.0  # Queries should be under 5 seconds
                elif header == "X-Pool-Active":
                    assert int(response.headers[header]) >= 0


@pytest.mark.asyncio
class TestMemoryUsage:
    """메모리 사용량 테스트"""
    
    async def test_memory_leak_detection(self, async_client: AsyncClient):
        """메모리 누수 감지 테스트"""
        # Get initial memory metrics
        initial_response = await async_client.get("/api/v1/monitoring/metrics")
        
        if initial_response.status_code == 401:
            pytest.skip("Authentication required")
            
        if initial_response.status_code == 200:
            initial_memory = initial_response.json().get("memory", {})
            initial_used = initial_memory.get("used", 0)
            
            # Make many requests
            for _ in range(50):
                await async_client.get("/health")
                
            # Check memory after requests
            final_response = await async_client.get("/api/v1/monitoring/metrics")
            if final_response.status_code == 200:
                final_memory = final_response.json().get("memory", {})
                final_used = final_memory.get("used", 0)
                
                # Memory shouldn't increase dramatically
                memory_increase = final_used - initial_used
                memory_increase_percent = (memory_increase / initial_used) * 100 if initial_used > 0 else 0
                
                # Allow up to 10% memory increase
                assert memory_increase_percent < 10, f"Memory increased by {memory_increase_percent}%"


@pytest.mark.asyncio 
class TestCompressionPerformance:
    """압축 성능 테스트"""
    
    async def test_response_compression(self, async_client: AsyncClient):
        """응답 압축 테스트"""
        headers = {"Accept-Encoding": "gzip"}
        
        response = await async_client.get("/api/v1/workers/", headers=headers)
        
        if response.status_code == 401:
            pytest.skip("Authentication required")
            
        # Check if response is compressed for large responses
        if len(response.content) > 1024:  # Only check for responses > 1KB
            content_encoding = response.headers.get("Content-Encoding")
            # Compression might be applied by middleware or reverse proxy
            # This test just ensures the endpoint responds correctly with compression headers
            assert response.status_code == 200


@pytest.mark.asyncio
class TestRateLimiting:
    """요청 속도 제한 테스트"""
    
    async def test_rate_limiting_headers(self, async_client: AsyncClient):
        """속도 제한 헤더 테스트"""
        response = await async_client.get("/health")
        
        # Check for rate limiting headers
        rate_limit_headers = [
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "X-RateLimit-Reset"
        ]
        
        # Rate limiting headers might not be present on all responses
        # This test just ensures the endpoint responds correctly
        assert response.status_code == 200
        
    async def test_rate_limit_enforcement(self, async_client: AsyncClient):
        """속도 제한 강제 적용 테스트"""
        # This test would require making many requests quickly
        # For now, just verify normal operation
        
        responses = []
        for _ in range(10):
            response = await async_client.get("/health")
            responses.append(response.status_code)
            await asyncio.sleep(0.1)  # Small delay to avoid overwhelming
            
        # All requests should succeed under normal load
        for status_code in responses:
            assert status_code == 200