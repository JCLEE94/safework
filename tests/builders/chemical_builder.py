"""
화학물질 관련 테스트 데이터 빌더
Chemical substance test data builders
"""

from datetime import datetime, date, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.chemical_substance import (
    ChemicalSubstance, ChemicalUsageRecord, HazardClass, StorageStatus
)
from tests.builders.base_builder import BaseBuilder


class ChemicalSubstanceBuilder(BaseBuilder[ChemicalSubstance]):
    """화학물질 빌더"""

    def __init__(self):
        super().__init__()
        self._korean_name: str = "테스트화학물질"
        self._english_name: Optional[str] = "Test Chemical"
        self._cas_number: Optional[str] = "123-45-6"
        self._un_number: Optional[str] = None
        self._hazard_class: HazardClass = HazardClass.TOXIC
        self._hazard_statement: Optional[str] = "피부 접촉시 유해함"
        self._precautionary_statement: Optional[str] = "보호장갑 착용"
        self._signal_word: Optional[str] = "경고"
        self._physical_state: Optional[str] = "액체"
        self._appearance: Optional[str] = "무색투명"
        self._odor: Optional[str] = "무취"
        self._ph_value: Optional[float] = 7.0
        self._boiling_point: Optional[float] = 100.0
        self._melting_point: Optional[float] = 0.0
        self._flash_point: Optional[float] = 50.0
        self._storage_location: Optional[str] = "화학물질보관소"
        self._storage_condition: Optional[str] = "실온보관, 직사광선 피함"
        self._incompatible_materials: Optional[str] = None
        self._current_quantity: Optional[float] = 100.0
        self._quantity_unit: Optional[str] = "L"
        self._minimum_quantity: Optional[float] = 20.0
        self._maximum_quantity: Optional[float] = 500.0
        self._exposure_limit_twa: Optional[float] = 10.0
        self._exposure_limit_stel: Optional[float] = 20.0
        self._exposure_limit_ceiling: Optional[float] = 50.0
        self._msds_file_path: Optional[str] = None
        self._msds_revision_date: Optional[date] = date.today()
        self._manufacturer: Optional[str] = "테스트제조사"
        self._supplier: Optional[str] = "테스트공급사"
        self._emergency_contact: Optional[str] = "02-1234-5678"
        self._special_management_material: str = "N"
        self._carcinogen: str = "N"
        self._mutagen: str = "N"
        self._reproductive_toxin: str = "N"
        self._status: StorageStatus = StorageStatus.IN_USE
        self._notes: Optional[str] = None
        self._created_by: Optional[str] = "test_user"
        self._updated_by: Optional[str] = "test_user"

    def with_korean_name(self, name: str) -> "ChemicalSubstanceBuilder":
        """한글명 설정"""
        self._korean_name = name
        return self

    def with_english_name(self, name: str) -> "ChemicalSubstanceBuilder":
        """영문명 설정"""
        self._english_name = name
        return self

    def with_cas_number(self, cas_number: str) -> "ChemicalSubstanceBuilder":
        """CAS 번호 설정"""
        self._cas_number = cas_number
        return self

    def with_un_number(self, un_number: str) -> "ChemicalSubstanceBuilder":
        """UN 번호 설정"""
        self._un_number = un_number
        return self

    def with_hazard_class(self, hazard_class: HazardClass) -> "ChemicalSubstanceBuilder":
        """유해성 분류 설정"""
        self._hazard_class = hazard_class
        return self

    def with_hazard_statements(self, hazard: str, precautionary: str, signal_word: str = "경고") -> "ChemicalSubstanceBuilder":
        """유해성 문구 설정"""
        self._hazard_statement = hazard
        self._precautionary_statement = precautionary
        self._signal_word = signal_word
        return self

    def with_physical_properties(
        self,
        physical_state: str = "액체",
        appearance: str = "무색투명",
        odor: str = "무취",
        ph_value: float = 7.0
    ) -> "ChemicalSubstanceBuilder":
        """물리적 특성 설정"""
        self._physical_state = physical_state
        self._appearance = appearance
        self._odor = odor
        self._ph_value = ph_value
        return self

    def with_temperature_properties(
        self,
        boiling_point: Optional[float] = None,
        melting_point: Optional[float] = None,
        flash_point: Optional[float] = None
    ) -> "ChemicalSubstanceBuilder":
        """온도 특성 설정"""
        if boiling_point is not None:
            self._boiling_point = boiling_point
        if melting_point is not None:
            self._melting_point = melting_point
        if flash_point is not None:
            self._flash_point = flash_point
        return self

    def with_storage_info(
        self,
        location: str,
        condition: str,
        incompatible_materials: str = None
    ) -> "ChemicalSubstanceBuilder":
        """보관 정보 설정"""
        self._storage_location = location
        self._storage_condition = condition
        self._incompatible_materials = incompatible_materials
        return self

    def with_inventory(
        self,
        current: float,
        unit: str,
        minimum: float = None,
        maximum: float = None
    ) -> "ChemicalSubstanceBuilder":
        """재고 정보 설정"""
        self._current_quantity = current
        self._quantity_unit = unit
        if minimum is not None:
            self._minimum_quantity = minimum
        if maximum is not None:
            self._maximum_quantity = maximum
        return self

    def with_exposure_limits(
        self,
        twa: Optional[float] = None,
        stel: Optional[float] = None,
        ceiling: Optional[float] = None
    ) -> "ChemicalSubstanceBuilder":
        """노출기준 설정"""
        if twa is not None:
            self._exposure_limit_twa = twa
        if stel is not None:
            self._exposure_limit_stel = stel
        if ceiling is not None:
            self._exposure_limit_ceiling = ceiling
        return self

    def with_msds_info(
        self,
        file_path: str = None,
        revision_date: date = None,
        manufacturer: str = None,
        supplier: str = None,
        emergency_contact: str = None
    ) -> "ChemicalSubstanceBuilder":
        """MSDS 정보 설정"""
        if file_path is not None:
            self._msds_file_path = file_path
        if revision_date is not None:
            self._msds_revision_date = revision_date
        if manufacturer is not None:
            self._manufacturer = manufacturer
        if supplier is not None:
            self._supplier = supplier
        if emergency_contact is not None:
            self._emergency_contact = emergency_contact
        return self

    def with_special_flags(
        self,
        special_management: bool = False,
        carcinogen: bool = False,
        mutagen: bool = False,
        reproductive_toxin: bool = False
    ) -> "ChemicalSubstanceBuilder":
        """특별관리 플래그 설정"""
        self._special_management_material = "Y" if special_management else "N"
        self._carcinogen = "Y" if carcinogen else "N"
        self._mutagen = "Y" if mutagen else "N"
        self._reproductive_toxin = "Y" if reproductive_toxin else "N"
        return self

    def with_status(self, status: StorageStatus) -> "ChemicalSubstanceBuilder":
        """상태 설정"""
        self._status = status
        return self

    def with_notes(self, notes: str) -> "ChemicalSubstanceBuilder":
        """비고 설정"""
        self._notes = notes
        return self

    def with_created_by(self, created_by: str) -> "ChemicalSubstanceBuilder":
        """생성자 설정"""
        self._created_by = created_by
        self._updated_by = created_by
        return self

    def with_korean_data(self) -> "ChemicalSubstanceBuilder":
        """한국어 테스트 데이터 설정"""
        self._korean_name = "아세톤"
        self._english_name = "Acetone"
        self._cas_number = "67-64-1"
        self._un_number = "UN1090"
        self._hazard_class = HazardClass.FLAMMABLE
        self._hazard_statement = "고인화성 액체 및 증기"
        self._precautionary_statement = "열·스파크·화염·고열로부터 멀리하시오"
        self._signal_word = "위험"
        self._physical_state = "액체"
        self._appearance = "무색투명한 액체"
        self._odor = "달콤한 냄새"
        self._storage_location = "인화성물질 보관소"
        self._storage_condition = "서늘하고 환기가 잘 되는 곳에 보관"
        self._incompatible_materials = "강산화제, 강염기와 분리보관"
        self._manufacturer = "한국화학공업㈜"
        self._supplier = "안전화학물질㈜"
        self._emergency_contact = "02-123-4567 (24시간)"
        return self

    def with_toxic_chemical(self) -> "ChemicalSubstanceBuilder":
        """독성 화학물질 설정"""
        self._korean_name = "벤젠"
        self._english_name = "Benzene"
        self._cas_number = "71-43-2"
        self._hazard_class = HazardClass.TOXIC
        self._hazard_statement = "암을 일으킬 수 있음"
        self._precautionary_statement = "적절한 개인보호구를 착용하시오"
        self._signal_word = "위험"
        self._carcinogen = "Y"
        self._special_management_material = "Y"
        self._exposure_limit_twa = 1.0
        self._exposure_limit_stel = 5.0
        return self

    def with_corrosive_chemical(self) -> "ChemicalSubstanceBuilder":
        """부식성 화학물질 설정"""
        self._korean_name = "황산"
        self._english_name = "Sulfuric Acid"
        self._cas_number = "7664-93-9"
        self._hazard_class = HazardClass.CORROSIVE
        self._hazard_statement = "심한 화상 및 눈 손상을 일으킴"
        self._precautionary_statement = "보호장갑·보호의·보안경·안면보호구를 착용하시오"
        self._signal_word = "위험"
        self._storage_condition = "내산성 용기에 보관, 환기시설 완비"
        return self

    def with_flammable_chemical(self) -> "ChemicalSubstanceBuilder":
        """인화성 화학물질 설정"""
        self._korean_name = "에탄올"
        self._english_name = "Ethanol"
        self._cas_number = "64-17-5"
        self._hazard_class = HazardClass.FLAMMABLE
        self._flash_point = 13.0
        self._storage_condition = "화기 엄금, 서늘한 곳 보관"
        return self

    def with_explosive_chemical(self) -> "ChemicalSubstanceBuilder":
        """폭발성 화학물질 설정"""
        self._korean_name = "니트로글리세린"
        self._english_name = "Nitroglycerin"
        self._cas_number = "55-63-0"
        self._hazard_class = HazardClass.EXPLOSIVE
        self._hazard_statement = "충격, 마찰, 화염에 의해 폭발할 수 있음"
        self._signal_word = "위험"
        self._special_management_material = "Y"
        self._storage_condition = "진동 및 충격 방지, 온도 조절"
        return self

    def with_low_stock(self) -> "ChemicalSubstanceBuilder":
        """재고 부족 상태 설정"""
        self._current_quantity = 5.0
        self._minimum_quantity = 20.0
        self._maximum_quantity = 100.0
        return self

    def with_excess_stock(self) -> "ChemicalSubstanceBuilder":
        """재고 과잉 상태 설정"""
        self._current_quantity = 150.0
        self._minimum_quantity = 20.0
        self._maximum_quantity = 100.0
        return self

    def with_expired_status(self) -> "ChemicalSubstanceBuilder":
        """만료된 상태 설정"""
        self._status = StorageStatus.EXPIRED
        return self

    def with_disposed_status(self) -> "ChemicalSubstanceBuilder":
        """폐기된 상태 설정"""
        self._status = StorageStatus.DISPOSED
        return self

    def with_outdated_msds(self) -> "ChemicalSubstanceBuilder":
        """오래된 MSDS 설정"""
        self._msds_revision_date = date.today() - timedelta(days=400)  # 1년 이상 전
        return self

    async def build(self, db_session: AsyncSession) -> ChemicalSubstance:
        """화학물질 생성"""
        chemical = ChemicalSubstance(
            korean_name=self._korean_name,
            english_name=self._english_name,
            cas_number=self._cas_number,
            un_number=self._un_number,
            hazard_class=self._hazard_class,
            hazard_statement=self._hazard_statement,
            precautionary_statement=self._precautionary_statement,
            signal_word=self._signal_word,
            physical_state=self._physical_state,
            appearance=self._appearance,
            odor=self._odor,
            ph_value=self._ph_value,
            boiling_point=self._boiling_point,
            melting_point=self._melting_point,
            flash_point=self._flash_point,
            storage_location=self._storage_location,
            storage_condition=self._storage_condition,
            incompatible_materials=self._incompatible_materials,
            current_quantity=self._current_quantity,
            quantity_unit=self._quantity_unit,
            minimum_quantity=self._minimum_quantity,
            maximum_quantity=self._maximum_quantity,
            exposure_limit_twa=self._exposure_limit_twa,
            exposure_limit_stel=self._exposure_limit_stel,
            exposure_limit_ceiling=self._exposure_limit_ceiling,
            msds_file_path=self._msds_file_path,
            msds_revision_date=self._msds_revision_date,
            manufacturer=self._manufacturer,
            supplier=self._supplier,
            emergency_contact=self._emergency_contact,
            special_management_material=self._special_management_material,
            carcinogen=self._carcinogen,
            mutagen=self._mutagen,
            reproductive_toxin=self._reproductive_toxin,
            status=self._status,
            notes=self._notes,
            created_by=self._created_by,
            updated_by=self._updated_by
        )

        db_session.add(chemical)
        await db_session.commit()
        await db_session.refresh(chemical)
        return chemical


