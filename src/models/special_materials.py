"""
특별관리물질 관리 모델
Special Materials Management Models
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, Enum as SQLEnum, ForeignKey, Float, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from ..config.database import Base


class SpecialMaterialType(enum.Enum):
    """특별관리물질 유형"""
    CARCINOGEN = "carcinogen"                    # 발암물질
    MUTAGEN = "mutagen"                          # 돌연변이 유발물질
    REPRODUCTIVE_TOXIN = "reproductive_toxin"    # 생식독성물질
    RESPIRATORY_SENSITIZER = "respiratory_sensitizer"  # 호흡기 과민성물질
    SKIN_SENSITIZER = "skin_sensitizer"          # 피부 과민성물질
    TOXIC_GAS = "toxic_gas"                      # 독성가스
    ASBESTOS = "asbestos"                        # 석면
    SILICA = "silica"                            # 규소 화합물
    HEAVY_METAL = "heavy_metal"                  # 중금속
    ORGANIC_SOLVENT = "organic_solvent"          # 유기용제


class ExposureLevel(enum.Enum):
    """노출 수준"""
    NONE = "none"        # 노출 없음
    LOW = "low"          # 낮음
    MEDIUM = "medium"    # 보통
    HIGH = "high"        # 높음
    CRITICAL = "critical"  # 위험


class ControlMeasureType(enum.Enum):
    """관리 조치 유형"""
    ENGINEERING = "engineering"        # 공학적 대책
    ADMINISTRATIVE = "administrative"  # 관리적 대책
    PPE = "ppe"                       # 개인보호구
    SUBSTITUTION = "substitution"     # 대체
    ELIMINATION = "elimination"       # 제거


class MonitoringStatus(enum.Enum):
    """모니터링 상태"""
    PENDING = "pending"      # 대기
    IN_PROGRESS = "in_progress"  # 진행중
    COMPLETED = "completed"  # 완료
    OVERDUE = "overdue"     # 기한초과
    CANCELLED = "cancelled"  # 취소


class SpecialMaterial(Base):
    """특별관리물질 마스터"""
    __tablename__ = "special_materials"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # 물질 기본 정보
    material_code = Column(String(50), unique=True, nullable=False, comment="물질 코드")
    material_name = Column(String(255), nullable=False, comment="물질명")
    material_name_korean = Column(String(255), nullable=False, comment="한글명")
    cas_number = Column(String(50), nullable=True, comment="CAS 번호")
    
    # 물질 분류
    material_type = Column(SQLEnum(SpecialMaterialType), nullable=False, comment="물질 유형")
    hazard_classification = Column(String(500), nullable=True, comment="유해성 분류")
    ghs_classification = Column(JSON, nullable=True, comment="GHS 분류")
    
    # 법적 기준
    occupational_exposure_limit = Column(Numeric(10, 6), nullable=True, comment="작업환경측정 기준(ppm/mg/m³)")
    short_term_exposure_limit = Column(Numeric(10, 6), nullable=True, comment="단기노출기준")
    ceiling_limit = Column(Numeric(10, 6), nullable=True, comment="최고노출기준")
    biological_exposure_index = Column(Numeric(10, 6), nullable=True, comment="생물학적 노출지수")
    
    # 관리 정보
    is_prohibited = Column(Boolean, nullable=False, default=False, comment="사용금지 여부")
    requires_permit = Column(Boolean, nullable=False, default=True, comment="허가 필요 여부")
    monitoring_frequency_days = Column(Integer, nullable=False, default=180, comment="측정 주기(일)")
    health_exam_frequency_months = Column(Integer, nullable=False, default=12, comment="건강진단 주기(월)")
    
    # 물리화학적 성질
    physical_state = Column(String(50), nullable=True, comment="물리적 상태")
    molecular_weight = Column(Numeric(10, 3), nullable=True, comment="분자량")
    boiling_point = Column(Numeric(10, 2), nullable=True, comment="끓는점(℃)")
    melting_point = Column(Numeric(10, 2), nullable=True, comment="녹는점(℃)")
    vapor_pressure = Column(Numeric(15, 6), nullable=True, comment="증기압(mmHg)")
    
    # 유해성 정보
    target_organs = Column(JSON, nullable=True, comment="표적장기")
    health_effects = Column(Text, nullable=True, comment="건강 영향")
    exposure_routes = Column(JSON, nullable=True, comment="노출 경로")
    
    # 응급처치 및 안전 정보
    first_aid_measures = Column(Text, nullable=True, comment="응급처치 요령")
    safety_precautions = Column(Text, nullable=True, comment="안전 주의사항")
    storage_requirements = Column(Text, nullable=True, comment="저장 요구사항")
    disposal_methods = Column(Text, nullable=True, comment="폐기 방법")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    
    # 관계
    usage_records = relationship("SpecialMaterialUsage", back_populates="material")
    exposure_assessments = relationship("ExposureAssessment", back_populates="material")
    monitoring_records = relationship("SpecialMaterialMonitoring", back_populates="material")

    def __repr__(self):
        return f"<SpecialMaterial(id={self.id}, name={self.material_name_korean})>"


class SpecialMaterialUsage(Base):
    """특별관리물질 사용 기록"""
    __tablename__ = "special_material_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    material_id = Column(UUID(as_uuid=True), ForeignKey("special_materials.id"), nullable=False)
    
    # 사용 정보
    usage_date = Column(DateTime, nullable=False, comment="사용일시")
    usage_location = Column(String(255), nullable=False, comment="사용 장소")
    usage_purpose = Column(String(500), nullable=False, comment="사용 목적")
    work_process = Column(String(500), nullable=True, comment="작업 공정")
    
    # 수량 정보
    quantity_used = Column(Numeric(15, 3), nullable=False, comment="사용량")
    unit = Column(String(20), nullable=False, comment="단위")
    concentration = Column(Numeric(10, 6), nullable=True, comment="농도(%)")
    
    # 작업자 정보
    worker_id = Column(UUID(as_uuid=True), ForeignKey("workers.id"), nullable=True)
    worker_count = Column(Integer, nullable=False, default=1, comment="작업자 수")
    exposure_duration_hours = Column(Numeric(5, 2), nullable=True, comment="노출 시간(시간)")
    
    # 관리 조치
    control_measures = Column(JSON, nullable=True, comment="관리 조치")
    ppe_used = Column(JSON, nullable=True, comment="사용 개인보호구")
    ventilation_type = Column(String(100), nullable=True, comment="환기 방식")
    
    # 승인 정보
    approved_by = Column(String(100), nullable=True, comment="승인자")
    approval_date = Column(DateTime, nullable=True, comment="승인일시")
    permit_number = Column(String(100), nullable=True, comment="허가번호")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    recorded_by = Column(String(100), nullable=False, comment="기록자")
    
    # 관계
    material = relationship("SpecialMaterial", back_populates="usage_records")
    worker = relationship("Worker")

    def __repr__(self):
        return f"<SpecialMaterialUsage(id={self.id}, material_id={self.material_id})>"


class ExposureAssessment(Base):
    """노출 평가"""
    __tablename__ = "exposure_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    material_id = Column(UUID(as_uuid=True), ForeignKey("special_materials.id"), nullable=False)
    
    # 평가 정보
    assessment_date = Column(DateTime, nullable=False, comment="평가일시")
    assessment_type = Column(String(100), nullable=False, comment="평가 유형")
    assessment_location = Column(String(255), nullable=False, comment="평가 장소")
    work_activity = Column(String(500), nullable=False, comment="작업 활동")
    
    # 측정 결과
    measured_concentration = Column(Numeric(15, 6), nullable=True, comment="측정 농도")
    measurement_unit = Column(String(20), nullable=True, comment="측정 단위")
    sampling_duration_minutes = Column(Integer, nullable=True, comment="시료채취 시간(분)")
    sampling_method = Column(String(200), nullable=True, comment="시료채취 방법")
    analysis_method = Column(String(200), nullable=True, comment="분석 방법")
    
    # 노출 평가
    exposure_level = Column(SQLEnum(ExposureLevel), nullable=False, comment="노출 수준")
    exposure_route = Column(String(100), nullable=True, comment="주요 노출 경로")
    risk_score = Column(Numeric(5, 2), nullable=True, comment="위험도 점수")
    
    # 관리 조치 권고
    recommended_controls = Column(JSON, nullable=True, comment="권고 관리 조치")
    priority_level = Column(String(20), nullable=False, default="medium", comment="우선순위")
    follow_up_required = Column(Boolean, nullable=False, default=False, comment="후속조치 필요")
    follow_up_date = Column(DateTime, nullable=True, comment="후속조치 예정일")
    
    # 평가자 정보
    assessor_name = Column(String(100), nullable=False, comment="평가자명")
    assessor_qualification = Column(String(200), nullable=True, comment="평가자 자격")
    assessment_organization = Column(String(200), nullable=True, comment="평가기관")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    
    # 관계
    material = relationship("SpecialMaterial", back_populates="exposure_assessments")

    def __repr__(self):
        return f"<ExposureAssessment(id={self.id}, level={self.exposure_level})>"


class SpecialMaterialMonitoring(Base):
    """특별관리물질 모니터링"""
    __tablename__ = "special_material_monitoring"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    material_id = Column(UUID(as_uuid=True), ForeignKey("special_materials.id"), nullable=False)
    
    # 모니터링 기본 정보
    monitoring_date = Column(DateTime, nullable=False, comment="모니터링 일시")
    monitoring_type = Column(String(100), nullable=False, comment="모니터링 유형")
    location = Column(String(255), nullable=False, comment="모니터링 장소")
    status = Column(SQLEnum(MonitoringStatus), nullable=False, default=MonitoringStatus.PENDING, comment="상태")
    
    # 모니터링 계획
    scheduled_date = Column(DateTime, nullable=False, comment="예정일")
    frequency_type = Column(String(50), nullable=False, comment="주기 유형")
    next_monitoring_date = Column(DateTime, nullable=True, comment="다음 모니터링 예정일")
    
    # 모니터링 결과
    measurement_results = Column(JSON, nullable=True, comment="측정 결과")
    compliance_status = Column(Boolean, nullable=True, comment="기준 준수 여부")
    exceedance_factor = Column(Numeric(10, 2), nullable=True, comment="기준 초과배수")
    
    # 시정조치
    corrective_actions = Column(JSON, nullable=True, comment="시정조치사항")
    action_due_date = Column(DateTime, nullable=True, comment="시정조치 마감일")
    action_responsible = Column(String(100), nullable=True, comment="시정조치 담당자")
    action_status = Column(String(50), nullable=True, comment="시정조치 상태")
    
    # 담당자 정보
    monitor_name = Column(String(100), nullable=False, comment="모니터링 담당자")
    monitor_organization = Column(String(200), nullable=True, comment="모니터링 기관")
    report_number = Column(String(100), nullable=True, comment="보고서 번호")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    
    # 관계
    material = relationship("SpecialMaterial", back_populates="monitoring_records")

    def __repr__(self):
        return f"<SpecialMaterialMonitoring(id={self.id}, status={self.status})>"


class ControlMeasure(Base):
    """관리 조치"""
    __tablename__ = "control_measures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    material_id = Column(UUID(as_uuid=True), ForeignKey("special_materials.id"), nullable=False)
    
    # 조치 정보
    measure_type = Column(SQLEnum(ControlMeasureType), nullable=False, comment="조치 유형")
    measure_name = Column(String(255), nullable=False, comment="조치명")
    description = Column(Text, nullable=False, comment="상세 설명")
    implementation_date = Column(DateTime, nullable=False, comment="시행일")
    
    # 효과성 정보
    effectiveness_rating = Column(Integer, nullable=True, comment="효과성 등급(1-5)")
    cost_estimate = Column(Numeric(15, 2), nullable=True, comment="예상 비용")
    maintenance_frequency = Column(String(100), nullable=True, comment="유지보수 주기")
    
    # 책임자 정보
    responsible_person = Column(String(100), nullable=False, comment="책임자")
    responsible_department = Column(String(100), nullable=True, comment="담당 부서")
    
    # 상태 정보
    is_active = Column(Boolean, nullable=False, default=True, comment="활성 상태")
    last_inspection_date = Column(DateTime, nullable=True, comment="마지막 점검일")
    next_inspection_date = Column(DateTime, nullable=True, comment="다음 점검 예정일")
    
    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정일시")
    created_by = Column(String(100), nullable=False, comment="생성자")

    def __repr__(self):
        return f"<ControlMeasure(id={self.id}, name={self.measure_name})>"