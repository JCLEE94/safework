"""
체크리스트 관리 모델
Checklist Management Models
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..config.database import Base


class ChecklistType(enum.Enum):
    """체크리스트 유형"""

    SAFETY_MANAGEMENT = "safety_management"  # 안전보건관리체계
    RISK_ASSESSMENT = "risk_assessment"  # 위험요인조사
    ACCIDENT_RESPONSE = "accident_response"  # 산업재해대응
    HEALTH_MANAGEMENT = "health_management"  # 건강관리
    EDUCATION_TRAINING = "education_training"  # 교육훈련
    FACILITY_INSPECTION = "facility_inspection"  # 시설점검
    ENVIRONMENT_MONITORING = "environment_monitoring"  # 환경측정
    CHEMICAL_MANAGEMENT = "chemical_management"  # 화학물질관리
    EMERGENCY_RESPONSE = "emergency_response"  # 비상대응
    COMPLIANCE_CHECK = "compliance_check"  # 법령준수


class ChecklistStatus(enum.Enum):
    """체크리스트 상태"""

    PENDING = "pending"  # 대기
    IN_PROGRESS = "in_progress"  # 진행중
    COMPLETED = "completed"  # 완료
    OVERDUE = "overdue"  # 기한초과
    CANCELLED = "cancelled"  # 취소


class ChecklistPriority(enum.Enum):
    """체크리스트 우선순위"""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ChecklistTemplate(Base):
    """체크리스트 템플릿"""

    __tablename__ = "checklist_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, comment="템플릿명")
    name_korean = Column(String(255), nullable=False, comment="한글명")
    type = Column(SQLEnum(ChecklistType), nullable=False, comment="체크리스트 유형")
    description = Column(Text, nullable=True, comment="설명")

    # 템플릿 설정
    is_active = Column(Boolean, nullable=False, default=True, comment="활성 상태")
    is_mandatory = Column(Boolean, nullable=False, default=False, comment="필수 여부")
    frequency_days = Column(Integer, nullable=True, comment="주기(일)")

    # 법적 근거
    legal_basis = Column(String(500), nullable=True, comment="법적 근거")

    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시"
    )
    created_by = Column(String(100), nullable=False, comment="생성자")

    # 관계
    items = relationship(
        "ChecklistTemplateItem", back_populates="template", cascade="all, delete-orphan"
    )
    instances = relationship("ChecklistInstance", back_populates="template")

    def __repr__(self):
        return f"<ChecklistTemplate(id={self.id}, name={self.name_korean})>"


class ChecklistTemplateItem(Base):
    """체크리스트 템플릿 항목"""

    __tablename__ = "checklist_template_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("checklist_templates.id"), nullable=False
    )

    # 항목 정보
    item_code = Column(String(50), nullable=False, comment="항목 코드")
    item_name = Column(String(255), nullable=False, comment="항목명")
    description = Column(Text, nullable=True, comment="상세 설명")
    check_method = Column(Text, nullable=True, comment="점검 방법")

    # 순서 및 분류
    order_index = Column(Integer, nullable=False, default=0, comment="순서")
    category = Column(String(100), nullable=True, comment="분류")

    # 필수 여부
    is_required = Column(Boolean, nullable=False, default=True, comment="필수 항목")

    # 점수 또는 가중치
    weight = Column(Integer, nullable=False, default=1, comment="가중치")
    max_score = Column(Integer, nullable=False, default=1, comment="최대 점수")

    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시"
    )

    # 관계
    template = relationship("ChecklistTemplate", back_populates="items")

    def __repr__(self):
        return f"<ChecklistTemplateItem(id={self.id}, item_name={self.item_name})>"


class ChecklistInstance(Base):
    """체크리스트 인스턴스 (실제 수행)"""

    __tablename__ = "checklist_instances"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("checklist_templates.id"), nullable=False
    )

    # 수행 정보
    title = Column(String(255), nullable=False, comment="제목")
    assignee = Column(String(100), nullable=False, comment="담당자")
    department = Column(String(100), nullable=True, comment="담당 부서")

    # 일정
    scheduled_date = Column(DateTime, nullable=False, comment="예정일")
    due_date = Column(DateTime, nullable=True, comment="마감일")
    started_at = Column(DateTime, nullable=True, comment="시작일시")
    completed_at = Column(DateTime, nullable=True, comment="완료일시")

    # 상태 및 우선순위
    status = Column(
        SQLEnum(ChecklistStatus),
        nullable=False,
        default=ChecklistStatus.PENDING,
        comment="상태",
    )
    priority = Column(
        SQLEnum(ChecklistPriority),
        nullable=False,
        default=ChecklistPriority.MEDIUM,
        comment="우선순위",
    )

    # 결과 정보
    total_score = Column(Integer, nullable=True, comment="총점")
    max_total_score = Column(Integer, nullable=True, comment="최대 총점")
    completion_rate = Column(Integer, nullable=True, comment="완료율(%)")

    # 추가 정보
    notes = Column(Text, nullable=True, comment="비고")
    location = Column(String(255), nullable=True, comment="점검 장소")

    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시"
    )
    created_by = Column(String(100), nullable=False, comment="생성자")

    # 관계
    template = relationship("ChecklistTemplate", back_populates="instances")
    items = relationship(
        "ChecklistInstanceItem", back_populates="instance", cascade="all, delete-orphan"
    )
    attachments = relationship(
        "ChecklistAttachment", back_populates="instance", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ChecklistInstance(id={self.id}, title={self.title}, status={self.status})>"


class ChecklistInstanceItem(Base):
    """체크리스트 인스턴스 항목 (실제 점검 결과)"""

    __tablename__ = "checklist_instance_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    instance_id = Column(
        UUID(as_uuid=True), ForeignKey("checklist_instances.id"), nullable=False
    )
    template_item_id = Column(
        UUID(as_uuid=True), ForeignKey("checklist_template_items.id"), nullable=False
    )

    # 점검 결과
    is_checked = Column(Boolean, nullable=False, default=False, comment="점검 완료")
    is_compliant = Column(Boolean, nullable=True, comment="적합 여부")
    score = Column(Integer, nullable=True, comment="점수")

    # 점검 세부사항
    checked_at = Column(DateTime, nullable=True, comment="점검일시")
    checked_by = Column(String(100), nullable=True, comment="점검자")
    findings = Column(Text, nullable=True, comment="점검 결과")
    corrective_action = Column(Text, nullable=True, comment="시정조치사항")
    corrective_due_date = Column(DateTime, nullable=True, comment="시정조치 마감일")

    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시"
    )

    # 관계
    instance = relationship("ChecklistInstance", back_populates="items")

    def __repr__(self):
        return f"<ChecklistInstanceItem(id={self.id}, is_checked={self.is_checked}, is_compliant={self.is_compliant})>"


class ChecklistAttachment(Base):
    """체크리스트 첨부파일"""

    __tablename__ = "checklist_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    instance_id = Column(
        UUID(as_uuid=True), ForeignKey("checklist_instances.id"), nullable=False
    )

    # 파일 정보
    file_name = Column(String(255), nullable=False, comment="파일명")
    file_path = Column(String(500), nullable=False, comment="파일 경로")
    file_size = Column(Integer, nullable=False, comment="파일 크기")
    file_type = Column(String(100), nullable=False, comment="파일 타입")

    # 첨부 정보
    uploaded_by = Column(String(100), nullable=False, comment="업로드자")
    uploaded_at = Column(DateTime, server_default=func.now(), comment="업로드일시")
    description = Column(Text, nullable=True, comment="설명")

    # 관계
    instance = relationship("ChecklistInstance", back_populates="attachments")

    def __repr__(self):
        return f"<ChecklistAttachment(id={self.id}, file_name={self.file_name})>"


class ChecklistSchedule(Base):
    """체크리스트 스케줄 (자동 생성 규칙)"""

    __tablename__ = "checklist_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    template_id = Column(
        UUID(as_uuid=True), ForeignKey("checklist_templates.id"), nullable=False
    )

    # 스케줄 정보
    name = Column(String(255), nullable=False, comment="스케줄명")
    is_active = Column(Boolean, nullable=False, default=True, comment="활성 상태")

    # 반복 설정
    frequency_type = Column(
        String(20), nullable=False, comment="반복 유형 (daily/weekly/monthly/yearly)"
    )
    frequency_value = Column(Integer, nullable=False, default=1, comment="반복 값")

    # 담당자 설정
    default_assignee = Column(String(100), nullable=True, comment="기본 담당자")
    default_department = Column(String(100), nullable=True, comment="기본 담당 부서")

    # 자동 생성 설정
    auto_create_days_before = Column(
        Integer, nullable=False, default=7, comment="자동 생성 일수 (사전)"
    )
    reminder_days_before = Column(
        Integer, nullable=False, default=3, comment="알림 일수 (사전)"
    )

    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시"
    )
    last_created_at = Column(DateTime, nullable=True, comment="마지막 생성일시")
    next_scheduled_at = Column(DateTime, nullable=True, comment="다음 예정일시")

    def __repr__(self):
        return f"<ChecklistSchedule(id={self.id}, name={self.name}, frequency_type={self.frequency_type})>"
