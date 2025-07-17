# 건강검진 관리 시스템 스키마
"""
건강검진 관리 시스템 Pydantic 스키마
- 건강검진 계획
- 예약 관리 개선
- 차트 관리
- 결과 추적
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class ExamPlanStatus(str, Enum):
    """검진 계획 상태"""
    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ExamCategory(str, Enum):
    """검진 분류"""
    GENERAL_REGULAR = "일반건강진단_정기"
    GENERAL_TEMPORARY = "일반건강진단_임시"
    SPECIAL_REGULAR = "특수건강진단_정기"
    SPECIAL_TEMPORARY = "특수건강진단_임시"
    PRE_PLACEMENT = "배치전건강진단"
    JOB_CHANGE = "직무전환건강진단"
    NIGHT_WORK = "야간작업건강진단"


class ResultDeliveryMethod(str, Enum):
    """결과 전달 방법"""
    DIRECT = "직접수령"
    POSTAL = "우편발송"
    EMAIL = "이메일"
    MOBILE = "모바일"
    COMPANY_BATCH = "회사일괄"


# 건강검진 계획 스키마
class HealthExamPlanBase(BaseModel):
    plan_year: int = Field(..., description="계획 연도")
    plan_name: str = Field(..., description="계획명")
    
    total_workers: int = Field(0, description="전체 근로자 수")
    general_exam_targets: int = Field(0, description="일반검진 대상자")
    special_exam_targets: int = Field(0, description="특수검진 대상자")
    night_work_targets: int = Field(0, description="야간작업 검진 대상자")
    
    plan_start_date: Optional[date] = Field(None, description="계획 시작일")
    plan_end_date: Optional[date] = Field(None, description="계획 종료일")
    
    primary_institution: Optional[str] = Field(None, description="주 검진기관")
    secondary_institutions: Optional[List[str]] = Field(None, description="추가 검진기관")
    
    estimated_budget: Optional[float] = Field(None, description="예상 예산")
    budget_per_person: Optional[float] = Field(None, description="1인당 예산")
    
    harmful_factors: Optional[List[str]] = Field(None, description="대상 유해인자")
    notes: Optional[str] = Field(None, description="비고")


class HealthExamPlanCreate(HealthExamPlanBase):
    pass


class HealthExamPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    plan_status: Optional[ExamPlanStatus] = None
    plan_start_date: Optional[date] = None
    plan_end_date: Optional[date] = None
    primary_institution: Optional[str] = None
    secondary_institutions: Optional[List[str]] = None
    estimated_budget: Optional[float] = None
    notes: Optional[str] = None


class HealthExamPlanResponse(HealthExamPlanBase):
    id: int
    plan_status: ExamPlanStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 검진 대상자 스키마
class HealthExamTargetBase(BaseModel):
    plan_id: int = Field(..., description="검진 계획 ID")
    worker_id: int = Field(..., description="근로자 ID")
    
    exam_categories: List[ExamCategory] = Field(..., description="해당 검진 종류")
    
    general_exam_required: bool = Field(False, description="일반검진 대상")
    general_exam_date: Optional[date] = None
    
    special_exam_required: bool = Field(False, description="특수검진 대상")
    special_exam_harmful_factors: Optional[List[str]] = Field(None, description="노출 유해인자")
    special_exam_date: Optional[date] = None
    
    night_work_exam_required: bool = Field(False, description="야간작업 검진 대상")
    night_work_months: Optional[int] = Field(None, description="야간작업 기간(개월)")
    night_work_exam_date: Optional[date] = None
    
    exam_cycle_months: int = Field(12, description="검진 주기(개월)")
    last_exam_date: Optional[date] = None
    next_exam_due_date: Optional[date] = None
    
    special_notes: Optional[str] = None


class HealthExamTargetCreate(HealthExamTargetBase):
    pass


class HealthExamTargetResponse(HealthExamTargetBase):
    id: int
    reservation_status: Optional[str] = None
    reserved_date: Optional[date] = None
    is_completed: bool
    completed_date: Optional[date] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 검진 일정 스키마
class HealthExamScheduleBase(BaseModel):
    plan_id: int = Field(..., description="검진 계획 ID")
    schedule_date: date = Field(..., description="검진 날짜")
    start_time: Optional[str] = Field(None, description="시작 시간 (HH:MM)")
    end_time: Optional[str] = Field(None, description="종료 시간 (HH:MM)")
    
    institution_name: str = Field(..., description="검진기관명")
    institution_address: Optional[str] = None
    institution_contact: Optional[str] = None
    
    exam_types: List[str] = Field(..., description="가능한 검진 종류")
    
    total_capacity: int = Field(50, description="총 정원")
    group_code: Optional[str] = Field(None, description="그룹 코드")
    
    special_requirements: Optional[str] = Field(None, description="특별 요구사항")


class HealthExamScheduleCreate(HealthExamScheduleBase):
    pass


class HealthExamScheduleResponse(HealthExamScheduleBase):
    id: int
    reserved_count: int
    available_slots: int
    is_active: bool
    is_full: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 검진 예약 스키마
class HealthExamReservationBase(BaseModel):
    schedule_id: int = Field(..., description="일정 ID")
    worker_id: int = Field(..., description="근로자 ID")
    
    reserved_exam_types: List[str] = Field(..., description="예약 검진 종류")
    reserved_time: Optional[str] = Field(None, description="예약 시간")
    estimated_duration: Optional[int] = Field(60, description="예상 소요시간(분)")
    
    fasting_required: bool = Field(True, description="금식 필요 여부")
    special_preparations: Optional[str] = None
    
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    result_delivery_method: Optional[ResultDeliveryMethod] = None
    result_delivery_address: Optional[str] = None


class HealthExamReservationCreate(HealthExamReservationBase):
    pass


class HealthExamReservationUpdate(BaseModel):
    reserved_time: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    result_delivery_method: Optional[ResultDeliveryMethod] = None
    result_delivery_address: Optional[str] = None


class HealthExamReservationResponse(HealthExamReservationBase):
    id: int
    reservation_number: str
    status: str
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    
    reminder_sent: bool
    reminder_sent_at: Optional[datetime] = None
    
    is_cancelled: bool
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 건강검진 차트 스키마
class MedicalHistoryInfo(BaseModel):
    past_diseases: List[str] = Field(default_factory=list)
    current_medications: List[str] = Field(default_factory=list)
    family_history: List[str] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    surgeries: List[str] = Field(default_factory=list)


class LifestyleHabitsInfo(BaseModel):
    smoking: Optional[Dict[str, Any]] = None
    drinking: Optional[Dict[str, Any]] = None
    exercise: Optional[Dict[str, Any]] = None
    sleep: Optional[Dict[str, Any]] = None


class HealthExamChartBase(BaseModel):
    reservation_id: Optional[int] = None
    worker_id: int = Field(..., description="근로자 ID")
    exam_date: date = Field(..., description="검진 날짜")
    exam_type: str = Field(..., description="검진 종류")
    
    medical_history: Optional[MedicalHistoryInfo] = None
    lifestyle_habits: Optional[LifestyleHabitsInfo] = None
    symptoms: Optional[Dict[str, List[str]]] = None
    work_environment: Optional[Dict[str, Any]] = None
    
    special_exam_questionnaire: Optional[Dict[str, Any]] = None
    female_health_info: Optional[Dict[str, Any]] = None
    exam_day_condition: Optional[Dict[str, Any]] = None
    
    doctor_notes: Optional[str] = None
    nurse_notes: Optional[str] = None


class HealthExamChartCreate(HealthExamChartBase):
    pass


class HealthExamChartResponse(HealthExamChartBase):
    id: int
    chart_number: str
    worker_signature: Optional[str] = None
    signed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 검진 결과 스키마
class AbnormalFinding(BaseModel):
    category: str
    item: str
    value: str
    reference: Optional[str] = None
    severity: Optional[str] = None


class HealthGuidance(BaseModel):
    lifestyle: List[str] = Field(default_factory=list)
    medical: List[str] = Field(default_factory=list)
    occupational: List[str] = Field(default_factory=list)


class HealthExamResultBase(BaseModel):
    chart_id: Optional[int] = None
    worker_id: int = Field(..., description="근로자 ID")
    health_exam_id: Optional[int] = None
    
    result_received_date: Optional[date] = None
    result_delivery_method: Optional[str] = None
    
    overall_result: Optional[str] = Field(None, description="종합 판정 (A/B/C/D/R)")
    overall_opinion: Optional[str] = None
    
    exam_summary: Optional[Dict[str, str]] = None
    abnormal_findings: Optional[List[AbnormalFinding]] = None
    
    followup_required: bool = Field(False)
    followup_items: Optional[List[str]] = None
    followup_deadline: Optional[date] = None
    
    work_fitness: Optional[str] = None
    work_restrictions: Optional[List[str]] = None
    
    health_guidance: Optional[HealthGuidance] = None


class HealthExamResultCreate(HealthExamResultBase):
    pass


class HealthExamResultUpdate(BaseModel):
    overall_result: Optional[str] = None
    overall_opinion: Optional[str] = None
    abnormal_findings: Optional[List[AbnormalFinding]] = None
    followup_required: Optional[bool] = None
    followup_items: Optional[List[str]] = None
    followup_deadline: Optional[date] = None
    work_fitness: Optional[str] = None
    work_restrictions: Optional[List[str]] = None
    health_guidance: Optional[HealthGuidance] = None


class HealthExamResultResponse(HealthExamResultBase):
    id: int
    worker_confirmed: bool
    worker_confirmed_at: Optional[datetime] = None
    worker_feedback: Optional[str] = None
    
    company_action_required: bool
    company_actions: Optional[List[str]] = None
    action_completed: bool
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 통계 스키마
class HealthExamStatisticsBase(BaseModel):
    year: int = Field(..., description="연도")
    month: Optional[int] = Field(None, description="월")
    
    total_targets: int = Field(0)
    completed_count: int = Field(0)
    completion_rate: float = Field(0.0)
    
    general_exam_count: int = Field(0)
    special_exam_count: int = Field(0)
    night_work_exam_count: int = Field(0)
    
    result_a_count: int = Field(0)
    result_b_count: int = Field(0)
    result_c_count: int = Field(0)
    result_d_count: int = Field(0)
    result_r_count: int = Field(0)
    
    abnormal_findings_count: int = Field(0)
    followup_required_count: int = Field(0)
    work_restriction_count: int = Field(0)
    
    disease_statistics: Optional[Dict[str, int]] = None
    
    total_cost: Optional[float] = None
    average_cost_per_person: Optional[float] = None


class HealthExamStatisticsResponse(HealthExamStatisticsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 대시보드용 요약 스키마
class HealthExamDashboard(BaseModel):
    """건강검진 대시보드 요약"""
    current_year_plan: Optional[HealthExamPlanResponse] = None
    
    # 진행 현황
    total_targets: int
    completed_count: int
    in_progress_count: int
    pending_count: int
    
    # 이번 달 예정
    this_month_scheduled: int
    next_month_scheduled: int
    
    # 주요 지표
    completion_rate: float
    abnormal_rate: float
    followup_rate: float
    
    # 최근 알림
    overdue_workers: List[Dict[str, Any]]
    upcoming_deadlines: List[Dict[str, Any]]
    pending_results: List[Dict[str, Any]]