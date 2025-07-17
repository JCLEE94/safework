# 근골격계질환 및 직무스트레스 평가 모델
"""
근골격계질환 및 직무스트레스 평가 시스템 모델
- 근골격계 증상 조사
- 인간공학적 위험요인 평가
- 직무스트레스 평가
- 심리사회적 위험요인 평가
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date, Float, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class BodyPart(str, enum.Enum):
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


class PainLevel(str, enum.Enum):
    """통증 수준"""
    NONE = "없음"
    MILD = "약함"
    MODERATE = "보통"
    SEVERE = "심함"
    VERY_SEVERE = "매우심함"


class AssessmentType(str, enum.Enum):
    """평가 유형"""
    INITIAL = "최초평가"
    PERIODIC = "정기평가"
    FOLLOWUP = "추적평가"
    SPECIAL = "특별평가"


class RiskLevel(str, enum.Enum):
    """위험 수준"""
    LOW = "낮음"
    MEDIUM = "중간"
    HIGH = "높음"
    VERY_HIGH = "매우높음"


class MusculoskeletalAssessment(Base):
    """근골격계 증상 평가"""
    __tablename__ = "musculoskeletal_assessments"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 평가 정보
    assessment_date = Column(Date, nullable=False)
    assessment_type = Column(SQLEnum(AssessmentType), nullable=False)
    assessor_name = Column(String(100))
    
    # 작업 정보
    department = Column(String(100))
    job_title = Column(String(100))
    work_years = Column(Float)  # 근무 연수
    work_hours_per_day = Column(Float)
    
    # 증상 조사
    symptoms_data = Column(JSON)
    """
    {
        "neck": {
            "pain_level": "moderate",
            "pain_frequency": "자주",
            "pain_duration": "1주일이상",
            "treatment_received": true,
            "work_impact": "약간 힘듦"
        },
        "lower_back": {...}
    }
    """
    
    # 전체적인 상태
    overall_pain_score = Column(Float)  # 0-10
    most_painful_parts = Column(JSON)  # ["허리", "어깨(우)"]
    pain_affecting_work = Column(Boolean, default=False)
    pain_affecting_daily_life = Column(Boolean, default=False)
    
    # 작업 특성
    work_characteristics = Column(JSON)
    """
    {
        "repetitive_motion": true,
        "heavy_lifting": true,
        "awkward_posture": true,
        "vibration_exposure": false,
        "prolonged_standing": true,
        "prolonged_sitting": false,
        "computer_work_hours": 2
    }
    """
    
    # 위험요인 평가
    risk_factors_identified = Column(JSON)
    ergonomic_risk_score = Column(Float)  # 0-100
    risk_level = Column(SQLEnum(RiskLevel))
    
    # 권고사항
    recommendations = Column(Text)
    work_improvement_needed = Column(Boolean, default=False)
    medical_referral_needed = Column(Boolean, default=False)
    
    # 후속 조치
    followup_required = Column(Boolean, default=False)
    followup_date = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    worker = relationship("Worker")
    ergonomic_evaluations = relationship("ErgonomicEvaluation", back_populates="musculoskeletal_assessment")


class ErgonomicEvaluation(Base):
    """인간공학적 작업환경 평가"""
    __tablename__ = "ergonomic_evaluations"
    
    id = Column(Integer, primary_key=True)
    musculoskeletal_assessment_id = Column(Integer, ForeignKey("musculoskeletal_assessments.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 평가 정보
    evaluation_date = Column(Date, nullable=False)
    evaluator_name = Column(String(100))
    evaluation_method = Column(String(100))  # RULA, REBA, OWAS 등
    
    # 작업 분석
    task_name = Column(String(200))
    task_description = Column(Text)
    task_frequency = Column(String(100))
    task_duration = Column(String(100))
    
    # 자세 평가
    posture_analysis = Column(JSON)
    """
    {
        "neck": {"angle": 30, "twist": true, "side_bend": false},
        "trunk": {"angle": 45, "twist": false, "side_bend": true},
        "upper_arm": {"angle": 60, "abduction": true, "shoulder_raised": false},
        "lower_arm": {"angle": 90, "midline_cross": false},
        "wrist": {"angle": 15, "twist": true}
    }
    """
    
    # 하중 평가
    load_assessment = Column(JSON)
    """
    {
        "weight": 15,  # kg
        "frequency": "분당 5회",
        "handle_quality": "보통",
        "coupling": "나쁨"
    }
    """
    
    # 평가 점수
    evaluation_scores = Column(JSON)
    """
    {
        "posture_score": 5,
        "force_score": 3,
        "activity_score": 2,
        "total_score": 10,
        "action_level": 3
    }
    """
    
    # 위험도 평가
    overall_risk_level = Column(SQLEnum(RiskLevel))
    immediate_action_required = Column(Boolean, default=False)
    
    # 개선 방안
    improvement_suggestions = Column(JSON)
    """
    [
        {"category": "작업대 높이", "suggestion": "10cm 상향 조정"},
        {"category": "도구", "suggestion": "인간공학적 핸들 도구로 교체"},
        {"category": "작업방법", "suggestion": "회전 작업 도입"}
    ]
    """
    
    # 이미지/비디오
    photo_paths = Column(JSON)  # 작업 자세 사진
    video_path = Column(String(500))  # 작업 동영상
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    musculoskeletal_assessment = relationship("MusculoskeletalAssessment", back_populates="ergonomic_evaluations")
    worker = relationship("Worker")


class JobStressAssessment(Base):
    """직무스트레스 평가"""
    __tablename__ = "job_stress_assessments"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 평가 정보
    assessment_date = Column(Date, nullable=False)
    assessment_type = Column(SQLEnum(AssessmentType), nullable=False)
    assessment_tool = Column(String(100))  # KOSS-SF, 등
    
    # 기본 정보
    age_group = Column(String(50))
    gender = Column(String(10))
    marital_status = Column(String(50))
    education_level = Column(String(50))
    
    # 직무요구 (Job Demand)
    job_demand_scores = Column(JSON)
    """
    {
        "time_pressure": 4,
        "workload": 3,
        "responsibility": 4,
        "emotional_demand": 2
    }
    """
    job_demand_total = Column(Float)
    
    # 직무자율 (Job Control)
    job_control_scores = Column(JSON)
    """
    {
        "decision_authority": 2,
        "skill_discretion": 3,
        "creativity": 2
    }
    """
    job_control_total = Column(Float)
    
    # 관계갈등 (Interpersonal Conflict)
    interpersonal_scores = Column(JSON)
    """
    {
        "coworker_support": 3,
        "supervisor_support": 2,
        "conflict_frequency": 3
    }
    """
    interpersonal_total = Column(Float)
    
    # 직무불안정 (Job Insecurity)
    job_insecurity_scores = Column(JSON)
    job_insecurity_total = Column(Float)
    
    # 조직체계 (Organizational System)
    organizational_scores = Column(JSON)
    organizational_total = Column(Float)
    
    # 보상부적절 (Lack of Reward)
    reward_scores = Column(JSON)
    reward_total = Column(Float)
    
    # 직장문화 (Workplace Culture)
    workplace_culture_scores = Column(JSON)
    workplace_culture_total = Column(Float)
    
    # 종합 평가
    total_score = Column(Float)
    stress_level = Column(SQLEnum(RiskLevel))
    high_risk_factors = Column(JSON)  # 고위험 요인들
    
    # 추가 평가
    burnout_score = Column(Float)  # 소진 정도
    depression_screening = Column(String(50))  # 우울 선별 결과
    anxiety_screening = Column(String(50))  # 불안 선별 결과
    
    # 개인 대처 자원
    coping_resources = Column(JSON)
    """
    {
        "social_support": "높음",
        "self_efficacy": "보통",
        "resilience": "높음",
        "stress_management_skills": "낮음"
    }
    """
    
    # 권고사항
    recommendations = Column(Text)
    counseling_needed = Column(Boolean, default=False)
    stress_management_program = Column(Boolean, default=False)
    work_environment_improvement = Column(Boolean, default=False)
    
    # 후속 조치
    followup_required = Column(Boolean, default=False)
    followup_date = Column(Date)
    referral_made = Column(String(200))  # 의뢰 기관
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    worker = relationship("Worker")
    interventions = relationship("StressIntervention", back_populates="job_stress_assessment")


class StressIntervention(Base):
    """스트레스 개입 프로그램"""
    __tablename__ = "stress_interventions"
    
    id = Column(Integer, primary_key=True)
    job_stress_assessment_id = Column(Integer, ForeignKey("job_stress_assessments.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 프로그램 정보
    program_name = Column(String(200), nullable=False)
    program_type = Column(String(100))  # 개인상담, 집단프로그램, 조직개입 등
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    
    # 세션 정보
    total_sessions_planned = Column(Integer)
    sessions_completed = Column(Integer, default=0)
    attendance_rate = Column(Float)
    
    # 내용
    intervention_goals = Column(JSON)
    intervention_methods = Column(JSON)
    """
    ["인지행동치료", "이완훈련", "명상", "운동프로그램"]
    """
    
    # 진행 기록
    session_records = Column(JSON)
    """
    [
        {
            "session_number": 1,
            "date": "2024-01-15",
            "topic": "스트레스 이해",
            "activities": ["강의", "토론"],
            "homework": "스트레스 일지 작성",
            "participant_feedback": "도움이 됨"
        }
    ]
    """
    
    # 평가
    pre_intervention_scores = Column(JSON)
    post_intervention_scores = Column(JSON)
    improvement_areas = Column(JSON)
    
    # 만족도
    participant_satisfaction = Column(Float)  # 1-5
    participant_feedback = Column(Text)
    
    # 결과
    outcome_achieved = Column(Boolean)
    outcome_summary = Column(Text)
    
    # 제공자
    provider_name = Column(String(100))
    provider_qualification = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    job_stress_assessment = relationship("JobStressAssessment", back_populates="interventions")
    worker = relationship("Worker")


class MusculoskeletalStatistics(Base):
    """근골격계질환 통계"""
    __tablename__ = "musculoskeletal_statistics"
    
    id = Column(Integer, primary_key=True)
    
    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer)
    department = Column(String(100))
    
    # 평가 통계
    total_assessments = Column(Integer, default=0)
    workers_assessed = Column(Integer, default=0)
    
    # 증상 통계
    symptom_prevalence = Column(JSON)
    """
    {
        "neck": 35,  # %
        "shoulder": 45,
        "lower_back": 60,
        "wrist": 25
    }
    """
    
    # 위험도 분포
    risk_distribution = Column(JSON)
    """
    {
        "low": 30,  # %
        "medium": 45,
        "high": 20,
        "very_high": 5
    }
    """
    
    # 작업 특성별
    by_work_characteristics = Column(JSON)
    
    # 개입 효과
    intervention_effectiveness = Column(JSON)
    improvement_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class JobStressStatistics(Base):
    """직무스트레스 통계"""
    __tablename__ = "job_stress_statistics"
    
    id = Column(Integer, primary_key=True)
    
    # 기간
    year = Column(Integer, nullable=False)
    month = Column(Integer)
    department = Column(String(100))
    
    # 평가 통계
    total_assessments = Column(Integer, default=0)
    workers_assessed = Column(Integer, default=0)
    
    # 스트레스 수준 분포
    stress_level_distribution = Column(JSON)
    """
    {
        "low": 25,  # %
        "medium": 50,
        "high": 20,
        "very_high": 5
    }
    """
    
    # 요인별 평균 점수
    factor_averages = Column(JSON)
    """
    {
        "job_demand": 65.5,
        "job_control": 45.2,
        "interpersonal": 55.8,
        "job_insecurity": 40.3,
        "organizational": 50.7,
        "reward": 48.9,
        "workplace_culture": 52.1
    }
    """
    
    # 고위험군
    high_risk_count = Column(Integer, default=0)
    high_risk_factors = Column(JSON)
    
    # 개입 프로그램
    intervention_participation = Column(Integer, default=0)
    intervention_completion_rate = Column(Float)
    stress_reduction_rate = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)