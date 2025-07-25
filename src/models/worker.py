"""
근로자 모델
Worker data models
"""

import enum

from sqlalchemy import (Boolean, Column, Date, DateTime, Enum, ForeignKey,
                        Index, Integer, String, Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..config.database import Base


class GenderType(enum.Enum):
    """성별"""

    MALE = "male"
    FEMALE = "female"


class EmploymentType(enum.Enum):
    """고용형태"""

    REGULAR = "regular"  # 정규직
    CONTRACT = "contract"  # 계약직
    TEMPORARY = "temporary"  # 임시직
    DAILY = "daily"  # 일용직


class WorkType(enum.Enum):
    """작업분류"""

    CONSTRUCTION = "construction"  # 건설
    ELECTRICAL = "electrical"  # 전기
    PLUMBING = "plumbing"  # 배관
    PAINTING = "painting"  # 도장
    WELDING = "welding"  # 용접
    DEMOLITION = "demolition"  # 해체
    EARTH_WORK = "earth_work"  # 토공
    CONCRETE = "concrete"  # 콘크리트


class HealthStatus(enum.Enum):
    """건강상태"""

    NORMAL = "normal"  # 정상
    CAUTION = "caution"  # 주의
    OBSERVATION = "observation"  # 관찰
    TREATMENT = "treatment"  # 치료


class Worker(Base):
    """근로자 기본정보"""

    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)

    # 기본정보
    employee_id = Column(
        String(20), unique=True, index=True, nullable=False, comment="사번"
    )
    name = Column(String(50), nullable=False, index=True, comment="성명")
    birth_date = Column(Date, index=True, comment="생년월일")
    gender = Column(String(10), nullable=True, comment="성별")
    phone = Column(String(20), comment="연락처")
    email = Column(String(100), comment="이메일")
    address = Column(Text, nullable=False, comment="거주지")

    # 업체정보
    company_name = Column(String(100), nullable=False, index=True, comment="업체명")
    work_category = Column(String(100), nullable=False, index=True, comment="공종")
    
    # 고용정보
    employment_type = Column(String(20), nullable=False, index=True, comment="고용형태")
    work_type = Column(String(20), nullable=False, index=True, comment="작업분류")
    hire_date = Column(Date, index=True, comment="입사일")
    department = Column(String(100), nullable=False, index=True, comment="부서(장비/작업)")
    position = Column(String(50), comment="직급")

    # 건강정보
    health_status = Column(String(20), default="normal", index=True, comment="건강상태")
    blood_type = Column(String(5), comment="혈액형")
    emergency_contact = Column(String(100), comment="비상연락처")
    emergency_relationship = Column(String(50), comment="비상연락 관계")
    
    # 안전교육 및 비자정보
    safety_education_cert = Column(Text, comment="건설업 기초안전보건교육 이수증")
    visa_type = Column(String(50), comment="비자종류")
    visa_cert = Column(Text, comment="비자관련 자격증")

    # 특수건강진단 대상 여부
    is_special_exam_target = Column(
        Boolean, default=False, index=True, comment="특수건강진단 대상여부"
    )
    harmful_factors = Column(Text, comment="유해인자 (JSON 배열)")

    # 시스템 정보
    is_active = Column(Boolean, default=True, index=True, comment="재직여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # 관계설정
    health_consultations = relationship(
        "HealthConsultation", back_populates="worker", cascade="all, delete-orphan"
    )
    health_exams = relationship(
        "HealthExam", back_populates="worker", cascade="all, delete-orphan"
    )
    exam_appointments = relationship(
        "HealthExamAppointment", back_populates="worker", cascade="all, delete-orphan"
    )
    feedbacks = relationship(
        "WorkerFeedback", back_populates="worker", cascade="all, delete-orphan"
    )
    
    # 건강관리실 관련 관계
    medication_records = relationship(
        "MedicationRecord", back_populates="worker", cascade="all, delete-orphan"
    )
    vital_sign_records = relationship(
        "VitalSignRecord", back_populates="worker", cascade="all, delete-orphan"
    )
    inbody_records = relationship(
        "InBodyRecord", back_populates="worker", cascade="all, delete-orphan"
    )
    health_room_visits = relationship(
        "HealthRoomVisit", back_populates="worker", cascade="all, delete-orphan"
    )

    # 복합 인덱스
    __table_args__ = (
        Index("ix_workers_dept_active", "department", "is_active"),
        Index("ix_workers_type_status", "employment_type", "health_status"),
        Index("ix_workers_work_special", "work_type", "is_special_exam_target"),
        Index("ix_workers_name_active", "name", "is_active"),
    )


# HealthConsultation 모델은 별도 파일로 이동됨
# src/models/health_consultation.py 참조
