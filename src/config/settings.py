"""
애플리케이션 설정
Application settings and configuration
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import os
import secrets

class Settings(BaseSettings):
    """애플리케이션 설정 클래스 - 하드코딩 값 제거됨"""
    
    # 애플리케이션 기본 설정
    app_name: str = Field(default="SafeWork Pro", env="APP_NAME")
    app_version: str = Field(default="1.0.1", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    
    # 서버 설정
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # 디렉토리 설정
    static_files_dir: str = Field(default="/app/dist", env="STATIC_FILES_DIR")
    uploads_dir: str = Field(default="/app/uploads", env="UPLOADS_DIR")
    logs_dir: str = Field(default="/app/logs", env="LOGS_DIR")
    document_dir: str = Field(default="/app/document", env="DOCUMENT_DIR")
    
    # 개발 환경 설정
    disable_auth: bool = Field(default=False, env="DISABLE_AUTH")
    
    # 데이터베이스 설정 - 하드코딩 제거
    database_host: str = Field(default="localhost", env="DATABASE_HOST")
    database_port: int = Field(default=5432, env="DATABASE_PORT")
    database_user: str = Field(default="admin", env="POSTGRES_USER")
    database_password: str = Field(default="safework123", env="POSTGRES_PASSWORD")
    database_name: str = Field(default="health_management", env="POSTGRES_DB")
    database_url: str = Field(default="", env="DATABASE_URL")
    
    # JWT 설정 - 보안 강화
    secret_key: str = Field(default="safework-app-secret-2024", env="SECRET_KEY")
    jwt_secret: str = Field(default="safework-pro-secret-key-2024", env="JWT_SECRET") 
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=1440, env="TOKEN_EXPIRE_MINUTES")
    
    # Redis 설정
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: str = Field(default="", env="REDIS_PASSWORD")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # 성능 설정 - Magic numbers 제거
    rate_limit: int = Field(default=100, env="RATE_LIMIT")
    rate_limit_window: int = Field(default=60, env="RATE_LIMIT_WINDOW")
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    max_batch_size: int = Field(default=100, env="MAX_BATCH_SIZE")
    slow_query_threshold: float = Field(default=1.0, env="SLOW_QUERY_THRESHOLD")
    cache_expire_seconds: int = Field(default=86400, env="CACHE_EXPIRE_SECONDS")
    
    # 파일 업로드 설정
    upload_dir: str = Field(default="uploads", env="UPLOAD_DIR")
    max_file_size: int = Field(default=10485760, env="MAX_FILE_SIZE")  # 10MB
    allowed_extensions: str = Field(default=".pdf,.doc,.docx,.xls,.xlsx,.jpg,.png,.gif", env="ALLOWED_EXTENSIONS")
    
    # 이메일 설정
    smtp_host: str = Field(default="localhost", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: str = Field(default="", env="SMTP_USERNAME")
    smtp_password: str = Field(default="", env="SMTP_PASSWORD")
    
    # 외부 API 설정
    kosha_api_url: str = Field(default="https://www.kosha.or.kr/api", env="KOSHA_API_URL")
    moel_api_url: str = Field(default="https://www.moel.go.kr/api", env="MOEL_API_URL")
    
    # 프로덕션 환경 설정
    production_url: str = Field(default="http://192.168.50.215:3001", env="PRODUCTION_URL")
    remote_host: str = Field(default="192.168.50.215", env="REMOTE_HOST")
    remote_port: int = Field(default=1111, env="REMOTE_PORT")
    remote_user: str = Field(default="docker", env="REMOTE_USER")
    
    # Docker 설정
    docker_registry: str = Field(default="registry.jclee.me", env="DOCKER_REGISTRY")
    
    # Watchtower 설정
    watchtower_url: str = Field(default="https://watchtower.jclee.me", env="WATCHTOWER_URL")
    watchtower_token: str = Field(default="MySuperSecretToken12345", env="WATCHTOWER_TOKEN")
    
    # 모니터링 설정
    sentry_dsn: str = Field(default="", env="SENTRY_DSN")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # 보고서 설정
    font_path: str = Field(default="/usr/share/fonts/truetype/nanum/NanumGothic.ttf", env="FONT_PATH")
    health_exam_interval_days: int = Field(default=365, env="HEALTH_EXAM_INTERVAL_DAYS")
    accident_report_deadline_hours: int = Field(default=24, env="ACCIDENT_REPORT_DEADLINE_HOURS")
    work_days_lost_threshold: int = Field(default=3, env="WORK_DAYS_LOST_THRESHOLD")
    
    # 업로드 디렉토리 설정
    msds_upload_subdir: str = Field(default="msds", env="MSDS_UPLOAD_SUBDIR")
    accident_upload_subdir: str = Field(default="accidents", env="ACCIDENT_UPLOAD_SUBDIR")
    
    # 기본 근로 계산 설정
    annual_work_days: int = Field(default=250, env="ANNUAL_WORK_DAYS")
    daily_work_hours: int = Field(default=8, env="DAILY_WORK_HOURS")
    default_worker_count: int = Field(default=100, env="DEFAULT_WORKER_COUNT")
    
    # 페이지네이션 설정
    max_recent_items: int = Field(default=10, env="MAX_RECENT_ITEMS")
    dashboard_recent_items: int = Field(default=5, env="DASHBOARD_RECENT_ITEMS")
    
    # GitHub 에러 리포팅 설정
    github_token: str = Field(default="", env="GITHUB_TOKEN")
    github_repo_owner: str = Field(default="JCLEE94", env="GITHUB_REPO_OWNER")
    github_repo_name: str = Field(default="safework", env="GITHUB_REPO_NAME")
    error_reporting_enabled: bool = Field(default=True, env="ERROR_REPORTING_ENABLED")
    
    @property
    def allowed_extensions_list(self) -> list:
        """허용된 확장자 리스트 반환"""
        return self.allowed_extensions.split(",")
    
    def generate_database_url(self) -> str:
        """데이터베이스 URL 동적 생성"""
        if self.database_url:
            return self.database_url
        return f"postgresql://{self.database_user}:{self.database_password}@{self.database_host}:{self.database_port}/{self.database_name}"
    
    def generate_redis_url(self) -> str:
        """Redis URL 동적 생성"""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env

@lru_cache()
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐시됨)"""
    return Settings()