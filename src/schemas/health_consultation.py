"""
보건상담 스키마
Health Consultation Schemas
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum

from .base import BaseResponse


class ConsultationType(str, Enum):
    """상담 유형"""
    ROUTINE = "정기상담"
    EMERGENCY = "응급상담" 
    FOLLOW_UP = "사후관리"
    HEALTH_ISSUE = "건강문제"
    OCCUPATIONAL_DISEASE = "직업병관련"


class ConsultationStatus(str, Enum):
    """상담 상태"""
    SCHEDULED = "예정"
    IN_PROGRESS = "진행중"
    COMPLETED = "완료"
    CANCELLED = "취소"
    RESCHEDULED = "재예약"


class HealthIssueCategory(str, Enum):
    """건강 문제 카테고리"""
    RESPIRATORY = "호흡기"
    MUSCULOSKELETAL = "근골격계"
    SKIN = "피부"
    EYE = "눈"
    CARDIOVASCULAR = "심혈관"
    MENTAL = "정신건강"
    DIGESTIVE = "소화기"
    OTHER = "기타"


class HealthConsultationBase(BaseModel):
    """보건상담 기본 스키마"""
    worker_id: int = Field(..., description="근로자 ID")
    consultation_date: datetime = Field(..., description="상담 일시")
    consultation_type: ConsultationType = Field(..., description="상담 유형")
    chief_complaint: str = Field(..., description="주 호소사항")
    consultation_location: str = Field(..., description="상담 장소")
    consultant_name: str = Field(..., description="상담자(보건관리자) 이름")


class HealthConsultationCreate(HealthConsultationBase):
    """보건상담 생성 스키마"""
    symptoms: Optional[str] = Field(None, description="증상 상세")
    work_related_factors: Optional[str] = Field(None, description="작업 관련 요인")
    health_issue_category: Optional[HealthIssueCategory] = Field(None, description="건강 문제 분류")
    vital_signs: Optional[str] = Field(None, description="활력징후 (혈압, 맥박 등)")
    physical_examination: Optional[str] = Field(None, description="신체검사 소견")
    consultation_notes: Optional[str] = Field(None, description="상담 내용")
    recommendations: Optional[str] = Field(None, description="권고사항")
    referral_needed: bool = Field(False, description="의료기관 의뢰 필요 여부")
    referral_hospital: Optional[str] = Field(None, description="의뢰 의료기관")
    follow_up_needed: bool = Field(False, description="추적관찰 필요 여부")
    follow_up_date: Optional[date] = Field(None, description="추적관찰 예정일")
    work_restriction: Optional[str] = Field(None, description="작업 제한사항")
    medication_prescribed: Optional[str] = Field(None, description="처방된 약물")


class HealthConsultationUpdate(BaseModel):
    """보건상담 수정 스키마"""
    consultation_date: Optional[datetime] = None
    consultation_type: Optional[ConsultationType] = None
    chief_complaint: Optional[str] = None
    consultation_location: Optional[str] = None
    consultant_name: Optional[str] = None
    symptoms: Optional[str] = None
    work_related_factors: Optional[str] = None
    health_issue_category: Optional[HealthIssueCategory] = None
    vital_signs: Optional[str] = None
    physical_examination: Optional[str] = None
    consultation_notes: Optional[str] = None
    recommendations: Optional[str] = None
    referral_needed: Optional[bool] = None
    referral_hospital: Optional[str] = None
    follow_up_needed: Optional[bool] = None
    follow_up_date: Optional[date] = None
    work_restriction: Optional[str] = None
    medication_prescribed: Optional[str] = None
    status: Optional[ConsultationStatus] = None


class HealthConsultationResponse(HealthConsultationBase):
    """보건상담 응답 스키마"""
    id: int
    symptoms: Optional[str] = None
    work_related_factors: Optional[str] = None
    health_issue_category: Optional[HealthIssueCategory] = None
    vital_signs: Optional[str] = None
    physical_examination: Optional[str] = None
    consultation_notes: Optional[str] = None
    recommendations: Optional[str] = None
    referral_needed: bool = False
    referral_hospital: Optional[str] = None
    follow_up_needed: bool = False
    follow_up_date: Optional[date] = None
    work_restriction: Optional[str] = None
    medication_prescribed: Optional[str] = None
    status: ConsultationStatus = ConsultationStatus.SCHEDULED
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    
    # 관련 데이터
    worker_name: Optional[str] = None
    worker_department: Optional[str] = None
    worker_position: Optional[str] = None

    class Config:
        from_attributes = True


class HealthConsultationListResponse(BaseResponse):
    """보건상담 목록 응답 스키마"""
    items: List[HealthConsultationResponse]
    total: int
    page: int
    size: int
    pages: int


class ConsultationStatistics(BaseModel):
    """상담 통계 스키마"""
    total_consultations: int = Field(..., description="총 상담 건수")
    by_type: dict = Field(..., description="유형별 상담 건수")
    by_category: dict = Field(..., description="카테고리별 건수")
    by_status: dict = Field(..., description="상태별 건수")
    monthly_trend: List[dict] = Field(..., description="월별 상담 추이")
    referral_rate: float = Field(..., description="의료기관 의뢰율")
    follow_up_rate: float = Field(..., description="추적관찰 비율")
    work_related_percentage: float = Field(..., description="작업 관련 상담 비율")


class ConsultationSchedule(BaseModel):
    """상담 일정 스키마"""
    consultation_id: int
    worker_id: int
    worker_name: str
    consultation_date: datetime
    consultation_type: ConsultationType
    status: ConsultationStatus
    duration_minutes: Optional[int] = Field(None, description="예상 소요시간(분)")
    location: str
    notes: Optional[str] = None


class FollowUpSchedule(BaseModel):
    """추적관찰 일정 스키마"""
    original_consultation_id: int
    worker_id: int
    worker_name: str
    follow_up_date: date
    reason: str
    completed: bool = False
    completion_date: Optional[date] = None
    notes: Optional[str] = None