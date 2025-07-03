"""
시스템 설정 관리 스키마
System Settings Management Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, Optional, Any
from datetime import datetime

from ..models.settings import BackupFrequency, ReportLanguage, DashboardLayout, Theme, Language


# ===== 시스템 설정 스키마 =====

class SystemSettingsBase(BaseModel):
    """시스템 설정 기본 스키마"""
    # 회사 정보
    company_name: str = Field(..., description="회사명", min_length=1, max_length=255)
    company_address: Optional[str] = Field(None, description="회사 주소")
    company_phone: Optional[str] = Field(None, description="회사 전화번호", max_length=50)
    company_registration_number: Optional[str] = Field(None, description="사업자등록번호", max_length=50)
    business_type: Optional[str] = Field(None, description="업종", max_length=100)
    total_employees: Optional[int] = Field(0, description="총 직원 수", ge=0)
    safety_manager: Optional[str] = Field(None, description="안전관리자", max_length=100)
    health_manager: Optional[str] = Field(None, description="보건관리자", max_length=100)
    representative_name: Optional[str] = Field(None, description="대표자명", max_length=100)
    
    # 백업 설정
    auto_backup_enabled: bool = Field(True, description="자동 백업 활성화")
    backup_frequency: str = Field("daily", description="백업 주기")
    
    # 알림 설정
    notification_enabled: bool = Field(True, description="알림 활성화")
    email_notifications: bool = Field(True, description="이메일 알림")
    sms_notifications: bool = Field(False, description="SMS 알림")
    
    # 보고서 설정
    report_language: str = Field("korean", description="보고서 언어")
    
    # 데이터 관리
    data_retention_period: int = Field(36, description="데이터 보존 기간(개월)", ge=1, le=120)
    audit_log_enabled: bool = Field(True, description="감사 로그 활성화")
    
    # 보안 설정
    password_policy_enabled: bool = Field(True, description="비밀번호 정책 활성화")
    session_timeout: int = Field(120, description="세션 타임아웃(분)", ge=5, le=1440)
    api_access_enabled: bool = Field(False, description="API 접근 허용")
    
    # 시스템 관리
    maintenance_mode: bool = Field(False, description="유지보수 모드")

    @validator('backup_frequency')
    def validate_backup_frequency(cls, v):
        """백업 주기 유효성 검사"""
        if v not in ['daily', 'weekly', 'monthly']:
            raise ValueError('백업 주기는 daily, weekly, monthly 중 하나여야 합니다')
        return v

    @validator('report_language')
    def validate_report_language(cls, v):
        """보고서 언어 유효성 검사"""
        if v not in ['korean', 'english', 'both']:
            raise ValueError('보고서 언어는 korean, english, both 중 하나여야 합니다')
        return v


class SystemSettingsCreate(SystemSettingsBase):
    """시스템 설정 생성 스키마"""
    pass


class SystemSettingsUpdate(BaseModel):
    """시스템 설정 수정 스키마"""
    # 회사 정보
    company_name: Optional[str] = Field(None, description="회사명", min_length=1, max_length=255)
    company_address: Optional[str] = Field(None, description="회사 주소")
    company_phone: Optional[str] = Field(None, description="회사 전화번호", max_length=50)
    company_registration_number: Optional[str] = Field(None, description="사업자등록번호", max_length=50)
    business_type: Optional[str] = Field(None, description="업종", max_length=100)
    total_employees: Optional[int] = Field(None, description="총 직원 수", ge=0)
    safety_manager: Optional[str] = Field(None, description="안전관리자", max_length=100)
    health_manager: Optional[str] = Field(None, description="보건관리자", max_length=100)
    representative_name: Optional[str] = Field(None, description="대표자명", max_length=100)
    
    # 백업 설정
    auto_backup_enabled: Optional[bool] = Field(None, description="자동 백업 활성화")
    backup_frequency: Optional[str] = Field(None, description="백업 주기")
    
    # 알림 설정
    notification_enabled: Optional[bool] = Field(None, description="알림 활성화")
    email_notifications: Optional[bool] = Field(None, description="이메일 알림")
    sms_notifications: Optional[bool] = Field(None, description="SMS 알림")
    
    # 보고서 설정
    report_language: Optional[str] = Field(None, description="보고서 언어")
    
    # 데이터 관리
    data_retention_period: Optional[int] = Field(None, description="데이터 보존 기간(개월)", ge=1, le=120)
    audit_log_enabled: Optional[bool] = Field(None, description="감사 로그 활성화")
    
    # 보안 설정
    password_policy_enabled: Optional[bool] = Field(None, description="비밀번호 정책 활성화")
    session_timeout: Optional[int] = Field(None, description="세션 타임아웃(분)", ge=5, le=1440)
    api_access_enabled: Optional[bool] = Field(None, description="API 접근 허용")
    
    # 시스템 관리
    maintenance_mode: Optional[bool] = Field(None, description="유지보수 모드")


class SystemSettingsResponse(SystemSettingsBase):
    """시스템 설정 응답 스키마"""
    id: int = Field(..., description="설정 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    updated_by: Optional[str] = Field(None, description="수정자")

    class Config:
        from_attributes = True


# ===== 사용자 설정 스키마 =====

class NotificationPreferences(BaseModel):
    """알림 설정 스키마"""
    accidents: bool = Field(True, description="사고 알림")
    health_exams: bool = Field(True, description="건강진단 알림")
    education_reminders: bool = Field(True, description="교육 알림")
    report_deadlines: bool = Field(True, description="보고서 마감 알림")
    system_updates: bool = Field(False, description="시스템 업데이트 알림")


class UserSettingsBase(BaseModel):
    """사용자 설정 기본 스키마"""
    user_name: str = Field(..., description="사용자명", min_length=1, max_length=100)
    user_email: Optional[str] = Field(None, description="이메일", max_length=255)
    user_phone: Optional[str] = Field(None, description="전화번호", max_length=50)
    user_role: Optional[str] = Field(None, description="역할", max_length=100)
    department: Optional[str] = Field(None, description="부서", max_length=100)
    
    # 알림 설정
    notification_preferences: NotificationPreferences = Field(default_factory=NotificationPreferences, description="알림 설정")
    
    # UI 설정
    dashboard_layout: str = Field("default", description="대시보드 레이아웃")
    theme: str = Field("light", description="테마")
    language: str = Field("korean", description="언어")
    timezone: str = Field("Asia/Seoul", description="시간대")

    @validator('dashboard_layout')
    def validate_dashboard_layout(cls, v):
        """대시보드 레이아웃 유효성 검사"""
        if v not in ['default', 'compact', 'detailed']:
            raise ValueError('대시보드 레이아웃은 default, compact, detailed 중 하나여야 합니다')
        return v

    @validator('theme')
    def validate_theme(cls, v):
        """테마 유효성 검사"""
        if v not in ['light', 'dark', 'auto']:
            raise ValueError('테마는 light, dark, auto 중 하나여야 합니다')
        return v

    @validator('language')
    def validate_language(cls, v):
        """언어 유효성 검사"""
        if v not in ['korean', 'english']:
            raise ValueError('언어는 korean, english 중 하나여야 합니다')
        return v


class UserSettingsCreate(UserSettingsBase):
    """사용자 설정 생성 스키마"""
    user_id: str = Field(..., description="사용자 ID", min_length=1, max_length=100)


class UserSettingsUpdate(BaseModel):
    """사용자 설정 수정 스키마"""
    user_name: Optional[str] = Field(None, description="사용자명", min_length=1, max_length=100)
    user_email: Optional[str] = Field(None, description="이메일", max_length=255)
    user_phone: Optional[str] = Field(None, description="전화번호", max_length=50)
    user_role: Optional[str] = Field(None, description="역할", max_length=100)
    department: Optional[str] = Field(None, description="부서", max_length=100)
    
    # 알림 설정
    notification_preferences: Optional[NotificationPreferences] = Field(None, description="알림 설정")
    
    # UI 설정
    dashboard_layout: Optional[str] = Field(None, description="대시보드 레이아웃")
    theme: Optional[str] = Field(None, description="테마")
    language: Optional[str] = Field(None, description="언어")
    timezone: Optional[str] = Field(None, description="시간대")


class UserSettingsResponse(UserSettingsBase):
    """사용자 설정 응답 스키마"""
    id: int = Field(..., description="설정 ID")
    user_id: str = Field(..., description="사용자 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


# ===== 설정 변경 이력 스키마 =====

class SettingsHistoryResponse(BaseModel):
    """설정 변경 이력 응답 스키마"""
    id: int = Field(..., description="이력 ID")
    setting_type: str = Field(..., description="설정 타입")
    setting_key: str = Field(..., description="설정 키")
    old_value: Optional[str] = Field(None, description="이전 값")
    new_value: Optional[str] = Field(None, description="새로운 값")
    changed_by: str = Field(..., description="변경자")
    change_reason: Optional[str] = Field(None, description="변경 사유")
    created_at: datetime = Field(..., description="변경일시")

    class Config:
        from_attributes = True


# ===== 통합 설정 스키마 =====

class AllSettingsResponse(BaseModel):
    """전체 설정 응답 스키마"""
    system: Optional[SystemSettingsResponse] = Field(None, description="시스템 설정")
    user: Optional[UserSettingsResponse] = Field(None, description="사용자 설정")


class AllSettingsUpdate(BaseModel):
    """전체 설정 수정 스키마"""
    system: Optional[SystemSettingsUpdate] = Field(None, description="시스템 설정")
    user: Optional[UserSettingsUpdate] = Field(None, description="사용자 설정")