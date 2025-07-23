"""
작업환경측정 관련 테스트 데이터 빌더
Work environment monitoring test data builders
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.work_environment import (
    WorkEnvironment, WorkEnvironmentWorkerExposure, MeasurementType, MeasurementResult
)
from tests.builders.base_builder import BaseBuilder


class WorkEnvironmentBuilder(BaseBuilder[WorkEnvironment]):
    """작업환경측정 기록 빌더"""

    def __init__(self):
        super().__init__()
        self._measurement_date: datetime = datetime.now()
        self._location: str = "테스트작업장"
        self._measurement_type: MeasurementType = MeasurementType.NOISE
        self._measurement_agency: str = "환경측정센터"
        self._measured_value: Optional[float] = 85.0
        self._measurement_unit: Optional[str] = "dB"
        self._standard_value: Optional[float] = 90.0
        self._standard_unit: Optional[str] = "dB"
        self._result: MeasurementResult = MeasurementResult.PASS
        self._improvement_measures: Optional[str] = None
        self._re_measurement_required: str = "N"
        self._re_measurement_date: Optional[datetime] = None
        self._report_number: Optional[str] = None
        self._report_file_path: Optional[str] = None
        self._notes: Optional[str] = None
        self._created_by: Optional[str] = "test_user"
        self._updated_by: Optional[str] = "test_user"

    def with_measurement_date(self, measurement_date: datetime) -> "WorkEnvironmentBuilder":
        """측정일 설정"""
        self._measurement_date = measurement_date
        return self

    def with_location(self, location: str) -> "WorkEnvironmentBuilder":
        """측정 위치 설정"""
        self._location = location
        return self

    def with_measurement_type(self, measurement_type: MeasurementType) -> "WorkEnvironmentBuilder":
        """측정 항목 설정"""
        self._measurement_type = measurement_type
        return self

    def with_measurement_agency(self, agency: str) -> "WorkEnvironmentBuilder":
        """측정 기관 설정"""
        self._measurement_agency = agency
        return self

    def with_measurement_values(
        self, 
        measured_value: float, 
        measured_unit: str, 
        standard_value: float, 
        standard_unit: str
    ) -> "WorkEnvironmentBuilder":
        """측정값 및 기준값 설정"""
        self._measured_value = measured_value
        self._measurement_unit = measured_unit
        self._standard_value = standard_value
        self._standard_unit = standard_unit
        return self

    def with_result(self, result: MeasurementResult) -> "WorkEnvironmentBuilder":
        """측정 결과 설정"""
        self._result = result
        return self

    def with_improvement_measures(self, measures: str) -> "WorkEnvironmentBuilder":
        """개선조치 사항 설정"""
        self._improvement_measures = measures
        return self

    def with_re_measurement_required(
        self, 
        required: bool = True, 
        re_measurement_date: Optional[datetime] = None
    ) -> "WorkEnvironmentBuilder":
        """재측정 필요 설정"""
        self._re_measurement_required = "Y" if required else "N"
        if required and re_measurement_date:
            self._re_measurement_date = re_measurement_date
        elif required:
            self._re_measurement_date = self._measurement_date + timedelta(days=90)  # 기본 3개월 후
        return self

    def with_report_info(self, report_number: str, report_file_path: Optional[str] = None) -> "WorkEnvironmentBuilder":
        """보고서 정보 설정"""
        self._report_number = report_number
        self._report_file_path = report_file_path
        return self

    def with_notes(self, notes: str) -> "WorkEnvironmentBuilder":
        """비고 설정"""
        self._notes = notes
        return self

    def with_created_by(self, created_by: str) -> "WorkEnvironmentBuilder":
        """생성자 설정"""
        self._created_by = created_by
        self._updated_by = created_by
        return self

    def with_korean_data(self) -> "WorkEnvironmentBuilder":
        """한국어 테스트 데이터 설정"""
        self._location = "제1공장 생산라인"
        self._measurement_agency = "한국산업보건공단"
        self._improvement_measures = "작업환경 개선조치 완료"
        self._report_number = "환경측정-2024-001"
        self._notes = "정기 작업환경측정 실시 완료"
        return self

    def with_noise_measurement(self, noise_level: float = 88.0, is_compliant: bool = True) -> "WorkEnvironmentBuilder":
        """소음 측정 데이터 설정"""
        self._measurement_type = MeasurementType.NOISE
        self._measured_value = noise_level
        self._measurement_unit = "dB"
        self._standard_value = 90.0
        self._standard_unit = "dB"
        self._result = MeasurementResult.PASS if is_compliant else MeasurementResult.FAIL
        
        if not is_compliant:
            self._improvement_measures = "방음시설 보강 및 개인보호구 지급"
            self._re_measurement_required = "Y"
        
        return self

    def with_dust_measurement(self, dust_level: float = 3.0, is_compliant: bool = True) -> "WorkEnvironmentBuilder":
        """분진 측정 데이터 설정"""
        self._measurement_type = MeasurementType.DUST
        self._measured_value = dust_level
        self._measurement_unit = "mg/m³"
        self._standard_value = 5.0
        self._standard_unit = "mg/m³"
        self._result = MeasurementResult.PASS if is_compliant else MeasurementResult.FAIL
        
        if not is_compliant:
            self._improvement_measures = "집진시설 설치 및 개인보호구 지급"
            self._re_measurement_required = "Y"
        
        return self

    def with_chemical_measurement(self, chemical_level: float = 15.0, is_compliant: bool = True) -> "WorkEnvironmentBuilder":
        """화학물질 측정 데이터 설정"""
        self._measurement_type = MeasurementType.CHEMICAL
        self._measured_value = chemical_level
        self._measurement_unit = "ppm"
        self._standard_value = 20.0
        self._standard_unit = "ppm"
        self._result = MeasurementResult.PASS if is_compliant else MeasurementResult.FAIL
        
        if not is_compliant:
            self._improvement_measures = "국소배기장치 설치 및 환기시설 개선"
            self._re_measurement_required = "Y"
        
        return self

    def with_temperature_measurement(self, temperature: float = 28.0, is_compliant: bool = True) -> "WorkEnvironmentBuilder":
        """고온 측정 데이터 설정"""
        self._measurement_type = MeasurementType.TEMPERATURE
        self._measured_value = temperature
        self._measurement_unit = "℃"
        self._standard_value = 30.0
        self._standard_unit = "℃"
        
        if temperature > 30.0:
            self._result = MeasurementResult.FAIL
        elif temperature > 28.0:
            self._result = MeasurementResult.CAUTION
        else:
            self._result = MeasurementResult.PASS
        
        if not is_compliant:
            self._improvement_measures = "냉방시설 보강 및 작업시간 조정"
            self._re_measurement_required = "Y"
        
        return self

    def with_vibration_measurement(self, vibration_level: float = 3.0, is_compliant: bool = True) -> "WorkEnvironmentBuilder":
        """진동 측정 데이터 설정"""
        self._measurement_type = MeasurementType.VIBRATION
        self._measured_value = vibration_level
        self._measurement_unit = "m/s²"
        self._standard_value = 5.0
        self._standard_unit = "m/s²"
        self._result = MeasurementResult.PASS if is_compliant else MeasurementResult.FAIL
        
        if not is_compliant:
            self._improvement_measures = "진동저감장치 설치 및 작업방법 개선"
            self._re_measurement_required = "Y"
        
        return self

    def with_failed_measurement(self) -> "WorkEnvironmentBuilder":
        """부적합 측정 데이터 설정"""
        self._result = MeasurementResult.FAIL
        self._improvement_measures = "즉시 개선조치 필요"
        self._re_measurement_required = "Y"
        self._re_measurement_date = self._measurement_date + timedelta(days=30)  # 1개월 후 재측정
        return self

    async def build(self, db_session: AsyncSession) -> WorkEnvironment:
        """작업환경측정 기록 생성"""
        work_environment = WorkEnvironment(
            measurement_date=self._measurement_date,
            location=self._location,
            measurement_type=self._measurement_type,
            measurement_agency=self._measurement_agency,
            measured_value=self._measured_value,
            measurement_unit=self._measurement_unit,
            standard_value=self._standard_value,
            standard_unit=self._standard_unit,
            result=self._result,
            improvement_measures=self._improvement_measures,
            re_measurement_required=self._re_measurement_required,
            re_measurement_date=self._re_measurement_date,
            report_number=self._report_number,
            report_file_path=self._report_file_path,
            notes=self._notes,
            created_by=self._created_by,
            updated_by=self._updated_by
        )

        db_session.add(work_environment)
        await db_session.commit()
        await db_session.refresh(work_environment)
        return work_environment


class WorkerExposureBuilder(BaseBuilder[WorkEnvironmentWorkerExposure]):
    """근로자 노출 정보 빌더"""

    def __init__(self):
        super().__init__()
        self._work_environment_id: Optional[int] = None
        self._worker_id: Optional[int] = None
        self._exposure_level: Optional[float] = 15.0
        self._exposure_duration_hours: Optional[float] = 8.0
        self._protection_equipment_used: Optional[str] = "방독마스크"
        self._health_effect_risk: Optional[str] = "경미"

    def with_work_environment_id(self, work_environment_id: int) -> "WorkerExposureBuilder":
        """작업환경측정 ID 설정"""
        self._work_environment_id = work_environment_id
        return self

    def with_worker_id(self, worker_id: int) -> "WorkerExposureBuilder":
        """근로자 ID 설정"""
        self._worker_id = worker_id
        return self

    def with_exposure_level(self, exposure_level: float) -> "WorkerExposureBuilder":
        """노출 수준 설정"""
        self._exposure_level = exposure_level
        return self

    def with_exposure_duration(self, duration_hours: float) -> "WorkerExposureBuilder":
        """노출 시간 설정"""
        self._exposure_duration_hours = duration_hours
        return self

    def with_protection_equipment(self, equipment: str) -> "WorkerExposureBuilder":
        """보호구 사용 설정"""
        self._protection_equipment_used = equipment
        return self

    def with_health_risk(self, risk: str) -> "WorkerExposureBuilder":
        """건강 영향 위험 설정"""
        self._health_effect_risk = risk
        return self

    def with_high_risk_exposure(self) -> "WorkerExposureBuilder":
        """고위험 노출 설정"""
        self._exposure_level = 35.0
        self._exposure_duration_hours = 8.0
        self._protection_equipment_used = "전면마스크, 보호복, 보호장갑"
        self._health_effect_risk = "높음"
        return self

    def with_moderate_risk_exposure(self) -> "WorkerExposureBuilder":
        """중위험 노출 설정"""
        self._exposure_level = 20.0
        self._exposure_duration_hours = 6.0
        self._protection_equipment_used = "반면마스크, 보호장갑"
        self._health_effect_risk = "보통"
        return self

    def with_low_risk_exposure(self) -> "WorkerExposureBuilder":
        """저위험 노출 설정"""
        self._exposure_level = 8.0
        self._exposure_duration_hours = 4.0
        self._protection_equipment_used = "일반마스크"
        self._health_effect_risk = "낮음"
        return self

    def with_korean_data(self) -> "WorkerExposureBuilder":
        """한국어 테스트 데이터 설정"""
        self._protection_equipment_used = "방독마스크, 안전장갑, 보호복"
        self._health_effect_risk = "호흡기 및 피부 접촉 위험"
        return self

    async def build(self, db_session: AsyncSession) -> WorkEnvironmentWorkerExposure:
        """근로자 노출 정보 생성"""
        if self._work_environment_id is None:
            raise ValueError("work_environment_id is required")
        if self._worker_id is None:
            raise ValueError("worker_id is required")

        worker_exposure = WorkEnvironmentWorkerExposure(
            work_environment_id=self._work_environment_id,
            worker_id=self._worker_id,
            exposure_level=self._exposure_level,
            exposure_duration_hours=self._exposure_duration_hours,
            protection_equipment_used=self._protection_equipment_used,
            health_effect_risk=self._health_effect_risk
        )

        db_session.add(worker_exposure)
        await db_session.commit()
        await db_session.refresh(worker_exposure)
        return worker_exposure


class WorkEnvironmentCompleteBuilder:
    """완전한 작업환경측정 기록 (측정+근로자노출) 생성 빌더"""

    def __init__(self):
        self._work_environment_builder = WorkEnvironmentBuilder()
        self._worker_exposure_builders: list[WorkerExposureBuilder] = []

    def with_work_environment_builder(self, builder: WorkEnvironmentBuilder) -> "WorkEnvironmentCompleteBuilder":
        """작업환경측정 빌더 설정"""
        self._work_environment_builder = builder
        return self

    def add_worker_exposure(self, builder: WorkerExposureBuilder) -> "WorkEnvironmentCompleteBuilder":
        """근로자 노출 정보 빌더 추가"""
        self._worker_exposure_builders.append(builder)
        return self

    def with_multiple_worker_exposures(self, worker_ids: list[int], risk_levels: list[str] = None) -> "WorkEnvironmentCompleteBuilder":
        """다중 근로자 노출 정보 설정"""
        if risk_levels is None:
            risk_levels = ["낮음"] * len(worker_ids)
        
        for worker_id, risk_level in zip(worker_ids, risk_levels):
            builder = WorkerExposureBuilder().with_worker_id(worker_id)
            
            if risk_level == "높음":
                builder = builder.with_high_risk_exposure()
            elif risk_level == "보통":
                builder = builder.with_moderate_risk_exposure()
            else:
                builder = builder.with_low_risk_exposure()
            
            self._worker_exposure_builders.append(builder)
        
        return self

    def with_high_risk_scenario(self, worker_ids: list[int]) -> "WorkEnvironmentCompleteBuilder":
        """고위험 시나리오 설정 (측정 부적합 + 고위험 노출)"""
        # 작업환경측정을 부적합으로 설정
        self._work_environment_builder = self._work_environment_builder.with_failed_measurement()
        
        # 모든 근로자를 고위험 노출로 설정
        for worker_id in worker_ids:
            builder = (
                WorkerExposureBuilder()
                .with_worker_id(worker_id)
                .with_high_risk_exposure()
                .with_korean_data()
            )
            self._worker_exposure_builders.append(builder)
        
        return self

    async def build(self, db_session: AsyncSession) -> WorkEnvironment:
        """완전한 작업환경측정 기록 생성"""
        # 1. 작업환경측정 기록 생성
        work_environment = await self._work_environment_builder.build(db_session)

        # 2. 근로자 노출 정보들 생성
        for exposure_builder in self._worker_exposure_builders:
            await exposure_builder.with_work_environment_id(work_environment.id).build(db_session)

        # 관계 로드를 위해 새로 고침
        await db_session.refresh(work_environment)
        return work_environment