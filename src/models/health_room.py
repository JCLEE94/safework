# 보건관리실 통합 모델
"""
보건관리실 기능을 위한 모델
- 약품관리
- 측정기록
- 체성분분석
- 일반업무
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, Boolean, Date, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from .database import Base


class MedicationType(str, enum.Enum):
    """약품 종류"""
    PAIN_RELIEF = "진통제"
    COLD_MEDICINE = "감기약"
    DIGESTIVE = "소화제"
    ANTIBIOTIC = "항생제"
    FIRST_AID = "응급처치약품"
    PRESCRIPTION = "처방약"
    OTHER = "기타"


class MeasurementType(str, enum.Enum):
    """측정 항목"""
    BLOOD_PRESSURE = "혈압"
    BLOOD_SUGAR = "혈당"
    BODY_TEMPERATURE = "체온"
    OXYGEN_SATURATION = "산소포화도"
    BODY_COMPOSITION = "체성분"
    HEIGHT_WEIGHT = "신장체중"
    VISION = "시력"
    HEARING = "청력"


class Medication(Base):
    """약품 관리"""
    __tablename__ = "medications"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(SQLEnum(MedicationType), nullable=False)
    manufacturer = Column(String(100))
    unit = Column(String(20))  # 정, 캡슐, ml 등
    
    # 재고 관리
    current_stock = Column(Integer, default=0)
    minimum_stock = Column(Integer, default=10)
    maximum_stock = Column(Integer, default=100)
    
    # 유효기간
    expiration_date = Column(Date)
    lot_number = Column(String(50))
    
    # 보관 정보
    storage_location = Column(String(100))
    storage_conditions = Column(String(200))
    
    # 용법용량
    dosage_instructions = Column(Text)
    precautions = Column(Text)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    dispensing_records = relationship("MedicationDispensing", back_populates="medication")
    inventory_logs = relationship("MedicationInventory", back_populates="medication")


class MedicationDispensing(Base):
    """약품 불출 기록"""
    __tablename__ = "medication_dispensing"
    
    id = Column(Integer, primary_key=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    quantity = Column(Integer, nullable=False)
    reason = Column(Text)
    symptoms = Column(Text)
    
    dispensed_by = Column(String(50))  # 불출 담당자
    dispensed_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    medication = relationship("Medication", back_populates="dispensing_records")
    worker = relationship("Worker", foreign_keys=[worker_id])


class MedicationInventory(Base):
    """약품 재고 변동 기록"""
    __tablename__ = "medication_inventory"
    
    id = Column(Integer, primary_key=True)
    medication_id = Column(Integer, ForeignKey("medications.id"), nullable=False)
    
    transaction_type = Column(String(20))  # 입고, 출고, 폐기, 조정
    quantity_change = Column(Integer)  # + or -
    quantity_after = Column(Integer)
    
    reason = Column(Text)
    reference_number = Column(String(50))  # 입고서 번호 등
    
    created_by = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    medication = relationship("Medication", back_populates="inventory_logs")


class HealthMeasurement(Base):
    """건강 측정 기록"""
    __tablename__ = "health_measurements"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    measurement_type = Column(SQLEnum(MeasurementType), nullable=False)
    
    # 측정 날짜/시간
    measured_at = Column(DateTime, default=datetime.utcnow)
    measured_by = Column(String(50))
    
    # 측정값 (JSON으로 유연하게 저장)
    values = Column(JSON)
    """
    혈압: {"systolic": 120, "diastolic": 80, "pulse": 70}
    혈당: {"value": 100, "timing": "공복"}
    체온: {"value": 36.5}
    산소포화도: {"value": 98}
    체성분: {"weight": 70, "muscle_mass": 30, "body_fat": 20, ...}
    """
    
    # 정상/비정상 판정
    is_normal = Column(Boolean)
    abnormal_findings = Column(Text)
    
    # 조치사항
    action_taken = Column(Text)
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계
    worker = relationship("Worker", foreign_keys=[worker_id])


class BodyCompositionAnalysis(Base):
    """체성분 분석 상세"""
    __tablename__ = "body_composition_analysis"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    measurement_id = Column(Integer, ForeignKey("health_measurements.id"))
    
    # 기본 정보
    measured_at = Column(DateTime, default=datetime.utcnow)
    device_model = Column(String(50))  # InBody 등
    
    # 체성분 데이터
    height = Column(Float)  # cm
    weight = Column(Float)  # kg
    bmi = Column(Float)
    
    # 근육/지방
    muscle_mass = Column(Float)  # kg
    body_fat_mass = Column(Float)  # kg
    body_fat_percentage = Column(Float)  # %
    visceral_fat_level = Column(Integer)
    
    # 수분/단백질/무기질
    total_body_water = Column(Float)  # L
    protein_mass = Column(Float)  # kg
    mineral_mass = Column(Float)  # kg
    
    # 부위별 근육량
    right_arm_muscle = Column(Float)
    left_arm_muscle = Column(Float)
    trunk_muscle = Column(Float)
    right_leg_muscle = Column(Float)
    left_leg_muscle = Column(Float)
    
    # 부위별 지방량
    right_arm_fat = Column(Float)
    left_arm_fat = Column(Float)
    trunk_fat = Column(Float)
    right_leg_fat = Column(Float)
    left_leg_fat = Column(Float)
    
    # 기타
    basal_metabolic_rate = Column(Float)  # kcal
    waist_hip_ratio = Column(Float)
    
    # 평가
    fitness_score = Column(Float)
    recommendations = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    worker = relationship("Worker", foreign_keys=[worker_id])
    measurement = relationship("HealthMeasurement")


class HealthRoomVisit(Base):
    """보건실 방문 기록"""
    __tablename__ = "health_room_visits"
    
    id = Column(Integer, primary_key=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    visit_datetime = Column(DateTime, default=datetime.utcnow)
    chief_complaint = Column(Text)  # 주호소
    
    # 처치 내용
    treatment_provided = Column(Text)
    medications_given = Column(Text)  # 투약 내역
    
    # 측정 수행 여부
    measurements_taken = Column(Boolean, default=False)
    measurement_ids = Column(JSON)  # 관련 측정 ID들
    
    # 후속 조치
    rest_taken = Column(Boolean, default=False)
    rest_duration_minutes = Column(Integer)
    referred_to_hospital = Column(Boolean, default=False)
    hospital_name = Column(String(100))
    
    # 업무 관련성
    work_related = Column(Boolean)
    accident_report_id = Column(Integer, ForeignKey("accident_reports.id"))
    
    notes = Column(Text)
    treated_by = Column(String(50))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계
    worker = relationship("Worker", foreign_keys=[worker_id])
    accident_report = relationship("AccidentReport")