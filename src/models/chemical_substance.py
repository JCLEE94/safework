from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum as SQLEnum, Text, Date, Index
from sqlalchemy.orm import relationship
from src.config.database import Base
import enum


class HazardClass(enum.Enum):
    EXPLOSIVE = "폭발성"
    FLAMMABLE = "인화성"
    OXIDIZING = "산화성"
    TOXIC = "독성"
    CORROSIVE = "부식성"
    IRRITANT = "자극성"
    CARCINOGENIC = "발암성"
    MUTAGENIC = "변이원성"
    REPRODUCTIVE = "생식독성"
    ENVIRONMENTAL = "환경유해성"
    OTHER = "기타"


class StorageStatus(enum.Enum):
    IN_USE = "사용중"
    STORED = "보관중"
    DISPOSED = "폐기"
    ORDERED = "주문중"
    EXPIRED = "유효기간만료"


class ChemicalSubstance(Base):
    __tablename__ = "chemical_substances"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic info
    korean_name = Column(String(200), nullable=False, index=True)
    english_name = Column(String(200), index=True)
    cas_number = Column(String(50), index=True)
    un_number = Column(String(50))
    
    # Classification
    hazard_class = Column(SQLEnum(HazardClass), nullable=False, index=True)
    hazard_statement = Column(Text)
    precautionary_statement = Column(Text)
    signal_word = Column(String(50))  # 위험 or 경고
    
    # Physical properties
    physical_state = Column(String(50))  # 고체, 액체, 기체
    appearance = Column(String(200))
    odor = Column(String(200))
    ph_value = Column(Float)
    boiling_point = Column(Float)
    melting_point = Column(Float)
    flash_point = Column(Float)
    
    # Storage info
    storage_location = Column(String(200), index=True)
    storage_condition = Column(String(500))
    incompatible_materials = Column(Text)
    
    # Inventory
    current_quantity = Column(Float)
    quantity_unit = Column(String(50))
    minimum_quantity = Column(Float)
    maximum_quantity = Column(Float)
    
    # Safety info
    exposure_limit_twa = Column(Float)  # 시간가중평균노출기준
    exposure_limit_stel = Column(Float)  # 단시간노출기준
    exposure_limit_ceiling = Column(Float)  # 최고노출기준
    
    # MSDS info
    msds_file_path = Column(String(500))
    msds_revision_date = Column(Date, index=True)
    manufacturer = Column(String(200), index=True)
    supplier = Column(String(200))
    emergency_contact = Column(String(200))
    
    # Management
    special_management_material = Column(String(1), default='N', index=True)  # 특별관리물질 여부
    carcinogen = Column(String(1), default='N', index=True)  # 발암물질 여부
    mutagen = Column(String(1), default='N')  # 변이원성물질 여부
    reproductive_toxin = Column(String(1), default='N')  # 생식독성물질 여부
    
    status = Column(SQLEnum(StorageStatus), default=StorageStatus.IN_USE, index=True)
    
    # Common fields
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))
    
    # 복합 인덱스
    __table_args__ = (
        Index('ix_chemicals_name_status', 'korean_name', 'status'),
        Index('ix_chemicals_hazard_special', 'hazard_class', 'special_management_material'),
        Index('ix_chemicals_location_quantity', 'storage_location', 'current_quantity'),
        Index('ix_chemicals_safety_flags', 'carcinogen', 'mutagen', 'reproductive_toxin'),
    )


class ChemicalUsageRecord(Base):
    __tablename__ = "chemical_usage_records"
    
    id = Column(Integer, primary_key=True, index=True)
    chemical_id = Column(Integer, ForeignKey("chemical_substances.id", ondelete="CASCADE"))
    
    usage_date = Column(DateTime, nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="SET NULL"))
    
    # Usage details
    quantity_used = Column(Float, nullable=False)
    quantity_unit = Column(String(50))
    purpose = Column(String(500))
    work_location = Column(String(200))
    
    # Safety measures
    ventilation_used = Column(String(1), default='N')
    ppe_used = Column(String(500))
    exposure_duration_minutes = Column(Integer)
    
    # Incidents
    incident_occurred = Column(String(1), default='N')
    incident_description = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    
    # Relationships
    chemical = relationship("ChemicalSubstance", backref="usage_records")
    worker = relationship("Worker", backref="chemical_usages")