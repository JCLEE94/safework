# 요관리대상자 관리 스키마
"""
요관리대상자 관리 시스템 Pydantic 스키마
- 유소견자 관리
- 직업병 의심자 관리
- 특별관리 대상자
- 추적관찰 대상자
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class RiskCategory(str, Enum):
    """위험 분류"""
    OCCUPATIONAL_DISEASE = "직업병의심"
    GENERAL_DISEASE = "일반질병의심"
    HEARING_LOSS = "청력이상"
    RESPIRATORY = "호흡기이상"
    MUSCULOSKELETAL = "근골격계이상"
    CARDIOVASCULAR = "심혈관계이상"
    MENTAL_HEALTH = "정신건강이상"
    CHEMICAL_EXPOSURE = "화학물질노출"
    PHYSICAL_HAZARD = "물리적유해인자"
    ERGONOMIC_RISK = "인간공학적위험"
    NIGHT_WORK = "야간작업"
    HIGH_STRESS = "고스트레스"


class ManagementLevel(str, Enum):
    """관리 수준"""
    OBSERVATION = "관찰"
    INTENSIVE = "집중관리"
    MEDICAL_CARE = "의료관리"
    WORK_RESTRICTION = "작업제한"


class InterventionType(str, Enum):
    """개입 유형"""
    HEALTH_CONSULTATION = "보건상담"
    MEDICAL_REFERRAL = "의료기관의뢰"
    WORK_ENVIRONMENT = "작업환경개선"
    PERSONAL_PROTECTION = "개인보호구"
    JOB_ROTATION = "작업전환"
    WORK_RESTRICTION = "작업제한"
    HEALTH_EDUCATION = "보건교육"
    LIFESTYLE_COACHING = "생활습관지도"
    STRESS_MANAGEMENT = "스트레스관리"
    REHABILITATION = "재활프로그램"


# 요관리대상자 스키마
class RiskFactors(BaseModel):
    """위험 요인"""
    occupational: List[str] = Field(default_factory=list, description="직업적 요인")
    personal: List[str] = Field(default_factory=list, description="개인적 요인")
    work_conditions: List[str] = Field(default_factory=list, description="작업 조건")


class AtRiskEmployeeBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    
    risk_categories: List[RiskCategory] = Field(..., description="위험 분류")
    primary_risk_category: RiskCategory = Field(..., description="주요 위험 분류")
    management_level: ManagementLevel = Field(..., description="관리 수준")
    
    detection_source: Optional[str] = Field(None, description="발견 경로")
    detection_date: Optional[date] = None
    related_exam_id: Optional[int] = None
    
    risk_factors: Optional[RiskFactors] = None
    
    severity_score: Optional[float] = Field(None, ge=1, le=10, description="심각도 점수")
    
    work_fitness_status: Optional[str] = None
    work_restrictions: Optional[List[str]] = None
    
    management_goals: Optional[str] = None
    target_improvement_date: Optional[date] = None


class AtRiskEmployeeCreate(AtRiskEmployeeBase):
    registered_by: Optional[str] = None


class AtRiskEmployeeUpdate(BaseModel):
    risk_categories: Optional[List[RiskCategory]] = None
    primary_risk_category: Optional[RiskCategory] = None
    management_level: Optional[ManagementLevel] = None
    
    severity_score: Optional[float] = None
    work_fitness_status: Optional[str] = None
    work_restrictions: Optional[List[str]] = None
    
    management_goals: Optional[str] = None
    target_improvement_date: Optional[date] = None
    
    current_status: Optional[str] = None


class AtRiskEmployeeResponse(AtRiskEmployeeBase):
    id: int
    registration_date: date
    registered_by: Optional[str] = None
    current_status: str
    is_active: bool
    resolution_date: Optional[date] = None
    resolution_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 관리 계획 스키마
class PlannedIntervention(BaseModel):
    """계획된 개입"""
    type: str
    frequency: str
    duration: str
    provider: str


class MonitoringSchedule(BaseModel):
    """모니터링 일정"""
    health_check: Optional[str] = None
    consultation: Optional[str] = None
    work_environment: Optional[str] = None


class RiskManagementPlanBase(BaseModel):
    at_risk_employee_id: int = Field(..., description="요관리대상자 ID")
    
    plan_name: str = Field(..., description="계획명")
    plan_period_start: date = Field(..., description="계획 시작일")
    plan_period_end: date = Field(..., description="계획 종료일")
    
    primary_goal: str = Field(..., description="주요 목표")
    specific_objectives: List[str] = Field(..., description="구체적 목표")
    
    planned_interventions: List[PlannedIntervention] = Field(..., description="계획된 개입")
    monitoring_schedule: MonitoringSchedule = Field(..., description="모니터링 일정")
    
    success_criteria: Optional[List[str]] = None
    evaluation_methods: Optional[str] = None
    
    primary_manager: str = Field(..., description="주 담당자")
    support_team: Optional[List[str]] = None


class RiskManagementPlanCreate(RiskManagementPlanBase):
    pass


class RiskManagementPlanUpdate(BaseModel):
    plan_name: Optional[str] = None
    plan_period_end: Optional[date] = None
    primary_goal: Optional[str] = None
    specific_objectives: Optional[List[str]] = None
    planned_interventions: Optional[List[PlannedIntervention]] = None
    monitoring_schedule: Optional[MonitoringSchedule] = None
    status: Optional[str] = None


class RiskManagementPlanResponse(RiskManagementPlanBase):
    id: int
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 개입 활동 스키마
class RiskInterventionBase(BaseModel):
    at_risk_employee_id: int = Field(..., description="요관리대상자 ID")
    management_plan_id: Optional[int] = None
    
    intervention_type: InterventionType = Field(..., description="개입 유형")
    intervention_date: datetime = Field(..., description="개입 일시")
    duration_minutes: Optional[int] = None
    
    provider_name: str = Field(..., description="제공자 이름")
    provider_role: Optional[str] = None
    
    intervention_content: str = Field(..., description="개입 내용")
    methods_used: Optional[List[str]] = None
    materials_provided: Optional[List[str]] = None
    
    worker_response: Optional[str] = None
    engagement_level: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    
    immediate_outcome: Optional[str] = None
    issues_identified: Optional[List[str]] = None
    
    recommendations: Optional[str] = None
    referrals_made: Optional[List[str]] = None
    
    followup_required: bool = Field(False)
    followup_date: Optional[date] = None
    followup_notes: Optional[str] = None


class RiskInterventionCreate(RiskInterventionBase):
    pass


class RiskInterventionResponse(RiskInterventionBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 모니터링 기록 스키마
class HealthIndicators(BaseModel):
    """건강 지표"""
    blood_pressure: Optional[Dict[str, int]] = None
    blood_sugar: Optional[float] = None
    hearing_level: Optional[Dict[str, int]] = None
    stress_score: Optional[int] = None
    
    # 추가 가능한 지표들
    body_weight: Optional[float] = None
    bmi: Optional[float] = None
    cholesterol: Optional[Dict[str, float]] = None


class LifestyleFactors(BaseModel):
    """생활습관 요인"""
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    exercise: Optional[str] = None
    sleep_quality: Optional[str] = None


class RiskMonitoringBase(BaseModel):
    at_risk_employee_id: int = Field(..., description="요관리대상자 ID")
    
    monitoring_date: date = Field(..., description="모니터링 날짜")
    monitoring_type: str = Field(..., description="모니터링 유형")
    
    health_indicators: Optional[HealthIndicators] = None
    
    work_performance: Optional[str] = Field(None, pattern="^(정상|저하|개선)$")
    work_incidents: int = Field(0, description="작업 중 사고")
    ppe_compliance: Optional[str] = Field(None, pattern="^(양호|보통|미흡)$")
    
    reported_symptoms: Optional[List[str]] = None
    symptom_severity: Optional[float] = Field(None, ge=1, le=10)
    
    lifestyle_factors: Optional[LifestyleFactors] = None
    
    improvement_status: Optional[str] = Field(None, pattern="^(개선|유지|악화)$")
    goal_achievement: Optional[float] = Field(None, ge=0, le=100)
    
    actions_taken: Optional[str] = None
    plan_adjustments: Optional[str] = None
    
    next_monitoring_date: Optional[date] = None
    next_monitoring_focus: Optional[str] = None
    
    monitored_by: str = Field(..., description="모니터링 수행자")


class RiskMonitoringCreate(RiskMonitoringBase):
    pass


class RiskMonitoringResponse(RiskMonitoringBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 통계 스키마
class RiskEmployeeStatisticsBase(BaseModel):
    year: int = Field(..., description="연도")
    month: Optional[int] = None
    
    total_at_risk: int = Field(0)
    new_registrations: int = Field(0)
    resolved_cases: int = Field(0)
    
    category_breakdown: Optional[Dict[str, int]] = None
    management_level_breakdown: Optional[Dict[str, int]] = None
    
    total_interventions: int = Field(0)
    intervention_types: Optional[Dict[str, int]] = None
    
    improvement_rate: Optional[float] = None
    compliance_rate: Optional[float] = None
    
    total_cost: Optional[float] = None
    cost_per_employee: Optional[float] = None


class RiskEmployeeStatisticsResponse(RiskEmployeeStatisticsBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 대시보드 스키마
class AtRiskDashboard(BaseModel):
    """요관리대상자 대시보드"""
    # 현황
    total_active: int
    by_management_level: Dict[str, int]
    by_risk_category: Dict[str, int]
    
    # 이번 달
    new_this_month: int
    resolved_this_month: int
    interventions_this_month: int
    
    # 경고
    overdue_monitoring: List[Dict[str, Any]]
    high_severity_cases: List[Dict[str, Any]]
    pending_followups: List[Dict[str, Any]]
    
    # 성과
    monthly_improvement_rate: float
    average_management_duration: float
    intervention_effectiveness: Dict[str, float]


# 요약 보고서 스키마
class AtRiskEmployeeSummary(BaseModel):
    """개인별 요약"""
    employee: AtRiskEmployeeResponse
    current_plan: Optional[RiskManagementPlanResponse] = None
    recent_interventions: List[RiskInterventionResponse]
    latest_monitoring: Optional[RiskMonitoringResponse] = None
    improvement_trend: str  # 개선중, 정체, 악화
    next_actions: List[Dict[str, Any]]