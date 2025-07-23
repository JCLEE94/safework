"""
건강 관련 테스트 데이터 빌더
Health-related test data builders
"""

from datetime import date, datetime, timedelta
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.health import (
    HealthExam, VitalSigns, LabResult, ExamType, ExamResult, PostManagement
)
from tests.builders.base_builder import BaseBuilder


class HealthExamBuilder(BaseBuilder[HealthExam]):
    """건강진단 기록 빌더"""

    def __init__(self):
        super().__init__()
        self._worker_id: Optional[int] = None
        self._exam_type: ExamType = ExamType.GENERAL
        self._exam_date: date = datetime.now().date()
        self._exam_institution: str = "테스트건강검진센터"
        self._exam_doctor: Optional[str] = "김의사"
        self._exam_result: Optional[ExamResult] = ExamResult.NORMAL_A
        self._post_management: Optional[PostManagement] = None
        self._next_exam_date: Optional[date] = None
        self._harmful_factors: Optional[List[str]] = None
        self._medical_opinion: Optional[str] = None
        self._work_suitability: Optional[str] = None
        self._recommendations: Optional[str] = None
        self._restrictions: Optional[str] = None
        self._is_followup_required: bool = False
        self._followup_date: Optional[date] = None
        self._followup_notes: Optional[str] = None
        self._report_file_path: Optional[str] = None
        self._notes: Optional[str] = None

    def with_worker_id(self, worker_id: int) -> "HealthExamBuilder":
        """근로자 ID 설정"""
        self._worker_id = worker_id
        return self

    def with_exam_type(self, exam_type: ExamType) -> "HealthExamBuilder":
        """검진 유형 설정"""
        self._exam_type = exam_type
        return self

    def with_exam_date(self, exam_date: date) -> "HealthExamBuilder":
        """검진일 설정"""
        self._exam_date = exam_date
        return self

    def with_exam_institution(self, institution: str) -> "HealthExamBuilder":
        """검진기관 설정"""
        self._exam_institution = institution
        return self

    def with_exam_doctor(self, doctor: str) -> "HealthExamBuilder":
        """검진의사 설정"""
        self._exam_doctor = doctor
        return self

    def with_exam_result(self, result: ExamResult) -> "HealthExamBuilder":
        """검진 결과 설정"""
        self._exam_result = result
        return self

    def with_post_management(self, management: PostManagement) -> "HealthExamBuilder":
        """사후관리 구분 설정"""
        self._post_management = management
        return self

    def with_next_exam_date(self, next_date: date) -> "HealthExamBuilder":
        """다음 검진일 설정"""
        self._next_exam_date = next_date
        return self

    def with_harmful_factors(self, factors: List[str]) -> "HealthExamBuilder":
        """유해인자 설정 (특수건강진단용)"""
        self._harmful_factors = factors
        return self

    def with_medical_opinion(self, opinion: str) -> "HealthExamBuilder":
        """의학적 소견 설정"""
        self._medical_opinion = opinion
        return self

    def with_work_suitability(self, suitability: str) -> "HealthExamBuilder":
        """작업 적합성 설정"""
        self._work_suitability = suitability
        return self

    def with_recommendations(self, recommendations: str) -> "HealthExamBuilder":
        """권고사항 설정"""
        self._recommendations = recommendations
        return self

    def with_restrictions(self, restrictions: str) -> "HealthExamBuilder":
        """제한사항 설정"""
        self._restrictions = restrictions
        return self

    def with_followup_required(self, required: bool = True, followup_date: Optional[date] = None, notes: Optional[str] = None) -> "HealthExamBuilder":
        """추적관리 필요 설정"""
        self._is_followup_required = required
        if followup_date:
            self._followup_date = followup_date
        elif required:
            self._followup_date = self._exam_date + timedelta(days=90)  # 기본 3개월 후
        if notes:
            self._followup_notes = notes
        return self

    def with_report_file(self, file_path: str) -> "HealthExamBuilder":
        """검진 보고서 파일 경로 설정"""
        self._report_file_path = file_path
        return self

    def with_notes(self, notes: str) -> "HealthExamBuilder":
        """비고 설정"""
        self._notes = notes
        return self

    def with_korean_data(self) -> "HealthExamBuilder":
        """한국어 테스트 데이터 설정"""
        self._exam_institution = "서울대학교병원 건강검진센터"
        self._exam_doctor = "김건강"
        self._medical_opinion = "전반적인 건강상태가 양호합니다."
        self._work_suitability = "현재 업무에 적합합니다."
        self._recommendations = "정기적인 운동과 금연을 권장합니다."
        self._notes = "정기검진 완료. 다음 검진까지 건강관리 유지 바랍니다."
        return self

    async def build(self, db_session: AsyncSession) -> HealthExam:
        """건강진단 기록 생성"""
        if self._worker_id is None:
            raise ValueError("worker_id is required")

        # 유해인자 JSON 변환 (특수건강진단의 경우)
        harmful_factors_json = None
        if self._harmful_factors:
            import json
            harmful_factors_json = json.dumps(self._harmful_factors, ensure_ascii=False)

        health_exam = HealthExam(
            worker_id=self._worker_id,
            exam_type=self._exam_type,
            exam_date=self._exam_date,
            exam_institution=self._exam_institution,
            exam_doctor=self._exam_doctor,
            exam_result=self._exam_result,
            post_management=self._post_management,
            next_exam_date=self._next_exam_date,
            harmful_factors=harmful_factors_json,
            medical_opinion=self._medical_opinion,
            work_suitability=self._work_suitability,
            recommendations=self._recommendations,
            restrictions=self._restrictions,
            is_followup_required=self._is_followup_required,
            followup_date=self._followup_date,
            followup_notes=self._followup_notes,
            report_file_path=self._report_file_path,
            notes=self._notes
        )

        db_session.add(health_exam)
        await db_session.commit()
        await db_session.refresh(health_exam)
        return health_exam


