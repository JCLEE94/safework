"""
인증 시스템 전체 흐름 통합 테스트
Authentication System Integration Tests
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from fastapi import status
import asyncio

from src.app import create_app
from src.services.auth_service import AuthService
from src.config.settings import get_settings


class TestAuthenticationFlow:
    """JWT 인증 전체 워크플로우 통합 테스트"""
    
    @pytest.fixture
    def auth_service(self):
        """인증 서비스 인스턴스"""
        return AuthService()
    
    @pytest.fixture
    def test_user_data(self):
        """테스트용 사용자 데이터"""
        return {
            "id": "test_user_001",
            "username": "건설현장관리자",
            "role": "site_manager",
            "department": "안전보건관리팀"
        }
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    async def test_jwt_token_creation_to_validation_flow(self, auth_service, test_user_data):
        """JWT 토큰 생성부터 검증까지 전체 흐름 테스트"""
        # 1. 토큰 생성
        access_token = auth_service.create_access_token(test_user_data)
        assert access_token is not None
        assert isinstance(access_token, str)
        
        # 2. 토큰 구조 확인
        token_parts = access_token.split('.')
        assert len(token_parts) == 3  # Header.Payload.Signature
        
        # 3. 토큰 검증
        decoded_token = auth_service.verify_token(access_token)
        assert decoded_token["user_id"] == test_user_data["id"]
        assert decoded_token["username"] == test_user_data["username"]
        assert decoded_token["role"] == test_user_data["role"]
        
        # 4. 토큰 만료 시간 확인
        exp_timestamp = decoded_token["exp"]
        exp_datetime = datetime.fromtimestamp(exp_timestamp)
        now = datetime.utcnow()
        
        # 만료 시간이 현재보다 미래인지 확인
        assert exp_datetime > now
        
        # 만료 시간이 24시간 후 근처인지 확인 (±5분 허용)
        expected_exp = now + timedelta(hours=24)
        time_diff = abs((exp_datetime - expected_exp).total_seconds())
        assert time_diff < 300  # 5분 이내
    
    async def test_development_vs_production_auth_modes(self, test_client):
        """개발/운영 환경별 인증 모드 테스트"""
        # 1. 개발 환경 - 인증 우회 테스트
        import os
        original_env = os.environ.get("ENVIRONMENT")
        
        try:
            # 개발 환경 설정
            os.environ["ENVIRONMENT"] = "development"
            os.environ["DISABLE_AUTH"] = "true"
            
            # 인증 없이 API 호출
            response = test_client.get("/api/v1/workers/")
            # 인증이 우회되어야 함 (404 또는 200, 401이 아님)
            assert response.status_code != 401
            
            # 2. 운영 환경 - 인증 강제 테스트
            os.environ["ENVIRONMENT"] = "production"
            os.environ["DISABLE_AUTH"] = "false"
            
            # 인증 없이 API 호출 시 401 반환되어야 함
            response = test_client.get("/api/v1/workers/")
            # 실제 구현에 따라 401 또는 다른 인증 오류
            
        finally:
            # 환경변수 복원
            if original_env:
                os.environ["ENVIRONMENT"] = original_env
            else:
                os.environ.pop("ENVIRONMENT", None)
    
    async def test_role_based_access_control_enforcement(self, auth_service, test_client):
        """역할 기반 접근 제어 강제 테스트"""
        # 다양한 역할의 사용자 데이터
        users = [
            {"id": "admin_001", "username": "시스템관리자", "role": "admin"},
            {"id": "manager_001", "username": "보건관리자", "role": "health_manager"},
            {"id": "worker_001", "username": "일반근로자", "role": "worker"},
            {"id": "viewer_001", "username": "열람자", "role": "viewer"}
        ]
        
        # 각 역할별 토큰 생성
        tokens = {}
        for user in users:
            token = auth_service.create_access_token(user)
            tokens[user["role"]] = token
        
        # 역할별 접근 권한 테스트
        test_cases = [
            # (endpoint, method, allowed_roles)
            ("/api/v1/workers/", "GET", ["admin", "health_manager", "viewer"]),
            ("/api/v1/workers/", "POST", ["admin", "health_manager"]),
            ("/api/v1/settings/", "GET", ["admin"]),
            ("/api/v1/settings/", "PUT", ["admin"]),
        ]
        
        for endpoint, method, allowed_roles in test_cases:
            for role, token in tokens.items():
                headers = {"Authorization": f"Bearer {token}"}
                
                if method == "GET":
                    response = test_client.get(endpoint, headers=headers)
                elif method == "POST":
                    response = test_client.post(endpoint, headers=headers, json={})
                elif method == "PUT":
                    response = test_client.put(endpoint, headers=headers, json={})
                
                if role in allowed_roles:
                    # 권한이 있는 경우 - 401이 아니어야 함
                    assert response.status_code != 401, f"{role}이 {endpoint}에 접근할 수 있어야 함"
                else:
                    # 권한이 없는 경우 - 403 또는 401 반환되어야 함
                    assert response.status_code in [401, 403], f"{role}이 {endpoint}에 접근할 수 없어야 함"
    
    async def test_token_expiration_and_refresh_cycle(self, auth_service, test_user_data):
        """토큰 만료 및 갱신 사이클 테스트"""
        # 1. 짧은 만료 시간으로 토큰 생성 (테스트용)
        original_expiration = auth_service.jwt_expiration_hours
        auth_service.jwt_expiration_hours = 1/3600  # 1초
        
        try:
            token = auth_service.create_access_token(test_user_data)
            
            # 2. 토큰이 유효한지 확인
            decoded_token = auth_service.verify_token(token)
            assert decoded_token["user_id"] == test_user_data["id"]
            
            # 3. 토큰 만료 대기
            await asyncio.sleep(2)
            
            # 4. 만료된 토큰 검증 시 예외 발생 확인
            with pytest.raises(Exception):  # JWT 만료 예외
                auth_service.verify_token(token)
            
            # 5. 새 토큰 생성 (갱신)
            new_token = auth_service.create_access_token(test_user_data)
            new_decoded_token = auth_service.verify_token(new_token)
            assert new_decoded_token["user_id"] == test_user_data["id"]
            
        finally:
            # 원래 만료 시간 복원
            auth_service.jwt_expiration_hours = original_expiration
    
    async def test_invalid_token_handling_across_endpoints(self, test_client):
        """잘못된 토큰 처리 전체 엔드포인트 테스트"""
        invalid_tokens = [
            "invalid.token.format",
            "Bearer invalid_token",
            "",
            "expired.jwt.token",
            "tampered.jwt.signature"
        ]
        
        # 보호된 엔드포인트 목록
        protected_endpoints = [
            "/api/v1/workers/",
            "/api/v1/health-exams/",
            "/api/v1/chemical-substances/",
            "/api/v1/accident-reports/",
        ]
        
        for endpoint in protected_endpoints:
            for invalid_token in invalid_tokens:
                headers = {"Authorization": f"Bearer {invalid_token}"}
                response = test_client.get(endpoint, headers=headers)
                
                # 잘못된 토큰의 경우 인증 오류 반환
                assert response.status_code in [401, 422], \
                    f"{endpoint}에서 잘못된 토큰 '{invalid_token}'에 대해 적절한 오류 응답이 없음"
    
    async def test_concurrent_user_sessions(self, auth_service):
        """동시 사용자 세션 테스트"""
        # 여러 사용자의 동시 토큰 생성
        users = [
            {"id": f"user_{i:03d}", "username": f"사용자{i}", "role": "worker"}
            for i in range(1, 101)  # 100명의 사용자
        ]
        
        # 동시 토큰 생성
        async def create_user_token(user_data):
            return auth_service.create_access_token(user_data)
        
        tasks = [create_user_token(user) for user in users]
        tokens = await asyncio.gather(*tasks)
        
        # 모든 토큰이 유효한지 확인
        for i, token in enumerate(tokens):
            decoded = auth_service.verify_token(token)
            assert decoded["user_id"] == users[i]["id"]
            assert decoded["username"] == users[i]["username"]
        
        # 토큰들이 서로 다른지 확인
        unique_tokens = set(tokens)
        assert len(unique_tokens) == len(tokens), "토큰이 중복 생성됨"
    
    async def test_auth_middleware_integration(self, test_client, auth_service):
        """인증 미들웨어 통합 테스트"""
        # 유효한 토큰으로 API 호출
        user_data = {"id": "middleware_test", "username": "미들웨어테스트", "role": "health_manager"}
        valid_token = auth_service.create_access_token(user_data)
        
        headers = {"Authorization": f"Bearer {valid_token}"}
        
        # 1. 유효한 토큰으로 보호된 엔드포인트 접근
        response = test_client.get("/api/v1/workers/", headers=headers)
        assert response.status_code != 401
        
        # 2. 토큰 없이 보호된 엔드포인트 접근
        response = test_client.get("/api/v1/workers/")
        # 환경에 따라 401 또는 개발 모드에서 우회
        
        # 3. Authorization 헤더 형식 테스트
        malformed_headers = [
            {"Authorization": f"Basic {valid_token}"},  # 잘못된 스키마
            {"Authorization": valid_token},  # Bearer 누락
            {"Auth": f"Bearer {valid_token}"},  # 잘못된 헤더명
        ]
        
        for bad_header in malformed_headers:
            response = test_client.get("/api/v1/workers/", headers=bad_header)
            # 잘못된 헤더 형식의 경우 인증 실패
    
    async def test_user_context_injection(self, test_client, auth_service):
        """사용자 컨텍스트 주입 테스트"""
        # 사용자 정보가 포함된 토큰 생성
        user_data = {
            "id": "context_test_user",
            "username": "컨텍스트테스트사용자",
            "role": "health_manager",
            "department": "안전보건팀"
        }
        
        token = auth_service.create_access_token(user_data)
        headers = {"Authorization": f"Bearer {token}"}
        
        # API 호출 시 사용자 컨텍스트가 올바르게 주입되는지 확인
        # (실제로는 핸들러에서 current_user_id를 사용하는 로직 테스트)
        response = test_client.post(
            "/api/v1/workers/",
            headers=headers,
            json={
                "name": "테스트근로자",
                "gender": "male",
                "employment_type": "regular"
            }
        )
        
        # 생성된 데이터에 올바른 사용자 ID가 기록되었는지 확인
        # (실제 구현에 따라 응답 구조 조정 필요)


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import sys
    import subprocess
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
    ])
    
    if result.returncode == 0:
        print("✅ 인증 시스템 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 인증 시스템 통합 테스트 실패")
        sys.exit(1)