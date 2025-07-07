"""
서비스 레이어 기본 테스트 - 커버리지 향상
Basic Service Layer Tests for Coverage Improvement
"""

import pytest
import pytest_asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
import json

from src.services.auth_service import AuthService, auth_service
from src.services.cache import CacheService
from src.services.monitoring import MonitoringService
from src.services.translation import TranslationService
from src.services.worker import WorkerService
from src.services.github_issues import GitHubIssueService


class TestAuthService:
    """인증 서비스 테스트"""
    
    def test_auth_service_initialization(self):
        """인증 서비스 초기화 테스트"""
        service = AuthService()
        assert service.jwt_secret is not None
        assert service.jwt_algorithm == "HS256"
        assert service.jwt_expiration_hours == 24
    
    def test_create_access_token(self):
        """액세스 토큰 생성 테스트"""
        service = AuthService()
        user_data = {
            "id": "user123",
            "username": "testuser",
            "role": "admin"
        }
        
        token = service.create_access_token(user_data)
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token(self):
        """토큰 검증 테스트"""
        service = AuthService()
        user_data = {
            "id": "user123",
            "username": "testuser",
            "role": "admin"
        }
        
        token = service.create_access_token(user_data)
        payload = service.verify_token(token)
        
        assert payload["user_id"] == "user123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "admin"
        assert payload["type"] == "access"
    
    def test_hash_password(self):
        """비밀번호 해시 테스트"""
        service = AuthService()
        password = "testpassword123"
        
        hashed = service.hash_password(password)
        assert isinstance(hashed, str)
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password(self):
        """비밀번호 검증 테스트"""
        service = AuthService()
        password = "testpassword123"
        
        hashed = service.hash_password(password)
        assert service.verify_password(password, hashed) is True
        assert service.verify_password("wrongpassword", hashed) is False
    
    def test_global_auth_service(self):
        """글로벌 인증 서비스 인스턴스 테스트"""
        assert auth_service is not None
        assert isinstance(auth_service, AuthService)


class TestCacheService:
    """캐시 서비스 테스트"""
    
    @pytest_asyncio.fixture
    async def cache_service(self):
        """테스트용 캐시 서비스"""
        with patch('redis.asyncio.from_url') as mock_redis:
            mock_redis_instance = AsyncMock()
            mock_redis.return_value = mock_redis_instance
            
            service = CacheService()
            yield service
    
    async def test_cache_service_initialization(self, cache_service):
        """캐시 서비스 초기화 테스트"""
        assert cache_service is not None
        assert hasattr(cache_service, 'redis')
    
    async def test_cache_set_get(self, cache_service):
        """캐시 설정/조회 테스트"""
        # Mock Redis behavior
        cache_service.redis.set = AsyncMock(return_value=True)
        cache_service.redis.get = AsyncMock(return_value=b'{"test": "value"}')
        
        # 테스트 데이터
        key = "test:key"
        value = {"test": "value"}
        
        # 캐시 설정
        await cache_service.set(key, value)
        cache_service.redis.set.assert_called_once()
        
        # 캐시 조회
        result = await cache_service.get(key)
        cache_service.redis.get.assert_called_once_with(key)
        assert result == value
    
    async def test_cache_delete(self, cache_service):
        """캐시 삭제 테스트"""
        cache_service.redis.delete = AsyncMock(return_value=1)
        
        key = "test:key"
        result = await cache_service.delete(key)
        
        cache_service.redis.delete.assert_called_once_with(key)
        assert result is True
    
    async def test_cache_exists(self, cache_service):
        """캐시 존재 확인 테스트"""
        cache_service.redis.exists = AsyncMock(return_value=1)
        
        key = "test:key"
        result = await cache_service.exists(key)
        
        cache_service.redis.exists.assert_called_once_with(key)
        assert result is True


class TestMonitoringService:
    """모니터링 서비스 테스트"""
    
    def test_monitoring_service_initialization(self):
        """모니터링 서비스 초기화 테스트"""
        service = MonitoringService()
        assert service is not None
    
    def test_get_system_metrics(self):
        """시스템 메트릭 조회 테스트"""
        service = MonitoringService()
        
        with patch('psutil.cpu_percent', return_value=50.0), \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_memory.return_value.percent = 60.0
            mock_disk.return_value.percent = 70.0
            
            metrics = service.get_system_metrics()
            
            assert 'cpu_percent' in metrics
            assert 'memory_percent' in metrics
            assert 'disk_percent' in metrics
            assert metrics['cpu_percent'] == 50.0
    
    def test_get_application_metrics(self):
        """애플리케이션 메트릭 조회 테스트"""
        service = MonitoringService()
        
        with patch.object(service, '_get_database_connections', return_value=10), \
             patch.object(service, '_get_active_users', return_value=5):
            
            metrics = service.get_application_metrics()
            
            assert 'database_connections' in metrics
            assert 'active_users' in metrics
            assert metrics['database_connections'] == 10
            assert metrics['active_users'] == 5
    
    def test_health_check(self):
        """헬스 체크 테스트"""
        service = MonitoringService()
        
        with patch.object(service, '_check_database_health', return_value=True), \
             patch.object(service, '_check_redis_health', return_value=True):
            
            health = service.health_check()
            
            assert health['status'] == 'healthy'
            assert health['database'] is True
            assert health['redis'] is True


