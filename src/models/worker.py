"""
근로자 모델
Worker data models
"""

from sqlalchemy import Column, Integer, String, Date, Boolean, Text, DateTime, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ..config.database import Base

class GenderType(enum.Enum):
    """성별"""
    MALE = "male"
    FEMALE = "female"

class EmploymentType(enum.Enum):
    """고용형태"""
    REGULAR = "regular"        # 정규직
    CONTRACT = "contract"      # 계약직
    TEMPORARY = "temporary"    # 임시직
    DAILY = "daily"           # 일용직

class WorkType(enum.Enum):
    """작업분류"""
    CONSTRUCTION = "construction"    # 건설
    ELECTRICAL = "electrical"       # 전기
    PLUMBING = "plumbing"           # 배관
    PAINTING = "painting"           # 도장
    WELDING = "welding"             # 용접
    DEMOLITION = "demolition"       # 해체
    EARTH_WORK = "earth_work"       # 토공
    CONCRETE = "concrete"           # 콘크리트

class HealthStatus(enum.Enum):
    """건강상태"""
    NORMAL = "normal"          # 정상
    CAUTION = "caution"        # 주의
    OBSERVATION = "observation" # 관찰
    TREATMENT = "treatment"     # 치료

class Worker(Base):
    """근로자 기본정보"""
    __tablename__ = "workers"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # 기본정보
    employee_id = Column(String(20), unique=True, index=True, nullable=False, comment="사번")
    name = Column(String(50), nullable=False, index=True, comment="성명")
    birth_date = Column(Date, index=True, comment="생년월일")
    gender = Column(String(10), nullable=True, comment="성별")
    phone = Column(String(20), comment="연락처")
    email = Column(String(100), comment="이메일")
    address = Column(Text, comment="주소")
    
    # 고용정보
    employment_type = Column(String(20), nullable=False, index=True, comment="고용형태")
    work_type = Column(String(20), nullable=False, index=True, comment="작업분류")
    hire_date = Column(Date, index=True, comment="입사일")
    department = Column(String(100), index=True, comment="소속부서")
    position = Column(String(50), comment="직급")
    
    # 건강정보
    health_status = Column(String(20), default="normal", index=True, comment="건강상태")
    blood_type = Column(String(5), comment="혈액형")
    emergency_contact = Column(String(100), comment="비상연락처")
    
    # 특수건강진단 대상 여부
    is_special_exam_target = Column(Boolean, default=False, index=True, comment="특수건강진단 대상여부")
    harmful_factors = Column(Text, comment="유해인자 (JSON 배열)")
    
    # 시스템 정보
    is_active = Column(Boolean, default=True, index=True, comment="재직여부")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 관계설정
    health_consultations = relationship("HealthConsultation", back_populates="worker", cascade="all, delete-orphan")
    health_exams = relationship("HealthExam", back_populates="worker", cascade="all, delete-orphan")
    
    # 복합 인덱스
    __table_args__ = (
        Index('ix_workers_dept_active', 'department', 'is_active'),
        Index('ix_workers_type_status', 'employment_type', 'health_status'),
        Index('ix_workers_work_special', 'work_type', 'is_special_exam_target'),
        Index('ix_workers_name_active', 'name', 'is_active'),
    )

class HealthConsultation(Base):
    """건강상담 기록"""
    __tablename__ = "health_consultations"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    consultation_date = Column(DateTime(timezone=True), nullable=False, comment="상담일시")
    consultation_type = Column(String(50), nullable=False, comment="상담유형")
    symptoms = Column(Text, comment="증상")
    consultation_content = Column(Text, comment="상담내용")
    recommendations = Column(Text, comment="권고사항")
    follow_up_date = Column(Date, comment="추후관리일")
    
    # 상담자 정보
    counselor_name = Column(String(50), comment="상담자명")
    counselor_title = Column(String(50), comment="상담자 직책")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계설정
    worker = relationship("Worker", back_populates="health_consultations")