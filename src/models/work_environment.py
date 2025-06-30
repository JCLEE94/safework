from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Index
from sqlalchemy.orm import relationship
from src.config.database import Base
import enum


class MeasurementType(enum.Enum):
    NOISE = "소음"
    DUST = "분진"
    CHEMICAL = "화학물질"
    ORGANIC_SOLVENT = "유기용제"
    METAL = "금속"
    ACID_ALKALI = "산알칼리"
    GAS = "가스"
    RADIATION = "방사선"
    TEMPERATURE = "고온"
    VIBRATION = "진동"
    ILLUMINATION = "조도"
    OTHER = "기타"


class MeasurementResult(enum.Enum):
    PASS = "적합"
    FAIL = "부적합"
    CAUTION = "주의"
    PENDING = "측정중"


class WorkEnvironment(Base):
    __tablename__ = "work_environments"
    
    id = Column(Integer, primary_key=True, index=True)
    measurement_date = Column(DateTime, nullable=False, index=True)
    location = Column(String(200), nullable=False, index=True)
    measurement_type = Column(SQLEnum(MeasurementType), nullable=False, index=True)
    measurement_agency = Column(String(200), nullable=False)
    
    # Measurement values
    measured_value = Column(Float)
    measurement_unit = Column(String(50))
    standard_value = Column(Float)
    standard_unit = Column(String(50))
    
    # Results
    result = Column(SQLEnum(MeasurementResult), nullable=False, index=True)
    improvement_measures = Column(Text)
    re_measurement_required = Column(String(1), default='N', index=True)
    re_measurement_date = Column(DateTime, index=True)
    
    # Report info
    report_number = Column(String(100), index=True)
    report_file_path = Column(String(500))
    
    # Common fields
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    
    # 복합 인덱스
    __table_args__ = (
        Index('ix_work_env_date_type', 'measurement_date', 'measurement_type'),
        Index('ix_work_env_location_result', 'location', 'result'),
        Index('ix_work_env_remeasure', 're_measurement_required', 're_measurement_date'),
    )


class WorkEnvironmentWorkerExposure(Base):
    __tablename__ = "work_environment_worker_exposures"
    
    id = Column(Integer, primary_key=True, index=True)
    work_environment_id = Column(Integer, ForeignKey("work_environments.id", ondelete="CASCADE"))
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"))
    
    exposure_level = Column(Float)
    exposure_duration_hours = Column(Float)
    protection_equipment_used = Column(String(200))
    health_effect_risk = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    work_environment = relationship("WorkEnvironment", backref="worker_exposures")
    worker = relationship("Worker", backref="environment_exposures")