from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from src.models.health import ExamType, ExamResult


class VitalSignsBase(BaseModel):
    blood_pressure_systolic: Optional[int] = Field(None, description="수축기 혈압")
    blood_pressure_diastolic: Optional[int] = Field(None, description="이완기 혈압")
    heart_rate: Optional[int] = Field(None, description="심박수")
    respiratory_rate: Optional[int] = Field(None, description="호흡수")
    body_temperature: Optional[float] = Field(None, description="체온")
    height: Optional[float] = Field(None, description="신장(cm)")
    weight: Optional[float] = Field(None, description="체중(kg)")
    bmi: Optional[float] = Field(None, description="체질량지수")
    waist_circumference: Optional[float] = Field(None, description="허리둘레(cm)")
    vision_left: Optional[float] = Field(None, description="시력(좌)")
    vision_right: Optional[float] = Field(None, description="시력(우)")
    hearing_left: Optional[str] = Field(None, description="청력(좌)")
    hearing_right: Optional[str] = Field(None, description="청력(우)")


class VitalSignsCreate(VitalSignsBase):
    exam_id: int


class VitalSignsResponse(VitalSignsBase):
    id: int
    exam_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LabResultBase(BaseModel):
    test_name: str = Field(..., description="검사명")
    test_value: Optional[str] = Field(None, description="검사값")
    test_unit: Optional[str] = Field(None, description="단위")
    reference_range: Optional[str] = Field(None, description="참고치")
    result_status: Optional[str] = Field(None, description="결과상태")
    notes: Optional[str] = Field(None, description="비고")


class LabResultCreate(LabResultBase):
    exam_id: int


class LabResultResponse(LabResultBase):
    id: int
    exam_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HealthExamBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    exam_date: datetime = Field(..., description="검진일")
    exam_type: ExamType = Field(..., description="검진유형")
    exam_result: Optional[ExamResult] = Field(None, description="검진결과")
    exam_agency: str = Field(..., description="검진기관")
    doctor_name: Optional[str] = Field(None, description="검진의사")
    
    overall_opinion: Optional[str] = Field(None, description="종합소견")
    disease_diagnosis: Optional[str] = Field(None, description="질병진단")
    work_fitness: Optional[str] = Field(None, description="업무적합성")
    restrictions: Optional[str] = Field(None, description="업무제한사항")
    followup_required: Optional[str] = Field('N', description="추적검사필요")
    followup_date: Optional[datetime] = Field(None, description="추적검사일")
    
    notes: Optional[str] = Field(None, description="비고")


class HealthExamCreate(HealthExamBase):
    vital_signs: Optional[VitalSignsBase] = None
    lab_results: Optional[List[LabResultBase]] = None


class HealthExamUpdate(BaseModel):
    exam_result: Optional[ExamResult] = None
    overall_opinion: Optional[str] = None
    disease_diagnosis: Optional[str] = None
    work_fitness: Optional[str] = None
    restrictions: Optional[str] = None
    followup_required: Optional[str] = None
    followup_date: Optional[datetime] = None
    notes: Optional[str] = None


class HealthExamResponse(HealthExamBase):
    id: int
    vital_signs: Optional[VitalSignsResponse] = None
    lab_results: List[LabResultResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthExamListResponse(BaseModel):
    items: List[HealthExamResponse]
    total: int
    page: int
    pages: int
    size: int