class VitalSignsBuilder(BaseBuilder[VitalSigns]):
    """기초검사 결과 빌더"""

    def __init__(self):
        super().__init__()
        self._health_exam_id: Optional[int] = None
        self._height: Optional[float] = 170.0
        self._weight: Optional[float] = 70.0
        self._bmi: Optional[float] = None
        self._waist_circumference: Optional[float] = 85.0
        self._systolic_bp: Optional[int] = 120
        self._diastolic_bp: Optional[int] = 80
        self._vision_left: Optional[float] = 1.0
        self._vision_right: Optional[float] = 1.0
        self._hearing_left_1000hz: Optional[int] = 15
        self._hearing_right_1000hz: Optional[int] = 15
        self._hearing_left_4000hz: Optional[int] = 20
        self._hearing_right_4000hz: Optional[int] = 20

    def with_health_exam_id(self, exam_id: int) -> "VitalSignsBuilder":
        """건강진단 ID 설정"""
        self._health_exam_id = exam_id
        return self

    def with_physical_measurements(self, height: float, weight: float, waist: Optional[float] = None) -> "VitalSignsBuilder":
        """신체계측 데이터 설정"""
        self._height = height
        self._weight = weight
        self._bmi = round(weight / ((height / 100) ** 2), 1)
        if waist:
            self._waist_circumference = waist
        return self

    def with_blood_pressure(self, systolic: int, diastolic: int) -> "VitalSignsBuilder":
        """혈압 데이터 설정"""
        self._systolic_bp = systolic
        self._diastolic_bp = diastolic
        return self

    def with_vision(self, left: float, right: float) -> "VitalSignsBuilder":
        """시력 데이터 설정"""
        self._vision_left = left
        self._vision_right = right
        return self

    def with_hearing(self, left_1000: int, right_1000: int, left_4000: int, right_4000: int) -> "VitalSignsBuilder":
        """청력 데이터 설정"""
        self._hearing_left_1000hz = left_1000
        self._hearing_right_1000hz = right_1000
        self._hearing_left_4000hz = left_4000
        self._hearing_right_4000hz = right_4000
        return self

    def with_abnormal_data(self) -> "VitalSignsBuilder":
        """이상 소견 데이터 설정"""
        self._height = 165.0
        self._weight = 85.0
        self._bmi = round(85.0 / ((165.0 / 100) ** 2), 1)  # 비만 BMI
        self._waist_circumference = 95.0  # 복부비만
        self._systolic_bp = 145  # 고혈압
        self._diastolic_bp = 95  # 고혈압
        self._vision_left = 0.6  # 시력 저하
        self._vision_right = 0.7  # 시력 저하
        self._hearing_left_4000hz = 35  # 청력 손실
        self._hearing_right_4000hz = 30  # 청력 손실
        return self

    async def build(self, db_session: AsyncSession) -> VitalSigns:
        """기초검사 결과 생성"""
        if self._health_exam_id is None:
            raise ValueError("health_exam_id is required")

        # BMI 자동 계산
        if self._bmi is None and self._height and self._weight:
            self._bmi = round(self._weight / ((self._height / 100) ** 2), 1)

        vital_signs = VitalSigns(
            health_exam_id=self._health_exam_id,
            height=self._height,
            weight=self._weight,
            bmi=self._bmi,
            waist_circumference=self._waist_circumference,
            systolic_bp=self._systolic_bp,
            diastolic_bp=self._diastolic_bp,
            vision_left=self._vision_left,
            vision_right=self._vision_right,
            hearing_left_1000hz=self._hearing_left_1000hz,
            hearing_right_1000hz=self._hearing_right_1000hz,
            hearing_left_4000hz=self._hearing_left_4000hz,
            hearing_right_4000hz=self._hearing_right_4000hz
        )

        db_session.add(vital_signs)
        await db_session.commit()
        await db_session.refresh(vital_signs)
        return vital_signs


