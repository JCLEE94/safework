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
    app_name: str = os.getenv("APP_NAME", "SafeWork Pro")
    app_version: str = os.getenv("APP_VERSION", "1.0.1")
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    # 개발 환경 설정
    disable_auth: bool = os.getenv("DISABLE_AUTH", "false").lower() == "true"
    
    # 데이터베이스 설정
    database_url: str = os.getenv("DATABASE_URL", "postgresql://admin:safework123@localhost:5432/health_management")
    
    # JWT 설정
    secret_key: str = os.getenv("SECRET_KEY", os.urandom(32).hex())
    jwt_secret: str = os.getenv("JWT_SECRET", os.urandom(32).hex())
    algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Redis 설정
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    redis_password: str = os.getenv("REDIS_PASSWORD", "")
    
    # 파일 업로드 설정
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # 10MB
    allowed_extensions: list = os.getenv("ALLOWED_EXTENSIONS", ".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png,.gif").split(",")
    
    # 이메일 설정
    smtp_host: str = os.getenv("SMTP_HOST", "localhost")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_username: str = os.getenv("SMTP_USERNAME", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    
    # 외부 API 설정
    kosha_api_url: str = os.getenv("KOSHA_API_URL", "https://www.kosha.or.kr/api")
    moel_api_url: str = os.getenv("MOEL_API_URL", "https://www.moel.go.kr/api")
    
    # 모니터링 설정
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()