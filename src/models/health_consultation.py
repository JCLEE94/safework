"""
보건상담 모델
Health Consultation Models
"""

from sqlalchemy import Column, Integer, String, DateTime, Date, Boolean, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime

from src.models import Base
from src.schemas.health_consultation import ConsultationType, ConsultationStatus, HealthIssueCategory


class HealthConsultation(Base):
    """보건상담 모델"""
    __tablename__ = "health_consultations"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False, index=True)
    consultation_date = Column(DateTime, nullable=False, index=True)
    consultation_type = Column(SQLEnum(ConsultationType), nullable=False, index=True)
    chief_complaint = Column(Text, nullable=False)
    consultation_location = Column(String(100), nullable=False)
    consultant_name = Column(String(50), nullable=False)
    
    # 상담 상세 내용
    symptoms = Column(Text, nullable=True)
    work_related_factors = Column(Text, nullable=True)
    health_issue_category = Column(SQLEnum(HealthIssueCategory), nullable=True, index=True)
    vital_signs = Column(String(200), nullable=True)  # "혈압: 120/80, 맥박: 72"
    physical_examination = Column(Text, nullable=True)
    consultation_notes = Column(Text, nullable=True)
    recommendations = Column(Text, nullable=True)
    
    # 의료기관 의뢰
    referral_needed = Column(Boolean, default=False, nullable=False)
    referral_hospital = Column(String(100), nullable=True)
    
    # 추적관찰
    follow_up_needed = Column(Boolean, default=False, nullable=False)
    follow_up_date = Column(Date, nullable=True)
    
    # 작업 관련 조치
    work_restriction = Column(Text, nullable=True)
    medication_prescribed = Column(Text, nullable=True)
    
    # 상담 상태
    status = Column(SQLEnum(ConsultationStatus), default=ConsultationStatus.SCHEDULED, nullable=False, index=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), nullable=True)
    
    # 관계
    worker = relationship("Worker", back_populates="health_consultations")
    follow_ups = relationship("ConsultationFollowUp", back_populates="consultation", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<HealthConsultation(id={self.id}, worker_id={self.worker_id}, date={self.consultation_date}, type={self.consultation_type})>"


class ConsultationFollowUp(Base):
    """상담 추적관찰 모델"""
    __tablename__ = "consultation_follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("health_consultations.id"), nullable=False, index=True)
    follow_up_date = Column(Date, nullable=False, index=True)
    reason = Column(Text, nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    completion_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)
    next_follow_up_date = Column(Date, nullable=True)
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by = Column(String(50), nullable=True)
    
    # 관계
    consultation = relationship("HealthConsultation", back_populates="follow_ups")

    def __repr__(self):
        return f"<ConsultationFollowUp(id={self.id}, consultation_id={self.consultation_id}, date={self.follow_up_date}, completed={self.completed})>"


class ConsultationAttachment(Base):
    """상담 첨부파일 모델"""
    __tablename__ = "consultation_attachments"

    id = Column(Integer, primary_key=True, index=True)
    consultation_id = Column(Integer, ForeignKey("health_consultations.id"), nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_type = Column(String(50), nullable=False)  # "image", "document", "medical_record"
    description = Column(Text, nullable=True)
    
    # 메타데이터
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by = Column(String(50), nullable=True)
    
    # 관계
    consultation = relationship("HealthConsultation")

    def __repr__(self):
        return f"<ConsultationAttachment(id={self.id}, consultation_id={self.consultation_id}, file_name={self.file_name})>"