class LabResultBuilder(BaseBuilder[LabResult]):
    """임상검사 결과 빌더"""

    def __init__(self):
        super().__init__()
        self._health_exam_id: Optional[int] = None
        self._test_name: str = "혈색소"
        self._test_value: Optional[str] = "14.5"
        self._test_unit: Optional[str] = "g/dL"
        self._reference_range: Optional[str] = "12-16"
        self._result_status: Optional[str] = "정상"
        self._hemoglobin: Optional[float] = 14.5
        self._hematocrit: Optional[float] = None
        self._ast: Optional[float] = None
        self._alt: Optional[float] = None
        self._gamma_gtp: Optional[float] = None
        self._creatinine: Optional[float] = None
        self._bun: Optional[float] = None
        self._fasting_glucose: Optional[float] = None
        self._hba1c: Optional[float] = None
        self._total_cholesterol: Optional[float] = None
        self._hdl_cholesterol: Optional[float] = None
        self._ldl_cholesterol: Optional[float] = None
        self._triglycerides: Optional[float] = None
        self._chest_xray_result: Optional[str] = None
        self._ecg_result: Optional[str] = None
        self._special_test_results: Optional[str] = None
        self._notes: Optional[str] = None

    def with_health_exam_id(self, exam_id: int) -> "LabResultBuilder":
        """건강진단 ID 설정"""
        self._health_exam_id = exam_id
        return self

    def with_basic_test(self, name: str, value: str, unit: str, reference: str, status: str) -> "LabResultBuilder":
        """기본 검사 설정"""
        self._test_name = name
        self._test_value = value
        self._test_unit = unit
        self._reference_range = reference
        self._result_status = status
        return self

    def with_blood_test(self, hemoglobin: float, hematocrit: float) -> "LabResultBuilder":
        """혈액검사 결과 설정"""
        self._hemoglobin = hemoglobin
        self._hematocrit = hematocrit
        return self

    def with_liver_function(self, ast: float, alt: float, gamma_gtp: float) -> "LabResultBuilder":
        """간기능검사 결과 설정"""
        self._ast = ast
        self._alt = alt
        self._gamma_gtp = gamma_gtp
        return self

    def with_kidney_function(self, creatinine: float, bun: float) -> "LabResultBuilder":
        """신기능검사 결과 설정"""
        self._creatinine = creatinine
        self._bun = bun
        return self

    def with_diabetes_test(self, glucose: float, hba1c: float) -> "LabResultBuilder":
        """당뇨검사 결과 설정"""
        self._fasting_glucose = glucose
        self._hba1c = hba1c
        return self

    def with_lipid_profile(self, total_chol: float, hdl: float, ldl: float, triglycerides: float) -> "LabResultBuilder":
        """지질검사 결과 설정"""
        self._total_cholesterol = total_chol
        self._hdl_cholesterol = hdl
        self._ldl_cholesterol = ldl
        self._triglycerides = triglycerides
        return self

    def with_chest_xray(self, result: str) -> "LabResultBuilder":
        """흉부X선 결과 설정"""
        self._chest_xray_result = result
        return self

    def with_ecg(self, result: str) -> "LabResultBuilder":
        """심전도 결과 설정"""
        self._ecg_result = result
        return self

    def with_special_tests(self, results_json: str) -> "LabResultBuilder":
        """특수검사 결과 설정 (JSON)"""
        self._special_test_results = results_json
        return self

    def with_notes(self, notes: str) -> "LabResultBuilder":
        """비고 설정"""
        self._notes = notes
        return self

    def with_abnormal_liver_function(self) -> "LabResultBuilder":
        """간기능 이상 데이터 설정"""
        self._test_name = "간기능검사"
        self._test_value = "AST 55, ALT 68, GGT 85"
        self._test_unit = "IU/L"
        self._reference_range = "AST<40, ALT<40, GGT<60"
        self._result_status = "이상"
        self._ast = 55.0
        self._alt = 68.0
        self._gamma_gtp = 85.0
        self._notes = "간기능 수치 상승, 추적검사 필요"
        return self

    def with_abnormal_cholesterol(self) -> "LabResultBuilder":
        """콜레스테롤 이상 데이터 설정"""
        self._test_name = "지질검사"
        self._test_value = "총콜레스테롤 250, LDL 180"
        self._test_unit = "mg/dL"
        self._reference_range = "총콜<200, LDL<130"
        self._result_status = "이상"
        self._total_cholesterol = 250.0
        self._hdl_cholesterol = 35.0  # 낮음
        self._ldl_cholesterol = 180.0  # 높음
        self._triglycerides = 220.0  # 높음
        self._notes = "이상지질혈증, 식이요법 및 운동요법 권장"
        return self

    def with_korean_test_data(self) -> "LabResultBuilder":
        """한국어 검사 데이터 설정"""
        self._test_name = "일반혈액검사"
        self._test_value = "정상범위"
        self._test_unit = "다양"
        self._reference_range = "연령별 정상범위"
        self._result_status = "정상"
        self._notes = "모든 혈액검사 수치가 정상범위 내에 있습니다."
        return self

    async def build(self, db_session: AsyncSession) -> LabResult:
        """임상검사 결과 생성"""
        if self._health_exam_id is None:
            raise ValueError("health_exam_id is required")

        lab_result = LabResult(
            health_exam_id=self._health_exam_id,
            test_name=self._test_name,
            test_value=self._test_value,
            test_unit=self._test_unit,
            reference_range=self._reference_range,
            result_status=self._result_status,
            hemoglobin=self._hemoglobin,
            hematocrit=self._hematocrit,
            ast=self._ast,
            alt=self._alt,
            gamma_gtp=self._gamma_gtp,
            creatinine=self._creatinine,
            bun=self._bun,
            fasting_glucose=self._fasting_glucose,
            hba1c=self._hba1c,
            total_cholesterol=self._total_cholesterol,
            hdl_cholesterol=self._hdl_cholesterol,
            ldl_cholesterol=self._ldl_cholesterol,
            triglycerides=self._triglycerides,
            chest_xray_result=self._chest_xray_result,
            ecg_result=self._ecg_result,
            special_test_results=self._special_test_results,
            notes=self._notes
        )

        db_session.add(lab_result)
        await db_session.commit()
        await db_session.refresh(lab_result)
        return lab_result


