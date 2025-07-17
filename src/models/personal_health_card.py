"""
개인 건강관리카드 시스템 모델

이 모듈은 작업자별 개인 건강관리카드 및 관련 기능을 제공합니다.
- 개인 건강관리카드 기본 정보
- 건강 이력 추적
- 유소견자 관리
- 건강 지표 모니터링
- 건강 권고사항 관리

외부 패키지:
- SQLAlchemy: ORM 및 데이터베이스 매핑 (https://sqlalchemy.org/)
- PostgreSQL: JSON 필드 지원 (https://postgresql.org/)

예시 입력:
- worker_id: 작업자 ID (UUID)
- card_number: "PHC-2025-001"
- health_indicators: {"blood_pressure": "120/80", "weight": "70.5"}

예시 출력:
- 개인 건강관리카드 정보
- 건강 이력 타임라인
- 유소견 사항 목록
"""

from datetime import datetime, date
from enum import Enum
from typing import Optional, Dict, Any, List
import json
from sqlalchemy import Column, String, DateTime, Boolean, Text, Date, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from src.config.database import Base


class HealthCardStatus(str, Enum):
    """건강관리카드 상태"""
    ACTIVE = "active"        # 활성
    INACTIVE = "inactive"    # 비활성
    SUSPENDED = "suspended"  # 중단


class FindingSeverity(str, Enum):
    """유소견 심각도"""
    MILD = "mild"           # 경미
    MODERATE = "moderate"   # 중등도
    SEVERE = "severe"       # 심각
    CRITICAL = "critical"   # 위험


class FindingStatus(str, Enum):
    """유소견 상태"""
    ACTIVE = "active"       # 활성
    MONITORING = "monitoring"  # 관찰중
    RESOLVED = "resolved"   # 해결
    CLOSED = "closed"       # 종료


class IndicatorType(str, Enum):
    """건강 지표 유형"""
    BLOOD_PRESSURE = "blood_pressure"     # 혈압
    WEIGHT = "weight"                     # 체중
    HEIGHT = "height"                     # 신장
    BMI = "bmi"                          # BMI
    BLOOD_SUGAR = "blood_sugar"          # 혈당
    CHOLESTEROL = "cholesterol"          # 콜레스테롤
    HEART_RATE = "heart_rate"            # 심박수
    TEMPERATURE = "temperature"          # 체온
    VISION = "vision"                    # 시력
    HEARING = "hearing"                  # 청력


class PersonalHealthCard(Base):
    """개인 건강관리카드"""
    
    __tablename__ = "personal_health_cards"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 기본 정보
    worker_id = Column(UUID(as_uuid=True), ForeignKey('workers.id'), nullable=False, unique=True, comment="작업자 ID")
    card_number = Column(String(20), unique=True, nullable=False, comment="카드 번호")
    issued_date = Column(Date, nullable=False, comment="발급일")
    
    # 상태 정보
    status = Column(String(20), default=HealthCardStatus.ACTIVE, nullable=False, comment="상태")
    is_active = Column(Boolean, default=True, nullable=False, comment="활성 여부")
    
    # 추가 정보
    notes = Column(Text, comment="비고")
    special_notes = Column(Text, comment="특이사항")
    
    # 관리 정보
    last_updated = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="마지막 업데이트")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    updated_by = Column(String(100), comment="수정자")
    
    # 관계 설정
    health_history = relationship("HealthHistory", back_populates="health_card", cascade="all, delete-orphan")
    abnormal_findings = relationship("AbnormalFinding", back_populates="health_card", cascade="all, delete-orphan")
    health_indicators = relationship("HealthIndicator", back_populates="health_card", cascade="all, delete-orphan")
    health_recommendations = relationship("HealthRecommendation", back_populates="health_card", cascade="all, delete-orphan")

    def get_latest_indicators(self) -> Dict[str, Any]:
        """최신 건강 지표 조회"""
        if not self.health_indicators:
            return {}
        
        latest_indicators = {}
        for indicator in self.health_indicators:
            if indicator.indicator_type not in latest_indicators:
                latest_indicators[indicator.indicator_type] = indicator
            elif indicator.measurement_date > latest_indicators[indicator.indicator_type].measurement_date:
                latest_indicators[indicator.indicator_type] = indicator
        
        return {k: v.value for k, v in latest_indicators.items()}

    def get_active_findings(self) -> List['AbnormalFinding']:
        """활성 유소견 사항 조회"""
        return [f for f in self.abnormal_findings if f.status == FindingStatus.ACTIVE]

    def has_critical_findings(self) -> bool:
        """위험 유소견 사항 존재 여부"""
        return any(f.severity == FindingSeverity.CRITICAL for f in self.get_active_findings())