class ChemicalUsageRecordBuilder(BaseBuilder[ChemicalUsageRecord]):
    """화학물질 사용 기록 빌더"""

    def __init__(self):
        super().__init__()
        self._chemical_id: Optional[int] = None
        self._usage_date: datetime = datetime.now()
        self._worker_id: Optional[int] = None
        self._quantity_used: float = 5.0
        self._quantity_unit: Optional[str] = "L"
        self._purpose: Optional[str] = "청소작업"
        self._work_location: Optional[str] = "작업장 A"
        self._ventilation_used: str = "Y"
        self._ppe_used: Optional[str] = "보호장갑, 안전고글"
        self._exposure_duration_minutes: Optional[int] = 60
        self._incident_occurred: str = "N"
        self._incident_description: Optional[str] = None
        self._created_by: Optional[str] = "test_user"

    def with_chemical_id(self, chemical_id: int) -> "ChemicalUsageRecordBuilder":
        """화학물질 ID 설정"""
        self._chemical_id = chemical_id
        return self

    def with_usage_date(self, usage_date: datetime) -> "ChemicalUsageRecordBuilder":
        """사용일시 설정"""
        self._usage_date = usage_date
        return self

    def with_worker_id(self, worker_id: int) -> "ChemicalUsageRecordBuilder":
        """근로자 ID 설정"""
        self._worker_id = worker_id
        return self

    def with_quantity_used(self, quantity: float, unit: str = "L") -> "ChemicalUsageRecordBuilder":
        """사용량 설정"""
        self._quantity_used = quantity
        self._quantity_unit = unit
        return self

    def with_purpose_and_location(self, purpose: str, work_location: str) -> "ChemicalUsageRecordBuilder":
        """사용 목적 및 장소 설정"""
        self._purpose = purpose
        self._work_location = work_location
        return self

    def with_safety_measures(
        self,
        ventilation_used: bool = True,
        ppe_used: str = "보호장갑, 안전고글",
        exposure_duration_minutes: int = 60
    ) -> "ChemicalUsageRecordBuilder":
        """안전조치 설정"""
        self._ventilation_used = "Y" if ventilation_used else "N"
        self._ppe_used = ppe_used
        self._exposure_duration_minutes = exposure_duration_minutes
        return self

    def with_incident(self, description: str) -> "ChemicalUsageRecordBuilder":
        """사고 발생 설정"""
        self._incident_occurred = "Y"
        self._incident_description = description
        return self

    def with_created_by(self, created_by: str) -> "ChemicalUsageRecordBuilder":
        """생성자 설정"""
        self._created_by = created_by
        return self

    def with_korean_data(self) -> "ChemicalUsageRecordBuilder":
        """한국어 테스트 데이터 설정"""
        self._purpose = "부품 세척 작업"
        self._work_location = "제1공장 세척실"
        self._ppe_used = "화학보호장갑, 보안경, 방독마스크"
        return self

    def with_high_risk_usage(self) -> "ChemicalUsageRecordBuilder":
        """고위험 사용 설정"""
        self._quantity_used = 50.0
        self._exposure_duration_minutes = 240  # 4시간
        self._ventilation_used = "N"
        self._purpose = "대량 청소 작업"
        return self

    def with_minimal_safety_usage(self) -> "ChemicalUsageRecordBuilder":
        """최소 안전조치 사용 설정"""
        self._ventilation_used = "N"
        self._ppe_used = "일반장갑"
        self._exposure_duration_minutes = 120
        return self

    def with_safe_usage(self) -> "ChemicalUsageRecordBuilder":
        """안전한 사용 설정"""
        self._quantity_used = 2.0
        self._exposure_duration_minutes = 30
        self._ventilation_used = "Y"
        self._ppe_used = "화학보호장갑, 보안경, 방독마스크, 보호복"
        return self

    def with_recent_usage(self, days_ago: int = 1) -> "ChemicalUsageRecordBuilder":
        """최근 사용 설정"""
        self._usage_date = datetime.now() - timedelta(days=days_ago)
        return self

    async def build(self, db_session: AsyncSession) -> ChemicalUsageRecord:
        """화학물질 사용 기록 생성"""
        if self._chemical_id is None:
            raise ValueError("chemical_id is required")
        if self._worker_id is None:
            raise ValueError("worker_id is required")

        usage_record = ChemicalUsageRecord(
            chemical_id=self._chemical_id,
            usage_date=self._usage_date,
            worker_id=self._worker_id,
            quantity_used=self._quantity_used,
            quantity_unit=self._quantity_unit,
            purpose=self._purpose,
            work_location=self._work_location,
            ventilation_used=self._ventilation_used,
            ppe_used=self._ppe_used,
            exposure_duration_minutes=self._exposure_duration_minutes,
            incident_occurred=self._incident_occurred,
            incident_description=self._incident_description,
            created_by=self._created_by
        )

        db_session.add(usage_record)
        await db_session.commit()
        await db_session.refresh(usage_record)
        return usage_record


