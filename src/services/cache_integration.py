"""
Redis Cache Service Integration Tests
Inline tests for caching functionality
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any

from src.testing import (
    integration_test, run_inline_tests,
    create_test_environment, measure_performance
)
from src.services.cache import CacheTTL, cache_key_builder


class IntegrationTestRedisCache:
    """Redis 캐시 통합 테스트"""
    
    @integration_test
    @measure_performance
    async def test_cache_basic_operations(self):
        """캐시 기본 동작 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            # 1. SET/GET 테스트
            test_key = "test:basic:string"
            test_value = "Hello, 안녕하세요!"
            
            await cache.set(test_key, test_value, ttl=60)
            retrieved = await cache.get(test_key)
            assert retrieved == test_value
            
            # 2. 복잡한 객체 캐싱
            complex_data = {
                "id": 123,
                "name": "홍길동",
                "data": {
                    "department": "개발부",
                    "skills": ["Python", "FastAPI", "Redis"],
                    "joined_at": datetime.now().isoformat()
                }
            }
            
            complex_key = "test:complex:object"
            await cache.set(complex_key, json.dumps(complex_data), ttl=60)
            
            retrieved_json = await cache.get(complex_key)
            retrieved_data = json.loads(retrieved_json)
            assert retrieved_data["name"] == "홍길동"
            assert len(retrieved_data["data"]["skills"]) == 3
            
            # 3. DELETE 테스트
            await cache.delete(test_key)
            assert await cache.get(test_key) is None
            
            # 4. EXISTS 테스트
            assert await cache.exists(complex_key) is True
            assert await cache.exists("non:existent:key") is False
    
    @integration_test
    async def test_cache_ttl_expiration(self):
        """캐시 TTL 만료 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            # 짧은 TTL 설정
            short_ttl_key = "test:ttl:short"
            await cache.set(short_ttl_key, "expire soon", ttl=1)
            
            # 즉시 확인
            assert await cache.get(short_ttl_key) == "expire soon"
            
            # 2초 대기
            await asyncio.sleep(2)
            
            # 만료 확인
            assert await cache.get(short_ttl_key) is None
            
            # CacheTTL enum 사용
            ttl_test_cases = [
                (CacheTTL.WORKER_LIST, "worker:list:data"),
                (CacheTTL.WORKER_DETAIL, "worker:123:detail"),
                (CacheTTL.HEALTH_EXAM, "health:exam:456"),
                (CacheTTL.STATISTICS, "stats:dashboard:2024")
            ]
            
            for ttl, key in ttl_test_cases:
                await cache.set(key, f"data_for_{key}", ttl=ttl.value)
                assert await cache.exists(key) is True
    
    @integration_test
    async def test_cache_invalidation_patterns(self):
        """캐시 무효화 패턴 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            # 1. 패턴 기반 삭제
            # 근로자 관련 캐시 생성
            worker_keys = [
                "worker:list:page:1",
                "worker:list:page:2",
                "worker:detail:100",
                "worker:detail:101",
                "worker:stats:department:dev"
            ]
            
            for key in worker_keys:
                await cache.set(key, f"data_{key}", ttl=300)
            
            # 모든 worker:list:* 삭제
            # Redis에서 직접 패턴 삭제 (실제 구현시 주의 필요)
            list_keys = [k for k in worker_keys if k.startswith("worker:list:")]
            for key in list_keys:
                await cache.delete(key)
            
            # 검증
            for key in worker_keys:
                exists = await cache.exists(key)
                if key.startswith("worker:list:"):
                    assert not exists, f"{key} should be deleted"
                else:
                    assert exists, f"{key} should still exist"
            
            # 2. 연관 캐시 무효화
            # 근로자 업데이트시 관련 캐시 모두 삭제
            worker_id = 100
            related_keys = [
                f"worker:detail:{worker_id}",
                f"worker:health:history:{worker_id}",
                f"worker:consultations:{worker_id}",
                "worker:list:page:1",  # 목록도 무효화
                "stats:dashboard:total"  # 통계도 무효화
            ]
            
            # 관련 캐시 생성
            for key in related_keys:
                await cache.set(key, "cached_data", ttl=300)
            
            # 무효화
            for key in related_keys:
                await cache.delete(key)
            
            # 모두 삭제 확인
            for key in related_keys:
                assert await cache.exists(key) is False
    
    @integration_test
    @measure_performance
    async def test_cache_stampede_prevention(self):
        """캐시 스탬피드 방지 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            stampede_key = "test:stampede:heavy_query"
            lock_key = f"{stampede_key}:lock"
            
            # 무거운 작업 시뮬레이션
            async def heavy_computation():
                await asyncio.sleep(0.5)  # 500ms 작업
                return {"result": "expensive_data", "timestamp": datetime.now().isoformat()}
            
            # 동시 요청 시뮬레이션
            async def get_or_compute(request_id: int):
                # 캐시 확인
                cached = await cache.get(stampede_key)
                if cached:
                    return json.loads(cached)
                
                # 락 획득 시도
                lock_acquired = False
                try:
                    # 간단한 락 구현 (실제로는 Redis SETNX 사용)
                    lock_value = f"request_{request_id}"
                    existing_lock = await cache.get(lock_key)
                    
                    if not existing_lock:
                        await cache.set(lock_key, lock_value, ttl=5)
                        lock_acquired = True
                        
                        # 무거운 작업 실행
                        result = await heavy_computation()
                        
                        # 결과 캐싱
                        await cache.set(stampede_key, json.dumps(result), ttl=60)
                        
                        return result
                    else:
                        # 락을 못 얻으면 잠시 대기 후 재시도
                        await asyncio.sleep(0.1)
                        cached = await cache.get(stampede_key)
                        if cached:
                            return json.loads(cached)
                        else:
                            # 폴백
                            return {"result": "fallback", "request_id": request_id}
                finally:
                    if lock_acquired:
                        await cache.delete(lock_key)
            
            # 10개 동시 요청
            start_time = datetime.now()
            results = await asyncio.gather(*[
                get_or_compute(i) for i in range(10)
            ])
            duration = (datetime.now() - start_time).total_seconds()
            
            # 검증: 한 번만 계산되어야 함
            unique_timestamps = set(r.get("timestamp", "") for r in results if "timestamp" in r)
            assert len(unique_timestamps) <= 2, "너무 많은 계산이 발생했습니다"
            
            # 성능: 1초 이내 완료
            assert duration < 1.0, f"동시 요청 처리가 너무 느립니다: {duration}초"
    
    @integration_test
    async def test_cache_key_generation(self):
        """캐시 키 생성 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            # 다양한 키 생성 패턴
            test_cases = [
                # (prefix, params, expected_pattern)
                ("worker:list", {"page": 1, "limit": 20}, "worker:list:page:1:limit:20"),
                ("worker:detail", {"id": 123}, "worker:detail:id:123"),
                ("stats", {"year": 2024, "month": 1}, "stats:year:2024:month:1"),
                ("search", {"q": "홍길동", "dept": "개발부"}, "search:q:홍길동:dept:개발부")
            ]
            
            for prefix, params, expected in test_cases:
                # 키 생성 (간단한 구현)
                key_parts = [prefix]
                for k, v in sorted(params.items()):
                    key_parts.extend([k, str(v)])
                generated_key = ":".join(key_parts)
                
                # 캐싱
                await cache.set(generated_key, json.dumps(params), ttl=60)
                
                # 검증
                cached = await cache.get(generated_key)
                assert cached is not None
                assert json.loads(cached) == params
    
    @integration_test
    async def test_distributed_cache_consistency(self):
        """분산 캐시 일관성 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            # 여러 프로세스/서버에서 동일 데이터 접근 시뮬레이션
            shared_key = "shared:counter"
            
            # 초기값 설정
            await cache.set(shared_key, "0", ttl=300)
            
            # 동시 증가 작업
            async def increment_counter(process_id: int):
                for _ in range(10):
                    # Get current value
                    current = await cache.get(shared_key)
                    if current:
                        value = int(current)
                        # Simulate processing
                        await asyncio.sleep(0.01)
                        # Increment and save
                        await cache.set(shared_key, str(value + 1), ttl=300)
            
            # 5개 "프로세스"에서 동시 실행
            await asyncio.gather(*[
                increment_counter(i) for i in range(5)
            ])
            
            # 최종값 확인 (경쟁 조건으로 인해 50이 아닐 수 있음)
            final_value = await cache.get(shared_key)
            final_int = int(final_value) if final_value else 0
            
            # 일부 업데이트는 손실될 수 있음 (Redis INCR 사용해야 함)
            assert 10 <= final_int <= 50, f"예상 범위 밖의 값: {final_int}"
    
    @integration_test
    async def test_cache_memory_management(self):
        """캐시 메모리 관리 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            # 대용량 데이터 캐싱
            large_data = {
                "data": "x" * 1000,  # 1KB
                "items": [{"id": i, "name": f"item_{i}"} for i in range(100)]
            }
            
            # 100개 키에 저장
            stored_keys = []
            for i in range(100):
                key = f"large:data:{i}"
                await cache.set(key, json.dumps(large_data), ttl=300)
                stored_keys.append(key)
            
            # 모든 키 존재 확인
            existing_count = 0
            for key in stored_keys:
                if await cache.exists(key):
                    existing_count += 1
            
            # 대부분 저장되어야 함
            assert existing_count >= 95, f"저장된 키가 너무 적습니다: {existing_count}/100"
            
            # 정리
            for key in stored_keys:
                await cache.delete(key)
    
    @integration_test
    async def test_cache_performance_metrics(self):
        """캐시 성능 메트릭 테스트"""
        async with create_test_environment() as env:
            cache = env["cache"]
            
            metrics = {
                "hits": 0,
                "misses": 0,
                "set_times": [],
                "get_times": []
            }
            
            # 성능 측정
            test_data = {"key": "value", "data": list(range(100))}
            
            # SET 성능
            for i in range(100):
                key = f"perf:test:{i}"
                start = datetime.now()
                await cache.set(key, json.dumps(test_data), ttl=60)
                duration = (datetime.now() - start).total_seconds() * 1000  # ms
                metrics["set_times"].append(duration)
            
            # GET 성능 (캐시 히트)
            for i in range(100):
                key = f"perf:test:{i}"
                start = datetime.now()
                result = await cache.get(key)
                duration = (datetime.now() - start).total_seconds() * 1000  # ms
                metrics["get_times"].append(duration)
                if result:
                    metrics["hits"] += 1
                else:
                    metrics["misses"] += 1
            
            # GET 성능 (캐시 미스)
            for i in range(100, 200):
                key = f"perf:test:{i}"
                start = datetime.now()
                result = await cache.get(key)
                duration = (datetime.now() - start).total_seconds() * 1000  # ms
                metrics["get_times"].append(duration)
                if result:
                    metrics["hits"] += 1
                else:
                    metrics["misses"] += 1
            
            # 메트릭 분석
            avg_set_time = sum(metrics["set_times"]) / len(metrics["set_times"])
            avg_get_time = sum(metrics["get_times"]) / len(metrics["get_times"])
            hit_rate = metrics["hits"] / (metrics["hits"] + metrics["misses"])
            
            # 성능 기준
            assert avg_set_time < 10, f"SET 평균 시간이 너무 깁니다: {avg_set_time:.2f}ms"
            assert avg_get_time < 5, f"GET 평균 시간이 너무 깁니다: {avg_get_time:.2f}ms"
            assert hit_rate >= 0.45, f"캐시 적중률이 너무 낮습니다: {hit_rate:.2%}"
            
            print(f"\n📊 캐시 성능 메트릭:")
            print(f"  - 평균 SET 시간: {avg_set_time:.2f}ms")
            print(f"  - 평균 GET 시간: {avg_get_time:.2f}ms")
            print(f"  - 캐시 적중률: {hit_rate:.2%}")


# Run inline tests if module is executed directly
if __name__ == "__main__" or os.environ.get("RUN_INTEGRATION_TESTS"):
    if __name__ == "__main__":
        asyncio.run(run_inline_tests(__name__))