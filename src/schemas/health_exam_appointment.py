"""
건강진단 예약 관리 스키마
Health Exam Appointment Management Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import date, datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    """예약 상태"""
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"


class NotificationType(str, Enum):
    """알림 유형"""
    SMS = "sms"
    EMAIL = "email"
    KAKAO = "kakao"
    APP_PUSH = "app_push"


class HealthExamAppointmentBase(BaseModel):
    """예약 기본 정보"""
    worker_id: int
    exam_type: str = Field(..., description="검진 유형: 일반건강진단, 특수건강진단, 배치전건강진단")
    scheduled_date: date
    scheduled_time: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    medical_institution: str
    institution_address: Optional[str] = None
    institution_phone: Optional[str] = None
    
    reminder_days_before: int = Field(3, ge=0, le=30)
    notification_methods: List[NotificationType] = []
    
    special_instructions: Optional[str] = None
    exam_items: Optional[List[str]] = []
    estimated_duration: Optional[int] = Field(None, ge=0, description="예상 소요시간(분)")


class HealthExamAppointmentCreate(HealthExamAppointmentBase):
    """예약 생성"""
    pass


class HealthExamAppointmentUpdate(BaseModel):
    """예약 수정"""
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = Field(None, regex="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
    medical_institution: Optional[str] = None
    institution_address: Optional[str] = None
    institution_phone: Optional[str] = None
    
    reminder_days_before: Optional[int] = Field(None, ge=0, le=30)
    notification_methods: Optional[List[NotificationType]] = None
    
    special_instructions: Optional[str] = None
    exam_items: Optional[List[str]] = None
    estimated_duration: Optional[int] = Field(None, ge=0)


class HealthExamAppointmentStatusUpdate(BaseModel):
    """예약 상태 변경"""
    status: AppointmentStatus
    reason: Optional[str] = None


class HealthExamAppointmentResponse(HealthExamAppointmentBase):
    """예약 응답"""
    id: int
    status: AppointmentStatus
    confirmed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    reminder_sent: bool = False
    reminder_sent_at: Optional[datetime] = None
    
    previous_appointment_id: Optional[int] = None
    
    created_at: datetime
    updated_at: datetime
    
    # Worker info
    worker_name: Optional[str] = None
    worker_employee_number: Optional[str] = None
    
    class Config:
        from_attributes = True


class AppointmentListResponse(BaseModel):
    """예약 목록 응답"""
    total: int
    items: List[HealthExamAppointmentResponse]


class AppointmentReminderRequest(BaseModel):
    """예약 알림 요청"""
    appointment_ids: Optional[List[int]] = None
    days_before: Optional[int] = Field(None, ge=0, le=30)
    force_send: bool = Field(False, description="이미 발송된 알림도 재발송")


class AppointmentStatistics(BaseModel):
    """예약 통계"""
    total_scheduled: int
    total_confirmed: int
    total_completed: int
    total_cancelled: int
    total_no_show: int
    
    upcoming_7_days: int
    upcoming_30_days: int
    overdue: int
    
    completion_rate: float
    no_show_rate: float
    
    by_exam_type: dict
    by_institution: dict


class BulkAppointmentCreate(BaseModel):
    """대량 예약 생성"""
    worker_ids: List[int]
    exam_type: str
    scheduled_date: date
    medical_institution: str
    institution_address: Optional[str] = None
    institution_phone: Optional[str] = None
    
    time_slots: List[str] = Field(..., description="예약 가능 시간대 목록")
    workers_per_slot: int = Field(1, ge=1, description="시간대별 인원수")
    
    notification_methods: List[NotificationType] = []
    special_instructions: Optional[str] = None