class ChemicalCompleteBuilder:
    """완전한 화학물질 기록 (화학물질+사용기록) 생성 빌더"""

    def __init__(self):
        self._chemical_builder = ChemicalSubstanceBuilder()
        self._usage_builders: list[ChemicalUsageRecordBuilder] = []

    def with_chemical_builder(self, builder: ChemicalSubstanceBuilder) -> "ChemicalCompleteBuilder":
        """화학물질 빌더 설정"""
        self._chemical_builder = builder
        return self

    def add_usage_record(self, builder: ChemicalUsageRecordBuilder) -> "ChemicalCompleteBuilder":
        """사용 기록 빌더 추가"""
        self._usage_builders.append(builder)
        return self

    def with_multiple_usage_records(
        self,
        worker_ids: list[int],
        purposes: list[str] = None,
        quantities: list[float] = None
    ) -> "ChemicalCompleteBuilder":
        """다중 사용 기록 설정"""
        if purposes is None:
            purposes = ["청소작업"] * len(worker_ids)
        if quantities is None:
            quantities = [5.0] * len(worker_ids)

        for i, worker_id in enumerate(worker_ids):
            purpose = purposes[i] if i < len(purposes) else purposes[-1]
            quantity = quantities[i] if i < len(quantities) else quantities[-1]
            
            builder = (
                ChemicalUsageRecordBuilder()
                .with_worker_id(worker_id)
                .with_purpose_and_location(purpose, f"작업장{i+1}")
                .with_quantity_used(quantity)
                .with_recent_usage(i + 1)
            )
            self._usage_builders.append(builder)

        return self

    def with_safety_violation_scenario(self, worker_ids: list[int]) -> "ChemicalCompleteBuilder":
        """안전수칙 위반 시나리오 설정"""
        # 위험한 화학물질로 설정
        self._chemical_builder = self._chemical_builder.with_toxic_chemical()

        for i, worker_id in enumerate(worker_ids):
            if i % 2 == 0:  # 안전조치 미흡
                builder = (
                    ChemicalUsageRecordBuilder()
                    .with_worker_id(worker_id)
                    .with_minimal_safety_usage()
                    .with_korean_data()
                )
            else:  # 사고 발생
                builder = (
                    ChemicalUsageRecordBuilder()
                    .with_worker_id(worker_id)
                    .with_high_risk_usage()
                    .with_incident("화학물질 누출로 인한 피부 접촉")
                    .with_korean_data()
                )
            
            self._usage_builders.append(builder)

        return self

    def with_inventory_depletion_scenario(self, worker_ids: list[int]) -> "ChemicalCompleteBuilder":
        """재고 소진 시나리오 설정"""
        # 재고 부족 화학물질로 설정
        self._chemical_builder = self._chemical_builder.with_low_stock()

        # 대량 사용으로 재고 더욱 감소
        for worker_id in worker_ids:
            builder = (
                ChemicalUsageRecordBuilder()
                .with_worker_id(worker_id)
                .with_quantity_used(10.0)  # 많은 양 사용
                .with_purpose_and_location("대규모 청소", "전체 공장")
                .with_korean_data()
            )
            self._usage_builders.append(builder)

        return self

    async def build(self, db_session: AsyncSession) -> ChemicalSubstance:
        """완전한 화학물질 기록 생성"""
        # 1. 화학물질 생성
        chemical = await self._chemical_builder.build(db_session)

        # 2. 사용 기록들 생성
        for usage_builder in self._usage_builders:
            await usage_builder.with_chemical_id(chemical.id).build(db_session)

        # 관계 로드를 위해 새로 고침
        await db_session.refresh(chemical)
        return chemical