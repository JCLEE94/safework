"""
근로자 관련 Pydantic 스키마
Worker-related Pydantic schemas
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# Enums - matching database model values
class EmploymentType(str, Enum):
    REGULAR = "regular"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    DAILY = "daily"


class WorkType(str, Enum):
    CONSTRUCTION = "construction"
    ELECTRICAL = "electrical"
    PLUMBING = "plumbing"
    PAINTING = "painting"
    WELDING = "welding"
    DEMOLITION = "demolition"
    EARTH_WORK = "earth_work"
    CONCRETE = "concrete"


class HealthStatus(str, Enum):
    NORMAL = "normal"
    CAUTION = "caution"
    OBSERVATION = "observation"
    TREATMENT = "treatment"


class ConsultationType(str, Enum):
    REGULAR = "정기"
    SPECIAL = "특별"
    REQUEST = "요청"
    FOLLOWUP = "사후관리"


# Base schemas
class GenderType(str, Enum):
    MALE = "male"
    FEMALE = "female"


class WorkerBase(BaseModel):
    name: str = Field(..., description="근로자명")
    employee_id: str = Field(..., description="사번")
    gender: Optional[str] = Field(None, description="성별")
    company_name: str = Field(..., description="업체명")
    work_category: str = Field(..., description="공종")
    department: str = Field(..., description="부서(장비/작업)")
    position: Optional[str] = Field(None, description="직책")
    employment_type: Optional[str] = Field(None, description="고용형태")
    work_type: Optional[str] = Field(None, description="작업분류")
    hire_date: Optional[date] = Field(None, description="입사일")
    birth_date: Optional[date] = Field(None, description="생년월일")
    phone: Optional[str] = Field(None, description="연락처")
    emergency_contact: Optional[str] = Field(None, description="비상연락처")
    emergency_relationship: Optional[str] = Field(None, description="비상연락 관계")
    address: str = Field(..., description="거주지")
    health_status: Optional[str] = Field(None, description="건강상태")
    safety_education_cert: Optional[str] = Field(None, description="건설업 기초안전보건교육 이수증")
    visa_type: Optional[str] = Field(None, description="비자종류")
    visa_cert: Optional[str] = Field(None, description="비자관련 자격증")
    is_active: bool = Field(True, description="재직여부")


class WorkerCreate(WorkerBase):
    """근로자 생성 스키마"""

    pass


class WorkerUpdate(BaseModel):
    """근로자 수정 스키마"""

    name: Optional[str] = None
    gender: Optional[str] = None
    company_name: Optional[str] = None
    work_category: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    employment_type: Optional[str] = None
    work_type: Optional[str] = None
    phone: Optional[str] = None
    emergency_contact: Optional[str] = None
    emergency_relationship: Optional[str] = None
    address: Optional[str] = None
    health_status: Optional[str] = None
    safety_education_cert: Optional[str] = None
    visa_type: Optional[str] = None
    visa_cert: Optional[str] = None
    is_active: Optional[bool] = None


class WorkerResponse(WorkerBase):
    """근로자 응답 스키마"""

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WorkerListResponse(BaseModel):
    """근로자 목록 응답 스키마"""

    items: List[WorkerResponse]
    total: int
    skip: int
    limit: int


# Health Consultation schemas
class HealthConsultationBase(BaseModel):
    consultation_date: date = Field(..., description="상담일자")
    consultation_type: ConsultationType = Field(..., description="상담유형")
    symptoms: Optional[str] = Field(None, description="증상")
    consultation_details: str = Field(..., description="상담내용")
    action_taken: Optional[str] = Field(None, description="조치사항")
    counselor_name: str = Field(..., description="상담자명")


class HealthConsultationCreate(HealthConsultationBase):
    """건강상담 생성 스키마"""

    worker_id: int = Field(..., description="근로자 ID")


class HealthConsultationUpdate(BaseModel):
    """건강상담 수정 스키마"""

    consultation_date: Optional[date] = None
    consultation_type: Optional[ConsultationType] = None
    symptoms: Optional[str] = None
    consultation_details: Optional[str] = None
    action_taken: Optional[str] = None
    counselor_name: Optional[str] = None


class HealthConsultationResponse(HealthConsultationBase):
    """건강상담 응답 스키마"""

    id: int
    worker_id: int
    worker_name: Optional[str] = Field(None, description="근로자명")
    worker_employee_id: Optional[str] = Field(None, description="사번")
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class HealthConsultationListResponse(BaseModel):
    """건강상담 목록 응답 스키마"""

    items: List[HealthConsultationResponse]
    total: int
    skip: int
    limit: int

    # 통계 정보
    statistics: Optional[dict] = Field(None, description="통계 정보")
