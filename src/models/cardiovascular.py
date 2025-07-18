"""
뇌심혈관계 관리 모델
Cardiovascular management models
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from src.config.database import Base


class RiskLevel(str, enum.Enum):
    """위험도 수준"""
    LOW = "낮음"
    MODERATE = "보통"
    HIGH = "높음"
    VERY_HIGH = "매우높음"


class MonitoringType(str, enum.Enum):
    """모니터링 유형"""
    BLOOD_PRESSURE = "혈압측정"
    HEART_RATE = "심박수"
    ECG = "심전도"
    BLOOD_TEST = "혈액검사"
    STRESS_TEST = "스트레스검사"
    CONSULTATION = "상담"


class EmergencyResponseStatus(str, enum.Enum):
    """응급상황 대응 상태"""
    STANDBY = "대기"
    ACTIVATED = "활성화"
    IN_PROGRESS = "진행중"
    COMPLETED = "완료"
    CANCELLED = "취소"


class CardiovascularRiskAssessment(Base):
    """뇌심혈관계 위험도 평가"""
    __tablename__ = "cardiovascular_risk_assessments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    worker_id = Column(String(50), nullable=False, comment="근로자 ID")
    assessment_date = Column(DateTime, default=datetime.now, comment="평가일시")
    
    # 기본 정보
    age = Column(Integer, comment="나이")
    gender = Column(String(10), comment="성별")
    
    # 위험 요인
    smoking = Column(Boolean, default=False, comment="흡연 여부")
    diabetes = Column(Boolean, default=False, comment="당뇨병 여부")
    hypertension = Column(Boolean, default=False, comment="고혈압 여부")
    family_history = Column(Boolean, default=False, comment="가족력 여부")
    obesity = Column(Boolean, default=False, comment="비만 여부")
    
    # 측정값
    systolic_bp = Column(Integer, comment="수축기혈압(mmHg)")
    diastolic_bp = Column(Integer, comment="이완기혈압(mmHg)")
    cholesterol = Column(Float, comment="총콜레스테롤(mg/dL)")
    ldl_cholesterol = Column(Float, comment="LDL콜레스테롤(mg/dL)")
    hdl_cholesterol = Column(Float, comment="HDL콜레스테롤(mg/dL)")
    triglycerides = Column(Float, comment="중성지방(mg/dL)")
    blood_sugar = Column(Float, comment="혈당(mg/dL)")
    bmi = Column(Float, comment="체질량지수")
    
    # 위험도 평가
    risk_score = Column(Float, comment="위험도 점수")
    risk_level = Column(String(20), comment="위험도 수준")  # Changed from Enum to String for Korean values
    ten_year_risk = Column(Float, comment="10년 위험도(%)")
    
    # 권고사항
    recommendations = Column(JSON, comment="권고사항 목록")
    follow_up_date = Column(DateTime, comment="재평가 예정일")
    
    # 관리 정보
    assessed_by = Column(String(50), comment="평가자")
    notes = Column(Text, comment="특이사항")
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 관계
    monitoring_schedules = relationship("CardiovascularMonitoring", back_populates="risk_assessment")


class CardiovascularMonitoring(Base):
    """뇌심혈관계 모니터링 스케줄 및 기록"""
    __tablename__ = "cardiovascular_monitoring"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey("cardiovascular_risk_assessments.id"))
    worker_id = Column(String(50), nullable=False, comment="근로자 ID")
    
    # 모니터링 정보
    monitoring_type = Column(String(50), nullable=False, comment="모니터링 유형")  # Changed from Enum to String
    scheduled_date = Column(DateTime, nullable=False, comment="예정일시")
    actual_date = Column(DateTime, comment="실제일시")
    
    # 측정값
    systolic_bp = Column(Integer, comment="수축기혈압")
    diastolic_bp = Column(Integer, comment="이완기혈압")
    heart_rate = Column(Integer, comment="심박수")
    measurement_values = Column(JSON, comment="기타 측정값")
    
    # 상태 및 결과
    is_completed = Column(Boolean, default=False, comment="완료 여부")
    is_normal = Column(Boolean, comment="정상 여부")
    abnormal_findings = Column(Text, comment="이상 소견")
    action_required = Column(Boolean, default=False, comment="조치 필요 여부")
    
    # 관리 정보
    monitored_by = Column(String(50), comment="모니터링 담당자")
    location = Column(String(100), comment="측정 장소")
    equipment_used = Column(String(100), comment="사용 장비")
    notes = Column(Text, comment="특이사항")
    
    # 다음 예약
    next_monitoring_date = Column(DateTime, comment="다음 모니터링 예정일")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 관계
    risk_assessment = relationship("CardiovascularRiskAssessment", back_populates="monitoring_schedules")
    emergency_responses = relationship("EmergencyResponse", back_populates="monitoring")


class EmergencyResponse(Base):
    """응급상황 대응 기록"""
    __tablename__ = "cardiovascular_emergency_responses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    monitoring_id = Column(UUID(as_uuid=True), ForeignKey("cardiovascular_monitoring.id"), nullable=True)
    worker_id = Column(String(50), nullable=False, comment="근로자 ID")
    
    # 응급상황 정보
    incident_datetime = Column(DateTime, default=datetime.now, comment="발생일시")
    incident_location = Column(String(200), comment="발생장소")
    incident_description = Column(Text, comment="상황 설명")
    
    # 증상 및 징후
    symptoms = Column(JSON, comment="증상 목록")
    vital_signs = Column(JSON, comment="생체징후")
    consciousness_level = Column(String(50), comment="의식 수준")
    
    # 대응 조치
    first_aid_provided = Column(Boolean, default=False, comment="응급처치 시행 여부")
    first_aid_details = Column(Text, comment="응급처치 내용")
    emergency_call_made = Column(Boolean, default=False, comment="응급실 연락 여부")
    hospital_transport = Column(Boolean, default=False, comment="병원 이송 여부")
    hospital_name = Column(String(100), comment="이송 병원명")
    
    # 대응팀 정보
    response_team = Column(JSON, comment="대응팀 구성")
    primary_responder = Column(String(50), comment="주 대응자")
    response_time = Column(Integer, comment="대응시간(분)")
    
    # 결과 및 후속조치
    outcome = Column(String(100), comment="결과")
    follow_up_required = Column(Boolean, default=False, comment="후속조치 필요 여부")
    follow_up_plan = Column(Text, comment="후속조치 계획")
    lesson_learned = Column(Text, comment="교훈 및 개선사항")
    
    # 상태
    status = Column(String(20), default="대기", comment="대응 상태")  # Changed from Enum to String
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = Column(String(50), comment="기록자")
    
    # 관계
    monitoring = relationship("CardiovascularMonitoring", back_populates="emergency_responses")


class PreventionEducation(Base):
    """예방 교육 프로그램"""
    __tablename__ = "cardiovascular_prevention_education"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 교육 정보
    title = Column(String(200), nullable=False, comment="교육명")
    description = Column(Text, comment="교육 설명")
    target_audience = Column(String(100), comment="대상자")
    education_type = Column(String(50), comment="교육 유형")
    
    # 일정 정보
    scheduled_date = Column(DateTime, nullable=False, comment="예정일시")
    duration_minutes = Column(Integer, comment="교육시간(분)")
    location = Column(String(100), comment="교육장소")
    
    # 교육 내용
    curriculum = Column(JSON, comment="교육과정")
    materials = Column(JSON, comment="교육자료 목록")
    learning_objectives = Column(JSON, comment="학습목표")
    
    # 참석자 관리
    target_participants = Column(Integer, comment="목표 참석자 수")
    actual_participants = Column(Integer, comment="실제 참석자 수")
    participant_list = Column(JSON, comment="참석자 목록")
    
    # 평가 및 피드백
    evaluation_method = Column(String(100), comment="평가 방법")
    evaluation_results = Column(JSON, comment="평가 결과")
    participant_feedback = Column(JSON, comment="참석자 피드백")
    effectiveness_score = Column(Float, comment="효과성 점수")
    
    # 관리 정보
    instructor = Column(String(50), comment="강사")
    organizer = Column(String(50), comment="주관자")
    is_completed = Column(Boolean, default=False, comment="완료 여부")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)