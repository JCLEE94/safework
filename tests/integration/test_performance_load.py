"""
성능 및 부하 통합 테스트
Performance and Load Integration Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json
import time
import concurrent.futures
import statistics

from src.app import create_app


class TestPerformanceLoad:
    """시스템 성능 및 부하 처리 능력 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def load_test_config(self):
        """부하 테스트 설정"""
        return {
            "scenarios": {
                "normal_load": {
                    "users": 100,
                    "duration_seconds": 300,
                    "ramp_up_seconds": 60
                },
                "peak_load": {
                    "users": 500,
                    "duration_seconds": 600,
                    "ramp_up_seconds": 120
                },
                "stress_test": {
                    "users": 1000,
                    "duration_seconds": 900,
                    "ramp_up_seconds": 180
                }
            },
            "endpoints": [
                {"path": "/api/v1/workers/", "method": "GET", "weight": 30},
                {"path": "/api/v1/health-exams/", "method": "GET", "weight": 20},
                {"path": "/api/v1/dashboard/", "method": "GET", "weight": 25},
                {"path": "/api/v1/workers/", "method": "POST", "weight": 15},
                {"path": "/api/v1/documents/generate-pdf", "method": "POST", "weight": 10}
            ],
            "think_time": {
                "min_seconds": 1,
                "max_seconds": 5
            }
        }
    
    async def test_api_response_time_benchmarks(self, test_client):
        """API 응답 시간 벤치마크 테스트"""
        
        benchmarks = {
            "GET /api/v1/workers/": {"target_ms": 100, "percentile_95": 200},
            "GET /api/v1/health-exams/": {"target_ms": 150, "percentile_95": 300},
            "POST /api/v1/workers/": {"target_ms": 200, "percentile_95": 400},
            "GET /api/v1/dashboard/": {"target_ms": 500, "percentile_95": 1000},
            "POST /api/v1/documents/generate-pdf": {"target_ms": 2000, "percentile_95": 5000}
        }
        
        results = {}
        
        for endpoint, benchmark in benchmarks.items():
            method, path = endpoint.split(" ")
            response_times = []
            
            # 100회 반복 측정
            for _ in range(100):
                start_time = time.time()
                
                if method == "GET":
                    response = test_client.get(path)
                elif method == "POST":
                    if "workers" in path:
                        data = {
                            "name": f"테스트_{time.time()}",
                            "employee_id": f"EMP{int(time.time())}",
                            "department": "테스트팀"
                        }
                    elif "generate-pdf" in path:
                        data = {
                            "form_type": "health_checkup_report",
                            "data_source": {"worker_id": 1}
                        }
                    else:
                        data = {}
                    
                    response = test_client.post(path, json=data)
                
                end_time = time.time()
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                
                # 응답 상태 확인
                assert response.status_code in [200, 201, 404]
            
            # 통계 계산
            avg_time = statistics.mean(response_times)
            percentile_95 = sorted(response_times)[int(len(response_times) * 0.95)]
            max_time = max(response_times)
            min_time = min(response_times)
            
            results[endpoint] = {
                "average_ms": round(avg_time, 2),
                "percentile_95_ms": round(percentile_95, 2),
                "max_ms": round(max_time, 2),
                "min_ms": round(min_time, 2),
                "meets_target": avg_time <= benchmark["target_ms"],
                "meets_percentile_95": percentile_95 <= benchmark["percentile_95"]
            }
            
            # 벤치마크 검증
            assert avg_time <= benchmark["target_ms"] * 1.2, \
                f"{endpoint} 평균 응답 시간이 목표치를 20% 이상 초과: {avg_time}ms > {benchmark['target_ms']}ms"
        
        return results
    
    async def test_concurrent_user_simulation(self, test_client):
        """동시 사용자 시뮬레이션 테스트"""
        
        async def simulate_user_session(user_id, duration_seconds):
            """단일 사용자 세션 시뮬레이션"""
            session_results = {
                "user_id": user_id,
                "requests": 0,
                "errors": 0,
                "total_response_time": 0
            }
            
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                # 랜덤 액션 선택
                actions = [
                    ("GET", "/api/v1/workers/", None),
                    ("GET", "/api/v1/health-exams/", None),
                    ("GET", "/api/v1/dashboard/", None),
                    ("POST", "/api/v1/workers/search", {"query": "김"}),
                ]
                
                method, path, data = actions[int(time.time()) % len(actions)]
                
                try:
                    request_start = time.time()
                    
                    if method == "GET":
                        response = test_client.get(path)
                    else:
                        response = test_client.post(path, json=data)
                    
                    request_time = time.time() - request_start
                    session_results["requests"] += 1
                    session_results["total_response_time"] += request_time
                    
                    if response.status_code >= 400:
                        session_results["errors"] += 1
                    
                except Exception:
                    session_results["errors"] += 1
                
                # Think time
                await asyncio.sleep(1)
            
            return session_results
        
        # 동시 사용자 수 단계별 테스트
        concurrent_users_tests = [10, 50, 100, 200]
        test_results = {}
        
        for num_users in concurrent_users_tests:
            print(f"\n동시 사용자 {num_users}명 테스트 시작...")
            
            # 비동기 태스크 생성
            tasks = []
            for i in range(num_users):
                task = simulate_user_session(f"user_{i}", duration_seconds=30)
                tasks.append(task)
            
            # 모든 사용자 세션 실행
            start_time = time.time()
            user_results = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            # 결과 집계
            total_requests = sum(r["requests"] for r in user_results)
            total_errors = sum(r["errors"] for r in user_results)
            avg_response_time = sum(r["total_response_time"] for r in user_results) / total_requests
            
            test_results[num_users] = {
                "total_requests": total_requests,
                "requests_per_second": total_requests / total_time,
                "error_rate": (total_errors / total_requests) * 100 if total_requests > 0 else 0,
                "avg_response_time": avg_response_time,
                "total_time": total_time
            }
            
            # 성능 기준 검증
            assert test_results[num_users]["error_rate"] < 5, \
                f"에러율이 5%를 초과: {test_results[num_users]['error_rate']}%"
            assert test_results[num_users]["avg_response_time"] < 2, \
                f"평균 응답 시간이 2초를 초과: {test_results[num_users]['avg_response_time']}초"
        
        return test_results
    
    async def test_database_connection_pooling(self, test_client):
        """데이터베이스 연결 풀링 성능 테스트"""
        
        # 1. 연결 풀 설정 확인
        response = test_client.get("/api/v1/system/database/pool-status")
        assert response.status_code == 200
        
        pool_status = response.json()
        assert "max_connections" in pool_status
        assert "active_connections" in pool_status
        assert "idle_connections" in pool_status
        
        # 2. 동시 데이터베이스 작업 테스트
        async def db_intensive_operation(operation_id):
            """데이터베이스 집약적 작업"""
            # 복잡한 쿼리 시뮬레이션
            response = test_client.post("/api/v1/reports/complex-analysis", json={
                "report_type": "comprehensive_health_analysis",
                "date_range": {
                    "start": "2024-01-01",
                    "end": "2024-12-31"
                },
                "aggregations": ["by_department", "by_age_group", "by_health_status"],
                "include_trends": True
            })
            return response.status_code, response.elapsed
        
        # 50개의 동시 데이터베이스 작업
        tasks = []
        for i in range(50):
            task = db_intensive_operation(i)
            tasks.append(task)
        
        start_time = time.time()
        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_time = time.time() - start_time
        
        # 결과 분석
        successful_ops = sum(1 for r in results if isinstance(r, tuple) and r[0] == 200)
        failed_ops = len(results) - successful_ops
        
        assert successful_ops >= 45, f"성공한 작업이 너무 적음: {successful_ops}/50"
        assert total_time < 30, f"전체 처리 시간이 너무 김: {total_time}초"
        
        # 3. 연결 풀 고갈 테스트
        response = test_client.post("/api/v1/system/database/stress-test", json={
            "concurrent_queries": 100,
            "query_duration_ms": 1000,
            "test_duration_seconds": 10
        })
        assert response.status_code == 200
        
        stress_results = response.json()
        assert stress_results["connection_timeouts"] < 5
        assert stress_results["average_wait_time_ms"] < 100
    
    async def test_cache_performance_optimization(self, test_client):
        """캐시 성능 최적화 테스트"""
        
        # 1. 캐시 히트율 측정
        cache_test_endpoints = [
            "/api/v1/workers/",
            "/api/v1/dashboard/stats",
            "/api/v1/chemical-substances/",
            "/api/v1/health-exams/statistics"
        ]
        
        cache_results = {}
        
        for endpoint in cache_test_endpoints:
            # 캐시 클리어
            test_client.post("/api/v1/system/cache/clear", json={"pattern": endpoint})
            
            # 첫 번째 요청 (캐시 미스)
            start_time = time.time()
            response1 = test_client.get(endpoint)
            first_request_time = time.time() - start_time
            
            # 두 번째 요청 (캐시 히트)
            start_time = time.time()
            response2 = test_client.get(endpoint)
            cached_request_time = time.time() - start_time
            
            # 캐시 효율성 계산
            cache_speedup = first_request_time / cached_request_time if cached_request_time > 0 else 0
            
            cache_results[endpoint] = {
                "first_request_ms": first_request_time * 1000,
                "cached_request_ms": cached_request_time * 1000,
                "speedup_factor": cache_speedup,
                "cache_hit": response2.headers.get("X-Cache") == "HIT"
            }
            
            # 캐시 성능 검증
            assert cache_speedup > 5, f"{endpoint}의 캐시 속도 향상이 부족: {cache_speedup}x"
        
        # 2. 캐시 무효화 전략 테스트
        invalidation_test = {
            "entity": "worker",
            "operation": "update",
            "affected_cache_keys": [
                "workers:list",
                "workers:1",
                "dashboard:worker_stats"
            ]
        }
        
        response = test_client.post("/api/v1/system/cache/test-invalidation", json=invalidation_test)
        assert response.status_code == 200
        
        invalidation_results = response.json()
        assert all(invalidation_results["invalidated"])
        
        # 3. 분산 캐시 동기화 테스트
        response = test_client.post("/api/v1/system/cache/distributed-sync-test", json={
            "nodes": 3,
            "operations": 1000,
            "sync_delay_ms": 10
        })
        assert response.status_code == 200
        
        sync_results = response.json()
        assert sync_results["consistency_rate"] > 99.9
        assert sync_results["average_sync_time_ms"] < 50
        
        return cache_results
    
    async def test_file_upload_performance(self, test_client):
        """파일 업로드 성능 테스트"""
        
        file_sizes = [
            {"size_mb": 1, "type": "image", "count": 10},
            {"size_mb": 10, "type": "document", "count": 5},
            {"size_mb": 50, "type": "video", "count": 2},
            {"size_mb": 100, "type": "archive", "count": 1}
        ]
        
        upload_results = {}
        
        for file_config in file_sizes:
            size_mb = file_config["size_mb"]
            file_type = file_config["type"]
            count = file_config["count"]
            
            # 테스트 파일 생성 (실제로는 메모리에서)
            file_content = b"0" * (size_mb * 1024 * 1024)
            
            upload_times = []
            
            for i in range(count):
                files = {
                    "file": (f"test_{size_mb}mb_{i}.bin", file_content, "application/octet-stream")
                }
                
                start_time = time.time()
                response = test_client.post(
                    "/api/v1/files/upload",
                    files=files,
                    data={"category": file_type}
                )
                upload_time = time.time() - start_time
                
                assert response.status_code == 201
                upload_times.append(upload_time)
            
            # 통계 계산
            avg_time = statistics.mean(upload_times)
            throughput_mbps = (size_mb * 8) / avg_time  # Mbps
            
            upload_results[f"{size_mb}MB_{file_type}"] = {
                "average_time_seconds": avg_time,
                "throughput_mbps": throughput_mbps,
                "total_files": count
            }
            
            # 성능 기준 검증 (최소 10Mbps)
            assert throughput_mbps > 10, f"업로드 속도가 너무 느림: {throughput_mbps}Mbps"
        
        return upload_results
    
    async def test_memory_leak_detection(self, test_client):
        """메모리 누수 감지 테스트"""
        
        # 1. 초기 메모리 상태 확인
        response = test_client.get("/api/v1/system/memory/status")
        assert response.status_code == 200
        
        initial_memory = response.json()
        initial_usage_mb = initial_memory["used_mb"]
        
        # 2. 반복적인 작업 수행
        iterations = 1000
        leak_suspicious_operations = [
            {
                "endpoint": "/api/v1/workers/bulk-import",
                "data": {"workers": [{"name": f"Worker{i}", "employee_id": f"EMP{i}"} for i in range(100)]}
            },
            {
                "endpoint": "/api/v1/documents/generate-pdf",
                "data": {"form_type": "batch_report", "worker_ids": list(range(1, 51))}
            },
            {
                "endpoint": "/api/v1/reports/complex-analysis",
                "data": {"include_all_data": True, "format": "memory"}
            }
        ]
        
        memory_samples = []
        
        for i in range(iterations):
            # 작업 수행
            operation = leak_suspicious_operations[i % len(leak_suspicious_operations)]
            response = test_client.post(operation["endpoint"], json=operation["data"])
            
            # 주기적으로 메모리 체크 (100회마다)
            if i % 100 == 0:
                response = test_client.get("/api/v1/system/memory/status")
                current_memory = response.json()
                memory_samples.append(current_memory["used_mb"])
                
                # 가비지 컬렉션 강제 실행
                test_client.post("/api/v1/system/gc/collect")
        
        # 3. 메모리 증가 추세 분석
        memory_growth_rate = (memory_samples[-1] - memory_samples[0]) / len(memory_samples)
        
        # 메모리 누수 기준: 샘플당 1MB 이상 증가
        assert memory_growth_rate < 1, f"메모리 누수 의심: 샘플당 {memory_growth_rate}MB 증가"
        
        # 4. 최종 메모리 상태
        response = test_client.get("/api/v1/system/memory/status")
        final_memory = response.json()
        total_increase = final_memory["used_mb"] - initial_usage_mb
        
        # 전체 증가량이 초기 사용량의 50% 미만이어야 함
        assert total_increase < initial_usage_mb * 0.5, \
            f"메모리 사용량이 과도하게 증가: {total_increase}MB"
        
        return {
            "initial_memory_mb": initial_usage_mb,
            "final_memory_mb": final_memory["used_mb"],
            "total_increase_mb": total_increase,
            "growth_rate_per_sample": memory_growth_rate,
            "samples": memory_samples
        }
    
    async def test_api_rate_limiting(self, test_client):
        """API 속도 제한 테스트"""
        
        # 1. 속도 제한 설정 확인
        response = test_client.get("/api/v1/system/rate-limits")
        assert response.status_code == 200
        
        rate_limits = response.json()
        default_limit = rate_limits["default"]["requests_per_minute"]
        
        # 2. 제한 초과 테스트
        endpoint = "/api/v1/workers/"
        requests_made = 0
        rate_limited = False
        
        start_time = time.time()
        while time.time() - start_time < 60 and not rate_limited:
            response = test_client.get(endpoint)
            requests_made += 1
            
            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                rate_limit_headers = {
                    "limit": response.headers.get("X-RateLimit-Limit"),
                    "remaining": response.headers.get("X-RateLimit-Remaining"),
                    "reset": response.headers.get("X-RateLimit-Reset")
                }
        
        assert rate_limited, "속도 제한이 작동하지 않음"
        assert requests_made <= default_limit + 10, \
            f"속도 제한이 너무 느슨함: {requests_made} > {default_limit}"
        
        # 3. 버스트 처리 테스트
        burst_test_results = []
        
        # 10초 대기 후 버스트 요청
        await asyncio.sleep(10)
        
        burst_size = 50
        burst_start = time.time()
        
        for _ in range(burst_size):
            response = test_client.get(endpoint)
            burst_test_results.append({
                "status": response.status_code,
                "time": time.time() - burst_start
            })
        
        # 버스트 분석
        successful_in_burst = sum(1 for r in burst_test_results if r["status"] == 200)
        
        # 토큰 버킷 알고리즘 검증
        assert successful_in_burst >= 10, \
            f"버스트 처리가 너무 제한적: {successful_in_burst}/50"
        
        return {
            "default_limit": default_limit,
            "requests_before_limit": requests_made,
            "burst_success_rate": successful_in_burst / burst_size * 100,
            "rate_limit_headers": rate_limit_headers
        }


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import sys
    import subprocess
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 성능 및 부하 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 성능 및 부하 통합 테스트 실패")
        sys.exit(1)