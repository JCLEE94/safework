"""
애플리케이션 설정
Application settings and configuration
"""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os

class Settings(BaseSettings):
    """애플리케이션 설정 클래스"""
    
    # 애플리케이션 기본 설정
    app_name: str = "건설업 보건관리 시스템"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # 데이터베이스 설정
    database_url: str = "postgresql://admin:password@health-postgres:5432/health_management"
    
    # JWT 설정
    secret_key: str = "super-secret-jwt-key-for-health-management-system"
    jwt_secret: str = "your-super-secret-jwt-key-here-32-chars-long"  # For compatibility
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24시간
    
    # Redis 설정
    redis_url: str = "redis://health-redis:6379/0"
    redis_password: str = ""
    
    # 파일 업로드 설정
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_extensions: list = [".pdf", ".doc", ".docx", ".xls", ".xlsx", ".jpg", ".png", ".gif"]
    
    # 이메일 설정
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = "noreply@healthmanagement.com"
    smtp_password: str = "app-password"
    
    # 외부 API 설정
    kosha_api_url: str = "https://www.kosha.or.kr/api"
    moel_api_url: str = "https://www.moel.go.kr/api"
    
    # 모니터링 설정
    sentry_dsn: str = ""
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()