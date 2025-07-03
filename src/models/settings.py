"""
시스템 설정 관리 모델
System Settings Management Models
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, JSON, DateTime
from sqlalchemy.sql import func
from datetime import datetime
import enum

from ..config.database import Base


class BackupFrequency(enum.Enum):
    """백업 주기"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReportLanguage(enum.Enum):
    """보고서 언어"""
    KOREAN = "korean"
    ENGLISH = "english"
    BOTH = "both"


class DashboardLayout(enum.Enum):
    """대시보드 레이아웃"""
    DEFAULT = "default"
    COMPACT = "compact"
    DETAILED = "detailed"


class Theme(enum.Enum):
    """테마"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class Language(enum.Enum):
    """언어"""
    KOREAN = "korean"
    ENGLISH = "english"


class SystemSettings(Base):
    """시스템 설정 테이블"""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, index=True)
    
    # 회사 정보
    company_name = Column(String(255), nullable=False, comment="회사명")
    company_address = Column(Text, nullable=True, comment="회사 주소")
    company_phone = Column(String(50), nullable=True, comment="회사 전화번호")
    company_registration_number = Column(String(50), nullable=True, comment="사업자등록번호")
    business_type = Column(String(100), nullable=True, comment="업종")
    total_employees = Column(Integer, nullable=True, default=0, comment="총 직원 수")
    safety_manager = Column(String(100), nullable=True, comment="안전관리자")
    health_manager = Column(String(100), nullable=True, comment="보건관리자")
    representative_name = Column(String(100), nullable=True, comment="대표자명")
    
    # 백업 설정
    auto_backup_enabled = Column(Boolean, nullable=False, default=True, comment="자동 백업 활성화")
    backup_frequency = Column(String(20), nullable=False, default="daily", comment="백업 주기")
    
    # 알림 설정
    notification_enabled = Column(Boolean, nullable=False, default=True, comment="알림 활성화")
    email_notifications = Column(Boolean, nullable=False, default=True, comment="이메일 알림")
    sms_notifications = Column(Boolean, nullable=False, default=False, comment="SMS 알림")
    
    # 보고서 설정
    report_language = Column(String(20), nullable=False, default="korean", comment="보고서 언어")
    
    # 데이터 관리
    data_retention_period = Column(Integer, nullable=False, default=36, comment="데이터 보존 기간(개월)")
    audit_log_enabled = Column(Boolean, nullable=False, default=True, comment="감사 로그 활성화")
    
    # 보안 설정
    password_policy_enabled = Column(Boolean, nullable=False, default=True, comment="비밀번호 정책 활성화")
    session_timeout = Column(Integer, nullable=False, default=120, comment="세션 타임아웃(분)")
    api_access_enabled = Column(Boolean, nullable=False, default=False, comment="API 접근 허용")
    
    # 시스템 관리
    maintenance_mode = Column(Boolean, nullable=False, default=False, comment="유지보수 모드")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    updated_by = Column(String(100), nullable=True, comment="수정자")

    def __repr__(self):
        return f"<SystemSettings(id={self.id}, company_name={self.company_name})>"


class UserSettings(Base):
    """사용자 설정 테이블"""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False, index=True, comment="사용자 ID")
    
    # 사용자 정보
    user_name = Column(String(100), nullable=False, comment="사용자명")
    user_email = Column(String(255), nullable=True, comment="이메일")
    user_phone = Column(String(50), nullable=True, comment="전화번호")
    user_role = Column(String(100), nullable=True, comment="역할")
    department = Column(String(100), nullable=True, comment="부서")
    
    # 알림 설정
    notification_preferences = Column(JSON, nullable=False, default=dict, comment="알림 설정")
    
    # UI 설정
    dashboard_layout = Column(String(20), nullable=False, default="default", comment="대시보드 레이아웃")
    theme = Column(String(20), nullable=False, default="light", comment="테마")
    language = Column(String(20), nullable=False, default="korean", comment="언어")
    timezone = Column(String(50), nullable=False, default="Asia/Seoul", comment="시간대")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")

    def __repr__(self):
        return f"<UserSettings(id={self.id}, user_id={self.user_id}, user_name={self.user_name})>"


class SettingsHistory(Base):
    """설정 변경 이력 테이블"""
    __tablename__ = "settings_history"

    id = Column(Integer, primary_key=True, index=True)
    setting_type = Column(String(50), nullable=False, comment="설정 타입 (system/user)")
    setting_key = Column(String(100), nullable=False, comment="설정 키")
    old_value = Column(Text, nullable=True, comment="이전 값")
    new_value = Column(Text, nullable=True, comment="새로운 값")
    changed_by = Column(String(100), nullable=False, comment="변경자")
    change_reason = Column(Text, nullable=True, comment="변경 사유")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="변경일시")

    def __repr__(self):
        return f"<SettingsHistory(id={self.id}, setting_type={self.setting_type}, setting_key={self.setting_key})>"