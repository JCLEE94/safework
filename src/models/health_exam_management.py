# 건강검진 관리 시스템 확장 모델
"""
건강검진 관리 시스템 확장 모델
- 건강검진 계획
- 예약 관리 개선
- 차트 관리
- 결과 추적
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Date, Float, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class ExamPlanStatus(str, enum.Enum):
    """검진 계획 상태"""
    DRAFT = "draft"  # 계획 수립중
    APPROVED = "approved"  # 승인됨
    IN_PROGRESS = "in_progress"  # 진행중
    COMPLETED = "completed"  # 완료
    CANCELLED = "cancelled"  # 취소


class ExamCategory(str, enum.Enum):
    """검진 분류"""
    GENERAL_REGULAR = "일반건강진단_정기"
    GENERAL_TEMPORARY = "일반건강진단_임시"
    SPECIAL_REGULAR = "특수건강진단_정기"
    SPECIAL_TEMPORARY = "특수건강진단_임시"
    PRE_PLACEMENT = "배치전건강진단"
    JOB_CHANGE = "직무전환건강진단"
    NIGHT_WORK = "야간작업건강진단"


class ResultDeliveryMethod(str, enum.Enum):
    """결과 전달 방법"""
    DIRECT = "직접수령"
    POSTAL = "우편발송"
    EMAIL = "이메일"
    MOBILE = "모바일"
    COMPANY_BATCH = "회사일괄"


class HealthExamPlan(Base):
    """건강검진 계획"""
    __tablename__ = "health_exam_plans"
    
    id = Column(Integer, primary_key=True)
    
    # 계획 기본 정보
    plan_year = Column(Integer, nullable=False)
    plan_name = Column(String(200), nullable=False)
    plan_status = Column(SQLEnum(ExamPlanStatus), default=ExamPlanStatus.DRAFT)
    
    # 대상자 정보
    total_workers = Column(Integer, default=0)
    general_exam_targets = Column(Integer, default=0)
    special_exam_targets = Column(Integer, default=0)
    night_work_targets = Column(Integer, default=0)
    
    # 일정 정보
    plan_start_date = Column(Date)
    plan_end_date = Column(Date)
    
    # 검진기관
    primary_institution = Column(String(200))
    secondary_institutions = Column(JSON)  # 추가 검진기관 목록
    
    # 예산
    estimated_budget = Column(Float)
    budget_per_person = Column(Float)
    
    # 특수검진 유해인자
    harmful_factors = Column(JSON)  # 대상 유해인자 목록
    
    # 승인 정보
    approved_by = Column(String(100))
    approved_at = Column(DateTime)
    
    # 비고
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    target_workers = relationship("HealthExamTarget", back_populates="exam_plan")
    schedules = relationship("HealthExamSchedule", back_populates="exam_plan")


class HealthExamTarget(Base):
    """건강검진 대상자"""
    __tablename__ = "health_exam_targets"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("health_exam_plans.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 검진 구분
    exam_categories = Column(JSON)  # 해당되는 검진 종류들
    
    # 일반검진
    general_exam_required = Column(Boolean, default=False)
    general_exam_date = Column(Date)
    
    # 특수검진
    special_exam_required = Column(Boolean, default=False)
    special_exam_harmful_factors = Column(JSON)  # 노출 유해인자
    special_exam_date = Column(Date)
    
    # 야간작업
    night_work_exam_required = Column(Boolean, default=False)
    night_work_months = Column(Integer)  # 야간작업 기간(개월)
    night_work_exam_date = Column(Date)
    
    # 검진 주기
    exam_cycle_months = Column(Integer, default=12)  # 검진 주기(개월)
    last_exam_date = Column(Date)
    next_exam_due_date = Column(Date)
    
    # 예약 상태
    reservation_status = Column(String(50))
    reserved_date = Column(Date)
    
    # 완료 여부
    is_completed = Column(Boolean, default=False)
    completed_date = Column(Date)
    
    # 비고
    special_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    exam_plan = relationship("HealthExamPlan", back_populates="target_workers")
    worker = relationship("Worker")


class HealthExamSchedule(Base):
    """건강검진 일정표"""
    __tablename__ = "health_exam_schedules"
    
    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("health_exam_plans.id"), nullable=False)
    
    # 일정 정보
    schedule_date = Column(Date, nullable=False)
    start_time = Column(String(10))  # HH:MM
    end_time = Column(String(10))
    
    # 검진기관
    institution_name = Column(String(200), nullable=False)
    institution_address = Column(Text)
    institution_contact = Column(String(50))
    
    # 검진 종류
    exam_types = Column(JSON)  # 가능한 검진 종류들
    
    # 정원
    total_capacity = Column(Integer, default=50)
    reserved_count = Column(Integer, default=0)
    available_slots = Column(Integer, default=50)
    
    # 그룹 예약
    group_code = Column(String(50))  # 부서/팀별 그룹 코드
    
    # 상태
    is_active = Column(Boolean, default=True)
    is_full = Column(Boolean, default=False)
    
    # 특이사항
    special_requirements = Column(Text)  # 금식, 준비사항 등
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    exam_plan = relationship("HealthExamPlan", back_populates="schedules")
    reservations = relationship("HealthExamReservation", back_populates="schedule")


class HealthExamReservation(Base):
    """건강검진 예약 (기존 appointment 개선)"""
    __tablename__ = "health_exam_reservations"
    
    id = Column(Integer, primary_key=True)
    schedule_id = Column(Integer, ForeignKey("health_exam_schedules.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 예약 정보
    reservation_number = Column(String(50), unique=True)  # 예약번호
    reserved_exam_types = Column(JSON)  # 예약한 검진 종류
    
    # 시간
    reserved_time = Column(String(10))  # 구체적 예약 시간
    estimated_duration = Column(Integer)  # 예상 소요시간(분)
    
    # 상태
    status = Column(String(50), default="reserved")
    check_in_time = Column(DateTime)
    check_out_time = Column(DateTime)
    
    # 사전 정보
    fasting_required = Column(Boolean, default=True)
    special_preparations = Column(Text)
    
    # 연락처 (예약 확인용)
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # 결과 수령
    result_delivery_method = Column(SQLEnum(ResultDeliveryMethod))
    result_delivery_address = Column(Text)
    
    # 알림
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    
    # 취소/변경
    is_cancelled = Column(Boolean, default=False)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    schedule = relationship("HealthExamSchedule", back_populates="reservations")
    worker = relationship("Worker")
    charts = relationship("HealthExamChart", back_populates="reservation")


class HealthExamChart(Base):
    """건강검진 차트 (문진표)"""
    __tablename__ = "health_exam_charts"
    
    id = Column(Integer, primary_key=True)
    reservation_id = Column(Integer, ForeignKey("health_exam_reservations.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    exam_date = Column(Date, nullable=False)
    
    # 기본 정보
    chart_number = Column(String(50), unique=True)
    exam_type = Column(String(50))
    
    # 문진 정보 (JSON으로 유연하게 저장)
    medical_history = Column(JSON)
    """
    {
        "past_diseases": ["고혈압", "당뇨"],
        "current_medications": ["혈압약"],
        "family_history": ["암", "심장질환"],
        "allergies": ["페니실린"],
        "surgeries": ["맹장수술 2020년"]
    }
    """
    
    lifestyle_habits = Column(JSON)
    """
    {
        "smoking": {"status": "current", "amount": "10개비/일", "years": 5},
        "drinking": {"frequency": "주2-3회", "amount": "소주1병"},
        "exercise": {"frequency": "주1회", "type": "걷기"},
        "sleep": {"hours": 6, "quality": "보통"}
    }
    """
    
    symptoms = Column(JSON)
    """
    {
        "general": ["피로감", "두통"],
        "respiratory": ["기침", "가래"],
        "cardiovascular": [],
        "musculoskeletal": ["요통"],
        "neurological": []
    }
    """
    
    work_environment = Column(JSON)
    """
    {
        "harmful_factors": ["소음", "분진"],
        "ppe_usage": {"귀마개": "항상", "방진마스크": "가끔"},
        "work_hours": {"day": 8, "overtime": 2},
        "shift_work": false
    }
    """
    
    # 특수검진 추가 문진
    special_exam_questionnaire = Column(JSON)
    
    # 여성 근로자 추가 문진
    female_health_info = Column(JSON)
    
    # 검진 당일 상태
    exam_day_condition = Column(JSON)
    """
    {
        "fasting": true,
        "last_meal_time": "전날 20:00",
        "current_symptoms": [],
        "medications_today": false
    }
    """
    
    # 서명
    worker_signature = Column(Text)  # Base64 encoded signature
    signed_at = Column(DateTime)
    
    # 검진의 소견
    doctor_notes = Column(Text)
    nurse_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    reservation = relationship("HealthExamReservation", back_populates="charts")
    worker = relationship("Worker")
    results = relationship("HealthExamResult", back_populates="chart")


class HealthExamResult(Base):
    """건강검진 결과 통합 관리"""
    __tablename__ = "health_exam_results"
    
    id = Column(Integer, primary_key=True)
    chart_id = Column(Integer, ForeignKey("health_exam_charts.id"))
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    health_exam_id = Column(Integer, ForeignKey("health_exams.id"))  # 기존 시스템 연동
    
    # 결과 수령
    result_received_date = Column(Date)
    result_delivery_method = Column(String(50))
    
    # 종합 판정
    overall_result = Column(String(50))  # A, B, C, D, R
    overall_opinion = Column(Text)
    
    # 검사별 결과 요약
    exam_summary = Column(JSON)
    """
    {
        "physical": "정상",
        "vision": "교정시력 정상",
        "hearing": "정상",
        "blood": "경계",
        "urine": "정상",
        "chest_xray": "정상",
        "special_exams": {...}
    }
    """
    
    # 이상 소견
    abnormal_findings = Column(JSON)
    """
    [
        {
            "category": "혈액검사",
            "item": "공복혈당",
            "value": "110",
            "reference": "70-100",
            "severity": "경계"
        }
    ]
    """
    
    # 사후관리
    followup_required = Column(Boolean, default=False)
    followup_items = Column(JSON)  # 추적검사 항목
    followup_deadline = Column(Date)
    
    # 업무 적합성
    work_fitness = Column(String(100))
    work_restrictions = Column(JSON)
    
    # 보건지도
    health_guidance = Column(JSON)
    """
    {
        "lifestyle": ["금연 권고", "체중 감량"],
        "medical": ["혈압 관리 필요"],
        "occupational": ["청력 보호구 착용 철저"]
    }
    """
    
    # 근로자 확인
    worker_confirmed = Column(Boolean, default=False)
    worker_confirmed_at = Column(DateTime)
    worker_feedback = Column(Text)
    
    # 회사 조치
    company_action_required = Column(Boolean, default=False)
    company_actions = Column(JSON)
    action_completed = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    chart = relationship("HealthExamChart", back_populates="results")
    worker = relationship("Worker")
    health_exam = relationship("HealthExam")


class HealthExamStatistics(Base):
    """건강검진 통계 (집계 테이블)"""
    __tablename__ = "health_exam_statistics"
    
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer)
    
    # 대상자 통계
    total_targets = Column(Integer, default=0)
    completed_count = Column(Integer, default=0)
    completion_rate = Column(Float, default=0.0)
    
    # 검진 종류별
    general_exam_count = Column(Integer, default=0)
    special_exam_count = Column(Integer, default=0)
    night_work_exam_count = Column(Integer, default=0)
    
    # 판정 결과
    result_a_count = Column(Integer, default=0)
    result_b_count = Column(Integer, default=0)
    result_c_count = Column(Integer, default=0)
    result_d_count = Column(Integer, default=0)
    result_r_count = Column(Integer, default=0)
    
    # 유소견자
    abnormal_findings_count = Column(Integer, default=0)
    followup_required_count = Column(Integer, default=0)
    work_restriction_count = Column(Integer, default=0)
    
    # 주요 질환
    disease_statistics = Column(JSON)
    """
    {
        "hypertension": 15,
        "diabetes": 8,
        "dyslipidemia": 12,
        "hearing_loss": 3
    }
    """
    
    # 비용
    total_cost = Column(Float)
    average_cost_per_person = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)