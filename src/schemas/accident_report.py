from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.accident_report import (AccidentSeverity, AccidentType,
                                        InjuryType, InvestigationStatus)


class AccidentReportBase(BaseModel):
    accident_datetime: datetime = Field(..., description="사고발생일시")
    report_datetime: datetime = Field(..., description="신고일시")
    accident_location: str = Field(..., description="사고장소")
    worker_id: int = Field(..., description="근로자ID")

    accident_type: AccidentType = Field(..., description="사고유형")
    injury_type: InjuryType = Field(..., description="부상유형")
    severity: AccidentSeverity = Field(..., description="중대성")

    accident_description: str = Field(..., description="사고경위")
    immediate_cause: Optional[str] = Field(None, description="직접원인")
    root_cause: Optional[str] = Field(None, description="근본원인")

    injured_body_part: Optional[str] = Field(None, description="부상부위")
    treatment_type: Optional[str] = Field(None, description="치료유형")
    hospital_name: Optional[str] = Field(None, description="병원명")
    doctor_name: Optional[str] = Field(None, description="담당의사")

    work_days_lost: Optional[int] = Field(0, description="휴업일수")
    return_to_work_date: Optional[date] = Field(None, description="복귀예정일")
    permanent_disability: Optional[str] = Field("N", description="영구장애여부")
    disability_rate: Optional[float] = Field(None, description="장애율")

    investigation_status: Optional[InvestigationStatus] = Field(
        InvestigationStatus.REPORTED, description="조사상태"
    )
    investigator_name: Optional[str] = Field(None, description="조사자")
    investigation_date: Optional[date] = Field(None, description="조사일")

    immediate_actions: Optional[str] = Field(None, description="즉시조치")
    corrective_actions: Optional[str] = Field(None, description="시정조치")
    preventive_measures: Optional[str] = Field(None, description="예방대책")
    action_completion_date: Optional[date] = Field(None, description="조치완료일")

    reported_to_authorities: Optional[str] = Field("N", description="당국신고여부")
    authority_report_date: Optional[datetime] = Field(None, description="당국신고일")
    authority_report_number: Optional[str] = Field(None, description="신고번호")

    accident_photo_paths: Optional[str] = Field(None, description="사고사진")
    investigation_report_path: Optional[str] = Field(None, description="조사보고서")
    medical_certificate_path: Optional[str] = Field(None, description="진단서")

    witness_names: Optional[str] = Field(None, description="목격자")
    witness_statements: Optional[str] = Field(None, description="목격자진술")

    medical_cost: Optional[float] = Field(0, description="의료비")
    compensation_cost: Optional[float] = Field(0, description="보상금")
    other_cost: Optional[float] = Field(0, description="기타비용")

    notes: Optional[str] = Field(None, description="비고")


class AccidentReportCreate(AccidentReportBase):
    pass


class AccidentReportUpdate(BaseModel):
    investigation_status: Optional[InvestigationStatus] = None
    investigator_name: Optional[str] = None
    investigation_date: Optional[date] = None
    immediate_actions: Optional[str] = None
    corrective_actions: Optional[str] = None
    preventive_measures: Optional[str] = None
    action_completion_date: Optional[date] = None
    work_days_lost: Optional[int] = None
    return_to_work_date: Optional[date] = None
    medical_cost: Optional[float] = None
    compensation_cost: Optional[float] = None
    notes: Optional[str] = None


class AccidentReportResponse(AccidentReportBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AccidentReportListResponse(BaseModel):
    items: List[AccidentReportResponse]
    total: int
    page: int
    pages: int
    size: int


class AccidentStatistics(BaseModel):
    total_accidents: int
    total_work_days_lost: int
    total_cost: float
    by_type: dict
    by_severity: dict
    by_month: dict
    investigation_pending: int
    actions_pending: int
    recent_accidents: List[dict]
