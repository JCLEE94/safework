# 요관리대상자 관리 모델
"""
요관리대상자 관리 시스템 모델
- 유소견자 관리
- 직업병 의심자 관리
- 특별관리 대상자
- 추적관찰 대상자
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date, Float, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from src.config.database import Base


class RiskCategory(str, enum.Enum):
    """위험 분류"""
    OCCUPATIONAL_DISEASE = "직업병의심"  # C1, C2
    GENERAL_DISEASE = "일반질병의심"  # D1, D2
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


class ManagementLevel(str, enum.Enum):
    """관리 수준"""
    OBSERVATION = "관찰"  # 경과 관찰
    INTENSIVE = "집중관리"  # 집중 관리
    MEDICAL_CARE = "의료관리"  # 의료기관 연계
    WORK_RESTRICTION = "작업제한"  # 작업 제한/전환


class InterventionType(str, enum.Enum):
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


class AtRiskEmployee(Base):
    """요관리대상자 기본 정보"""
    __tablename__ = "at_risk_employees"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 등록 정보
    registration_date = Column(Date, nullable=False, default=datetime.utcnow)
    registered_by = Column(String(100))
    
    # 위험 분류
    risk_categories = Column(JSON)  # 복수 선택 가능
    primary_risk_category = Column(SQLEnum(RiskCategory), nullable=False)
    management_level = Column(SQLEnum(ManagementLevel), nullable=False)
    
    # 발견 경로
    detection_source = Column(String(100))  # 건강진단, 작업환경측정, 자발적신고 등
    detection_date = Column(Date)
    related_exam_id = Column(Integer, ForeignKey("health_exams.id"))
    
    # 위험 요인
    risk_factors = Column(JSON)
    """
    {
        "occupational": ["소음", "분진", "화학물질"],
        "personal": ["고혈압", "당뇨", "흡연"],
        "work_conditions": ["야간작업", "중량물취급"]
    }
    """
    
    # 현재 상태
    current_status = Column(String(50), default="active")  # active, resolved, monitoring
    severity_score = Column(Float)  # 1-10 심각도 점수
    
    # 업무 적합성
    work_fitness_status = Column(String(100))
    work_restrictions = Column(JSON)  # 작업 제한 사항
    
    # 목표 및 계획
    management_goals = Column(Text)
    target_improvement_date = Column(Date)
    
    # 종료 정보
    is_active = Column(Boolean, default=True)
    resolution_date = Column(Date)
    resolution_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    worker = relationship("Worker")
    health_exam = relationship("HealthExam")
    management_plans = relationship("RiskManagementPlan", back_populates="at_risk_employee")
    interventions = relationship("RiskIntervention", back_populates="at_risk_employee")
    monitoring_records = relationship("RiskMonitoring", back_populates="at_risk_employee")


class RiskManagementPlan(Base):
    """위험 관리 계획"""
    __tablename__ = "risk_management_plans"
    
    id = Column(Integer, primary_key=True)
    at_risk_employee_id = Column(Integer, ForeignKey("at_risk_employees.id"), nullable=False)
    
    # 계획 정보
    plan_name = Column(String(200), nullable=False)
    plan_period_start = Column(Date, nullable=False)
    plan_period_end = Column(Date, nullable=False)
    
    # 목표
    primary_goal = Column(Text)
    specific_objectives = Column(JSON)  # 구체적 목표 리스트
    
    # 개입 계획
    planned_interventions = Column(JSON)
    """
    [
        {
            "type": "보건상담",
            "frequency": "월 1회",
            "duration": "6개월",
            "provider": "보건관리자"
        }
    ]
    """
    
    # 모니터링 계획
    monitoring_schedule = Column(JSON)
    """
    {
        "health_check": "3개월마다",
        "consultation": "매월",
        "work_environment": "분기별"
    }
    """
    
    # 평가 지표
    success_criteria = Column(JSON)
    evaluation_methods = Column(Text)
    
    # 담당자
    primary_manager = Column(String(100))
    support_team = Column(JSON)  # 지원팀 구성원
    
    # 상태
    status = Column(String(50), default="active")  # active, completed, revised
    
    # 승인
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    at_risk_employee = relationship("AtRiskEmployee", back_populates="management_plans")
    interventions = relationship("RiskIntervention", back_populates="management_plan")


class RiskIntervention(Base):
    """개입 활동 기록"""
    __tablename__ = "risk_interventions"
    
    id = Column(Integer, primary_key=True)
    at_risk_employee_id = Column(Integer, ForeignKey("at_risk_employees.id"), nullable=False)
    management_plan_id = Column(Integer, ForeignKey("risk_management_plans.id"))
    
    # 개입 정보
    intervention_type = Column(SQLEnum(InterventionType), nullable=False)
    intervention_date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer)
    
    # 제공자
    provider_name = Column(String(100))
    provider_role = Column(String(50))  # 보건관리자, 의사, 상담사 등
    
    # 내용
    intervention_content = Column(Text)
    methods_used = Column(JSON)  # 사용된 방법/도구
    materials_provided = Column(JSON)  # 제공된 자료
    
    # 근로자 반응
    worker_response = Column(Text)
    engagement_level = Column(String(50))  # high, medium, low
    
    # 결과
    immediate_outcome = Column(Text)
    issues_identified = Column(JSON)
    
    # 추천사항
    recommendations = Column(Text)
    referrals_made = Column(JSON)
    
    # 후속 조치
    followup_required = Column(Boolean, default=False)
    followup_date = Column(Date)
    followup_notes = Column(Text)
    
    # 첨부파일
    attachments = Column(JSON)  # 파일 경로들
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    at_risk_employee = relationship("AtRiskEmployee", back_populates="interventions")
    management_plan = relationship("RiskManagementPlan", back_populates="interventions")


class RiskMonitoring(Base):
    """정기 모니터링 기록"""
    __tablename__ = "risk_monitoring"
    
    id = Column(Integer, primary_key=True)
    at_risk_employee_id = Column(Integer, ForeignKey("at_risk_employees.id"), nullable=False)
    
    # 모니터링 정보
    monitoring_date = Column(Date, nullable=False)
    monitoring_type = Column(String(100))  # 정기점검, 건강상태확인, 작업관찰 등
    
    # 건강 지표
    health_indicators = Column(JSON)
    """
    {
        "blood_pressure": {"systolic": 130, "diastolic": 85},
        "blood_sugar": 110,
        "hearing_level": {"left": 25, "right": 30},
        "stress_score": 7
    }
    """
    
    # 작업 관련
    work_performance = Column(String(50))  # 정상, 저하, 개선
    work_incidents = Column(Integer, default=0)
    ppe_compliance = Column(String(50))  # 양호, 보통, 미흡
    
    # 증상 및 불편
    reported_symptoms = Column(JSON)
    symptom_severity = Column(Float)  # 1-10
    
    # 생활습관
    lifestyle_factors = Column(JSON)
    """
    {
        "smoking": "금연중",
        "drinking": "주1회",
        "exercise": "주3회",
        "sleep_quality": "보통"
    }
    """
    
    # 개선도 평가
    improvement_status = Column(String(50))  # 개선, 유지, 악화
    goal_achievement = Column(Float)  # 0-100%
    
    # 조치사항
    actions_taken = Column(Text)
    plan_adjustments = Column(Text)
    
    # 다음 모니터링
    next_monitoring_date = Column(Date)
    next_monitoring_focus = Column(Text)
    
    monitored_by = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    at_risk_employee = relationship("AtRiskEmployee", back_populates="monitoring_records")


class RiskEmployeeStatistics(Base):
    """요관리대상자 통계"""
    __tablename__ = "risk_employee_statistics"
    
    id = Column(Integer, primary_key=True)
    
    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer)
    
    # 대상자 수
    total_at_risk = Column(Integer, default=0)
    new_registrations = Column(Integer, default=0)
    resolved_cases = Column(Integer, default=0)
    
    # 카테고리별
    category_breakdown = Column(JSON)
    """
    {
        "occupational_disease": 15,
        "hearing_loss": 8,
        "musculoskeletal": 12
    }
    """
    
    # 관리 수준별
    management_level_breakdown = Column(JSON)
    
    # 개입 통계
    total_interventions = Column(Integer, default=0)
    intervention_types = Column(JSON)
    
    # 성과 지표
    improvement_rate = Column(Float)  # 개선율
    compliance_rate = Column(Float)  # 순응도
    
    # 비용
    total_cost = Column(Float)
    cost_per_employee = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)