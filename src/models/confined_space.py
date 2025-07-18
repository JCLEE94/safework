"""
밀폐공간 작업 관리 모델
Confined space work management models
"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from src.config.database import Base


class ConfinedSpaceType(str, enum.Enum):
    """밀폐공간 유형"""
    TANK = "탱크"
    MANHOLE = "맨홀"
    PIPE = "배관"
    PIT = "피트"
    SILO = "사일로"
    TUNNEL = "터널"
    BOILER = "보일러"
    FURNACE = "용광로"
    VESSEL = "용기"
    OTHER = "기타"


class HazardType(str, enum.Enum):
    """위험 요인 유형"""
    OXYGEN_DEFICIENCY = "산소결핍"
    TOXIC_GAS = "유독가스"
    FLAMMABLE_GAS = "가연성가스"
    DROWNING = "익사"
    ENGULFMENT = "매몰"
    HIGH_TEMPERATURE = "고온"
    LOW_TEMPERATURE = "저온"
    ELECTRICAL = "감전"
    MECHANICAL = "기계적위험"
    OTHER = "기타"


class WorkPermitStatus(str, enum.Enum):
    """작업 허가서 상태"""
    DRAFT = "작성중"
    SUBMITTED = "제출됨"
    APPROVED = "승인됨"
    IN_PROGRESS = "작업중"
    COMPLETED = "완료됨"
    CANCELLED = "취소됨"
    EXPIRED = "만료됨"


class ConfinedSpace(Base):
    """밀폐공간 정보"""
    __tablename__ = "confined_spaces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, comment="밀폐공간명")
    location = Column(String(200), nullable=False, comment="위치")
    type = Column(SQLEnum(ConfinedSpaceType), nullable=False, comment="밀폐공간 유형")
    description = Column(Text, comment="설명")
    
    # 공간 특성
    volume = Column(Float, comment="용적(m³)")
    depth = Column(Float, comment="깊이(m)")
    entry_points = Column(Integer, default=1, comment="출입구 수")
    ventilation_type = Column(String(50), comment="환기 방식")
    
    # 위험 요인
    hazards = Column(JSON, comment="위험 요인 목록")
    oxygen_level_normal = Column(Float, comment="정상 산소 농도(%)")
    
    # 관리 정보
    responsible_person = Column(String(50), comment="관리책임자")
    last_inspection_date = Column(DateTime, comment="최근 점검일")
    inspection_cycle_days = Column(Integer, default=30, comment="점검주기(일)")
    
    # 상태
    is_active = Column(Boolean, default=True, comment="사용 가능 여부")
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    created_by = Column(String(50), comment="생성자")
    
    # 관계
    work_permits = relationship("ConfinedSpaceWorkPermit", back_populates="confined_space")
    safety_checklists = relationship("ConfinedSpaceSafetyChecklist", back_populates="confined_space")


class ConfinedSpaceWorkPermit(Base):
    """밀폐공간 작업 허가서"""
    __tablename__ = "confined_space_work_permits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    permit_number = Column(String(50), unique=True, nullable=False, comment="허가서 번호")
    confined_space_id = Column(UUID(as_uuid=True), ForeignKey("confined_spaces.id"), nullable=False)
    
    # 작업 정보
    work_description = Column(Text, nullable=False, comment="작업 내용")
    work_purpose = Column(String(200), comment="작업 목적")
    contractor = Column(String(100), comment="작업 업체")
    
    # 작업 일정
    scheduled_start = Column(DateTime, nullable=False, comment="작업 시작 예정일시")
    scheduled_end = Column(DateTime, nullable=False, comment="작업 종료 예정일시")
    actual_start = Column(DateTime, comment="실제 시작일시")
    actual_end = Column(DateTime, comment="실제 종료일시")
    
    # 작업자 정보
    supervisor_name = Column(String(50), nullable=False, comment="작업 감독자")
    supervisor_contact = Column(String(20), comment="감독자 연락처")
    workers = Column(JSON, comment="작업자 목록")  # [{"name": "홍길동", "role": "용접공", "contact": "010-1234-5678"}]
    
    # 안전 조치
    hazard_assessment = Column(JSON, comment="위험성 평가")
    safety_measures = Column(JSON, comment="안전 조치 사항")
    required_ppe = Column(JSON, comment="필수 보호구")  # ["안전모", "안전화", "가스마스크"]
    
    # 가스 측정
    gas_test_required = Column(Boolean, default=True, comment="가스 측정 필요 여부")
    gas_test_interval_minutes = Column(Integer, default=60, comment="가스 측정 주기(분)")
    gas_test_results = Column(JSON, comment="가스 측정 결과")
    
    # 비상 대응
    emergency_contact = Column(String(20), comment="비상 연락처")
    emergency_procedures = Column(Text, comment="비상 대응 절차")
    rescue_equipment = Column(JSON, comment="구조 장비 목록")
    
    # 승인 정보
    status = Column(SQLEnum(WorkPermitStatus), default=WorkPermitStatus.DRAFT, comment="상태")
    submitted_by = Column(String(50), comment="제출자")
    submitted_at = Column(DateTime, comment="제출일시")
    approved_by = Column(String(50), comment="승인자")
    approved_at = Column(DateTime, comment="승인일시")
    
    # 메타데이터
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    
    # 관계
    confined_space = relationship("ConfinedSpace", back_populates="work_permits")
    gas_measurements = relationship("ConfinedSpaceGasMeasurement", back_populates="work_permit")


class ConfinedSpaceGasMeasurement(Base):
    """밀폐공간 가스 측정 기록"""
    __tablename__ = "confined_space_gas_measurements"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    work_permit_id = Column(UUID(as_uuid=True), ForeignKey("confined_space_work_permits.id"), nullable=False)
    
    # 측정 정보
    measurement_time = Column(DateTime, nullable=False, default=datetime.now, comment="측정 시간")
    measurement_location = Column(String(100), comment="측정 위치")
    measured_by = Column(String(50), nullable=False, comment="측정자")
    
    # 측정값
    oxygen_level = Column(Float, comment="산소 농도(%)")
    carbon_monoxide = Column(Float, comment="일산화탄소(ppm)")
    hydrogen_sulfide = Column(Float, comment="황화수소(ppm)")
    methane = Column(Float, comment="메탄(%LEL)")
    other_gases = Column(JSON, comment="기타 가스 측정값")
    
    # 판정
    is_safe = Column(Boolean, nullable=False, comment="안전 여부")
    remarks = Column(Text, comment="비고")
    
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    
    # 관계
    work_permit = relationship("ConfinedSpaceWorkPermit", back_populates="gas_measurements")


class ConfinedSpaceSafetyChecklist(Base):
    """밀폐공간 안전 점검 체크리스트"""
    __tablename__ = "confined_space_safety_checklists"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    confined_space_id = Column(UUID(as_uuid=True), ForeignKey("confined_spaces.id"), nullable=False)
    
    # 점검 정보
    inspection_date = Column(DateTime, nullable=False, default=datetime.now, comment="점검일시")
    inspector_name = Column(String(50), nullable=False, comment="점검자")
    
    # 체크리스트 항목
    checklist_items = Column(JSON, nullable=False, comment="체크리스트 항목")
    """
    예시:
    [
        {
            "category": "진입 전 조치",
            "item": "작업 허가서 확인",
            "checked": true,
            "comment": "허가서 번호: CS-2024-001"
        },
        {
            "category": "환기 조치",
            "item": "강제 환기 실시",
            "checked": true,
            "comment": "30분간 환기 완료"
        }
    ]
    """
    
    # 전체 평가
    overall_status = Column(String(20), comment="전체 상태")  # "안전", "조건부안전", "위험"
    corrective_actions = Column(JSON, comment="시정 조치 사항")
    
    # 서명
    inspector_signature = Column(Text, comment="점검자 서명")
    reviewer_name = Column(String(50), comment="검토자")
    reviewer_signature = Column(Text, comment="검토자 서명")
    
    created_at = Column(DateTime, default=datetime.now, comment="생성일시")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="수정일시")
    
    # 관계
    confined_space = relationship("ConfinedSpace", back_populates="safety_checklists")