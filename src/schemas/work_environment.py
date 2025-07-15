from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class WorkEnvironmentBase(BaseModel):
    measurement_date: datetime = Field(..., description="측정일")
    location: str = Field(..., description="측정위치")
    measurement_type: Literal[
        "소음",
        "분진",
        "화학물질",
        "유기용제",
        "금속",
        "산알칼리",
        "가스",
        "방사선",
        "고온",
        "진동",
        "조도",
        "기타",
    ] = Field(..., description="측정항목")
    measurement_agency: str = Field(..., description="측정기관")

    measured_value: Optional[float] = Field(None, description="측정값")
    measurement_unit: Optional[str] = Field(None, description="측정단위")
    standard_value: Optional[float] = Field(None, description="기준값")
    standard_unit: Optional[str] = Field(None, description="기준단위")

    result: Literal["적합", "부적합", "주의", "측정중"] = Field(
        ..., description="측정결과"
    )
    improvement_measures: Optional[str] = Field(None, description="개선조치")
    re_measurement_required: Optional[str] = Field("N", description="재측정필요")
    re_measurement_date: Optional[datetime] = Field(None, description="재측정일")

    report_number: Optional[str] = Field(None, description="보고서번호")
    report_file_path: Optional[str] = Field(None, description="보고서파일")

    notes: Optional[str] = Field(None, description="비고")


class WorkEnvironmentCreate(WorkEnvironmentBase):
    pass


class WorkEnvironmentUpdate(BaseModel):
    result: Optional[Literal["적합", "부적합", "주의", "측정중"]] = None
    improvement_measures: Optional[str] = None
    re_measurement_required: Optional[str] = None
    re_measurement_date: Optional[datetime] = None
    notes: Optional[str] = None


class WorkEnvironmentResponse(WorkEnvironmentBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WorkerExposureBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    exposure_level: Optional[float] = Field(None, description="노출수준")
    exposure_duration_hours: Optional[float] = Field(None, description="노출시간")
    protection_equipment_used: Optional[str] = Field(None, description="보호구사용")
    health_effect_risk: Optional[str] = Field(None, description="건강영향위험")


class WorkerExposureCreate(WorkerExposureBase):
    work_environment_id: int


class WorkerExposureResponse(WorkerExposureBase):
    id: int
    work_environment_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class WorkEnvironmentWithExposuresResponse(WorkEnvironmentResponse):
    worker_exposures: List[WorkerExposureResponse] = []


class WorkEnvironmentListResponse(BaseModel):
    items: List[WorkEnvironmentResponse]
    total: int
    page: int
    pages: int
    size: int


class WorkEnvironmentStatistics(BaseModel):
    total_measurements: int
    pass_count: int
    fail_count: int
    pending_count: int
    re_measurement_required: int
    by_type: dict
    recent_failures: List[dict]
