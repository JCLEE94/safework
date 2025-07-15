"""
법정서식 관리 스키마
Legal Forms Management Schemas
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator

from ..models.legal_forms import (LegalFormCategory, LegalFormPriority,
                                  LegalFormStatus)

# ===== 기본 스키마 =====


class LegalFormFieldSchema(BaseModel):
    """법정서식 필드 스키마"""

    field_name: str = Field(..., description="필드명")
    field_label: str = Field(..., description="필드 라벨")
    field_type: str = Field(default="text", description="필드 타입")
    required: bool = Field(default=False, description="필수 여부")
    validation_rules: Optional[Dict[str, Any]] = Field(
        None, description="유효성 검사 규칙"
    )
    options: Optional[List[str]] = Field(None, description="선택 옵션")
    default_value: Optional[str] = Field(None, description="기본값")
    help_text: Optional[str] = Field(None, description="도움말 텍스트")


class LegalFormAttachmentSchema(BaseModel):
    """법정서식 첨부파일 스키마"""

    id: UUID
    file_name: str = Field(..., description="파일명")
    file_size: int = Field(..., description="파일 크기")
    file_type: str = Field(..., description="파일 타입")
    uploaded_at: datetime = Field(..., description="업로드일시")
    uploaded_by: str = Field(..., description="업로드한 사용자")

    class Config:
        from_attributes = True


class LegalFormApprovalSchema(BaseModel):
    """법정서식 승인 이력 스키마"""

    id: UUID
    approver: str = Field(..., description="승인자")
    status: str = Field(..., description="승인 상태")
    comment: Optional[str] = Field(None, description="승인/반려 의견")
    approved_at: Optional[datetime] = Field(None, description="승인일시")

    class Config:
        from_attributes = True


# ===== 생성/수정 스키마 =====


class LegalFormCreate(BaseModel):
    """법정서식 생성 스키마"""

    form_code: str = Field(..., description="서식 코드", min_length=1, max_length=50)
    form_name: str = Field(..., description="서식명", min_length=1, max_length=200)
    form_name_korean: str = Field(
        ..., description="한글 서식명", min_length=1, max_length=200
    )
    category: LegalFormCategory = Field(..., description="서식 분류")
    department: Optional[str] = Field(None, description="담당 부서", max_length=100)
    description: Optional[str] = Field(None, description="서식 설명")
    required_fields: List[LegalFormFieldSchema] = Field(
        default_factory=list, description="필수 입력 필드"
    )
    submission_deadline: Optional[datetime] = Field(None, description="제출 마감일")
    regulatory_basis: Optional[str] = Field(
        None, description="법적 근거", max_length=500
    )
    template_path: Optional[str] = Field(
        None, description="템플릿 파일 경로", max_length=500
    )
    priority: LegalFormPriority = Field(
        default=LegalFormPriority.MEDIUM, description="우선순위"
    )
    assignee: Optional[str] = Field(None, description="담당자", max_length=100)

    @validator("form_code")
    def validate_form_code(cls, v):
        """서식 코드 유효성 검사"""
        if not v or not v.strip():
            raise ValueError("서식 코드는 필수입니다")
        return v.strip().upper()

    @validator("form_name_korean")
    def validate_form_name_korean(cls, v):
        """한글 서식명 유효성 검사"""
        if not v or not v.strip():
            raise ValueError("한글 서식명은 필수입니다")
        return v.strip()


class LegalFormUpdate(BaseModel):
    """법정서식 수정 스키마"""

    form_name: Optional[str] = Field(
        None, description="서식명", min_length=1, max_length=200
    )
    form_name_korean: Optional[str] = Field(
        None, description="한글 서식명", min_length=1, max_length=200
    )
    category: Optional[LegalFormCategory] = Field(None, description="서식 분류")
    department: Optional[str] = Field(None, description="담당 부서", max_length=100)
    description: Optional[str] = Field(None, description="서식 설명")
    required_fields: Optional[List[LegalFormFieldSchema]] = Field(
        None, description="필수 입력 필드"
    )
    submission_deadline: Optional[datetime] = Field(None, description="제출 마감일")
    regulatory_basis: Optional[str] = Field(
        None, description="법적 근거", max_length=500
    )
    template_path: Optional[str] = Field(
        None, description="템플릿 파일 경로", max_length=500
    )
    status: Optional[LegalFormStatus] = Field(None, description="서식 상태")
    priority: Optional[LegalFormPriority] = Field(None, description="우선순위")
    assignee: Optional[str] = Field(None, description="담당자", max_length=100)


# ===== 응답 스키마 =====


class LegalFormResponse(BaseModel):
    """법정서식 응답 스키마"""

    id: UUID = Field(..., description="서식 ID")
    form_code: str = Field(..., description="서식 코드")
    form_name: str = Field(..., description="서식명")
    form_name_korean: str = Field(..., description="한글 서식명")
    category: LegalFormCategory = Field(..., description="서식 분류")
    department: Optional[str] = Field(None, description="담당 부서")
    description: Optional[str] = Field(None, description="서식 설명")
    required_fields: List[Dict[str, Any]] = Field(..., description="필수 입력 필드")
    submission_deadline: Optional[datetime] = Field(None, description="제출 마감일")
    regulatory_basis: Optional[str] = Field(None, description="법적 근거")
    template_path: Optional[str] = Field(None, description="템플릿 파일 경로")
    status: LegalFormStatus = Field(..., description="서식 상태")
    priority: LegalFormPriority = Field(..., description="우선순위")
    assignee: Optional[str] = Field(None, description="담당자")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    submitted_at: Optional[datetime] = Field(None, description="제출일시")
    approved_at: Optional[datetime] = Field(None, description="승인일시")
    version: int = Field(..., description="버전")
    attachments: List[LegalFormAttachmentSchema] = Field(
        default_factory=list, description="첨부파일"
    )
    approval_history: List[LegalFormApprovalSchema] = Field(
        default_factory=list, description="승인 이력"
    )

    class Config:
        from_attributes = True


class LegalFormListResponse(BaseModel):
    """법정서식 목록 응답 스키마"""

    id: UUID = Field(..., description="서식 ID")
    form_code: str = Field(..., description="서식 코드")
    form_name_korean: str = Field(..., description="한글 서식명")
    category: LegalFormCategory = Field(..., description="서식 분류")
    department: Optional[str] = Field(None, description="담당 부서")
    status: LegalFormStatus = Field(..., description="서식 상태")
    priority: LegalFormPriority = Field(..., description="우선순위")
    assignee: Optional[str] = Field(None, description="담당자")
    submission_deadline: Optional[datetime] = Field(None, description="제출 마감일")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    class Config:
        from_attributes = True


# ===== 통계 스키마 =====


class LegalFormStatistics(BaseModel):
    """법정서식 통계 스키마"""

    total_forms: int = Field(..., description="총 서식 수")
    by_status: Dict[str, int] = Field(..., description="상태별 통계")
    by_category: Dict[str, int] = Field(..., description="분류별 통계")
    by_priority: Dict[str, int] = Field(..., description="우선순위별 통계")
    upcoming_deadlines: int = Field(..., description="마감 임박 서식 수")
    overdue_forms: int = Field(..., description="마감 초과 서식 수")
    completion_rate: float = Field(..., description="완료율")
    monthly_submissions: int = Field(..., description="이번 달 제출 수")


class DepartmentStatistics(BaseModel):
    """부서별 통계 스키마"""

    department: str = Field(..., description="부서명")
    total_forms: int = Field(..., description="총 서식 수")
    pending_forms: int = Field(..., description="대기 중인 서식 수")
    overdue_forms: int = Field(..., description="마감 초과 서식 수")
    completion_rate: float = Field(..., description="완료율")


# ===== 통합 문서 스키마 =====


class UnifiedDocumentCreate(BaseModel):
    """통합 문서 생성 스키마"""

    title: str = Field(..., description="문서 제목", min_length=1, max_length=255)
    type: str = Field(..., description="문서 타입", max_length=100)
    category: str = Field(..., description="문서 카테고리", max_length=100)
    description: Optional[str] = Field(None, description="문서 설명")
    tags: List[str] = Field(default_factory=list, description="태그 목록")
    is_template: bool = Field(default=False, description="템플릿 여부")
    access_level: str = Field(default="public", description="접근 권한")
    document_metadata: Optional[Dict[str, Any]] = Field(
        None, description="추가 메타데이터"
    )


class UnifiedDocumentUpdate(BaseModel):
    """통합 문서 수정 스키마"""

    title: Optional[str] = Field(
        None, description="문서 제목", min_length=1, max_length=255
    )
    type: Optional[str] = Field(None, description="문서 타입", max_length=100)
    category: Optional[str] = Field(None, description="문서 카테고리", max_length=100)
    description: Optional[str] = Field(None, description="문서 설명")
    tags: Optional[List[str]] = Field(None, description="태그 목록")
    status: Optional[str] = Field(None, description="문서 상태")
    is_template: Optional[bool] = Field(None, description="템플릿 여부")
    access_level: Optional[str] = Field(None, description="접근 권한")
    document_metadata: Optional[Dict[str, Any]] = Field(
        None, description="추가 메타데이터"
    )


class UnifiedDocumentResponse(BaseModel):
    """통합 문서 응답 스키마"""

    id: int = Field(..., description="문서 ID")
    title: str = Field(..., description="문서 제목")
    type: str = Field(..., description="문서 타입")
    category: str = Field(..., description="문서 카테고리")
    file_path: str = Field(..., description="파일 경로")
    file_size: int = Field(..., description="파일 크기")
    mime_type: str = Field(..., description="MIME 타입")
    description: Optional[str] = Field(None, description="문서 설명")
    tags: List[str] = Field(..., description="태그 목록")
    created_by: str = Field(..., description="생성자")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    status: str = Field(..., description="문서 상태")
    version: int = Field(..., description="버전")
    is_template: bool = Field(..., description="템플릿 여부")
    access_level: str = Field(..., description="접근 권한")
    document_metadata: Optional[Dict[str, Any]] = Field(
        None, description="추가 메타데이터"
    )

    class Config:
        from_attributes = True


# ===== 필터 및 검색 스키마 =====


class LegalFormFilter(BaseModel):
    """법정서식 필터 스키마"""

    category: Optional[LegalFormCategory] = Field(None, description="서식 분류")
    status: Optional[LegalFormStatus] = Field(None, description="서식 상태")
    priority: Optional[LegalFormPriority] = Field(None, description="우선순위")
    department: Optional[str] = Field(None, description="담당 부서")
    assignee: Optional[str] = Field(None, description="담당자")
    deadline_upcoming: Optional[bool] = Field(None, description="마감 임박 여부")
    search: Optional[str] = Field(None, description="검색어")


class DocumentCategoryStats(BaseModel):
    """문서 카테고리 통계 스키마"""

    category_id: str = Field(..., description="카테고리 ID")
    category_name: str = Field(..., description="카테고리명")
    count: int = Field(..., description="문서 수")
    templates: int = Field(..., description="템플릿 수")


# ===== 페이지네이션 응답 스키마 =====


class PaginatedLegalFormResponse(BaseModel):
    """페이지네이션된 법정서식 응답"""

    items: List[LegalFormListResponse] = Field(..., description="법정서식 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")


class PaginatedDocumentResponse(BaseModel):
    """페이지네이션된 문서 응답"""

    items: List[UnifiedDocumentResponse] = Field(..., description="문서 목록")
    total: int = Field(..., description="전체 개수")
    page: int = Field(..., description="현재 페이지")
    size: int = Field(..., description="페이지 크기")
    pages: int = Field(..., description="전체 페이지 수")
