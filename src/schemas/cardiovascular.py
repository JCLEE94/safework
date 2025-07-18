"""
뇌심혈관계 관리 스키마
Cardiovascular management schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

from src.models.cardiovascular import RiskLevel, MonitoringType, EmergencyResponseStatus


# 뇌심혈관계 위험도 평가 스키마
class CardiovascularRiskAssessmentBase(BaseModel):
    """위험도 평가 기본 스키마"""
    worker_id: str = Field(..., description="근로자 ID")
    age: Optional[int] = Field(None, ge=0, le=100, description="나이")
    gender: Optional[str] = Field(None, description="성별")
    
    # 위험 요인
    smoking: bool = Field(False, description="흡연 여부")
    diabetes: bool = Field(False, description="당뇨병 여부")
    hypertension: bool = Field(False, description="고혈압 여부")
    family_history: bool = Field(False, description="가족력 여부")
    obesity: bool = Field(False, description="비만 여부")
    
    # 측정값
    systolic_bp: Optional[int] = Field(None, ge=70, le=250, description="수축기혈압(mmHg)")
    diastolic_bp: Optional[int] = Field(None, ge=40, le=150, description="이완기혈압(mmHg)")
    cholesterol: Optional[float] = Field(None, ge=100, le=500, description="총콜레스테롤(mg/dL)")
    ldl_cholesterol: Optional[float] = Field(None, ge=50, le=300, description="LDL콜레스테롤(mg/dL)")
    hdl_cholesterol: Optional[float] = Field(None, ge=20, le=100, description="HDL콜레스테롤(mg/dL)")
    triglycerides: Optional[float] = Field(None, ge=50, le=1000, description="중성지방(mg/dL)")
    blood_sugar: Optional[float] = Field(None, ge=50, le=500, description="혈당(mg/dL)")
    bmi: Optional[float] = Field(None, ge=15, le=50, description="체질량지수")
    
    # 권고사항
    recommendations: Optional[List[str]] = Field(None, description="권고사항 목록")
    notes: Optional[str] = Field(None, description="특이사항")
    
    @validator('systolic_bp', 'diastolic_bp')
    def validate_blood_pressure(cls, v, values):
        """혈압 유효성 검증"""
        if v is not None:
            if 'systolic_bp' in values and 'diastolic_bp' in values:
                systolic = values.get('systolic_bp')
                diastolic = values.get('diastolic_bp')
                if systolic and diastolic and systolic <= diastolic:
                    raise ValueError('수축기혈압은 이완기혈압보다 높아야 합니다')
        return v


class CardiovascularRiskAssessmentCreate(CardiovascularRiskAssessmentBase):
    """위험도 평가 생성 스키마"""
    pass


class CardiovascularRiskAssessmentUpdate(BaseModel):
    """위험도 평가 수정 스키마"""
    age: Optional[int] = None
    smoking: Optional[bool] = None
    diabetes: Optional[bool] = None
    hypertension: Optional[bool] = None
    family_history: Optional[bool] = None
    obesity: Optional[bool] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    cholesterol: Optional[float] = None
    ldl_cholesterol: Optional[float] = None
    hdl_cholesterol: Optional[float] = None
    triglycerides: Optional[float] = None
    blood_sugar: Optional[float] = None
    bmi: Optional[float] = None
    recommendations: Optional[List[str]] = None
    notes: Optional[str] = None


class CardiovascularRiskAssessmentResponse(CardiovascularRiskAssessmentBase):
    """위험도 평가 응답 스키마"""
    id: UUID
    assessment_date: datetime
    risk_score: Optional[float] = Field(None, description="위험도 점수")
    risk_level: Optional[RiskLevel] = Field(None, description="위험도 수준")
    ten_year_risk: Optional[float] = Field(None, description="10년 위험도(%)")
    follow_up_date: Optional[datetime] = Field(None, description="재평가 예정일")
    assessed_by: Optional[str] = Field(None, description="평가자")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 모니터링 스키마
class CardiovascularMonitoringBase(BaseModel):
    """모니터링 기본 스키마"""
    worker_id: str = Field(..., description="근로자 ID")
    monitoring_type: MonitoringType = Field(..., description="모니터링 유형")
    scheduled_date: datetime = Field(..., description="예정일시")
    
    # 측정값
    systolic_bp: Optional[int] = Field(None, ge=70, le=250, description="수축기혈압")
    diastolic_bp: Optional[int] = Field(None, ge=40, le=150, description="이완기혈압")
    heart_rate: Optional[int] = Field(None, ge=30, le=220, description="심박수")
    measurement_values: Optional[Dict[str, Any]] = Field(None, description="기타 측정값")
    
    # 결과
    abnormal_findings: Optional[str] = Field(None, description="이상 소견")
    location: Optional[str] = Field(None, description="측정 장소")
    equipment_used: Optional[str] = Field(None, description="사용 장비")
    notes: Optional[str] = Field(None, description="특이사항")


class CardiovascularMonitoringCreate(CardiovascularMonitoringBase):
    """모니터링 생성 스키마"""
    risk_assessment_id: Optional[UUID] = Field(None, description="위험도 평가 ID")


class CardiovascularMonitoringUpdate(BaseModel):
    """모니터링 수정 스키마"""
    actual_date: Optional[datetime] = None
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    measurement_values: Optional[Dict[str, Any]] = None
    is_completed: Optional[bool] = None
    is_normal: Optional[bool] = None
    abnormal_findings: Optional[str] = None
    action_required: Optional[bool] = None
    next_monitoring_date: Optional[datetime] = None
    notes: Optional[str] = None


class CardiovascularMonitoringResponse(CardiovascularMonitoringBase):
    """모니터링 응답 스키마"""
    id: UUID
    risk_assessment_id: Optional[UUID]
    actual_date: Optional[datetime]
    is_completed: bool
    is_normal: Optional[bool]
    action_required: bool
    monitored_by: Optional[str]
    next_monitoring_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 응급상황 대응 스키마
class EmergencyResponseBase(BaseModel):
    """응급상황 대응 기본 스키마"""
    worker_id: str = Field(..., description="근로자 ID")
    incident_location: Optional[str] = Field(None, description="발생장소")
    incident_description: str = Field(..., description="상황 설명")
    
    # 증상 및 징후
    symptoms: Optional[List[str]] = Field(None, description="증상 목록")
    vital_signs: Optional[Dict[str, Any]] = Field(None, description="생체징후")
    consciousness_level: Optional[str] = Field(None, description="의식 수준")
    
    # 대응 조치
    first_aid_provided: bool = Field(False, description="응급처치 시행 여부")
    first_aid_details: Optional[str] = Field(None, description="응급처치 내용")
    emergency_call_made: bool = Field(False, description="응급실 연락 여부")
    hospital_transport: bool = Field(False, description="병원 이송 여부")
    hospital_name: Optional[str] = Field(None, description="이송 병원명")
    
    # 대응팀 정보
    response_team: Optional[List[str]] = Field(None, description="대응팀 구성")
    primary_responder: Optional[str] = Field(None, description="주 대응자")
    response_time: Optional[int] = Field(None, ge=0, description="대응시간(분)")


class EmergencyResponseCreate(EmergencyResponseBase):
    """응급상황 대응 생성 스키마"""
    monitoring_id: Optional[UUID] = Field(None, description="모니터링 ID")


class EmergencyResponseUpdate(BaseModel):
    """응급상황 대응 수정 스키마"""
    incident_description: Optional[str] = None
    symptoms: Optional[List[str]] = None
    vital_signs: Optional[Dict[str, Any]] = None
    first_aid_details: Optional[str] = None
    outcome: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_plan: Optional[str] = None
    lesson_learned: Optional[str] = None
    status: Optional[EmergencyResponseStatus] = None


class EmergencyResponseResponse(EmergencyResponseBase):
    """응급상황 대응 응답 스키마"""
    id: UUID
    monitoring_id: Optional[UUID]
    incident_datetime: datetime
    outcome: Optional[str]
    follow_up_required: bool
    follow_up_plan: Optional[str]
    lesson_learned: Optional[str]
    status: EmergencyResponseStatus
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# 예방 교육 스키마
class PreventionEducationBase(BaseModel):
    """예방 교육 기본 스키마"""
    title: str = Field(..., description="교육명")
    description: Optional[str] = Field(None, description="교육 설명")
    target_audience: Optional[str] = Field(None, description="대상자")
    education_type: Optional[str] = Field(None, description="교육 유형")
    scheduled_date: datetime = Field(..., description="예정일시")
    duration_minutes: Optional[int] = Field(None, ge=10, le=480, description="교육시간(분)")
    location: Optional[str] = Field(None, description="교육장소")
    
    # 교육 내용
    curriculum: Optional[List[str]] = Field(None, description="교육과정")
    materials: Optional[List[str]] = Field(None, description="교육자료 목록")
    learning_objectives: Optional[List[str]] = Field(None, description="학습목표")
    
    # 참석자 관리
    target_participants: Optional[int] = Field(None, ge=1, description="목표 참석자 수")
    instructor: Optional[str] = Field(None, description="강사")
    organizer: Optional[str] = Field(None, description="주관자")


class PreventionEducationCreate(PreventionEducationBase):
    """예방 교육 생성 스키마"""
    pass


class PreventionEducationUpdate(BaseModel):
    """예방 교육 수정 스키마"""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    location: Optional[str] = None
    curriculum: Optional[List[str]] = None
    materials: Optional[List[str]] = None
    actual_participants: Optional[int] = None
    participant_list: Optional[List[str]] = None
    evaluation_results: Optional[Dict[str, Any]] = None
    participant_feedback: Optional[List[str]] = None
    effectiveness_score: Optional[float] = None
    is_completed: Optional[bool] = None


class PreventionEducationResponse(PreventionEducationBase):
    """예방 교육 응답 스키마"""
    id: UUID
    actual_participants: Optional[int]
    participant_list: Optional[List[str]]
    evaluation_method: Optional[str]
    evaluation_results: Optional[Dict[str, Any]]
    participant_feedback: Optional[List[str]]
    effectiveness_score: Optional[float]
    is_completed: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 통계 스키마
class CardiovascularStatistics(BaseModel):
    """뇌심혈관계 관리 통계"""
    total_assessments: int = Field(0, description="총 평가 건수")
    high_risk_count: int = Field(0, description="고위험군 수")
    moderate_risk_count: int = Field(0, description="중위험군 수")
    low_risk_count: int = Field(0, description="저위험군 수")
    
    # 모니터링 통계
    active_monitoring: int = Field(0, description="진행 중인 모니터링")
    overdue_monitoring: int = Field(0, description="지연된 모니터링")
    completed_this_month: int = Field(0, description="이달 완료된 모니터링")
    
    # 응급상황 통계
    emergency_cases_this_month: int = Field(0, description="이달 응급상황 건수")
    emergency_response_time_avg: Optional[float] = Field(None, description="평균 대응시간(분)")
    
    # 교육 통계
    scheduled_education: int = Field(0, description="예정된 교육")
    completed_education: int = Field(0, description="완료된 교육")
    education_effectiveness_avg: Optional[float] = Field(None, description="평균 교육 효과성")
    
    # 위험도별 통계
    by_risk_level: Dict[str, int] = Field(default_factory=dict, description="위험도별 분포")
    by_age_group: Dict[str, int] = Field(default_factory=dict, description="연령대별 분포")
    by_gender: Dict[str, int] = Field(default_factory=dict, description="성별 분포")
    
    # 월별 추이
    monthly_trend: Dict[str, int] = Field(default_factory=dict, description="월별 추이")


# 위험도 계산 요청 스키마
class RiskCalculationRequest(BaseModel):
    """위험도 계산 요청"""
    age: int = Field(..., ge=20, le=80)
    gender: str = Field(..., description="성별 (male/female)")
    systolic_bp: int = Field(..., ge=90, le=200)
    cholesterol: float = Field(..., ge=150, le=300)
    smoking: bool = Field(False)
    diabetes: bool = Field(False)
    hypertension: bool = Field(False)


class RiskCalculationResponse(BaseModel):
    """위험도 계산 응답"""
    risk_score: float = Field(..., description="위험도 점수")
    risk_level: str = Field(..., description="위험도 수준")  # Changed to str for Korean values
    ten_year_risk: float = Field(..., description="10년 위험도(%)")
    recommendations: List[str] = Field(..., description="권고사항")
    next_assessment_months: int = Field(..., description="다음 평가까지 개월 수")