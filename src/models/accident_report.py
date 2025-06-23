from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Date
from sqlalchemy.orm import relationship
from src.config.database import Base
import enum


class AccidentType(enum.Enum):
    FALL = "떨어짐"
    TRIP = "넘어짐"
    COLLISION = "부딪힘"
    STRUCK_BY = "맞음"
    CAUGHT_IN = "끼임"
    CUT = "베임/찔림"
    BURN = "화상"
    ELECTRIC_SHOCK = "감전"
    EXPLOSION = "폭발"
    CHEMICAL_EXPOSURE = "화학물질노출"
    OCCUPATIONAL_DISEASE = "업무상질병"
    TRAFFIC = "교통사고"
    OTHER = "기타"


class InjuryType(enum.Enum):
    NONE = "부상없음"
    BRUISE = "타박상"
    SPRAIN = "염좌"
    FRACTURE = "골절"
    CUT_WOUND = "찰과상/열상"
    BURN_INJURY = "화상"
    POISONING = "중독"
    HEARING_LOSS = "청력손실"
    VISION_LOSS = "시력손실"
    RESPIRATORY = "호흡기질환"
    SKIN_DISEASE = "피부질환"
    MUSCULOSKELETAL = "근골격계질환"
    DEATH = "사망"
    OTHER = "기타"


class AccidentSeverity(enum.Enum):
    MINOR = "경미"
    MODERATE = "중등도"
    SEVERE = "중대"
    FATAL = "사망"


class InvestigationStatus(enum.Enum):
    REPORTED = "신고접수"
    INVESTIGATING = "조사중"
    COMPLETED = "조사완료"
    CLOSED = "종결"


class AccidentReport(Base):
    __tablename__ = "accident_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Accident info
    accident_datetime = Column(DateTime, nullable=False)
    report_datetime = Column(DateTime, nullable=False)
    accident_location = Column(String(300), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"))
    
    # Classification
    accident_type = Column(SQLEnum(AccidentType), nullable=False)
    injury_type = Column(SQLEnum(InjuryType), nullable=False)
    severity = Column(SQLEnum(AccidentSeverity), nullable=False)
    
    # Details
    accident_description = Column(Text, nullable=False)
    immediate_cause = Column(Text)
    root_cause = Column(Text)
    
    # Injury details
    injured_body_part = Column(String(200))
    treatment_type = Column(String(200))
    hospital_name = Column(String(200))
    doctor_name = Column(String(100))
    
    # Work loss
    work_days_lost = Column(Integer, default=0)
    return_to_work_date = Column(Date)
    permanent_disability = Column(String(1), default='N')
    disability_rate = Column(Float)
    
    # Investigation
    investigation_status = Column(SQLEnum(InvestigationStatus), default=InvestigationStatus.REPORTED)
    investigator_name = Column(String(100))
    investigation_date = Column(Date)
    
    # Corrective actions
    immediate_actions = Column(Text)
    corrective_actions = Column(Text)
    preventive_measures = Column(Text)
    action_completion_date = Column(Date)
    
    # Reporting
    reported_to_authorities = Column(String(1), default='N')
    authority_report_date = Column(DateTime)
    authority_report_number = Column(String(100))
    
    # Documents
    accident_photo_paths = Column(Text)  # JSON array of file paths
    investigation_report_path = Column(String(500))
    medical_certificate_path = Column(String(500))
    
    # Witness info
    witness_names = Column(Text)  # JSON array
    witness_statements = Column(Text)
    
    # Costs
    medical_cost = Column(Float, default=0)
    compensation_cost = Column(Float, default=0)
    other_cost = Column(Float, default=0)
    
    # Common fields
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    
    # Relationships
    worker = relationship("Worker", backref="accident_reports")