class HealthHistory(Base):
    """건강 이력"""
    
    __tablename__ = "health_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관련 정보
    card_id = Column(UUID(as_uuid=True), ForeignKey('personal_health_cards.id'), nullable=False, comment="건강관리카드 ID")
    
    # 검진 정보
    exam_date = Column(Date, nullable=False, comment="검진일")
    exam_type = Column(String(50), nullable=False, comment="검진 유형")
    exam_institution = Column(String(200), comment="검진 기관")
    
    # 결과 정보
    result_summary = Column(Text, comment="결과 요약")
    detailed_results = Column(JSON, comment="상세 결과")
    
    # 권고사항
    recommendations = Column(Text, comment="권고사항")
    follow_up_required = Column(Boolean, default=False, comment="후속조치 필요")
    follow_up_date = Column(Date, comment="후속조치 예정일")
    follow_up_completed = Column(Boolean, default=False, comment="후속조치 완료")
    
    # 첨부파일
    attachments = Column(JSON, comment="첨부파일 정보")
    
    # 생성 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    
    # 관계 설정
    health_card = relationship("PersonalHealthCard", back_populates="health_history")

    def get_detailed_results(self) -> Dict[str, Any]:
        """상세 결과 파싱"""
        if not self.detailed_results:
            return {}
        return self.detailed_results if isinstance(self.detailed_results, dict) else {}

    def get_attachments(self) -> List[Dict[str, Any]]:
        """첨부파일 정보 파싱"""
        if not self.attachments:
            return []
        return self.attachments if isinstance(self.attachments, list) else []


class AbnormalFinding(Base):
    """유소견자 관리"""
    
    __tablename__ = "abnormal_findings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관련 정보
    card_id = Column(UUID(as_uuid=True), ForeignKey('personal_health_cards.id'), nullable=False, comment="건강관리카드 ID")
    
    # 유소견 정보
    finding_date = Column(Date, nullable=False, comment="발견일")
    category = Column(String(50), nullable=False, comment="분류")
    subcategory = Column(String(100), comment="세부 분류")
    
    # 심각도 및 상태
    severity = Column(String(20), nullable=False, comment="심각도")
    status = Column(String(20), default=FindingStatus.ACTIVE, nullable=False, comment="상태")
    
    # 상세 정보
    description = Column(Text, nullable=False, comment="상세 설명")
    clinical_findings = Column(Text, comment="임상 소견")
    
    # 조치 사항
    action_taken = Column(Text, comment="취해진 조치")
    action_plan = Column(Text, comment="조치 계획")
    
    # 후속 관리
    follow_up_required = Column(Boolean, default=True, comment="후속조치 필요")
    next_checkup_date = Column(Date, comment="다음 점검일")
    monitoring_frequency = Column(String(50), comment="모니터링 주기")
    
    # 해결 정보
    resolved_date = Column(Date, comment="해결일")
    resolution_notes = Column(Text, comment="해결 방법")
    
    # 관련 문서
    related_documents = Column(JSON, comment="관련 문서")
    
    # 생성 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    updated_by = Column(String(100), comment="수정자")
    
    # 관계 설정
    health_card = relationship("PersonalHealthCard", back_populates="abnormal_findings")

    def is_overdue(self) -> bool:
        """후속조치 지연 여부"""
        if not self.next_checkup_date or self.status != FindingStatus.ACTIVE:
            return False
        return date.today() > self.next_checkup_date

    def get_related_documents(self) -> List[Dict[str, Any]]:
        """관련 문서 파싱"""
        if not self.related_documents:
            return []
        return self.related_documents if isinstance(self.related_documents, list) else []


class HealthIndicator(Base):
    """건강 지표"""
    
    __tablename__ = "health_indicators"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관련 정보
    card_id = Column(UUID(as_uuid=True), ForeignKey('personal_health_cards.id'), nullable=False, comment="건강관리카드 ID")
    
    # 측정 정보
    measurement_date = Column(Date, nullable=False, comment="측정일")
    indicator_type = Column(String(50), nullable=False, comment="지표 유형")
    
    # 측정값
    value = Column(Numeric(10, 2), nullable=False, comment="측정값")
    unit = Column(String(20), nullable=False, comment="단위")
    
    # 기준값
    normal_range_min = Column(Numeric(10, 2), comment="정상 범위 최소값")
    normal_range_max = Column(Numeric(10, 2), comment="정상 범위 최대값")
    reference_value = Column(Numeric(10, 2), comment="기준값")
    
    # 평가
    is_abnormal = Column(Boolean, default=False, comment="이상 여부")
    abnormal_level = Column(String(20), comment="이상 정도")
    
    # 추가 정보
    measurement_method = Column(String(100), comment="측정 방법")
    measurement_conditions = Column(Text, comment="측정 조건")
    notes = Column(Text, comment="비고")
    
    # 생성 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    
    # 관계 설정
    health_card = relationship("PersonalHealthCard", back_populates="health_indicators")

    def evaluate_abnormality(self) -> bool:
        """이상 여부 평가"""
        if self.normal_range_min is None or self.normal_range_max is None:
            return False
        
        value_float = float(self.value)
        min_float = float(self.normal_range_min)
        max_float = float(self.normal_range_max)
        
        return value_float < min_float or value_float > max_float

    def get_trend_direction(self, previous_value: Optional[float]) -> str:
        """이전 값과 비교한 변화 방향"""
        if previous_value is None:
            return "neutral"
        
        current_value = float(self.value)
        if current_value > previous_value:
            return "increasing"
        elif current_value < previous_value:
            return "decreasing"
        else:
            return "stable"


