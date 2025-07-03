"""
체크리스트 관리 스키마
Checklist Management Schemas
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from ..models.checklist import ChecklistType, ChecklistStatus, ChecklistPriority


# ===== 체크리스트 템플릿 스키마 =====

class ChecklistTemplateItemSchema(BaseModel):
    """체크리스트 템플릿 항목 스키마"""
    item_code: str = Field(..., description="항목 코드", max_length=50)
    item_name: str = Field(..., description="항목명", max_length=255)
    description: Optional[str] = Field(None, description="상세 설명")
    check_method: Optional[str] = Field(None, description="점검 방법")
    order_index: int = Field(0, description="순서", ge=0)
    category: Optional[str] = Field(None, description="분류", max_length=100)
    is_required: bool = Field(True, description="필수 항목")
    weight: int = Field(1, description="가중치", ge=1)
    max_score: int = Field(1, description="최대 점수", ge=1)


class ChecklistTemplateItemResponse(ChecklistTemplateItemSchema):
    """체크리스트 템플릿 항목 응답 스키마"""
    id: UUID = Field(..., description="항목 ID")
    template_id: UUID = Field(..., description="템플릿 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


class ChecklistTemplateCreate(BaseModel):
    """체크리스트 템플릿 생성 스키마"""
    name: str = Field(..., description="템플릿명", min_length=1, max_length=255)
    name_korean: str = Field(..., description="한글명", min_length=1, max_length=255)
    type: ChecklistType = Field(..., description="체크리스트 유형")
    description: Optional[str] = Field(None, description="설명")
    is_active: bool = Field(True, description="활성 상태")
    is_mandatory: bool = Field(False, description="필수 여부")
    frequency_days: Optional[int] = Field(None, description="주기(일)", ge=1)
    legal_basis: Optional[str] = Field(None, description="법적 근거", max_length=500)
    items: List[ChecklistTemplateItemSchema] = Field(default_factory=list, description="체크리스트 항목")


class ChecklistTemplateUpdate(BaseModel):
    """체크리스트 템플릿 수정 스키마"""
    name: Optional[str] = Field(None, description="템플릿명", min_length=1, max_length=255)
    name_korean: Optional[str] = Field(None, description="한글명", min_length=1, max_length=255)
    type: Optional[ChecklistType] = Field(None, description="체크리스트 유형")
    description: Optional[str] = Field(None, description="설명")
    is_active: Optional[bool] = Field(None, description="활성 상태")
    is_mandatory: Optional[bool] = Field(None, description="필수 여부")
    frequency_days: Optional[int] = Field(None, description="주기(일)", ge=1)
    legal_basis: Optional[str] = Field(None, description="법적 근거", max_length=500)
    items: Optional[List[ChecklistTemplateItemSchema]] = Field(None, description="체크리스트 항목")


class ChecklistTemplateResponse(BaseModel):
    """체크리스트 템플릿 응답 스키마"""
    id: UUID = Field(..., description="템플릿 ID")
    name: str = Field(..., description="템플릿명")
    name_korean: str = Field(..., description="한글명")
    type: ChecklistType = Field(..., description="체크리스트 유형")
    description: Optional[str] = Field(None, description="설명")
    is_active: bool = Field(..., description="활성 상태")
    is_mandatory: bool = Field(..., description="필수 여부")
    frequency_days: Optional[int] = Field(None, description="주기(일)")
    legal_basis: Optional[str] = Field(None, description="법적 근거")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    created_by: str = Field(..., description="생성자")
    items: List[ChecklistTemplateItemResponse] = Field(default_factory=list, description="체크리스트 항목")
    total_instances: Optional[int] = Field(None, description="총 인스턴스 수")

    class Config:
        from_attributes = True


# ===== 체크리스트 인스턴스 스키마 =====

class ChecklistInstanceItemCheck(BaseModel):
    """체크리스트 항목 점검 결과 스키마"""
    template_item_id: UUID = Field(..., description="템플릿 항목 ID")
    is_checked: bool = Field(True, description="점검 완료")
    is_compliant: Optional[bool] = Field(None, description="적합 여부")
    score: Optional[int] = Field(None, description="점수", ge=0)
    findings: Optional[str] = Field(None, description="점검 결과")
    corrective_action: Optional[str] = Field(None, description="시정조치사항")
    corrective_due_date: Optional[datetime] = Field(None, description="시정조치 마감일")


class ChecklistInstanceItemResponse(ChecklistInstanceItemCheck):
    """체크리스트 인스턴스 항목 응답 스키마"""
    id: UUID = Field(..., description="항목 ID")
    instance_id: UUID = Field(..., description="인스턴스 ID")
    checked_at: Optional[datetime] = Field(None, description="점검일시")
    checked_by: Optional[str] = Field(None, description="점검자")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


class ChecklistInstanceCreate(BaseModel):
    """체크리스트 인스턴스 생성 스키마"""
    template_id: UUID = Field(..., description="템플릿 ID")
    title: str = Field(..., description="제목", min_length=1, max_length=255)
    assignee: str = Field(..., description="담당자", min_length=1, max_length=100)
    department: Optional[str] = Field(None, description="담당 부서", max_length=100)
    scheduled_date: datetime = Field(..., description="예정일")
    due_date: Optional[datetime] = Field(None, description="마감일")
    priority: ChecklistPriority = Field(ChecklistPriority.MEDIUM, description="우선순위")
    notes: Optional[str] = Field(None, description="비고")
    location: Optional[str] = Field(None, description="점검 장소", max_length=255)


class ChecklistInstanceUpdate(BaseModel):
    """체크리스트 인스턴스 수정 스키마"""
    title: Optional[str] = Field(None, description="제목", min_length=1, max_length=255)
    assignee: Optional[str] = Field(None, description="담당자", min_length=1, max_length=100)
    department: Optional[str] = Field(None, description="담당 부서", max_length=100)
    scheduled_date: Optional[datetime] = Field(None, description="예정일")
    due_date: Optional[datetime] = Field(None, description="마감일")
    status: Optional[ChecklistStatus] = Field(None, description="상태")
    priority: Optional[ChecklistPriority] = Field(None, description="우선순위")
    notes: Optional[str] = Field(None, description="비고")
    location: Optional[str] = Field(None, description="점검 장소", max_length=255)
    items: Optional[List[ChecklistInstanceItemCheck]] = Field(None, description="점검 항목들")


class ChecklistInstanceResponse(BaseModel):
    """체크리스트 인스턴스 응답 스키마"""
    id: UUID = Field(..., description="인스턴스 ID")
    template_id: UUID = Field(..., description="템플릿 ID")
    title: str = Field(..., description="제목")
    assignee: str = Field(..., description="담당자")
    department: Optional[str] = Field(None, description="담당 부서")
    scheduled_date: datetime = Field(..., description="예정일")
    due_date: Optional[datetime] = Field(None, description="마감일")
    started_at: Optional[datetime] = Field(None, description="시작일시")
    completed_at: Optional[datetime] = Field(None, description="완료일시")
    status: ChecklistStatus = Field(..., description="상태")
    priority: ChecklistPriority = Field(..., description="우선순위")
    total_score: Optional[int] = Field(None, description="총점")
    max_total_score: Optional[int] = Field(None, description="최대 총점")
    completion_rate: Optional[int] = Field(None, description="완료율(%)")
    notes: Optional[str] = Field(None, description="비고")
    location: Optional[str] = Field(None, description="점검 장소")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    created_by: str = Field(..., description="생성자")
    items: List[ChecklistInstanceItemResponse] = Field(default_factory=list, description="점검 항목들")
    template_name: Optional[str] = Field(None, description="템플릿명")

    class Config:
        from_attributes = True


class ChecklistInstanceListResponse(BaseModel):
    """체크리스트 인스턴스 목록 응답 스키마"""
    id: UUID = Field(..., description="인스턴스 ID")
    template_id: UUID = Field(..., description="템플릿 ID")
    title: str = Field(..., description="제목")
    assignee: str = Field(..., description="담당자")
    department: Optional[str] = Field(None, description="담당 부서")
    scheduled_date: datetime = Field(..., description="예정일")
    due_date: Optional[datetime] = Field(None, description="마감일")
    status: ChecklistStatus = Field(..., description="상태")
    priority: ChecklistPriority = Field(..., description="우선순위")
    completion_rate: Optional[int] = Field(None, description="완료율(%)")
    created_at: datetime = Field(..., description="생성일시")
    template_name: Optional[str] = Field(None, description="템플릿명")
    template_type: Optional[ChecklistType] = Field(None, description="템플릿 유형")

    class Config:
        from_attributes = True


# ===== 체크리스트 통계 스키마 =====

class ChecklistStatistics(BaseModel):
    """체크리스트 통계 스키마"""
    total_instances: int = Field(..., description="총 인스턴스 수")
    by_status: Dict[str, int] = Field(..., description="상태별 통계")
    by_type: Dict[str, int] = Field(..., description="유형별 통계")
    by_priority: Dict[str, int] = Field(..., description="우선순위별 통계")
    overdue_count: int = Field(..., description="기한 초과 개수")
    due_soon_count: int = Field(..., description="마감 임박 개수")
    completion_rate: float = Field(..., description="평균 완료율")
    this_month_completed: int = Field(..., description="이번 달 완료 수")


class DepartmentChecklistStats(BaseModel):
    """부서별 체크리스트 통계 스키마"""
    department: str = Field(..., description="부서명")
    total_instances: int = Field(..., description="총 인스턴스 수")
    pending_instances: int = Field(..., description="대기 중인 인스턴스 수")
    overdue_instances: int = Field(..., description="기한 초과 인스턴스 수")
    completion_rate: float = Field(..., description="완료율")


# ===== 필터 및 검색 스키마 =====

class ChecklistFilter(BaseModel):
    """체크리스트 필터 스키마"""
    type: Optional[ChecklistType] = Field(None, description="체크리스트 유형")
    status: Optional[ChecklistStatus] = Field(None, description="상태")
    priority: Optional[ChecklistPriority] = Field(None, description="우선순위")
    assignee: Optional[str] = Field(None, description="담당자")
    department: Optional[str] = Field(None, description="부서")
    due_soon: Optional[bool] = Field(None, description="마감 임박 여부")
    overdue: Optional[bool] = Field(None, description="기한 초과 여부")
    search: Optional[str] = Field(None, description="검색어")


# ===== 페이지네이션 응답 스키마 =====

class PaginatedChecklistTemplateResponse(BaseModel):
    """페이지네이션된 체크리스트 템플릿 응답"""
    items: List[ChecklistTemplateResponse] = Field(..., description="템플릿 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")


class PaginatedChecklistInstanceResponse(BaseModel):
    """페이지네이션된 체크리스트 인스턴스 응답"""
    items: List[ChecklistInstanceListResponse] = Field(..., description="인스턴스 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")


# ===== 스케줄 관리 스키마 =====

class ChecklistScheduleCreate(BaseModel):
    """체크리스트 스케줄 생성 스키마"""
    template_id: UUID = Field(..., description="템플릿 ID")
    name: str = Field(..., description="스케줄명", min_length=1, max_length=255)
    is_active: bool = Field(True, description="활성 상태")
    frequency_type: str = Field(..., description="반복 유형")
    frequency_value: int = Field(1, description="반복 값", ge=1)
    default_assignee: Optional[str] = Field(None, description="기본 담당자", max_length=100)
    default_department: Optional[str] = Field(None, description="기본 담당 부서", max_length=100)
    auto_create_days_before: int = Field(7, description="자동 생성 일수", ge=1)
    reminder_days_before: int = Field(3, description="알림 일수", ge=1)

    @validator('frequency_type')
    def validate_frequency_type(cls, v):
        """반복 유형 유효성 검사"""
        if v not in ['daily', 'weekly', 'monthly', 'yearly']:
            raise ValueError('반복 유형은 daily, weekly, monthly, yearly 중 하나여야 합니다')
        return v


class ChecklistScheduleResponse(ChecklistScheduleCreate):
    """체크리스트 스케줄 응답 스키마"""
    id: UUID = Field(..., description="스케줄 ID")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    last_created_at: Optional[datetime] = Field(None, description="마지막 생성일시")
    next_scheduled_at: Optional[datetime] = Field(None, description="다음 예정일시")

    class Config:
        from_attributes = True