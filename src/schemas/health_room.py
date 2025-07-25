"""
건강관리실 관련 Pydantic 스키마

이 모듈은 건강관리실 API에서 사용되는 요청/응답 스키마를 정의합니다.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime


# 투약 기록 스키마
class MedicationRecordBase(BaseModel):
    medication_name: str = Field(..., description="약품명")
    dosage: str = Field(..., description="용량")
    quantity: int = Field(..., description="수량", ge=1)
    purpose: Optional[str] = Field(None, description="투약 목적")
    symptoms: Optional[str] = Field(None, description="증상")
    administered_by: Optional[str] = Field(None, description="투약자")
    notes: Optional[str] = Field(None, description="비고")
    follow_up_required: bool = Field(False, description="추적 관찰 필요 여부")


class MedicationRecordCreate(MedicationRecordBase):
    worker_id: int = Field(..., description="근로자 ID")


class MedicationRecordUpdate(BaseModel):
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=1)
    purpose: Optional[str] = None
    symptoms: Optional[str] = None
    notes: Optional[str] = None
    follow_up_required: Optional[bool] = None


class MedicationRecordResponse(MedicationRecordBase):
    id: int
    worker_id: int
    administered_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 생체 신호 측정 스키마
class VitalSignRecordBase(BaseModel):
    systolic_bp: Optional[int] = Field(None, description="수축기 혈압", ge=50, le=300)
    diastolic_bp: Optional[int] = Field(None, description="이완기 혈압", ge=30, le=200)
    blood_sugar: Optional[int] = Field(None, description="혈당 (mg/dL)", ge=20, le=600)
    blood_sugar_type: Optional[str] = Field(None, description="공복/식후")
    heart_rate: Optional[int] = Field(None, description="심박수", ge=30, le=300)
    body_temperature: Optional[float] = Field(None, description="체온", ge=30.0, le=45.0)
    oxygen_saturation: Optional[int] = Field(None, description="산소포화도", ge=50, le=100)
    measured_by: Optional[str] = Field(None, description="측정자")
    notes: Optional[str] = Field(None, description="비고")
    
    @validator('blood_sugar_type')
    def validate_blood_sugar_type(cls, v):
        if v and v not in ['공복', '식후']:
            raise ValueError('혈당 타입은 "공복" 또는 "식후"여야 합니다')
        return v


class VitalSignRecordCreate(VitalSignRecordBase):
    worker_id: int = Field(..., description="근로자 ID")
    
    @validator('*', pre=True)
    def at_least_one_measurement(cls, v, values):
        if not any([
            values.get('systolic_bp'), values.get('diastolic_bp'),
            values.get('blood_sugar'), values.get('heart_rate'),
            values.get('body_temperature'), values.get('oxygen_saturation')
        ]):
            raise ValueError('최소 하나 이상의 측정값이 필요합니다')
        return v


class VitalSignRecordUpdate(VitalSignRecordBase):
    pass


class VitalSignRecordResponse(VitalSignRecordBase):
    id: int
    worker_id: int
    measured_at: datetime
    status: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 인바디 측정 스키마
class InBodyRecordBase(BaseModel):
    height: float = Field(..., description="신장 (cm)", ge=100, le=250)
    weight: float = Field(..., description="체중 (kg)", ge=20, le=300)
    bmi: float = Field(..., description="BMI", ge=10, le=50)
    
    # 체성분 분석
    body_fat_mass: Optional[float] = Field(None, description="체지방량 (kg)", ge=0)
    body_fat_percentage: Optional[float] = Field(None, description="체지방률 (%)", ge=0, le=60)
    muscle_mass: Optional[float] = Field(None, description="근육량 (kg)", ge=0)
    lean_body_mass: Optional[float] = Field(None, description="제지방량 (kg)", ge=0)
    total_body_water: Optional[float] = Field(None, description="체수분 (L)", ge=0)
    
    # 부위별 측정값
    right_arm_muscle: Optional[float] = Field(None, ge=0)
    left_arm_muscle: Optional[float] = Field(None, ge=0)
    trunk_muscle: Optional[float] = Field(None, ge=0)
    right_leg_muscle: Optional[float] = Field(None, ge=0)
    left_leg_muscle: Optional[float] = Field(None, ge=0)
    
    right_arm_fat: Optional[float] = Field(None, ge=0)
    left_arm_fat: Optional[float] = Field(None, ge=0)
    trunk_fat: Optional[float] = Field(None, ge=0)
    right_leg_fat: Optional[float] = Field(None, ge=0)
    left_leg_fat: Optional[float] = Field(None, ge=0)
    
    # 기타 지표
    visceral_fat_level: Optional[int] = Field(None, description="내장지방 레벨", ge=1, le=20)
    basal_metabolic_rate: Optional[int] = Field(None, description="기초대사량 (kcal)", ge=500)
    body_age: Optional[int] = Field(None, description="체성분 나이", ge=10, le=100)
    
    device_model: Optional[str] = Field(None, description="측정 장비 모델")
    evaluation: Optional[str] = Field(None, description="종합 평가")
    recommendations: Optional[str] = Field(None, description="권고사항")


class InBodyRecordCreate(InBodyRecordBase):
    worker_id: int = Field(..., description="근로자 ID")


class InBodyRecordUpdate(BaseModel):
    evaluation: Optional[str] = None
    recommendations: Optional[str] = None


class InBodyRecordResponse(InBodyRecordBase):
    id: int
    worker_id: int
    measured_at: datetime
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 건강관리실 방문 스키마
class HealthRoomVisitBase(BaseModel):
    visit_reason: str = Field(..., description="방문 사유")
    chief_complaint: Optional[str] = Field(None, description="주요 증상")
    treatment_provided: Optional[str] = Field(None, description="제공된 처치")
    medication_given: bool = Field(False, description="투약 여부")
    measurement_taken: bool = Field(False, description="측정 여부")
    follow_up_required: bool = Field(False, description="추적 관찰 필요")
    referral_required: bool = Field(False, description="의뢰 필요")
    referral_location: Optional[str] = Field(None, description="의뢰 기관")
    notes: Optional[str] = Field(None, description="비고")


class HealthRoomVisitCreate(HealthRoomVisitBase):
    worker_id: int = Field(..., description="근로자 ID")


class HealthRoomVisitUpdate(BaseModel):
    visit_reason: Optional[str] = None
    chief_complaint: Optional[str] = None
    treatment_provided: Optional[str] = None
    medication_given: Optional[bool] = None
    measurement_taken: Optional[bool] = None
    follow_up_required: Optional[bool] = None
    referral_required: Optional[bool] = None
    referral_location: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class HealthRoomVisitResponse(HealthRoomVisitBase):
    id: int
    worker_id: int
    visit_date: datetime
    status: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 통계 및 대시보드 스키마
class HealthRoomStats(BaseModel):
    total_visits: int
    total_medications: int
    total_measurements: int
    total_inbody_records: int
    visits_by_reason: dict
    common_medications: List[dict]
    abnormal_vital_signs: int
    follow_up_required: int


class WorkerHealthSummary(BaseModel):
    worker_id: int
    worker_name: str
    recent_visits: List[HealthRoomVisitResponse]
    recent_medications: List[MedicationRecordResponse]
    recent_vital_signs: List[VitalSignRecordResponse]
    latest_inbody: Optional[InBodyRecordResponse]