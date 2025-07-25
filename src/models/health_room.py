"""
건강관리실 관련 데이터베이스 모델

이 모듈은 건강관리실에서 사용되는 투약, 측정, 인바디 관리를 위한 모델을 정의합니다.
- 투약 기록 관리
- 혈압/혈당 등 측정 기록
- 인바디 측정 결과 관리

참고 문서:
- SQLAlchemy: https://docs.sqlalchemy.org/
- PostgreSQL Date/Time: https://www.postgresql.org/docs/current/datatype-datetime.html
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, Boolean, Date
from sqlalchemy.orm import relationship
from datetime import datetime

from ..config.database import Base


class MedicationRecord(Base):
    """투약 기록 모델"""
    __tablename__ = "medication_records"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 투약 정보
    medication_name = Column(String(200), nullable=False)  # 약품명
    dosage = Column(String(100), nullable=False)  # 용량
    quantity = Column(Integer, nullable=False)  # 수량
    purpose = Column(String(500), nullable=True)  # 투약 목적
    symptoms = Column(Text, nullable=True)  # 증상
    
    # 투약 시간
    administered_at = Column(DateTime, nullable=False, default=datetime.now)
    administered_by = Column(String(100), nullable=True)  # 투약자 (보건관리자)
    
    # 추가 정보
    notes = Column(Text, nullable=True)  # 비고
    follow_up_required = Column(Boolean, default=False)  # 추적 관찰 필요 여부
    
    # 관계
    worker = relationship("Worker", back_populates="medication_records")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class VitalSignRecord(Base):
    """생체 신호 측정 기록 (혈압, 혈당 등)"""
    __tablename__ = "vital_sign_records"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 혈압
    systolic_bp = Column(Integer, nullable=True)  # 수축기 혈압
    diastolic_bp = Column(Integer, nullable=True)  # 이완기 혈압
    
    # 혈당
    blood_sugar = Column(Integer, nullable=True)  # mg/dL
    blood_sugar_type = Column(String(20), nullable=True)  # 공복/식후
    
    # 기타 측정값
    heart_rate = Column(Integer, nullable=True)  # 심박수
    body_temperature = Column(Float, nullable=True)  # 체온
    oxygen_saturation = Column(Integer, nullable=True)  # 산소포화도
    
    # 측정 정보
    measured_at = Column(DateTime, nullable=False, default=datetime.now)
    measured_by = Column(String(100), nullable=True)  # 측정자
    
    # 상태 평가
    status = Column(String(20), nullable=True)  # 정상/주의/위험
    notes = Column(Text, nullable=True)
    
    # 관계
    worker = relationship("Worker", back_populates="vital_sign_records")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class InBodyRecord(Base):
    """인바디 측정 기록"""
    __tablename__ = "inbody_records"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 기본 측정값
    height = Column(Float, nullable=False)  # 신장 (cm)
    weight = Column(Float, nullable=False)  # 체중 (kg)
    bmi = Column(Float, nullable=False)  # BMI
    
    # 체성분 분석
    body_fat_mass = Column(Float, nullable=True)  # 체지방량 (kg)
    body_fat_percentage = Column(Float, nullable=True)  # 체지방률 (%)
    muscle_mass = Column(Float, nullable=True)  # 근육량 (kg)
    lean_body_mass = Column(Float, nullable=True)  # 제지방량 (kg)
    
    # 체수분
    total_body_water = Column(Float, nullable=True)  # 체수분 (L)
    
    # 부위별 근육량
    right_arm_muscle = Column(Float, nullable=True)  # 오른팔 근육량
    left_arm_muscle = Column(Float, nullable=True)  # 왼팔 근육량
    trunk_muscle = Column(Float, nullable=True)  # 몸통 근육량
    right_leg_muscle = Column(Float, nullable=True)  # 오른다리 근육량
    left_leg_muscle = Column(Float, nullable=True)  # 왼다리 근육량
    
    # 부위별 체지방
    right_arm_fat = Column(Float, nullable=True)  # 오른팔 체지방
    left_arm_fat = Column(Float, nullable=True)  # 왼팔 체지방
    trunk_fat = Column(Float, nullable=True)  # 몸통 체지방
    right_leg_fat = Column(Float, nullable=True)  # 오른다리 체지방
    left_leg_fat = Column(Float, nullable=True)  # 왼다리 체지방
    
    # 기타 지표
    visceral_fat_level = Column(Integer, nullable=True)  # 내장지방 레벨
    basal_metabolic_rate = Column(Integer, nullable=True)  # 기초대사량 (kcal)
    body_age = Column(Integer, nullable=True)  # 체성분 나이
    
    # 측정 정보
    measured_at = Column(DateTime, nullable=False, default=datetime.now)
    device_model = Column(String(100), nullable=True)  # 측정 장비 모델
    
    # 평가 및 권고사항
    evaluation = Column(Text, nullable=True)  # 종합 평가
    recommendations = Column(Text, nullable=True)  # 권고사항
    
    # 관계
    worker = relationship("Worker", back_populates="inbody_records")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


class HealthRoomVisit(Base):
    """건강관리실 방문 기록"""
    __tablename__ = "health_room_visits"
    
    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id"), nullable=False)
    
    # 방문 정보
    visit_date = Column(DateTime, nullable=False, default=datetime.now)
    visit_reason = Column(String(500), nullable=False)  # 방문 사유
    chief_complaint = Column(Text, nullable=True)  # 주요 증상
    
    # 처치 내용
    treatment_provided = Column(Text, nullable=True)  # 제공된 처치
    medication_given = Column(Boolean, default=False)  # 투약 여부
    measurement_taken = Column(Boolean, default=False)  # 측정 여부
    
    # 후속 조치
    follow_up_required = Column(Boolean, default=False)  # 추적 관찰 필요
    referral_required = Column(Boolean, default=False)  # 의뢰 필요
    referral_location = Column(String(200), nullable=True)  # 의뢰 기관
    
    # 상태
    status = Column(String(50), default="completed")  # 방문 상태
    notes = Column(Text, nullable=True)
    
    # 관계
    worker = relationship("Worker", back_populates="health_room_visits")
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


if __name__ == "__main__":
    print("✅ 건강관리실 모델 정의 완료")
    print("📝 모델 구성:")
    print("  - MedicationRecord: 투약 기록 관리")
    print("  - VitalSignRecord: 생체 신호 측정 (혈압, 혈당 등)")
    print("  - InBodyRecord: 인바디 측정 결과")
    print("  - HealthRoomVisit: 건강관리실 방문 기록")