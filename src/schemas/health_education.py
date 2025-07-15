from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.health_education import (EducationMethod, EducationStatus,
                                         EducationType)


class HealthEducationBase(BaseModel):
    education_date: datetime = Field(..., description="교육일시")
    education_type: EducationType = Field(..., description="교육유형")
    education_title: str = Field(..., description="교육제목")
    education_content: Optional[str] = Field(None, description="교육내용")

    education_method: EducationMethod = Field(..., description="교육방법")
    education_hours: float = Field(..., description="교육시간")
    instructor_name: Optional[str] = Field(None, description="강사명")
    instructor_qualification: Optional[str] = Field(None, description="강사자격")
    education_location: Optional[str] = Field(None, description="교육장소")

    required_by_law: Optional[str] = Field("Y", description="법정필수여부")
    legal_requirement_hours: Optional[float] = Field(None, description="법정교육시간")

    education_material_path: Optional[str] = Field(None, description="교육자료")
    attendance_sheet_path: Optional[str] = Field(None, description="출석부")

    notes: Optional[str] = Field(None, description="비고")


class HealthEducationCreate(HealthEducationBase):
    pass


class HealthEducationUpdate(BaseModel):
    education_content: Optional[str] = None
    instructor_name: Optional[str] = None
    instructor_qualification: Optional[str] = None
    education_material_path: Optional[str] = None
    attendance_sheet_path: Optional[str] = None
    notes: Optional[str] = None


class HealthEducationResponse(HealthEducationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AttendanceBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    status: EducationStatus = Field(..., description="출석상태")
    attendance_hours: Optional[float] = Field(None, description="참석시간")
    test_score: Optional[float] = Field(None, description="테스트점수")
    certificate_number: Optional[str] = Field(None, description="수료증번호")
    certificate_issue_date: Optional[datetime] = Field(None, description="수료증발급일")
    satisfaction_score: Optional[int] = Field(
        None, ge=1, le=5, description="만족도점수"
    )
    feedback_comments: Optional[str] = Field(None, description="피드백")


class AttendanceCreate(AttendanceBase):
    education_id: int


class AttendanceUpdate(BaseModel):
    status: Optional[EducationStatus] = None
    attendance_hours: Optional[float] = None
    test_score: Optional[float] = None
    certificate_number: Optional[str] = None
    certificate_issue_date: Optional[datetime] = None
    satisfaction_score: Optional[int] = None
    feedback_comments: Optional[str] = None


class AttendanceResponse(AttendanceBase):
    id: int
    education_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EducationWithAttendanceResponse(HealthEducationResponse):
    attendances: List[AttendanceResponse] = []
    total_attendees: int = 0
    completed_count: int = 0


class HealthEducationListResponse(BaseModel):
    items: List[HealthEducationResponse]
    total: int
    page: int
    pages: int
    size: int


class EducationStatistics(BaseModel):
    total_sessions: int
    total_hours: float
    total_attendees: int
    by_type: dict
    by_method: dict
    completion_rate: float
    upcoming_sessions: List[dict]
    overdue_trainings: List[dict]
