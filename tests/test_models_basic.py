"""
기본 모델 테스트 - 커버리지 향상을 위한 핵심 테스트
Basic Model Tests for Coverage Improvement
"""

import pytest
import pytest_asyncio
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.worker import Worker, Gender, BloodType, HealthStatus
from src.models.health_exam import HealthExam, VitalSigns, LabResult, HealthExamType, HealthExamResult
from src.models.work_environment import WorkEnvironment, MeasurementType, MeasurementResult
from src.models.accident_report import AccidentReport, AccidentType, AccidentSeverity
from src.models.chemical_substance import ChemicalSubstance, HazardLevel
from src.models.health_education import HealthEducation, EducationType


class TestWorkerModel:
    """근로자 모델 기본 테스트"""
    
    @pytest_asyncio.fixture
    async def worker_data(self):
        return {
            "name": "테스트근로자",
            "employee_number": "EMP001",
            "department": "건설부",
            "position": "기술자",
            "phone": "010-1234-5678",
            "email": "test@example.com",
            "hire_date": date.today(),
            "birth_date": date(1985, 1, 1),
            "gender": Gender.MALE,
            "blood_type": BloodType.A,
            "health_status": HealthStatus.NORMAL
        }
    
    async def test_worker_creation(self, async_session: AsyncSession, worker_data):
        """근로자 생성 테스트"""
        worker = Worker(**worker_data)
        async_session.add(worker)
        await async_session.commit()
        await async_session.refresh(worker)
        
        assert worker.id is not None
        assert worker.name == "테스트근로자"
        assert worker.employee_number == "EMP001"
        assert worker.gender == Gender.MALE
    
    async def test_worker_str_representation(self, worker_data):
        """근로자 문자열 표현 테스트"""
        worker = Worker(**worker_data)
        assert str(worker) == "테스트근로자 (EMP001)"
    
    async def test_worker_properties(self, worker_data):
        """근로자 속성 테스트"""
        worker = Worker(**worker_data)
        assert worker.age > 0
        assert worker.is_active is True


class TestHealthExamModel:
    """건강진단 모델 기본 테스트"""
    
    @pytest_asyncio.fixture
    async def health_exam_data(self, test_worker):
        return {
            "worker_id": test_worker.id,
            "exam_date": date.today(),
            "exam_type": HealthExamType.GENERAL,
            "exam_result": HealthExamResult.NORMAL,
            "medical_institution": "테스트병원",
            "doctor_name": "김의사",
            "exam_details": "정상 소견"
        }
    
    async def test_health_exam_creation(self, async_session: AsyncSession, health_exam_data):
        """건강진단 생성 테스트"""
        exam = HealthExam(**health_exam_data)
        async_session.add(exam)
        await async_session.commit()
        await async_session.refresh(exam)
        
        assert exam.id is not None
        assert exam.exam_type == HealthExamType.GENERAL
        assert exam.exam_result == HealthExamResult.NORMAL
    
    async def test_vital_signs_creation(self, async_session: AsyncSession, health_exam_data):
        """생체신호 생성 테스트"""
        exam = HealthExam(**health_exam_data)
        async_session.add(exam)
        await async_session.flush()
        
        vital_signs = VitalSigns(
            exam_id=exam.id,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            heart_rate=72,
            temperature=36.5,
            weight=70.0,
            height=175.0
        )
        async_session.add(vital_signs)
        await async_session.commit()
        
        assert vital_signs.id is not None
        assert vital_signs.blood_pressure_systolic == 120
        assert vital_signs.bmi == pytest.approx(22.86, rel=1e-2)


class TestWorkEnvironmentModel:
    """작업환경 모델 기본 테스트"""
    
    async def test_work_environment_creation(self, async_session: AsyncSession):
        """작업환경측정 생성 테스트"""
        work_env = WorkEnvironment(
            location="1층 작업장",
            measurement_type=MeasurementType.DUST,
            measurement_date=date.today(),
            measured_value=0.5,
            standard_value=1.0,
            result=MeasurementResult.PASS,
            measurement_unit="mg/m³",
            weather_conditions="맑음",
            temperature=25.0,
            humidity=60.0
        )
        
        async_session.add(work_env)
        await async_session.commit()
        await async_session.refresh(work_env)
        
        assert work_env.id is not None
        assert work_env.measurement_type == MeasurementType.DUST
        assert work_env.result == MeasurementResult.PASS
        assert work_env.is_compliant is True


