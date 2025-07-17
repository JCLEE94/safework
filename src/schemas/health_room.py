# 보건관리실 스키마
"""
보건관리실 기능을 위한 Pydantic 스키마
- 약품관리
- 측정기록
- 체성분분석
- 일반업무
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum


class MedicationType(str, Enum):
    """약품 종류"""
    PAIN_RELIEF = "진통제"
    COLD_MEDICINE = "감기약"
    DIGESTIVE = "소화제"
    ANTIBIOTIC = "항생제"
    FIRST_AID = "응급처치약품"
    PRESCRIPTION = "처방약"
    OTHER = "기타"


class MeasurementType(str, Enum):
    """측정 항목"""
    BLOOD_PRESSURE = "혈압"
    BLOOD_SUGAR = "혈당"
    BODY_TEMPERATURE = "체온"
    OXYGEN_SATURATION = "산소포화도"
    BODY_COMPOSITION = "체성분"
    HEIGHT_WEIGHT = "신장체중"
    VISION = "시력"
    HEARING = "청력"


# 약품 관리 스키마
class MedicationBase(BaseModel):
    name: str = Field(..., description="약품명")
    type: MedicationType = Field(..., description="약품 종류")
    manufacturer: Optional[str] = Field(None, description="제조사")
    unit: Optional[str] = Field(None, description="단위 (정, 캡슐, ml 등)")
    
    current_stock: int = Field(0, description="현재 재고")
    minimum_stock: int = Field(10, description="최소 재고")
    maximum_stock: int = Field(100, description="최대 재고")
    
    expiration_date: Optional[date] = Field(None, description="유효기간")
    lot_number: Optional[str] = Field(None, description="로트번호")
    
    storage_location: Optional[str] = Field(None, description="보관 위치")
    storage_conditions: Optional[str] = Field(None, description="보관 조건")
    
    dosage_instructions: Optional[str] = Field(None, description="용법용량")
    precautions: Optional[str] = Field(None, description="주의사항")


class MedicationCreate(MedicationBase):
    pass


class MedicationUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[MedicationType] = None
    manufacturer: Optional[str] = None
    unit: Optional[str] = None
    
    current_stock: Optional[int] = None
    minimum_stock: Optional[int] = None
    maximum_stock: Optional[int] = None
    
    expiration_date: Optional[date] = None
    lot_number: Optional[str] = None
    
    storage_location: Optional[str] = None
    storage_conditions: Optional[str] = None
    
    dosage_instructions: Optional[str] = None
    precautions: Optional[str] = None
    
    is_active: Optional[bool] = None


class MedicationResponse(MedicationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 약품 불출 스키마
class MedicationDispensingBase(BaseModel):
    medication_id: int = Field(..., description="약품 ID")
    worker_id: int = Field(..., description="근로자 ID")
    quantity: int = Field(..., description="수량")
    reason: Optional[str] = Field(None, description="사유")
    symptoms: Optional[str] = Field(None, description="증상")
    dispensed_by: Optional[str] = Field(None, description="불출 담당자")


class MedicationDispensingCreate(MedicationDispensingBase):
    pass


class MedicationDispensingResponse(MedicationDispensingBase):
    id: int
    dispensed_at: datetime
    medication: Optional[MedicationResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


# 약품 재고 변동 스키마
class MedicationInventoryBase(BaseModel):
    medication_id: int = Field(..., description="약품 ID")
    transaction_type: str = Field(..., description="거래 유형 (입고, 출고, 폐기, 조정)")
    quantity_change: int = Field(..., description="수량 변동 (+/-)")
    quantity_after: int = Field(..., description="변동 후 재고")
    reason: Optional[str] = Field(None, description="사유")
    reference_number: Optional[str] = Field(None, description="참조 번호")
    created_by: Optional[str] = Field(None, description="처리자")


class MedicationInventoryCreate(MedicationInventoryBase):
    pass


class MedicationInventoryResponse(MedicationInventoryBase):
    id: int
    created_at: datetime
    medication: Optional[MedicationResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


# 건강 측정 스키마
class HealthMeasurementBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    measurement_type: MeasurementType = Field(..., description="측정 항목")
    values: Dict[str, Any] = Field(..., description="측정값")
    measured_by: Optional[str] = Field(None, description="측정자")
    
    is_normal: Optional[bool] = Field(None, description="정상 여부")
    abnormal_findings: Optional[str] = Field(None, description="이상 소견")
    
    action_taken: Optional[str] = Field(None, description="조치사항")
    follow_up_required: bool = Field(False, description="추적관찰 필요")
    follow_up_date: Optional[date] = Field(None, description="추적관찰 날짜")
    
    notes: Optional[str] = Field(None, description="비고")


class HealthMeasurementCreate(HealthMeasurementBase):
    pass


class HealthMeasurementUpdate(BaseModel):
    values: Optional[Dict[str, Any]] = None
    is_normal: Optional[bool] = None
    abnormal_findings: Optional[str] = None
    action_taken: Optional[str] = None
    follow_up_required: Optional[bool] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None


class HealthMeasurementResponse(HealthMeasurementBase):
    id: int
    measured_at: datetime
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 체성분 분석 스키마
class BodyCompositionBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    measurement_id: Optional[int] = Field(None, description="측정 ID")
    device_model: Optional[str] = Field(None, description="측정 장비")
    
    # 기본 측정값
    height: float = Field(..., description="신장 (cm)")
    weight: float = Field(..., description="체중 (kg)")
    bmi: Optional[float] = Field(None, description="BMI")
    
    # 근육/지방
    muscle_mass: Optional[float] = Field(None, description="근육량 (kg)")
    body_fat_mass: Optional[float] = Field(None, description="체지방량 (kg)")
    body_fat_percentage: Optional[float] = Field(None, description="체지방률 (%)")
    visceral_fat_level: Optional[int] = Field(None, description="내장지방 레벨")
    
    # 수분/단백질/무기질
    total_body_water: Optional[float] = Field(None, description="체수분 (L)")
    protein_mass: Optional[float] = Field(None, description="단백질량 (kg)")
    mineral_mass: Optional[float] = Field(None, description="무기질량 (kg)")
    
    # 부위별 근육량
    right_arm_muscle: Optional[float] = None
    left_arm_muscle: Optional[float] = None
    trunk_muscle: Optional[float] = None
    right_leg_muscle: Optional[float] = None
    left_leg_muscle: Optional[float] = None
    
    # 부위별 지방량
    right_arm_fat: Optional[float] = None
    left_arm_fat: Optional[float] = None
    trunk_fat: Optional[float] = None
    right_leg_fat: Optional[float] = None
    left_leg_fat: Optional[float] = None
    
    # 기타
    basal_metabolic_rate: Optional[float] = Field(None, description="기초대사율 (kcal)")
    waist_hip_ratio: Optional[float] = Field(None, description="허리-엉덩이 비율")
    
    fitness_score: Optional[float] = Field(None, description="체력 점수")
    recommendations: Optional[str] = Field(None, description="권장사항")


class BodyCompositionCreate(BodyCompositionBase):
    pass


class BodyCompositionResponse(BodyCompositionBase):
    id: int
    measured_at: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 보건실 방문 스키마
class HealthRoomVisitBase(BaseModel):
    worker_id: int = Field(..., description="근로자 ID")
    chief_complaint: Optional[str] = Field(None, description="주호소")
    
    treatment_provided: Optional[str] = Field(None, description="처치 내용")
    medications_given: Optional[str] = Field(None, description="투약 내역")
    
    measurements_taken: bool = Field(False, description="측정 수행 여부")
    measurement_ids: Optional[List[int]] = Field(None, description="관련 측정 ID들")
    
    rest_taken: bool = Field(False, description="휴식 여부")
    rest_duration_minutes: Optional[int] = Field(None, description="휴식 시간 (분)")
    referred_to_hospital: bool = Field(False, description="병원 의뢰 여부")
    hospital_name: Optional[str] = Field(None, description="의뢰 병원명")
    
    work_related: Optional[bool] = Field(None, description="업무 관련성")
    accident_report_id: Optional[int] = Field(None, description="사고 보고서 ID")
    
    notes: Optional[str] = Field(None, description="비고")
    treated_by: Optional[str] = Field(None, description="처치자")


class HealthRoomVisitCreate(HealthRoomVisitBase):
    pass


class HealthRoomVisitResponse(HealthRoomVisitBase):
    id: int
    visit_datetime: datetime
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# 통계 및 대시보드용 스키마
class MedicationStockAlert(BaseModel):
    """재고 부족 알림"""
    medication: MedicationResponse
    stock_percentage: float
    days_until_expiration: Optional[int] = None


class HealthRoomStatistics(BaseModel):
    """보건실 통계"""
    total_visits_today: int
    total_visits_week: int
    total_visits_month: int
    
    common_complaints: List[Dict[str, Any]]
    medication_usage: List[Dict[str, Any]]
    measurement_summary: Dict[str, int]