class HealthExamCompleteBuilder:
    """완전한 건강진단 기록 (검진+기초검사+임상검사) 생성 빌더"""

    def __init__(self):
        self._health_exam_builder = HealthExamBuilder()
        self._vital_signs_builder: Optional[VitalSignsBuilder] = None
        self._lab_result_builders: List[LabResultBuilder] = []

    def with_health_exam_builder(self, builder: HealthExamBuilder) -> "HealthExamCompleteBuilder":
        """건강진단 빌더 설정"""
        self._health_exam_builder = builder
        return self

    def with_vital_signs(self, builder: VitalSignsBuilder) -> "HealthExamCompleteBuilder":
        """기초검사 빌더 설정"""
        self._vital_signs_builder = builder
        return self

    def add_lab_result(self, builder: LabResultBuilder) -> "HealthExamCompleteBuilder":
        """임상검사 빌더 추가"""
        self._lab_result_builders.append(builder)
        return self

    def with_standard_tests(self) -> "HealthExamCompleteBuilder":
        """표준 검사 항목들 추가"""
        # 기초검사
        self._vital_signs_builder = VitalSignsBuilder()

        # 기본 임상검사들
        self._lab_result_builders = [
            LabResultBuilder().with_basic_test("혈색소", "14.2", "g/dL", "12-16", "정상"),
            LabResultBuilder().with_basic_test("총콜레스테롤", "185", "mg/dL", "<200", "정상"),
            LabResultBuilder().with_basic_test("공복혈당", "92", "mg/dL", "70-100", "정상"),
            LabResultBuilder().with_basic_test("AST", "28", "IU/L", "<40", "정상"),
            LabResultBuilder().with_basic_test("ALT", "32", "IU/L", "<40", "정상")
        ]
        return self

    async def build(self, db_session: AsyncSession) -> HealthExam:
        """완전한 건강진단 기록 생성"""
        # 1. 건강진단 기록 생성
        health_exam = await self._health_exam_builder.build(db_session)

        # 2. 기초검사 결과 생성
        if self._vital_signs_builder:
            await self._vital_signs_builder.with_health_exam_id(health_exam.id).build(db_session)

        # 3. 임상검사 결과들 생성
        for lab_builder in self._lab_result_builders:
            await lab_builder.with_health_exam_id(health_exam.id).build(db_session)

        # 관계 로드를 위해 새로 고침
        await db_session.refresh(health_exam)
        return health_exam