# 근골격계질환 및 직무스트레스 평가 스키마
"""
근골격계질환 및 직무스트레스 평가 시스템 Pydantic 스키마
- 근골격계 증상 조사
- 인간공학적 위험요인 평가
- 직무스트레스 평가
- 심리사회적 위험요인 평가
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class BodyPart(str, Enum):
    """신체 부위"""
    NECK = "목"
    SHOULDER_LEFT = "어깨(좌)"
    SHOULDER_RIGHT = "어깨(우)"
    ELBOW_LEFT = "팔꿈치(좌)"
    ELBOW_RIGHT = "팔꿈치(우)"
    WRIST_LEFT = "손목(좌)"
    WRIST_RIGHT = "손목(우)"
    HAND_LEFT = "손(좌)"
    HAND_RIGHT = "손(우)"
    UPPER_BACK = "등(상부)"
    LOWER_BACK = "허리"
    HIP = "엉덩이"
    KNEE_LEFT = "무릎(좌)"
    KNEE_RIGHT = "무릎(우)"
    ANKLE_LEFT = "발목(좌)"
    ANKLE_RIGHT = "발목(우)"
    FOOT_LEFT = "발(좌)"
    FOOT_RIGHT = "발(우)"


class PainLevel(str, Enum):
    """통증 수준"""
    NONE = "없음"
    MILD = "약함"
    MODERATE = "보통"
    SEVERE = "심함"
    VERY_SEVERE = "매우심함"


class AssessmentType(str, Enum):
    """평가 유형"""
    INITIAL = "최초평가"
    PERIODIC = "정기평가"
    FOLLOWUP = "추적평가"
    SPECIAL = "특별평가"


class RiskLevel(str, Enum):
    """위험 수준"""
    LOW = "낮음"
    MEDIUM = "중간"
    HIGH = "높음"
    VERY_HIGH = "매우높음"


# 근골격계 증상 평가 스키마
class SymptomData(BaseModel):
    """증상 데이터"""
    pain_level: PainLevel
    pain_frequency: str = Field(..., description="빈도 (없음, 가끔, 자주, 항상)")
    pain_duration: str = Field(..., description="지속시간 (1일미만, 1일-1주일, 1주일-1개월, 1개월이상)")
    treatment_received: bool = False
    work_impact: str = Field(..., description="업무영향 (없음, 약간 힘듦, 힘듦, 매우 힘듦)")


class WorkCharacteristics(BaseModel):
    """작업 특성"""
    repetitive_motion: bool = False
    heavy_lifting: bool = False
    awkward_posture: bool = False
    vibration_exposure: bool = False
    prolonged_standing: bool = False
    prolonged_sitting: bool = False
    computer_work_hours: Optional[float] = None


class MusculoskeletalAssessmentBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    
    assessment_date: date = Field(..., description="평가일")
    assessment_type: AssessmentType = Field(..., description="평가 유형")
    assessor_name: Optional[str] = None
    
    # 작업 정보
    department: Optional[str] = None
    job_title: Optional[str] = None
    work_years: Optional[float] = None
    work_hours_per_day: Optional[float] = None
    
    # 증상 조사
    symptoms_data: Dict[str, SymptomData] = Field(..., description="부위별 증상")
    
    # 전체적인 상태
    overall_pain_score: float = Field(..., ge=0, le=10)
    most_painful_parts: List[str] = Field(..., description="가장 아픈 부위")
    pain_affecting_work: bool = False
    pain_affecting_daily_life: bool = False
    
    # 작업 특성
    work_characteristics: WorkCharacteristics
    
    # 위험요인 평가
    risk_factors_identified: List[str] = Field(default_factory=list)
    ergonomic_risk_score: Optional[float] = Field(None, ge=0, le=100)
    risk_level: RiskLevel
    
    # 권고사항
    recommendations: Optional[str] = None
    work_improvement_needed: bool = False
    medical_referral_needed: bool = False
    
    # 후속 조치
    followup_required: bool = False
    followup_date: Optional[date] = None


class MusculoskeletalAssessmentCreate(MusculoskeletalAssessmentBase):
    pass


class MusculoskeletalAssessmentUpdate(BaseModel):
    symptoms_data: Optional[Dict[str, SymptomData]] = None
    overall_pain_score: Optional[float] = None
    recommendations: Optional[str] = None
    followup_required: Optional[bool] = None
    followup_date: Optional[date] = None


class MusculoskeletalAssessmentResponse(MusculoskeletalAssessmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 인간공학적 평가 스키마
class PostureAnalysis(BaseModel):
    """자세 분석"""
    neck: Dict[str, Any]
    trunk: Dict[str, Any]
    upper_arm: Dict[str, Any]
    lower_arm: Dict[str, Any]
    wrist: Dict[str, Any]


class LoadAssessment(BaseModel):
    """하중 평가"""
    weight: float = Field(..., description="무게 (kg)")
    frequency: str
    handle_quality: str = Field(..., pattern="^(좋음|보통|나쁨)$")
    coupling: str = Field(..., pattern="^(좋음|보통|나쁨)$")


class EvaluationScores(BaseModel):
    """평가 점수"""
    posture_score: int
    force_score: int
    activity_score: int
    total_score: int
    action_level: int = Field(..., ge=1, le=4)


class ImprovementSuggestion(BaseModel):
    """개선 제안"""
    category: str
    suggestion: str


class ErgonomicEvaluationBase(BaseModel):
    musculoskeletal_assessment_id: Optional[int] = None
    worker_id: int = Field(..., description="근로자 ID")
    
    evaluation_date: date = Field(..., description="평가일")
    evaluator_name: Optional[str] = None
    evaluation_method: str = Field(..., description="평가 방법 (RULA, REBA, OWAS 등)")
    
    # 작업 분석
    task_name: str = Field(..., description="작업명")
    task_description: Optional[str] = None
    task_frequency: Optional[str] = None
    task_duration: Optional[str] = None
    
    # 자세 평가
    posture_analysis: PostureAnalysis
    
    # 하중 평가
    load_assessment: LoadAssessment
    
    # 평가 점수
    evaluation_scores: EvaluationScores
    
    # 위험도 평가
    overall_risk_level: RiskLevel
    immediate_action_required: bool = False
    
    # 개선 방안
    improvement_suggestions: List[ImprovementSuggestion]
    
    # 이미지/비디오
    photo_paths: Optional[List[str]] = None
    video_path: Optional[str] = None


class ErgonomicEvaluationCreate(ErgonomicEvaluationBase):
    pass


class ErgonomicEvaluationResponse(ErgonomicEvaluationBase):
    id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 직무스트레스 평가 스키마
class JobDemandScores(BaseModel):
    """직무요구 점수"""
    time_pressure: int = Field(..., ge=1, le=5)
    workload: int = Field(..., ge=1, le=5)
    responsibility: int = Field(..., ge=1, le=5)
    emotional_demand: int = Field(..., ge=1, le=5)


class JobControlScores(BaseModel):
    """직무자율 점수"""
    decision_authority: int = Field(..., ge=1, le=5)
    skill_discretion: int = Field(..., ge=1, le=5)
    creativity: int = Field(..., ge=1, le=5)


class InterpersonalScores(BaseModel):
    """관계갈등 점수"""
    coworker_support: int = Field(..., ge=1, le=5)
    supervisor_support: int = Field(..., ge=1, le=5)
    conflict_frequency: int = Field(..., ge=1, le=5)


class CopingResources(BaseModel):
    """대처 자원"""
    social_support: str = Field(..., pattern="^(높음|보통|낮음)$")
    self_efficacy: str = Field(..., pattern="^(높음|보통|낮음)$")
    resilience: str = Field(..., pattern="^(높음|보통|낮음)$")
    stress_management_skills: str = Field(..., pattern="^(높음|보통|낮음)$")


class JobStressAssessmentBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    
    assessment_date: date = Field(..., description="평가일")
    assessment_type: AssessmentType = Field(..., description="평가 유형")
    assessment_tool: str = Field(..., description="평가 도구 (KOSS-SF 등)")
    
    # 기본 정보
    age_group: Optional[str] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    education_level: Optional[str] = None
    
    # 직무요구
    job_demand_scores: JobDemandScores
    job_demand_total: float
    
    # 직무자율
    job_control_scores: JobControlScores
    job_control_total: float
    
    # 관계갈등
    interpersonal_scores: InterpersonalScores
    interpersonal_total: float
    
    # 직무불안정
    job_insecurity_scores: Dict[str, int]
    job_insecurity_total: float
    
    # 조직체계
    organizational_scores: Dict[str, int]
    organizational_total: float
    
    # 보상부적절
    reward_scores: Dict[str, int]
    reward_total: float
    
    # 직장문화
    workplace_culture_scores: Dict[str, int]
    workplace_culture_total: float
    
    # 종합 평가
    total_score: float
    stress_level: RiskLevel
    high_risk_factors: List[str] = Field(default_factory=list)
    
    # 추가 평가
    burnout_score: Optional[float] = None
    depression_screening: Optional[str] = None
    anxiety_screening: Optional[str] = None
    
    # 개인 대처 자원
    coping_resources: Optional[CopingResources] = None
    
    # 권고사항
    recommendations: Optional[str] = None
    counseling_needed: bool = False
    stress_management_program: bool = False
    work_environment_improvement: bool = False
    
    # 후속 조치
    followup_required: bool = False
    followup_date: Optional[date] = None
    referral_made: Optional[str] = None


class JobStressAssessmentCreate(JobStressAssessmentBase):
    pass


class JobStressAssessmentUpdate(BaseModel):
    recommendations: Optional[str] = None
    counseling_needed: Optional[bool] = None
    stress_management_program: Optional[bool] = None
    followup_required: Optional[bool] = None
    followup_date: Optional[date] = None


class JobStressAssessmentResponse(JobStressAssessmentBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 스트레스 개입 프로그램 스키마
class SessionRecord(BaseModel):
    """세션 기록"""
    session_number: int
    date: date
    topic: str
    activities: List[str]
    homework: Optional[str] = None
    participant_feedback: Optional[str] = None


class StressInterventionBase(BaseModel):
    job_stress_assessment_id: Optional[int] = None
    worker_id: int = Field(..., description="근로자 ID")
    
    program_name: str = Field(..., description="프로그램명")
    program_type: str = Field(..., description="프로그램 유형")
    start_date: date = Field(..., description="시작일")
    end_date: Optional[date] = None
    
    # 세션 정보
    total_sessions_planned: int
    sessions_completed: int = 0
    attendance_rate: Optional[float] = None
    
    # 내용
    intervention_goals: List[str]
    intervention_methods: List[str]
    
    # 진행 기록
    session_records: Optional[List[SessionRecord]] = None
    
    # 평가
    pre_intervention_scores: Optional[Dict[str, float]] = None
    post_intervention_scores: Optional[Dict[str, float]] = None
    improvement_areas: Optional[List[str]] = None
    
    # 만족도
    participant_satisfaction: Optional[float] = Field(None, ge=1, le=5)
    participant_feedback: Optional[str] = None
    
    # 결과
    outcome_achieved: Optional[bool] = None
    outcome_summary: Optional[str] = None
    
    # 제공자
    provider_name: Optional[str] = None
    provider_qualification: Optional[str] = None


class StressInterventionCreate(StressInterventionBase):
    pass


class StressInterventionUpdate(BaseModel):
    sessions_completed: Optional[int] = None
    attendance_rate: Optional[float] = None
    session_records: Optional[List[SessionRecord]] = None
    post_intervention_scores: Optional[Dict[str, float]] = None
    participant_satisfaction: Optional[float] = None
    participant_feedback: Optional[str] = None
    outcome_achieved: Optional[bool] = None
    outcome_summary: Optional[str] = None


class StressInterventionResponse(StressInterventionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 통계 스키마
class MusculoskeletalStatisticsResponse(BaseModel):
    """근골격계질환 통계"""
    id: int
    year: int
    month: Optional[int] = None
    department: Optional[str] = None
    
    total_assessments: int
    workers_assessed: int
    
    symptom_prevalence: Dict[str, float]
    risk_distribution: Dict[str, float]
    by_work_characteristics: Optional[Dict[str, Any]] = None
    
    intervention_effectiveness: Optional[Dict[str, float]] = None
    improvement_rate: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class JobStressStatisticsResponse(BaseModel):
    """직무스트레스 통계"""
    id: int
    year: int
    month: Optional[int] = None
    department: Optional[str] = None
    
    total_assessments: int
    workers_assessed: int
    
    stress_level_distribution: Dict[str, float]
    factor_averages: Dict[str, float]
    
    high_risk_count: int
    high_risk_factors: Optional[List[str]] = None
    
    intervention_participation: int
    intervention_completion_rate: Optional[float] = None
    stress_reduction_rate: Optional[float] = None
    
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 대시보드 스키마
class MusculoskeletalDashboard(BaseModel):
    """근골격계 대시보드"""
    # 현황
    total_assessments_this_month: int
    high_risk_workers: int
    pending_followups: int
    
    # 증상 분포
    symptom_distribution: Dict[str, int]
    most_common_symptoms: List[Dict[str, Any]]
    
    # 위험도
    risk_level_distribution: Dict[str, int]
    departments_at_risk: List[Dict[str, Any]]
    
    # 개입 효과
    intervention_success_rate: float
    average_pain_reduction: float
    
    # 경고
    urgent_cases: List[Dict[str, Any]]
    overdue_assessments: List[Dict[str, Any]]


class JobStressDashboard(BaseModel):
    """직무스트레스 대시보드"""
    # 현황
    total_assessments_this_month: int
    high_stress_workers: int
    ongoing_interventions: int
    
    # 스트레스 수준
    stress_level_distribution: Dict[str, int]
    average_stress_score: float
    trend_direction: str  # 상승, 하락, 유지
    
    # 주요 요인
    top_stress_factors: List[Dict[str, Any]]
    department_comparison: List[Dict[str, Any]]
    
    # 개입 프로그램
    active_programs: int
    program_participation_rate: float
    program_effectiveness: float
    
    # 경고
    critical_cases: List[Dict[str, Any]]
    program_dropouts: List[Dict[str, Any]]