class HealthRecommendation(Base):
    """건강 권고사항"""
    
    __tablename__ = "health_recommendations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관련 정보
    card_id = Column(UUID(as_uuid=True), ForeignKey('personal_health_cards.id'), nullable=False, comment="건강관리카드 ID")
    
    # 권고사항 정보
    recommendation_date = Column(Date, nullable=False, comment="권고일")
    category = Column(String(50), nullable=False, comment="분류")
    priority = Column(String(20), nullable=False, comment="우선순위")
    
    # 내용
    title = Column(String(200), nullable=False, comment="제목")
    description = Column(Text, nullable=False, comment="상세 설명")
    action_items = Column(JSON, comment="실행 항목")
    
    # 기간 및 상태
    target_date = Column(Date, comment="목표일")
    completion_date = Column(Date, comment="완료일")
    status = Column(String(20), default="pending", comment="상태")
    
    # 결과
    outcome = Column(Text, comment="결과")
    effectiveness_rating = Column(Integer, comment="효과성 평가 (1-5)")
    
    # 생성 정보
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성일시")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정일시")
    created_by = Column(String(100), nullable=False, comment="생성자")
    updated_by = Column(String(100), comment="수정자")
    
    # 관계 설정
    health_card = relationship("PersonalHealthCard", back_populates="health_recommendations")

    def is_overdue(self) -> bool:
        """목표일 초과 여부"""
        if not self.target_date or self.status == "completed":
            return False
        return date.today() > self.target_date

    def get_action_items(self) -> List[Dict[str, Any]]:
        """실행 항목 파싱"""
        if not self.action_items:
            return []
        return self.action_items if isinstance(self.action_items, list) else []


if __name__ == "__main__":
    # 검증 테스트
    print("✅ 개인 건강관리카드 모델 검증 시작")
    
    # 1. 건강관리카드 생성 테스트
    health_card = PersonalHealthCard(
        worker_id=uuid.uuid4(),
        card_number="PHC-2025-001",
        issued_date=date.today(),
        created_by="admin"
    )
    
    # 2. 건강 이력 생성 테스트
    health_history = HealthHistory(
        card_id=health_card.id,
        exam_date=date.today(),
        exam_type="일반건강진단",
        result_summary="정상",
        created_by="admin"
    )
    
    # 3. 유소견 사항 생성 테스트
    finding = AbnormalFinding(
        card_id=health_card.id,
        finding_date=date.today(),
        category="심혈관계",
        severity=FindingSeverity.MILD,
        description="경미한 고혈압 소견",
        created_by="admin"
    )
    
    # 4. 건강 지표 생성 테스트
    indicator = HealthIndicator(
        card_id=health_card.id,
        measurement_date=date.today(),
        indicator_type=IndicatorType.BLOOD_PRESSURE,
        value=140,
        unit="mmHg",
        normal_range_min=90,
        normal_range_max=140,
        created_by="admin"
    )
    
    # 5. 이상 여부 평가 테스트
    assert indicator.evaluate_abnormality() == False  # 경계값이므로 정상으로 판정
    
    # 6. 권고사항 생성 테스트
    recommendation = HealthRecommendation(
        card_id=health_card.id,
        recommendation_date=date.today(),
        category="생활습관",
        priority="medium",
        title="염분 섭취 줄이기",
        description="일일 나트륨 섭취량을 2000mg 이하로 제한",
        created_by="admin"
    )
    
    # 7. 관계 테스트
    health_card.health_history = [health_history]
    health_card.abnormal_findings = [finding]
    health_card.health_indicators = [indicator]
    health_card.health_recommendations = [recommendation]
    
    # 8. 메서드 테스트
    assert len(health_card.get_active_findings()) == 1
    assert not health_card.has_critical_findings()
    assert not finding.is_overdue()
    assert not recommendation.is_overdue()
    
    print("✅ 모든 검증 테스트 통과!")
    print("개인 건강관리카드 시스템 모델이 정상적으로 작동합니다.")