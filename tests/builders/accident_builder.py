"""
산업재해 보고 관련 테스트 데이터 빌더
Accident report test data builders
"""

import json
from datetime import datetime, date, timedelta
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.accident_report import (
    AccidentReport, AccidentType, InjuryType, AccidentSeverity, InvestigationStatus
)
from tests.builders.base_builder import BaseBuilder


class AccidentReportBuilder(BaseBuilder[AccidentReport]):
    """산업재해 보고 빌더"""

    def __init__(self):
        super().__init__()
        self._accident_datetime: datetime = datetime.now() - timedelta(hours=2)
        self._report_datetime: datetime = datetime.now()
        self._accident_location: str = "건설현장 작업장"
        self._worker_id: Optional[int] = None
        self._accident_type: AccidentType = AccidentType.FALL
        self._injury_type: InjuryType = InjuryType.BRUISE
        self._severity: AccidentSeverity = AccidentSeverity.MINOR
        self._accident_description: str = "작업 중 실족으로 인한 넘어짐"
        self._immediate_cause: Optional[str] = "바닥 물기로 인한 미끄러짐"
        self._root_cause: Optional[str] = "안전수칙 미준수 및 작업환경 관리 부족"
        self._injured_body_part: Optional[str] = "왼쪽 무릎"
        self._treatment_type: Optional[str] = "외래진료"
        self._hospital_name: Optional[str] = "세종병원"
        self._doctor_name: Optional[str] = "김의사"
        self._work_days_lost: int = 0
        self._return_to_work_date: Optional[date] = None
        self._permanent_disability: str = "N"
        self._disability_rate: Optional[float] = None
        self._investigation_status: InvestigationStatus = InvestigationStatus.REPORTED
        self._investigator_name: Optional[str] = None
        self._investigation_date: Optional[date] = None
        self._immediate_actions: Optional[str] = "응급처치 및 병원 이송"
        self._corrective_actions: Optional[str] = None
        self._preventive_measures: Optional[str] = None
        self._action_completion_date: Optional[date] = None
        self._reported_to_authorities: str = "N"
        self._authority_report_date: Optional[datetime] = None
        self._authority_report_number: Optional[str] = None
        self._accident_photo_paths: Optional[str] = None
        self._investigation_report_path: Optional[str] = None
        self._medical_certificate_path: Optional[str] = None
        self._witness_names: Optional[str] = None
        self._witness_statements: Optional[str] = None
        self._medical_cost: float = 0.0
        self._compensation_cost: float = 0.0
        self._other_cost: float = 0.0
        self._notes: Optional[str] = None
        self._created_by: Optional[str] = "test_user"
        self._updated_by: Optional[str] = "test_user"

    def with_accident_datetime(self, accident_datetime: datetime) -> "AccidentReportBuilder":
        """사고 발생 일시 설정"""
        self._accident_datetime = accident_datetime
        return self

    def with_report_datetime(self, report_datetime: datetime) -> "AccidentReportBuilder":
        """신고 일시 설정"""
        self._report_datetime = report_datetime
        return self

    def with_accident_location(self, location: str) -> "AccidentReportBuilder":
        """사고 장소 설정"""
        self._accident_location = location
        return self

    def with_worker_id(self, worker_id: int) -> "AccidentReportBuilder":
        """근로자 ID 설정"""
        self._worker_id = worker_id
        return self

    def with_accident_classification(
        self,
        accident_type: AccidentType,
        injury_type: InjuryType,
        severity: AccidentSeverity
    ) -> "AccidentReportBuilder":
        """사고 분류 설정"""
        self._accident_type = accident_type
        self._injury_type = injury_type
        self._severity = severity
        return self

    def with_accident_details(
        self,
        description: str,
        immediate_cause: str = None,
        root_cause: str = None
    ) -> "AccidentReportBuilder":
        """사고 세부사항 설정"""
        self._accident_description = description
        if immediate_cause:
            self._immediate_cause = immediate_cause
        if root_cause:
            self._root_cause = root_cause
        return self

    def with_injury_details(
        self,
        body_part: str,
        treatment_type: str = "외래진료",
        hospital_name: str = "세종병원",
        doctor_name: str = "김의사"
    ) -> "AccidentReportBuilder":
        """부상 세부사항 설정"""
        self._injured_body_part = body_part
        self._treatment_type = treatment_type
        self._hospital_name = hospital_name
        self._doctor_name = doctor_name
        return self

    def with_work_loss(
        self,
        days_lost: int,
        return_date: date = None,
        permanent_disability: bool = False,
        disability_rate: float = None
    ) -> "AccidentReportBuilder":
        """휴업 관련 정보 설정"""
        self._work_days_lost = days_lost
        self._return_to_work_date = return_date
        self._permanent_disability = "Y" if permanent_disability else "N"
        self._disability_rate = disability_rate
        return self

    def with_investigation_info(
        self,
        status: InvestigationStatus,
        investigator: str = None,
        investigation_date: date = None
    ) -> "AccidentReportBuilder":
        """조사 정보 설정"""
        self._investigation_status = status
        self._investigator_name = investigator
        self._investigation_date = investigation_date
        return self

    def with_corrective_actions(
        self,
        immediate_actions: str = None,
        corrective_actions: str = None,
        preventive_measures: str = None,
        completion_date: date = None
    ) -> "AccidentReportBuilder":
        """시정조치 설정"""
        if immediate_actions:
            self._immediate_actions = immediate_actions
        if corrective_actions:
            self._corrective_actions = corrective_actions
        if preventive_measures:
            self._preventive_measures = preventive_measures
        self._action_completion_date = completion_date
        return self

    def with_authority_reporting(
        self,
        reported: bool = True,
        report_date: datetime = None,
        report_number: str = None
    ) -> "AccidentReportBuilder":
        """관계당국 신고 정보 설정"""
        self._reported_to_authorities = "Y" if reported else "N"
        self._authority_report_date = report_date
        self._authority_report_number = report_number
        return self

    def with_documents(
        self,
        photo_paths: List[str] = None,
        investigation_report: str = None,
        medical_certificate: str = None
    ) -> "AccidentReportBuilder":
        """관련 문서 설정"""
        if photo_paths:
            self._accident_photo_paths = json.dumps(photo_paths)
        self._investigation_report_path = investigation_report
        self._medical_certificate_path = medical_certificate
        return self

    def with_witnesses(
        self,
        witness_names: List[str] = None,
        witness_statements: str = None
    ) -> "AccidentReportBuilder":
        """목격자 정보 설정"""
        if witness_names:
            self._witness_names = json.dumps(witness_names)
        self._witness_statements = witness_statements
        return self

    def with_costs(
        self,
        medical_cost: float = 0.0,
        compensation_cost: float = 0.0,
        other_cost: float = 0.0
    ) -> "AccidentReportBuilder":
        """비용 정보 설정"""
        self._medical_cost = medical_cost
        self._compensation_cost = compensation_cost
        self._other_cost = other_cost
        return self

    def with_notes(self, notes: str) -> "AccidentReportBuilder":
        """비고 설정"""
        self._notes = notes
        return self

    def with_created_by(self, created_by: str) -> "AccidentReportBuilder":
        """생성자 설정"""
        self._created_by = created_by
        self._updated_by = created_by
        return self

    def with_korean_data(self) -> "AccidentReportBuilder":
        """한국어 테스트 데이터 설정"""
        self._accident_location = "건설현장 제1공구 3층"
        self._accident_description = "비계 작업 중 안전대 미착용으로 인한 추락사고"
        self._immediate_cause = "안전대 미착용 및 작업발판 불량"
        self._root_cause = "안전교육 미실시 및 안전관리자 현장 부재"
        self._injured_body_part = "머리, 허리"
        self._hospital_name = "서울대학교병원"
        self._doctor_name = "이정호 과장"
        self._immediate_actions = "119 신고 후 응급실 이송, 응급처치 실시"
        return self

    def with_fall_accident(self) -> "AccidentReportBuilder":
        """떨어짐 사고 설정"""
        self._accident_type = AccidentType.FALL
        self._accident_description = "고소작업 중 추락"
        self._immediate_cause = "안전대 미착용"
        self._injured_body_part = "머리, 허리"
        self._severity = AccidentSeverity.SEVERE
        self._work_days_lost = 30
        return self

    def with_collision_accident(self) -> "AccidentReportBuilder":
        """부딪힘 사고 설정"""
        self._accident_type = AccidentType.COLLISION
        self._injury_type = InjuryType.BRUISE
        self._accident_description = "중장비와 충돌"
        self._injured_body_part = "다리"
        self._severity = AccidentSeverity.MODERATE
        self._work_days_lost = 7
        return self

    def with_caught_in_accident(self) -> "AccidentReportBuilder":
        """끼임 사고 설정"""
        self._accident_type = AccidentType.CAUGHT_IN
        self._injury_type = InjuryType.FRACTURE
        self._accident_description = "기계에 손 끼임"
        self._injured_body_part = "오른손 검지"
        self._severity = AccidentSeverity.MODERATE
        self._work_days_lost = 14
        return self

    def with_chemical_exposure_accident(self) -> "AccidentReportBuilder":
        """화학물질 노출 사고 설정"""
        self._accident_type = AccidentType.CHEMICAL_EXPOSURE
        self._injury_type = InjuryType.POISONING
        self._accident_description = "화학물질 흡입으로 인한 중독"
        self._injured_body_part = "호흡기"
        self._severity = AccidentSeverity.SEVERE
        self._work_days_lost = 21
        return self

    def with_electric_shock_accident(self) -> "AccidentReportBuilder":
        """감전 사고 설정"""
        self._accident_type = AccidentType.ELECTRIC_SHOCK
        self._injury_type = InjuryType.BURN_INJURY
        self._accident_description = "전기 작업 중 감전"
        self._injured_body_part = "손, 팔"
        self._severity = AccidentSeverity.SEVERE
        self._work_days_lost = 45
        return self

    def with_fatal_accident(self) -> "AccidentReportBuilder":
        """사망 사고 설정"""
        self._severity = AccidentSeverity.FATAL
        self._injury_type = InjuryType.DEATH
        self._accident_description = "고소작업 중 추락으로 인한 사망"
        self._injured_body_part = "머리, 전신"
        self._work_days_lost = 0  # 사망으로 인한 영구 작업 불능
        self._permanent_disability = "Y"
        self._disability_rate = 100.0
        self._reported_to_authorities = "Y"
        self._authority_report_date = datetime.now()
        self._authority_report_number = "FATAL-2024-001"
        return self

    def with_minor_accident(self) -> "AccidentReportBuilder":
        """경미한 사고 설정"""
        self._severity = AccidentSeverity.MINOR
        self._injury_type = InjuryType.CUT_WOUND
        self._accident_description = "작업도구에 의한 경미한 베임"
        self._injured_body_part = "왼손 엄지"
        self._treatment_type = "응급처치"
        self._work_days_lost = 0
        return self

    def with_lost_time_accident(self, days_lost: int = 15) -> "AccidentReportBuilder":
        """휴업재해 설정"""
        self._severity = AccidentSeverity.MODERATE
        self._work_days_lost = days_lost
        self._return_to_work_date = date.today() + timedelta(days=days_lost)
        return self

    def with_completed_investigation(self) -> "AccidentReportBuilder":
        """완료된 조사 설정"""
        self._investigation_status = InvestigationStatus.COMPLETED
        self._investigator_name = "박안전관리자"
        self._investigation_date = date.today() - timedelta(days=3)
        self._corrective_actions = "안전교육 실시, 작업절차 개선"
        self._preventive_measures = "정기 안전점검 강화, 보호구 착용 의무화"
        self._action_completion_date = date.today()
        return self

    def with_pending_investigation(self) -> "AccidentReportBuilder":
        """조사 진행중 설정"""
        self._investigation_status = InvestigationStatus.INVESTIGATING
        self._investigator_name = "이조사관"
        self._investigation_date = date.today() - timedelta(days=1)
        return self

    def with_authority_reportable_accident(self) -> "AccidentReportBuilder":
        """관계당국 신고 대상 사고 설정"""
        self._severity = AccidentSeverity.SEVERE
        self._work_days_lost = 10  # 법적 신고 기준 초과
        self._reported_to_authorities = "Y"
        self._authority_report_date = datetime.now()
        self._authority_report_number = "REP-2024-" + str(datetime.now().strftime("%m%d%H%M"))
        return self

    def with_unreported_severe_accident(self) -> "AccidentReportBuilder":
        """미신고 중대사고 설정"""
        self._severity = AccidentSeverity.SEVERE
        self._work_days_lost = 20
        self._reported_to_authorities = "N"  # 신고 누락
        self._accident_datetime = datetime.now() - timedelta(days=5)  # 5일 전 발생
        return self

    def with_high_cost_accident(self) -> "AccidentReportBuilder":
        """고비용 사고 설정"""
        self._medical_cost = 5000000.0  # 500만원
        self._compensation_cost = 10000000.0  # 1000만원
        self._other_cost = 2000000.0  # 200만원
        self._severity = AccidentSeverity.SEVERE
        self._work_days_lost = 60
        return self

    def with_recent_accident(self, days_ago: int = 1) -> "AccidentReportBuilder":
        """최근 사고 설정"""
        self._accident_datetime = datetime.now() - timedelta(days=days_ago)
        self._report_datetime = datetime.now() - timedelta(days=days_ago, hours=-1)
        return self

    def with_old_accident(self, days_ago: int = 90) -> "AccidentReportBuilder":
        """오래된 사고 설정"""
        self._accident_datetime = datetime.now() - timedelta(days=days_ago)
        self._report_datetime = datetime.now() - timedelta(days=days_ago, hours=-2)
        return self

    async def build(self, db_session: AsyncSession) -> AccidentReport:
        """산업재해 보고서 생성"""
        if self._worker_id is None:
            raise ValueError("worker_id is required")

        accident_report = AccidentReport(
            accident_datetime=self._accident_datetime,
            report_datetime=self._report_datetime,
            accident_location=self._accident_location,
            worker_id=self._worker_id,
            accident_type=self._accident_type,
            injury_type=self._injury_type,
            severity=self._severity,
            accident_description=self._accident_description,
            immediate_cause=self._immediate_cause,
            root_cause=self._root_cause,
            injured_body_part=self._injured_body_part,
            treatment_type=self._treatment_type,
            hospital_name=self._hospital_name,
            doctor_name=self._doctor_name,
            work_days_lost=self._work_days_lost,
            return_to_work_date=self._return_to_work_date,
            permanent_disability=self._permanent_disability,
            disability_rate=self._disability_rate,
            investigation_status=self._investigation_status,
            investigator_name=self._investigator_name,
            investigation_date=self._investigation_date,
            immediate_actions=self._immediate_actions,
            corrective_actions=self._corrective_actions,
            preventive_measures=self._preventive_measures,
            action_completion_date=self._action_completion_date,
            reported_to_authorities=self._reported_to_authorities,
            authority_report_date=self._authority_report_date,
            authority_report_number=self._authority_report_number,
            accident_photo_paths=self._accident_photo_paths,
            investigation_report_path=self._investigation_report_path,
            medical_certificate_path=self._medical_certificate_path,
            witness_names=self._witness_names,
            witness_statements=self._witness_statements,
            medical_cost=self._medical_cost,
            compensation_cost=self._compensation_cost,
            other_cost=self._other_cost,
            notes=self._notes,
            created_by=self._created_by,
            updated_by=self._updated_by
        )

        db_session.add(accident_report)
        await db_session.commit()
        await db_session.refresh(accident_report)
        return accident_report