class TestTranslationService:
    """번역 서비스 테스트"""
    
    def test_translation_service_initialization(self):
        """번역 서비스 초기화 테스트"""
        service = TranslationService()
        assert service is not None
    
    def test_translate_to_korean(self):
        """한국어 번역 테스트"""
        service = TranslationService()
        
        # 영어 -> 한국어
        result = service.translate_to_korean("Hello World")
        assert isinstance(result, str)
        
        # 이미 한국어인 경우
        result = service.translate_to_korean("안녕하세요")
        assert result == "안녕하세요"
    
    def test_translate_to_english(self):
        """영어 번역 테스트"""
        service = TranslationService()
        
        # 한국어 -> 영어
        result = service.translate_to_english("안녕하세요")
        assert isinstance(result, str)
        
        # 이미 영어인 경우
        result = service.translate_to_english("Hello World")
        assert result == "Hello World"
    
    def test_detect_language(self):
        """언어 감지 테스트"""
        service = TranslationService()
        
        korean_text = "안녕하세요 반갑습니다"
        english_text = "Hello World"
        
        assert service.detect_language(korean_text) == "ko"
        assert service.detect_language(english_text) == "en"


class TestWorkerService:
    """근로자 서비스 테스트"""
    
    @pytest_asyncio.fixture
    async def worker_service(self):
        """테스트용 근로자 서비스"""
        with patch('src.services.worker.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            service = WorkerService()
            service.db = mock_db
            yield service
    
    async def test_worker_service_initialization(self, worker_service):
        """근로자 서비스 초기화 테스트"""
        assert worker_service is not None
    
    async def test_calculate_worker_statistics(self, worker_service):
        """근로자 통계 계산 테스트"""
        # Mock 데이터베이스 응답
        worker_service.db.scalar = AsyncMock(side_effect=[100, 80, 15, 5])
        
        stats = await worker_service.calculate_worker_statistics()
        
        assert stats['total_workers'] == 100
        assert stats['active_workers'] == 80
        assert stats['on_leave'] == 15
        assert stats['terminated'] == 5
    
    async def test_get_workers_by_department(self, worker_service):
        """부서별 근로자 조회 테스트"""
        mock_result = AsyncMock()
        mock_result.scalars.return_value.all.return_value = []
        worker_service.db.execute = AsyncMock(return_value=mock_result)
        
        workers = await worker_service.get_workers_by_department("기술부")
        
        assert isinstance(workers, list)
        worker_service.db.execute.assert_called_once()


class TestGitHubIssueService:
    """GitHub 이슈 서비스 테스트"""
    
    def test_github_service_initialization(self):
        """GitHub 서비스 초기화 테스트"""
        with patch('src.config.settings.get_settings') as mock_settings:
            mock_settings.return_value.github_token = "test_token"
            mock_settings.return_value.github_repo_owner = "test_owner"
            mock_settings.return_value.github_repo_name = "test_repo"
            
            service = GitHubIssueService()
            assert service.github_token == "test_token"
            assert service.repo_owner == "test_owner"
            assert service.repo_name == "test_repo"
    
    @pytest.mark.asyncio
    async def test_create_issue(self):
        """GitHub 이슈 생성 테스트"""
        with patch('src.config.settings.get_settings') as mock_settings, \
             patch('aiohttp.ClientSession.post') as mock_post:
            
            mock_settings.return_value.github_token = "test_token"
            mock_settings.return_value.github_repo_owner = "test_owner"
            mock_settings.return_value.github_repo_name = "test_repo"
            
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value={"number": 123})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            service = GitHubIssueService()
            result = await service.create_issue("Test Issue", "Test body")
            
            assert result["number"] == 123
    
    def test_format_error_issue(self):
        """에러 이슈 포맷팅 테스트"""
        with patch('src.config.settings.get_settings') as mock_settings:
            mock_settings.return_value.github_token = "test_token"
            mock_settings.return_value.github_repo_owner = "test_owner"
            mock_settings.return_value.github_repo_name = "test_repo"
            
            service = GitHubIssueService()
            error_info = {
                "error_type": "ValueError",
                "error_message": "Test error",
                "traceback": "Traceback...",
                "timestamp": datetime.now(),
                "user_id": "test_user"
            }
            
            title, body = service.format_error_issue(error_info)
            
            assert "ValueError" in title
            assert "Test error" in body
            assert "test_user" in body


# 모듈 단위 검증 함수
if __name__ == "__main__":
    import asyncio
    import sys
    
    def validate_services():
        """서비스 검증 실행"""
        try:
            # AuthService 테스트
            auth_service = AuthService()
            token = auth_service.create_access_token({"id": "test", "username": "test"})
            payload = auth_service.verify_token(token)
            assert payload["id"] == "test"
            
            # TranslationService 테스트
            translation_service = TranslationService()
            result = translation_service.detect_language("안녕하세요")
            assert result in ["ko", "unknown"]
            
            # MonitoringService 테스트
            monitoring_service = MonitoringService()
            assert monitoring_service is not None
            
            print("✅ 모든 서비스 검증 통과")
            print("   - AuthService: 토큰 생성/검증 성공")
            print("   - TranslationService: 언어 감지 성공")
            print("   - MonitoringService: 초기화 성공")
            return True
            
        except Exception as e:
            print(f"❌ 서비스 검증 실패: {e}")
            return False
    
    # 검증 실행
    success = validate_services()
    sys.exit(0 if success else 1)