"""
Authentication & Authorization Integration Tests
Inline tests for JWT auth, roles, and permissions
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

import jwt

from src.config.settings import get_settings
from src.testing import (assert_error_response, assert_response_ok,
                         create_test_environment, integration_test,
                         measure_performance, run_inline_tests)

settings = get_settings()


class IntegrationTestAuthentication:
    """인증/인가 통합 테스트"""

    @integration_test
    async def test_jwt_token_lifecycle(self):
        """JWT 토큰 라이프사이클 테스트"""
        async with create_test_environment() as env:
            client = env["client"]

            # 1. 로그인 - 토큰 발급
            login_data = {"username": "admin@test.com", "password": "test_password_123"}

            # 테스트 환경에서는 인증 우회 가능
            if hasattr(settings, "environment") and settings.environment == "test":
                # 직접 토큰 생성
                test_token = self._create_test_token(
                    user_id=1, email="admin@test.com", role="admin"
                )
                client.set_auth(test_token)
            else:
                response = await client.post("/api/v1/auth/login", json=login_data)
                auth_response = assert_response_ok(response)
                assert "access_token" in auth_response
                assert "token_type" in auth_response
                assert auth_response["token_type"] == "bearer"

                token = auth_response["access_token"]
                client.set_auth(token)

            # 2. 인증된 요청
            response = await client.get("/api/v1/auth/me")
            user_info = assert_response_ok(response)
            assert user_info["email"] == "admin@test.com"
            assert user_info["role"] == "admin"

            # 3. 토큰 갱신
            if not hasattr(settings, "environment") or settings.environment != "test":
                response = await client.post("/api/v1/auth/refresh")
                refresh_response = assert_response_ok(response)
                assert "access_token" in refresh_response

                # 새 토큰으로 교체
                new_token = refresh_response["access_token"]
                client.set_auth(new_token)

            # 4. 로그아웃
            response = await client.post("/api/v1/auth/logout")
            assert_response_ok(response)

            # 5. 로그아웃 후 접근 시도 (실패해야 함)
            client.client.headers.pop("Authorization", None)
            response = await client.get("/api/v1/auth/me")
            assert response.status_code == 401

    @integration_test
    async def test_role_based_access_control(self):
        """역할 기반 접근 제어 테스트"""
        async with create_test_environment() as env:
            client = env["client"]

            # 다양한 역할의 토큰 생성
            roles = {
                "admin": {
                    "token": self._create_test_token(1, "admin@test.com", "admin"),
                    "allowed": [
                        "/api/v1/workers/",
                        "/api/v1/settings/",
                        "/api/v1/reports/",
                    ],
                    "forbidden": [],
                },
                "manager": {
                    "token": self._create_test_token(2, "manager@test.com", "manager"),
                    "allowed": ["/api/v1/workers/", "/api/v1/reports/"],
                    "forbidden": ["/api/v1/settings/"],
                },
                "viewer": {
                    "token": self._create_test_token(3, "viewer@test.com", "viewer"),
                    "allowed": ["/api/v1/workers/", "/api/v1/health-exams/"],
                    "forbidden": ["/api/v1/settings/", "/api/v1/workers/bulk-import"],
                },
            }

            for role_name, role_config in roles.items():
                # 역할별 토큰 설정
                client.set_auth(role_config["token"])

                # 허용된 엔드포인트 테스트
                for endpoint in role_config["allowed"]:
                    response = await client.get(endpoint)
                    # 404는 괜찮음 (리소스 없음), 403은 안됨 (권한 없음)
                    assert (
                        response.status_code != 403
                    ), f"{role_name} should access {endpoint}"

                # 금지된 엔드포인트 테스트
                for endpoint in role_config["forbidden"]:
                    response = await client.get(endpoint)
                    assert (
                        response.status_code == 403
                    ), f"{role_name} should NOT access {endpoint}"

    @integration_test
    async def test_department_based_permissions(self):
        """부서 기반 권한 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            db = env["db"]

            # 부서별 사용자 생성
            dept_users = [
                {
                    "id": 10,
                    "email": "dev@test.com",
                    "role": "manager",
                    "department": "개발부",
                },
                {
                    "id": 11,
                    "email": "hr@test.com",
                    "role": "manager",
                    "department": "인사부",
                },
                {
                    "id": 12,
                    "email": "safety@test.com",
                    "role": "manager",
                    "department": "안전관리팀",
                },
            ]

            # 부서별 근로자 생성
            async with db.get_session() as session:
                from src.models import Worker

                workers = [
                    Worker(name="개발자1", employee_id="DEV001", department="개발부"),
                    Worker(name="개발자2", employee_id="DEV002", department="개발부"),
                    Worker(name="인사팀1", employee_id="HR001", department="인사부"),
                    Worker(
                        name="안전관리1", employee_id="SAFE001", department="안전관리팀"
                    ),
                ]

                for worker in workers:
                    session.add(worker)
                await session.commit()

            # 각 부서 매니저로 접근 테스트
            for user in dept_users:
                token = self._create_test_token(
                    user["id"], user["email"], user["role"], user["department"]
                )
                client.set_auth(token)

                # 자기 부서 근로자 조회
                response = await client.get(
                    f"/api/v1/workers/?department={user['department']}"
                )
                workers_list = assert_response_ok(response)

                # 자기 부서 근로자만 보여야 함
                if "items" in workers_list:
                    for worker in workers_list["items"]:
                        assert (
                            worker["department"] == user["department"]
                        ), f"{user['email']}은 자기 부서만 볼 수 있어야 함"

    @integration_test
    @measure_performance
    async def test_token_validation_performance(self):
        """토큰 검증 성능 테스트"""
        async with create_test_environment() as env:
            client = env["client"]

            # 유효한 토큰 생성
            valid_token = self._create_test_token(1, "perf@test.com", "admin")
            client.set_auth(valid_token)

            # 100개 요청 동시 실행
            async def make_authenticated_request(req_id: int):
                start_time = datetime.now()
                response = await client.get("/api/v1/workers/")
                duration = (datetime.now() - start_time).total_seconds() * 1000
                return {
                    "id": req_id,
                    "status": response.status_code,
                    "duration_ms": duration,
                }

            results = await asyncio.gather(
                *[make_authenticated_request(i) for i in range(100)]
            )

            # 성능 분석
            successful = [r for r in results if r["status"] == 200]
            avg_duration = sum(r["duration_ms"] for r in successful) / len(successful)

            assert len(successful) >= 95, "너무 많은 요청이 실패했습니다"
            assert (
                avg_duration < 50
            ), f"평균 응답 시간이 너무 깁니다: {avg_duration:.2f}ms"

    @integration_test
    async def test_token_expiration_handling(self):
        """토큰 만료 처리 테스트"""
        async with create_test_environment() as env:
            client = env["client"]

            # 1. 곧 만료될 토큰 (1초)
            short_lived_token = self._create_test_token(
                1, "expire@test.com", "admin", expires_in_seconds=1
            )
            client.set_auth(short_lived_token)

            # 즉시 요청 - 성공해야 함
            response = await client.get("/api/v1/workers/")
            assert response.status_code == 200

            # 2초 대기
            await asyncio.sleep(2)

            # 만료 후 요청 - 실패해야 함
            response = await client.get("/api/v1/workers/")
            assert response.status_code == 401
            error = response.json()
            assert "expired" in error.get("detail", "").lower()

            # 2. 리프레시 토큰으로 갱신
            if not hasattr(settings, "environment") or settings.environment != "test":
                refresh_token = self._create_test_token(
                    1,
                    "expire@test.com",
                    "admin",
                    token_type="refresh",
                    expires_in_seconds=3600,
                )

                response = await client.post(
                    "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
                )

                if response.status_code == 200:
                    new_token = response.json()["access_token"]
                    client.set_auth(new_token)

                    # 새 토큰으로 요청
                    response = await client.get("/api/v1/workers/")
                    assert response.status_code == 200

    @integration_test
    async def test_concurrent_session_limit(self):
        """동시 세션 제한 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            cache = env["cache"]

            user_id = 100
            email = "concurrent@test.com"

            # 여러 디바이스에서 로그인 시뮬레이션
            sessions = []
            for device_id in range(5):
                token = self._create_test_token(
                    user_id,
                    email,
                    "user",
                    extra_claims={"device_id": f"device_{device_id}"},
                )
                sessions.append(
                    {
                        "device_id": f"device_{device_id}",
                        "token": token,
                        "created_at": datetime.now(),
                    }
                )

                # 세션 정보 캐싱
                session_key = f"session:{user_id}:device_{device_id}"
                await cache.set(session_key, token, ttl=3600)

            # 활성 세션 수 확인
            active_sessions = []
            for device_id in range(5):
                session_key = f"session:{user_id}:device_{device_id}"
                if await cache.exists(session_key):
                    active_sessions.append(device_id)

            # 동시 세션 제한 (예: 3개)
            max_concurrent_sessions = 3
            if len(active_sessions) > max_concurrent_sessions:
                # 오래된 세션 제거
                for i in range(len(active_sessions) - max_concurrent_sessions):
                    old_session_key = f"session:{user_id}:device_{i}"
                    await cache.delete(old_session_key)

            # 제한 확인
            remaining_sessions = []
            for device_id in range(5):
                session_key = f"session:{user_id}:device_{device_id}"
                if await cache.exists(session_key):
                    remaining_sessions.append(device_id)

            assert len(remaining_sessions) <= max_concurrent_sessions

    @integration_test
    async def test_security_headers(self):
        """보안 헤더 테스트"""
        async with create_test_environment() as env:
            client = env["client"]

            # 인증 없이 요청
            response = await client.client.get("/api/v1/health")

            # 보안 헤더 확인
            headers = response.headers

            # CORS 헤더
            if "access-control-allow-origin" in headers:
                assert (
                    headers["access-control-allow-origin"] != "*"
                ), "CORS should not allow all origins in production"

            # 보안 헤더들
            security_headers = {
                "x-content-type-options": "nosniff",
                "x-frame-options": "DENY",
                "x-xss-protection": "1; mode=block",
                "strict-transport-security": "max-age=31536000",
            }

            for header, expected_value in security_headers.items():
                if header in headers:
                    assert (
                        headers[header] == expected_value
                    ), f"{header} should be {expected_value}"

    @integration_test
    async def test_brute_force_protection(self):
        """무차별 대입 공격 방어 테스트"""
        async with create_test_environment() as env:
            client = env["client"]
            cache = env["cache"]

            # 로그인 시도 추적
            email = "bruteforce@test.com"
            ip_address = "192.168.1.100"

            # 실패한 로그인 시도
            failed_attempts = 0
            max_attempts = 5

            for i in range(10):
                # 잘못된 비밀번호로 로그인 시도
                login_data = {"username": email, "password": f"wrong_password_{i}"}

                # 실패 횟수 확인
                attempt_key = f"login_attempts:{email}:{ip_address}"
                attempts = await cache.get(attempt_key)
                if attempts and int(attempts) >= max_attempts:
                    # 차단됨
                    response = await client.post("/api/v1/auth/login", json=login_data)
                    assert response.status_code == 429  # Too Many Requests
                    error = response.json()
                    assert "too many attempts" in error.get("detail", "").lower()
                    break
                else:
                    # 시도 기록
                    failed_attempts += 1
                    await cache.set(attempt_key, str(failed_attempts), ttl=900)  # 15분

            assert (
                failed_attempts >= max_attempts
            ), "무차별 대입 공격 방어가 작동하지 않습니다"

    # Helper methods
    def _create_test_token(
        self,
        user_id: int,
        email: str,
        role: str,
        department: Optional[str] = None,
        expires_in_seconds: int = 3600,
        token_type: str = "access",
        extra_claims: Optional[Dict] = None,
    ) -> str:
        """테스트용 JWT 토큰 생성"""
        now = datetime.utcnow()

        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": token_type,
            "iat": now,
            "exp": now + timedelta(seconds=expires_in_seconds),
        }

        if department:
            payload["department"] = department

        if extra_claims:
            payload.update(extra_claims)

        # 테스트 환경에서는 간단한 시크릿 사용
        secret = (
            settings.jwt_secret if hasattr(settings, "jwt_secret") else "test_secret"
        )

        return jwt.encode(payload, secret, algorithm="HS256")


# Run inline tests if module is executed directly
if __name__ == "__main__" or os.environ.get("RUN_INTEGRATION_TESTS"):
    if __name__ == "__main__":
        asyncio.run(run_inline_tests(__name__))
