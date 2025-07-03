"""
특별관리물질 관리 스키마
Special Materials Management Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

from ..models.special_materials import (
    SpecialMaterialType, ExposureLevel, ControlMeasureType, MonitoringStatus
)


# ===== 특별관리물질 마스터 스키마 =====

class SpecialMaterialCreate(BaseModel):
    """특별관리물질 생성 스키마"""
    material_code: str = Field(..., description="물질 코드", min_length=1, max_length=50)
    material_name: str = Field(..., description="물질명", min_length=1, max_length=255)
    material_name_korean: str = Field(..., description="한글명", min_length=1, max_length=255)
    cas_number: Optional[str] = Field(None, description="CAS 번호", max_length=50)
    
    material_type: SpecialMaterialType = Field(..., description="물질 유형")
    hazard_classification: Optional[str] = Field(None, description="유해성 분류", max_length=500)
    ghs_classification: Optional[Dict[str, Any]] = Field(None, description="GHS 분류")
    
    # 법적 기준
    occupational_exposure_limit: Optional[Decimal] = Field(None, description="작업환경측정 기준")
    short_term_exposure_limit: Optional[Decimal] = Field(None, description="단기노출기준")
    ceiling_limit: Optional[Decimal] = Field(None, description="최고노출기준")
    biological_exposure_index: Optional[Decimal] = Field(None, description="생물학적 노출지수")
    
    # 관리 정보
    is_prohibited: bool = Field(False, description="사용금지 여부")
    requires_permit: bool = Field(True, description="허가 필요 여부")
    monitoring_frequency_days: int = Field(180, description="측정 주기(일)", ge=1)
    health_exam_frequency_months: int = Field(12, description="건강진단 주기(월)", ge=1)
    
    # 물리화학적 성질
    physical_state: Optional[str] = Field(None, description="물리적 상태", max_length=50)
    molecular_weight: Optional[Decimal] = Field(None, description="분자량")
    boiling_point: Optional[Decimal] = Field(None, description="끓는점(℃)")
    melting_point: Optional[Decimal] = Field(None, description="녹는점(℃)")
    vapor_pressure: Optional[Decimal] = Field(None, description="증기압(mmHg)")
    
    # 유해성 정보
    target_organs: Optional[List[str]] = Field(None, description="표적장기")
    health_effects: Optional[str] = Field(None, description="건강 영향")
    exposure_routes: Optional[List[str]] = Field(None, description="노출 경로")
    
    # 안전 정보
    first_aid_measures: Optional[str] = Field(None, description="응급처치 요령")
    safety_precautions: Optional[str] = Field(None, description="안전 주의사항")
    storage_requirements: Optional[str] = Field(None, description="저장 요구사항")
    disposal_methods: Optional[str] = Field(None, description="폐기 방법")


class SpecialMaterialUpdate(BaseModel):
    """특별관리물질 수정 스키마"""
    material_name: Optional[str] = Field(None, description="물질명", min_length=1, max_length=255)
    material_name_korean: Optional[str] = Field(None, description="한글명", min_length=1, max_length=255)
    cas_number: Optional[str] = Field(None, description="CAS 번호", max_length=50)
    
    material_type: Optional[SpecialMaterialType] = Field(None, description="물질 유형")
    hazard_classification: Optional[str] = Field(None, description="유해성 분류", max_length=500)
    ghs_classification: Optional[Dict[str, Any]] = Field(None, description="GHS 분류")
    
    # 법적 기준
    occupational_exposure_limit: Optional[Decimal] = Field(None, description="작업환경측정 기준")
    short_term_exposure_limit: Optional[Decimal] = Field(None, description="단기노출기준")
    ceiling_limit: Optional[Decimal] = Field(None, description="최고노출기준")
    biological_exposure_index: Optional[Decimal] = Field(None, description="생물학적 노출지수")
    
    # 관리 정보
    is_prohibited: Optional[bool] = Field(None, description="사용금지 여부")
    requires_permit: Optional[bool] = Field(None, description="허가 필요 여부")
    monitoring_frequency_days: Optional[int] = Field(None, description="측정 주기(일)", ge=1)
    health_exam_frequency_months: Optional[int] = Field(None, description="건강진단 주기(월)", ge=1)
    
    # 물리화학적 성질
    physical_state: Optional[str] = Field(None, description="물리적 상태", max_length=50)
    molecular_weight: Optional[Decimal] = Field(None, description="분자량")
    boiling_point: Optional[Decimal] = Field(None, description="끓는점(℃)")
    melting_point: Optional[Decimal] = Field(None, description="녹는점(℃)")
    vapor_pressure: Optional[Decimal] = Field(None, description="증기압(mmHg)")
    
    # 유해성 정보
    target_organs: Optional[List[str]] = Field(None, description="표적장기")
    health_effects: Optional[str] = Field(None, description="건강 영향")
    exposure_routes: Optional[List[str]] = Field(None, description="노출 경로")
    
    # 안전 정보
    first_aid_measures: Optional[str] = Field(None, description="응급처치 요령")
    safety_precautions: Optional[str] = Field(None, description="안전 주의사항")
    storage_requirements: Optional[str] = Field(None, description="저장 요구사항")
    disposal_methods: Optional[str] = Field(None, description="폐기 방법")


class SpecialMaterialResponse(BaseModel):
    """특별관리물질 응답 스키마"""
    id: UUID = Field(..., description="물질 ID")
    material_code: str = Field(..., description="물질 코드")
    material_name: str = Field(..., description="물질명")
    material_name_korean: str = Field(..., description="한글명")
    cas_number: Optional[str] = Field(None, description="CAS 번호")
    
    material_type: SpecialMaterialType = Field(..., description="물질 유형")
    hazard_classification: Optional[str] = Field(None, description="유해성 분류")
    ghs_classification: Optional[Dict[str, Any]] = Field(None, description="GHS 분류")
    
    # 법적 기준
    occupational_exposure_limit: Optional[Decimal] = Field(None, description="작업환경측정 기준")
    short_term_exposure_limit: Optional[Decimal] = Field(None, description="단기노출기준")
    ceiling_limit: Optional[Decimal] = Field(None, description="최고노출기준")
    biological_exposure_index: Optional[Decimal] = Field(None, description="생물학적 노출지수")
    
    # 관리 정보
    is_prohibited: bool = Field(..., description="사용금지 여부")
    requires_permit: bool = Field(..., description="허가 필요 여부")
    monitoring_frequency_days: int = Field(..., description="측정 주기(일)")
    health_exam_frequency_months: int = Field(..., description="건강진단 주기(월)")
    
    # 물리화학적 성질
    physical_state: Optional[str] = Field(None, description="물리적 상태")
    molecular_weight: Optional[Decimal] = Field(None, description="분자량")
    boiling_point: Optional[Decimal] = Field(None, description="끓는점(℃)")
    melting_point: Optional[Decimal] = Field(None, description="녹는점(℃)")
    vapor_pressure: Optional[Decimal] = Field(None, description="증기압(mmHg)")
    
    # 유해성 정보
    target_organs: Optional[List[str]] = Field(None, description="표적장기")
    health_effects: Optional[str] = Field(None, description="건강 영향")
    exposure_routes: Optional[List[str]] = Field(None, description="노출 경로")
    
    # 안전 정보
    first_aid_measures: Optional[str] = Field(None, description="응급처치 요령")
    safety_precautions: Optional[str] = Field(None, description="안전 주의사항")
    storage_requirements: Optional[str] = Field(None, description="저장 요구사항")
    disposal_methods: Optional[str] = Field(None, description="폐기 방법")
    
    # 메타데이터
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    created_by: str = Field(..., description="생성자")
    
    # 관련 통계
    total_usage_records: Optional[int] = Field(None, description="총 사용 기록 수")
    total_monitoring_records: Optional[int] = Field(None, description="총 모니터링 기록 수")
    last_monitoring_date: Optional[datetime] = Field(None, description="마지막 모니터링 일시")

    class Config:
        from_attributes = True


# ===== 사용 기록 스키마 =====

class SpecialMaterialUsageCreate(BaseModel):
    """특별관리물질 사용 기록 생성 스키마"""
    material_id: UUID = Field(..., description="물질 ID")
    
    # 사용 정보
    usage_date: datetime = Field(..., description="사용일시")
    usage_location: str = Field(..., description="사용 장소", min_length=1, max_length=255)
    usage_purpose: str = Field(..., description="사용 목적", min_length=1, max_length=500)
    work_process: Optional[str] = Field(None, description="작업 공정", max_length=500)
    
    # 수량 정보
    quantity_used: Decimal = Field(..., description="사용량", ge=0)
    unit: str = Field(..., description="단위", min_length=1, max_length=20)
    concentration: Optional[Decimal] = Field(None, description="농도(%)", ge=0, le=100)
    
    # 작업자 정보
    worker_id: Optional[UUID] = Field(None, description="작업자 ID")
    worker_count: int = Field(1, description="작업자 수", ge=1)
    exposure_duration_hours: Optional[Decimal] = Field(None, description="노출 시간(시간)", ge=0)
    
    # 관리 조치
    control_measures: Optional[List[str]] = Field(None, description="관리 조치")
    ppe_used: Optional[List[str]] = Field(None, description="사용 개인보호구")
    ventilation_type: Optional[str] = Field(None, description="환기 방식", max_length=100)
    
    # 승인 정보
    approved_by: Optional[str] = Field(None, description="승인자", max_length=100)
    approval_date: Optional[datetime] = Field(None, description="승인일시")
    permit_number: Optional[str] = Field(None, description="허가번호", max_length=100)


class SpecialMaterialUsageResponse(SpecialMaterialUsageCreate):
    """특별관리물질 사용 기록 응답 스키마"""
    id: UUID = Field(..., description="사용 기록 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    recorded_by: str = Field(..., description="기록자")
    
    # 관련 정보
    material_name: Optional[str] = Field(None, description="물질명")
    worker_name: Optional[str] = Field(None, description="작업자명")

    class Config:
        from_attributes = True


# ===== 노출 평가 스키마 =====

class ExposureAssessmentCreate(BaseModel):
    """노출 평가 생성 스키마"""
    material_id: UUID = Field(..., description="물질 ID")
    
    # 평가 정보
    assessment_date: datetime = Field(..., description="평가일시")
    assessment_type: str = Field(..., description="평가 유형", min_length=1, max_length=100)
    assessment_location: str = Field(..., description="평가 장소", min_length=1, max_length=255)
    work_activity: str = Field(..., description="작업 활동", min_length=1, max_length=500)
    
    # 측정 결과
    measured_concentration: Optional[Decimal] = Field(None, description="측정 농도", ge=0)
    measurement_unit: Optional[str] = Field(None, description="측정 단위", max_length=20)
    sampling_duration_minutes: Optional[int] = Field(None, description="시료채취 시간(분)", ge=1)
    sampling_method: Optional[str] = Field(None, description="시료채취 방법", max_length=200)
    analysis_method: Optional[str] = Field(None, description="분석 방법", max_length=200)
    
    # 노출 평가
    exposure_level: ExposureLevel = Field(..., description="노출 수준")
    exposure_route: Optional[str] = Field(None, description="주요 노출 경로", max_length=100)
    risk_score: Optional[Decimal] = Field(None, description="위험도 점수", ge=0, le=10)
    
    # 관리 조치 권고
    recommended_controls: Optional[List[str]] = Field(None, description="권고 관리 조치")
    priority_level: str = Field("medium", description="우선순위", max_length=20)
    follow_up_required: bool = Field(False, description="후속조치 필요")
    follow_up_date: Optional[datetime] = Field(None, description="후속조치 예정일")
    
    # 평가자 정보
    assessor_name: str = Field(..., description="평가자명", min_length=1, max_length=100)
    assessor_qualification: Optional[str] = Field(None, description="평가자 자격", max_length=200)
    assessment_organization: Optional[str] = Field(None, description="평가기관", max_length=200)


class ExposureAssessmentResponse(ExposureAssessmentCreate):
    """노출 평가 응답 스키마"""
    id: UUID = Field(..., description="평가 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    
    # 관련 정보
    material_name: Optional[str] = Field(None, description="물질명")

    class Config:
        from_attributes = True


# ===== 모니터링 스키마 =====

class SpecialMaterialMonitoringCreate(BaseModel):
    """특별관리물질 모니터링 생성 스키마"""
    material_id: UUID = Field(..., description="물질 ID")
    
    # 모니터링 기본 정보
    monitoring_date: datetime = Field(..., description="모니터링 일시")
    monitoring_type: str = Field(..., description="모니터링 유형", min_length=1, max_length=100)
    location: str = Field(..., description="모니터링 장소", min_length=1, max_length=255)
    
    # 모니터링 계획
    scheduled_date: datetime = Field(..., description="예정일")
    frequency_type: str = Field(..., description="주기 유형", min_length=1, max_length=50)
    next_monitoring_date: Optional[datetime] = Field(None, description="다음 모니터링 예정일")
    
    # 모니터링 결과
    measurement_results: Optional[Dict[str, Any]] = Field(None, description="측정 결과")
    compliance_status: Optional[bool] = Field(None, description="기준 준수 여부")
    exceedance_factor: Optional[Decimal] = Field(None, description="기준 초과배수", ge=0)
    
    # 시정조치
    corrective_actions: Optional[List[str]] = Field(None, description="시정조치사항")
    action_due_date: Optional[datetime] = Field(None, description="시정조치 마감일")
    action_responsible: Optional[str] = Field(None, description="시정조치 담당자", max_length=100)
    action_status: Optional[str] = Field(None, description="시정조치 상태", max_length=50)
    
    # 담당자 정보
    monitor_name: str = Field(..., description="모니터링 담당자", min_length=1, max_length=100)
    monitor_organization: Optional[str] = Field(None, description="모니터링 기관", max_length=200)
    report_number: Optional[str] = Field(None, description="보고서 번호", max_length=100)


class SpecialMaterialMonitoringResponse(SpecialMaterialMonitoringCreate):
    """특별관리물질 모니터링 응답 스키마"""
    id: UUID = Field(..., description="모니터링 ID")
    status: MonitoringStatus = Field(..., description="상태")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    created_by: str = Field(..., description="생성자")
    
    # 관련 정보
    material_name: Optional[str] = Field(None, description="물질명")

    class Config:
        from_attributes = True


# ===== 관리 조치 스키마 =====

class ControlMeasureCreate(BaseModel):
    """관리 조치 생성 스키마"""
    material_id: UUID = Field(..., description="물질 ID")
    
    # 조치 정보
    measure_type: ControlMeasureType = Field(..., description="조치 유형")
    measure_name: str = Field(..., description="조치명", min_length=1, max_length=255)
    description: str = Field(..., description="상세 설명", min_length=1)
    implementation_date: datetime = Field(..., description="시행일")
    
    # 효과성 정보
    effectiveness_rating: Optional[int] = Field(None, description="효과성 등급(1-5)", ge=1, le=5)
    cost_estimate: Optional[Decimal] = Field(None, description="예상 비용", ge=0)
    maintenance_frequency: Optional[str] = Field(None, description="유지보수 주기", max_length=100)
    
    # 책임자 정보
    responsible_person: str = Field(..., description="책임자", min_length=1, max_length=100)
    responsible_department: Optional[str] = Field(None, description="담당 부서", max_length=100)
    
    # 상태 정보
    is_active: bool = Field(True, description="활성 상태")
    last_inspection_date: Optional[datetime] = Field(None, description="마지막 점검일")
    next_inspection_date: Optional[datetime] = Field(None, description="다음 점검 예정일")


class ControlMeasureResponse(ControlMeasureCreate):
    """관리 조치 응답 스키마"""
    id: UUID = Field(..., description="조치 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    created_by: str = Field(..., description="생성자")
    
    # 관련 정보
    material_name: Optional[str] = Field(None, description="물질명")

    class Config:
        from_attributes = True


# ===== 통계 스키마 =====

class SpecialMaterialStatistics(BaseModel):
    """특별관리물질 통계 스키마"""
    total_materials: int = Field(..., description="총 물질 수")
    by_type: Dict[str, int] = Field(..., description="유형별 통계")
    prohibited_materials: int = Field(..., description="사용금지 물질 수")
    permit_required_materials: int = Field(..., description="허가 필요 물질 수")
    total_usage_records: int = Field(..., description="총 사용 기록 수")
    total_exposure_assessments: int = Field(..., description="총 노출 평가 수")
    high_risk_exposures: int = Field(..., description="고위험 노출 수")
    overdue_monitoring: int = Field(..., description="기한 초과 모니터링 수")
    pending_corrective_actions: int = Field(..., description="대기 중인 시정조치 수")


class DepartmentSpecialMaterialStats(BaseModel):
    """부서별 특별관리물질 통계 스키마"""
    department: str = Field(..., description="부서명")
    total_materials_used: int = Field(..., description="사용 물질 수")
    total_usage_records: int = Field(..., description="총 사용 기록 수")
    high_risk_exposures: int = Field(..., description="고위험 노출 수")
    overdue_monitoring: int = Field(..., description="기한 초과 모니터링 수")
    compliance_rate: float = Field(..., description="준수율")


# ===== 필터 및 검색 스키마 =====

class SpecialMaterialFilter(BaseModel):
    """특별관리물질 필터 스키마"""
    material_type: Optional[SpecialMaterialType] = Field(None, description="물질 유형")
    is_prohibited: Optional[bool] = Field(None, description="사용금지 여부")
    requires_permit: Optional[bool] = Field(None, description="허가 필요 여부")
    search: Optional[str] = Field(None, description="검색어")


# ===== 페이지네이션 응답 스키마 =====

class PaginatedSpecialMaterialResponse(BaseModel):
    """페이지네이션된 특별관리물질 응답"""
    items: List[SpecialMaterialResponse] = Field(..., description="물질 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")


class PaginatedUsageResponse(BaseModel):
    """페이지네이션된 사용 기록 응답"""
    items: List[SpecialMaterialUsageResponse] = Field(..., description="사용 기록 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")


class PaginatedMonitoringResponse(BaseModel):
    """페이지네이션된 모니터링 응답"""
    items: List[SpecialMaterialMonitoringResponse] = Field(..., description="모니터링 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")