"""
건강 관련 모델 - 통합버전
Consolidated health related models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Date, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from datetime import datetime

from ..config.database import Base


class ExamType(enum.Enum):
    """검진 유형"""
    GENERAL = "general"              # 일반건강진단
    SPECIAL = "special"              # 특수건강진단  
    PRE_EMPLOYMENT = "pre_employment" # 배치전건강진단
    TEMPORARY = "temporary"          # 임시건강진단
    RANDOM = "random"               # 수시건강진단


class ExamResult(enum.Enum):
    """판정결과"""
    NORMAL = "normal"               # 정상
    NORMAL_A = "normal_a"           # 정상A (이상없음)
    NORMAL_B = "normal_b"           # 정상B (경미한 이상소견)
    OCCUPATIONAL_C1 = "occupational_c1"  # 직업성질환 의심
    OCCUPATIONAL_C2 = "occupational_c2"  # 직업성질환
    GENERAL_D1 = "general_d1"       # 일반질환 의심
    GENERAL_D2 = "general_d2"       # 일반질환


class PostManagement(enum.Enum):
    """사후관리 구분"""
    NO_RESTRICTION = "no_restriction"     # 제한없음
    WORK_RESTRICTION = "work_restriction"  # 작업제한
    WORK_CHANGE = "work_change"           # 작업전환
    WORK_PROHIBITION = "work_prohibition"  # 작업금지
    OBSERVATION = "observation"           # 경과관찰
    REEXAM_3M = "reexam_3m"              # 3개월후 재검
    REEXAM_6M = "reexam_6m"              # 6개월후 재검
    REEXAM_12M = "reexam_12m"            # 12개월후 재검


class HealthExam(Base):
    """건강진단 기본정보 - 통합버전"""
    __tablename__ = "health_exams"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 진단정보
    exam_type = Column(SQLEnum(ExamType), nullable=False, index=True)
    exam_date = Column(Date, nullable=False, index=True)
    exam_institution = Column(String(100), nullable=False)
    exam_doctor = Column(String(50))
    
    # 결과정보
    exam_result = Column(SQLEnum(ExamResult), index=True)
    post_management = Column(SQLEnum(PostManagement))
    next_exam_date = Column(Date, index=True)
    
    # 특수건강진단 대상 유해인자
    harmful_factors = Column(Text, comment="유해인자 (JSON 배열)")
    
    # 소견 및 권고사항
    medical_opinion = Column(Text)
    work_suitability = Column(Text)
    recommendations = Column(Text)
    restrictions = Column(Text)
    
    # 추적관리
    is_followup_required = Column(Boolean, default=False, index=True)
    followup_date = Column(Date)
    followup_notes = Column(Text)
    
    # 첨부파일
    report_file_path = Column(String(500))
    
    # 공통 필드
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    worker = relationship("Worker", back_populates="health_exams")
    vital_signs = relationship("VitalSigns", back_populates="health_exam", cascade="all, delete-orphan")
    lab_results = relationship("LabResult", back_populates="health_exam", cascade="all, delete-orphan")

    # 복합 인덱스
    __table_args__ = (
        Index('ix_health_exams_worker_date', 'worker_id', 'exam_date'),
        Index('ix_health_exams_type_result', 'exam_type', 'exam_result'),
        Index('ix_health_exams_followup', 'is_followup_required', 'followup_date'),
    )


class VitalSigns(Base):
    """기초검사 결과"""
    __tablename__ = "vital_signs"
    
    id = Column(Integer, primary_key=True, index=True)
    health_exam_id = Column(Integer, ForeignKey("health_exams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 신체계측
    height = Column(Float, comment="신장(cm)")
    weight = Column(Float, comment="체중(kg)")
    bmi = Column(Float, comment="BMI")
    waist_circumference = Column(Float, comment="허리둘레(cm)")
    
    # 혈압
    systolic_bp = Column(Integer, comment="수축기혈압")
    diastolic_bp = Column(Integer, comment="이완기혈압")
    
    # 시력
    vision_left = Column(Float, comment="좌안시력")
    vision_right = Column(Float, comment="우안시력")
    
    # 청력
    hearing_left_1000hz = Column(Integer, comment="좌청력1000Hz")
    hearing_right_1000hz = Column(Integer, comment="우청력1000Hz")
    hearing_left_4000hz = Column(Integer, comment="좌청력4000Hz")
    hearing_right_4000hz = Column(Integer, comment="우청력4000Hz")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계설정
    health_exam = relationship("HealthExam", back_populates="vital_signs")


class LabResult(Base):
    """임상검사 결과"""
    __tablename__ = "lab_results"
    
    id = Column(Integer, primary_key=True, index=True)
    health_exam_id = Column(Integer, ForeignKey("health_exams.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 검사 정보
    test_name = Column(String(200), nullable=False, index=True)
    test_value = Column(String(200))
    test_unit = Column(String(50))
    reference_range = Column(String(100))
    result_status = Column(String(50), index=True)  # 정상, 이상, 위험 등
    
    # 혈액검사
    hemoglobin = Column(Float, comment="혈색소(g/dL)")
    hematocrit = Column(Float, comment="적혈구용적률(%)")
    
    # 간기능검사
    ast = Column(Float, comment="AST(U/L)")
    alt = Column(Float, comment="ALT(U/L)")
    gamma_gtp = Column(Float, comment="감마지티피(U/L)")
    
    # 신기능검사
    creatinine = Column(Float, comment="크레아티닌(mg/dL)")
    bun = Column(Float, comment="혈중요소질소(mg/dL)")
    
    # 당뇨검사
    fasting_glucose = Column(Float, comment="공복혈당(mg/dL)")
    hba1c = Column(Float, comment="당화혈색소(%)")
    
    # 지질검사
    total_cholesterol = Column(Float, comment="총콜레스테롤(mg/dL)")
    hdl_cholesterol = Column(Float, comment="HDL콜레스테롤(mg/dL)")
    ldl_cholesterol = Column(Float, comment="LDL콜레스테롤(mg/dL)")
    triglycerides = Column(Float, comment="중성지방(mg/dL)")
    
    # 흉부X선
    chest_xray_result = Column(String(200), comment="흉부X선결과")
    
    # 심전도
    ecg_result = Column(String(200), comment="심전도결과")
    
    # 특수검사 (유해인자별)
    special_test_results = Column(Text, comment="특수검사결과 (JSON)")
    
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계설정
    health_exam = relationship("HealthExam", back_populates="lab_results")