class TestAccidentReportModel:
    """사고신고 모델 기본 테스트"""
    
    async def test_accident_report_creation(self, async_session: AsyncSession, test_worker):
        """사고신고 생성 테스트"""
        accident = AccidentReport(
            worker_id=test_worker.id,
            accident_datetime=datetime.now(),
            accident_type=AccidentType.FALL,
            severity=AccidentSeverity.MINOR,
            location="2층 작업장",
            description="사다리에서 낙상",
            immediate_cause="안전장비 미착용",
            injury_details="무릎 타박상",
            first_aid_given=True,
            hospital_visit_required=False,
            work_days_lost=1,
            medical_cost=50000,
            compensation_cost=0,
            other_cost=0
        )
        
        async_session.add(accident)
        await async_session.commit()
        await async_session.refresh(accident)
        
        assert accident.id is not None
        assert accident.accident_type == AccidentType.FALL
        assert accident.severity == AccidentSeverity.MINOR
        assert accident.total_cost == 50000


class TestChemicalSubstanceModel:
    """화학물질 모델 기본 테스트"""
    
    async def test_chemical_substance_creation(self, async_session: AsyncSession):
        """화학물질 생성 테스트"""
        chemical = ChemicalSubstance(
            name="톨루엔",
            cas_number="108-88-3",
            hazard_level=HazardLevel.HIGH,
            usage_location="도장작업장",
            usage_purpose="희석제",
            monthly_usage_amount=100.0,
            storage_amount=500.0,
            exposure_limit=200.0,
            exposure_limit_unit="ppm",
            msds_file_path="/uploads/msds/toluene.pdf",
            supplier="화학공업(주)",
            emergency_contact="119"
        )
        
        async_session.add(chemical)
        await async_session.commit()
        await async_session.refresh(chemical)
        
        assert chemical.id is not None
        assert chemical.name == "톨루엔"
        assert chemical.hazard_level == HazardLevel.HIGH
        assert chemical.is_hazardous is True


class TestHealthEducationModel:
    """보건교육 모델 기본 테스트"""
    
    async def test_health_education_creation(self, async_session: AsyncSession):
        """보건교육 생성 테스트"""
        education = HealthEducation(
            title="산업안전보건 기초교육",
            education_type=EducationType.MANDATORY,
            target_department="전체",
            education_date=date.today(),
            duration_hours=4,
            instructor="안전관리자",
            content="산업안전보건법 기초",
            location="교육장",
            max_participants=50,
            current_participants=25
        )
        
        async_session.add(education)
        await async_session.commit()
        await async_session.refresh(education)
        
        assert education.id is not None
        assert education.education_type == EducationType.MANDATORY
        assert education.is_mandatory is True
        assert education.completion_rate == 50.0


# 모듈 단위 검증 함수
if __name__ == "__main__":
    import asyncio
    import sys
    from src.config.database import get_test_db_url, create_test_tables
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    
    async def validate_models():
        """모델 검증 실행"""
        engine = create_async_engine(get_test_db_url())
        async_session_factory = sessionmaker(engine, class_=AsyncSession)
        
        try:
            # 테스트 테이블 생성
            await create_test_tables(engine)
            
            async with async_session_factory() as session:
                # Worker 테스트
                worker = Worker(
                    name="검증용근로자",
                    employee_number="VAL001",
                    department="검증부서",
                    position="검증자",
                    gender=Gender.MALE,
                    blood_type=BloodType.A
                )
                session.add(worker)
                await session.commit()
                
                # HealthExam 테스트
                exam = HealthExam(
                    worker_id=worker.id,
                    exam_date=date.today(),
                    exam_type=HealthExamType.GENERAL,
                    exam_result=HealthExamResult.NORMAL,
                    medical_institution="검증병원"
                )
                session.add(exam)
                await session.commit()
                
                print("✅ 모든 모델 검증 통과")
                print(f"   - Worker ID: {worker.id}")
                print(f"   - HealthExam ID: {exam.id}")
                return True
                
        except Exception as e:
            print(f"❌ 모델 검증 실패: {e}")
            return False
        finally:
            await engine.dispose()
    
    # 검증 실행
    success = asyncio.run(validate_models())
    sys.exit(0 if success else 1)