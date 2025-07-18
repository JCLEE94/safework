"""
밀폐공간 작업 관리 스키마
Confined space work management schemas
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from uuid import UUID

from src.models.confined_space import ConfinedSpaceType, HazardType, WorkPermitStatus


# 밀폐공간 스키마
class ConfinedSpaceBase(BaseModel):
    """밀폐공간 기본 스키마"""
    name: str = Field(..., description="밀폐공간명")
    location: str = Field(..., description="위치")
    type: ConfinedSpaceType = Field(..., description="밀폐공간 유형")
    description: Optional[str] = Field(None, description="설명")
    
    # 공간 특성
    volume: Optional[float] = Field(None, description="용적(m³)")
    depth: Optional[float] = Field(None, description="깊이(m)")
    entry_points: int = Field(1, description="출입구 수")
    ventilation_type: Optional[str] = Field(None, description="환기 방식")
    
    # 위험 요인
    hazards: Optional[List[str]] = Field(None, description="위험 요인 목록")
    oxygen_level_normal: Optional[float] = Field(None, description="정상 산소 농도(%)")
    
    # 관리 정보
    responsible_person: Optional[str] = Field(None, description="관리책임자")
    inspection_cycle_days: int = Field(30, description="점검주기(일)")


class ConfinedSpaceCreate(ConfinedSpaceBase):
    """밀폐공간 생성 스키마"""
    pass


class ConfinedSpaceUpdate(BaseModel):
    """밀폐공간 수정 스키마"""
    name: Optional[str] = None
    location: Optional[str] = None
    type: Optional[ConfinedSpaceType] = None
    description: Optional[str] = None
    volume: Optional[float] = None
    depth: Optional[float] = None
    entry_points: Optional[int] = None
    ventilation_type: Optional[str] = None
    hazards: Optional[List[str]] = None
    oxygen_level_normal: Optional[float] = None
    responsible_person: Optional[str] = None
    inspection_cycle_days: Optional[int] = None
    is_active: Optional[bool] = None


class ConfinedSpaceResponse(ConfinedSpaceBase):
    """밀폐공간 응답 스키마"""
    id: UUID
    is_active: bool
    last_inspection_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    
    class Config:
        from_attributes = True


# 작업 허가서 스키마
class WorkerInfo(BaseModel):
    """작업자 정보"""
    name: str = Field(..., description="작업자명")
    role: str = Field(..., description="역할")
    contact: Optional[str] = Field(None, description="연락처")


class GasTestResult(BaseModel):
    """가스 측정 결과"""
    time: datetime = Field(..., description="측정 시간")
    oxygen: float = Field(..., description="산소 농도(%)")
    carbon_monoxide: Optional[float] = Field(None, description="일산화탄소(ppm)")
    hydrogen_sulfide: Optional[float] = Field(None, description="황화수소(ppm)")
    methane: Optional[float] = Field(None, description="메탄(%LEL)")
    is_safe: bool = Field(..., description="안전 여부")


class WorkPermitBase(BaseModel):
    """작업 허가서 기본 스키마"""
    confined_space_id: UUID = Field(..., description="밀폐공간 ID")
    
    # 작업 정보
    work_description: str = Field(..., description="작업 내용")
    work_purpose: Optional[str] = Field(None, description="작업 목적")
    contractor: Optional[str] = Field(None, description="작업 업체")
    
    # 작업 일정
    scheduled_start: datetime = Field(..., description="작업 시작 예정일시")
    scheduled_end: datetime = Field(..., description="작업 종료 예정일시")
    
    # 작업자 정보
    supervisor_name: str = Field(..., description="작업 감독자")
    supervisor_contact: Optional[str] = Field(None, description="감독자 연락처")
    workers: List[WorkerInfo] = Field(..., description="작업자 목록")
    
    # 안전 조치
    hazard_assessment: Optional[Dict[str, Any]] = Field(None, description="위험성 평가")
    safety_measures: Optional[List[str]] = Field(None, description="안전 조치 사항")
    required_ppe: List[str] = Field(..., description="필수 보호구")
    
    # 가스 측정
    gas_test_required: bool = Field(True, description="가스 측정 필요 여부")
    gas_test_interval_minutes: int = Field(60, description="가스 측정 주기(분)")
    
    # 비상 대응
    emergency_contact: Optional[str] = Field(None, description="비상 연락처")
    emergency_procedures: Optional[str] = Field(None, description="비상 대응 절차")
    rescue_equipment: Optional[List[str]] = Field(None, description="구조 장비 목록")


class WorkPermitCreate(WorkPermitBase):
    """작업 허가서 생성 스키마"""
    
    @validator('scheduled_end')
    def validate_schedule(cls, v, values):
        if 'scheduled_start' in values and v <= values['scheduled_start']:
            raise ValueError('종료 시간은 시작 시간보다 늦어야 합니다')
        return v


class WorkPermitUpdate(BaseModel):
    """작업 허가서 수정 스키마"""
    work_description: Optional[str] = None
    work_purpose: Optional[str] = None
    contractor: Optional[str] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None
    actual_start: Optional[datetime] = None
    actual_end: Optional[datetime] = None
    supervisor_name: Optional[str] = None
    supervisor_contact: Optional[str] = None
    workers: Optional[List[WorkerInfo]] = None
    hazard_assessment: Optional[Dict[str, Any]] = None
    safety_measures: Optional[List[str]] = None
    required_ppe: Optional[List[str]] = None
    gas_test_results: Optional[List[GasTestResult]] = None
    emergency_contact: Optional[str] = None
    emergency_procedures: Optional[str] = None
    rescue_equipment: Optional[List[str]] = None


class WorkPermitApproval(BaseModel):
    """작업 허가서 승인 스키마"""
    approved: bool = Field(..., description="승인 여부")
    comments: Optional[str] = Field(None, description="검토 의견")


class WorkPermitResponse(WorkPermitBase):
    """작업 허가서 응답 스키마"""
    id: UUID
    permit_number: str
    status: WorkPermitStatus
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    gas_test_results: Optional[List[GasTestResult]]
    submitted_by: Optional[str]
    submitted_at: Optional[datetime]
    approved_by: Optional[str]
    approved_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 가스 측정 스키마
class GasMeasurementBase(BaseModel):
    """가스 측정 기본 스키마"""
    work_permit_id: UUID = Field(..., description="작업 허가서 ID")
    measurement_location: Optional[str] = Field(None, description="측정 위치")
    measured_by: str = Field(..., description="측정자")
    
    # 측정값
    oxygen_level: float = Field(..., description="산소 농도(%)")
    carbon_monoxide: Optional[float] = Field(None, description="일산화탄소(ppm)")
    hydrogen_sulfide: Optional[float] = Field(None, description="황화수소(ppm)")
    methane: Optional[float] = Field(None, description="메탄(%LEL)")
    other_gases: Optional[Dict[str, float]] = Field(None, description="기타 가스 측정값")
    
    remarks: Optional[str] = Field(None, description="비고")
    
    @validator('oxygen_level')
    def validate_oxygen_level(cls, v):
        if not 0 <= v <= 100:
            raise ValueError('산소 농도는 0-100% 범위여야 합니다')
        return v


class GasMeasurementCreate(GasMeasurementBase):
    """가스 측정 생성 스키마"""
    
    @property
    def is_safe(self) -> bool:
        """안전 여부 자동 판정"""
        # 산소 농도: 18% ~ 23.5%
        if not (18.0 <= self.oxygen_level <= 23.5):
            return False
        
        # 일산화탄소: 30ppm 이하
        if self.carbon_monoxide and self.carbon_monoxide > 30:
            return False
        
        # 황화수소: 10ppm 이하
        if self.hydrogen_sulfide and self.hydrogen_sulfide > 10:
            return False
        
        # 메탄: 10%LEL 이하
        if self.methane and self.methane > 10:
            return False
        
        return True


class GasMeasurementResponse(GasMeasurementBase):
    """가스 측정 응답 스키마"""
    id: UUID
    measurement_time: datetime
    is_safe: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# 안전 체크리스트 스키마
class ChecklistItem(BaseModel):
    """체크리스트 항목"""
    category: str = Field(..., description="카테고리")
    item: str = Field(..., description="점검 항목")
    checked: bool = Field(..., description="체크 여부")
    comment: Optional[str] = Field(None, description="코멘트")


class SafetyChecklistBase(BaseModel):
    """안전 체크리스트 기본 스키마"""
    confined_space_id: UUID = Field(..., description="밀폐공간 ID")
    inspector_name: str = Field(..., description="점검자")
    checklist_items: List[ChecklistItem] = Field(..., description="체크리스트 항목")
    overall_status: str = Field(..., description="전체 상태", pattern="^(안전|조건부안전|위험)$")
    corrective_actions: Optional[List[str]] = Field(None, description="시정 조치 사항")


class SafetyChecklistCreate(SafetyChecklistBase):
    """안전 체크리스트 생성 스키마"""
    pass


class SafetyChecklistResponse(SafetyChecklistBase):
    """안전 체크리스트 응답 스키마"""
    id: UUID
    inspection_date: datetime
    reviewer_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# 통계 스키마
class ConfinedSpaceStatistics(BaseModel):
    """밀폐공간 통계"""
    total_spaces: int = Field(..., description="전체 밀폐공간 수")
    active_spaces: int = Field(..., description="사용 중인 밀폐공간 수")
    permits_today: int = Field(..., description="오늘 작업 허가 수")
    permits_this_month: int = Field(..., description="이번 달 작업 허가 수")
    pending_approvals: int = Field(..., description="승인 대기 중인 허가서")
    overdue_inspections: int = Field(..., description="점검 기한 초과")
    
    by_type: Dict[str, int] = Field(..., description="유형별 밀폐공간 수")
    by_hazard: Dict[str, int] = Field(..., description="위험 요인별 공간 수")
    recent_incidents: int = Field(..., description="최근 사고 발생 수")