class AccidentScenarioBuilder:
    """사고 시나리오 빌더"""

    @staticmethod
    async def create_construction_site_accidents(
        db_session: AsyncSession,
        worker_ids: List[int]
    ) -> List[AccidentReport]:
        """건설현장 다양한 사고 시나리오 생성"""
        accidents = []

        # 1. 고소작업 추락사고 (중대)
        fall_accident = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[0])
            .with_fall_accident()
            .with_korean_data()
            .with_authority_reportable_accident()
            .with_completed_investigation()
            .with_costs(3000000, 8000000, 1000000)
            .build(db_session)
        )
        accidents.append(fall_accident)

        # 2. 중장비 충돌사고 (중등도)
        collision_accident = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[1])
            .with_collision_accident()
            .with_recent_accident(7)
            .with_pending_investigation()
            .with_costs(500000, 2000000, 0)
            .build(db_session)
        )
        accidents.append(collision_accident)

        # 3. 기계 끼임사고 (중등도)
        caught_in_accident = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[2])
            .with_caught_in_accident()
            .with_recent_accident(14)
            .with_completed_investigation()
            .with_costs(800000, 3000000, 200000)
            .build(db_session)
        )
        accidents.append(caught_in_accident)

        # 4. 화학물질 노출사고 (중대)
        chemical_accident = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[3])
            .with_chemical_exposure_accident()
            .with_recent_accident(21)
            .with_unreported_severe_accident()  # 신고 누락 사례
            .with_costs(2000000, 5000000, 500000)
            .build(db_session)
        )
        accidents.append(chemical_accident)

        # 5. 경미한 베임사고
        if len(worker_ids) > 4:
            minor_accident = await (
                AccidentReportBuilder()
                .with_worker_id(worker_ids[4])
                .with_minor_accident()
                .with_recent_accident(2)
                .with_completed_investigation()
                .with_costs(50000, 0, 0)
                .build(db_session)
            )
            accidents.append(minor_accident)

        return accidents

    @staticmethod
    async def create_safety_violations_scenario(
        db_session: AsyncSession,
        worker_ids: List[int]
    ) -> List[AccidentReport]:
        """안전수칙 위반으로 인한 사고 시나리오"""
        accidents = []

        # 안전대 미착용으로 인한 추락
        violation_accident1 = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[0])
            .with_fall_accident()
            .with_accident_details(
                "비계 작업 중 안전대 미착용으로 인한 추락",
                "안전대 미착용",
                "안전교육 미실시 및 감독 소홀"
            )
            .with_authority_reportable_accident()
            .build(db_session)
        )
        accidents.append(violation_accident1)

        # 보호구 미착용으로 인한 감전
        violation_accident2 = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[1])
            .with_electric_shock_accident()
            .with_accident_details(
                "절연장갑 미착용 상태로 전기작업 중 감전",
                "절연장갑 미착용",
                "안전수칙 무시 및 작업관리 부실"
            )
            .with_pending_investigation()
            .build(db_session)
        )
        accidents.append(violation_accident2)

        return accidents

    @staticmethod
    async def create_emergency_response_scenario(
        db_session: AsyncSession,
        worker_ids: List[int]
    ) -> List[AccidentReport]:
        """응급대응 시나리오"""
        accidents = []

        # 사망사고 - 즉시 신고 필요
        fatal_accident = await (
            AccidentReportBuilder()
            .with_worker_id(worker_ids[0])
            .with_fatal_accident()
            .with_korean_data()
            .with_immediate_actions("119 신고, 응급처치 시도, 경찰 신고")
            .with_witnesses(
                ["김목격자1", "이목격자2"],
                "고소작업 중 추락하는 것을 목격"
            )
            .with_high_cost_accident()
            .build(db_session)
        )
        accidents.append(fatal_accident)

        return accidents