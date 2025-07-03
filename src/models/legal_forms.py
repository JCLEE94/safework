"""
법정서식 관리 모델
Legal Forms Management Models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..config.database import Base


class LegalFormStatus(enum.Enum):
    """법정서식 상태"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class LegalFormPriority(enum.Enum):
    """법정서식 우선순위"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LegalFormCategory(enum.Enum):
    """법정서식 분류"""
    SAFETY = "safety"           # 안전관리
    HEALTH = "health"           # 보건관리
    ENVIRONMENT = "environment" # 환경관리
    LABOR = "labor"             # 노무관리
    CONSTRUCTION = "construction" # 건설업무
    REPORTING = "reporting"     # 신고업무
    PERMIT = "permit"           # 허가업무
    INSPECTION = "inspection"   # 점검업무


class LegalForm(Base):
    """법정서식 메인 테이블"""
    __tablename__ = "legal_forms"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    form_code = Column(String(50), unique=True, nullable=False, index=True, comment="서식 코드")
    form_name = Column(String(200), nullable=False, comment="서식명")
    form_name_korean = Column(String(200), nullable=False, comment="한글 서식명")
    category = Column(SQLEnum(LegalFormCategory), nullable=False, comment="서식 분류")
    department = Column(String(100), nullable=True, comment="담당 부서")
    description = Column(Text, nullable=True, comment="서식 설명")
    
    # 폼 필드 정의
    required_fields = Column(JSON, nullable=False, default=list, comment="필수 입력 필드")
    
    # 제출 및 승인 관련
    submission_deadline = Column(DateTime, nullable=True, comment="제출 마감일")
    regulatory_basis = Column(String(500), nullable=True, comment="법적 근거")
    
    # 템플릿 관련
    template_path = Column(String(500), nullable=True, comment="템플릿 파일 경로")
    
    # 상태 및 우선순위
    status = Column(SQLEnum(LegalFormStatus), nullable=False, default=LegalFormStatus.DRAFT, comment="서식 상태")
    priority = Column(SQLEnum(LegalFormPriority), nullable=False, default=LegalFormPriority.MEDIUM, comment="우선순위")
    
    # 담당자 및 승인 관련
    assignee = Column(String(100), nullable=True, comment="담당자")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    submitted_at = Column(DateTime, nullable=True, comment="제출일시")
    approved_at = Column(DateTime, nullable=True, comment="승인일시")
    
    # 버전 관리
    version = Column(Integer, nullable=False, default=1, comment="버전")
    
    # 관계
    attachments = relationship("LegalFormAttachment", back_populates="legal_form", cascade="all, delete-orphan")
    approval_history = relationship("LegalFormApproval", back_populates="legal_form", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<LegalForm(id={self.id}, form_code={self.form_code}, form_name_korean={self.form_name_korean})>"


class LegalFormField(Base):
    """법정서식 필드 정의"""
    __tablename__ = "legal_form_fields"

    id = Column(Integer, primary_key=True, index=True)
    legal_form_id = Column(UUID(as_uuid=True), ForeignKey("legal_forms.id"), nullable=False)
    field_name = Column(String(100), nullable=False, comment="필드명")
    field_label = Column(String(200), nullable=False, comment="필드 라벨")
    field_type = Column(String(50), nullable=False, default="text", comment="필드 타입")
    required = Column(Boolean, nullable=False, default=False, comment="필수 여부")
    validation_rules = Column(JSON, nullable=True, comment="유효성 검사 규칙")
    options = Column(JSON, nullable=True, comment="선택 옵션 (select 타입용)")
    default_value = Column(String(500), nullable=True, comment="기본값")
    help_text = Column(Text, nullable=True, comment="도움말 텍스트")
    display_order = Column(Integer, nullable=False, default=0, comment="표시 순서")
    
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")

    def __repr__(self):
        return f"<LegalFormField(id={self.id}, field_name={self.field_name}, field_label={self.field_label})>"


class LegalFormAttachment(Base):
    """법정서식 첨부파일"""
    __tablename__ = "legal_form_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    legal_form_id = Column(UUID(as_uuid=True), ForeignKey("legal_forms.id"), nullable=False)
    file_name = Column(String(255), nullable=False, comment="파일명")
    file_path = Column(String(500), nullable=False, comment="파일 경로")
    file_size = Column(Integer, nullable=False, comment="파일 크기 (bytes)")
    file_type = Column(String(100), nullable=False, comment="파일 타입")
    uploaded_at = Column(DateTime, server_default=func.now(), comment="업로드일시")
    uploaded_by = Column(String(100), nullable=False, comment="업로드한 사용자")

    # 관계
    legal_form = relationship("LegalForm", back_populates="attachments")

    def __repr__(self):
        return f"<LegalFormAttachment(id={self.id}, file_name={self.file_name})>"


class LegalFormApproval(Base):
    """법정서식 승인 이력"""
    __tablename__ = "legal_form_approvals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    legal_form_id = Column(UUID(as_uuid=True), ForeignKey("legal_forms.id"), nullable=False)
    approver = Column(String(100), nullable=False, comment="승인자")
    status = Column(String(50), nullable=False, comment="승인 상태")
    comment = Column(Text, nullable=True, comment="승인/반려 의견")
    approved_at = Column(DateTime, nullable=True, comment="승인일시")
    
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")

    # 관계
    legal_form = relationship("LegalForm", back_populates="approval_history")

    def __repr__(self):
        return f"<LegalFormApproval(id={self.id}, approver={self.approver}, status={self.status})>"


class UnifiedDocument(Base):
    """통합 문서 관리"""
    __tablename__ = "unified_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, comment="문서 제목")
    type = Column(String(100), nullable=False, comment="문서 타입")
    category = Column(String(100), nullable=False, comment="문서 카테고리")
    file_path = Column(String(500), nullable=False, comment="파일 경로")
    file_size = Column(Integer, nullable=False, comment="파일 크기")
    mime_type = Column(String(200), nullable=False, comment="MIME 타입")
    description = Column(Text, nullable=True, comment="문서 설명")
    tags = Column(JSON, nullable=False, default=list, comment="태그 목록")
    
    # 메타데이터
    created_by = Column(String(100), nullable=False, comment="생성자")
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    
    # 상태 관리
    status = Column(String(50), nullable=False, default="draft", comment="문서 상태")
    version = Column(Integer, nullable=False, default=1, comment="버전")
    is_template = Column(Boolean, nullable=False, default=False, comment="템플릿 여부")
    access_level = Column(String(50), nullable=False, default="public", comment="접근 권한")
    
    # 추가 메타데이터
    document_metadata = Column(JSON, nullable=True, comment="추가 메타데이터")

    def __repr__(self):
        return f"<UnifiedDocument(id={self.id}, title={self.title}, category={self.category})>"