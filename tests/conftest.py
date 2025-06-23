import pytest
import asyncio
from datetime import datetime, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.app import create_app
from src.models import (
    Base, Worker, HealthExam, VitalSigns, LabResult,
    WorkEnvironment, HealthEducation, ChemicalSubstance, AccidentReport
)
from src.config.database import get_db


# Test database URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

# Create test session
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Setup test database"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def async_client(setup_database):
    """Create test client"""
    app = create_app()
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def db_session():
    """Create test database session"""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def test_worker(db_session: AsyncSession):
    """Create test worker"""
    worker = Worker(
        employee_id="TEST001",
        name="테스트근로자",
        birth_date=date(1990, 1, 1),
        gender="male",
        employment_type="regular",
        work_type="construction",
        hire_date=date(2024, 1, 1),
        health_status="normal",
        phone="010-1234-5678",
        department="건설팀",
        is_special_exam_target=False
    )
    db_session.add(worker)
    await db_session.commit()
    await db_session.refresh(worker)
    return worker


@pytest.fixture
async def test_health_exam(db_session: AsyncSession, test_worker):
    """Create test health exam"""
    exam = HealthExam(
        worker_id=test_worker.id,
        exam_date=datetime.now(),
        exam_type="GENERAL",
        exam_result="NORMAL",
        exam_agency="테스트의료원",
        doctor_name="김의사",
        overall_opinion="정상",
        work_fitness="업무가능"
    )
    db_session.add(exam)
    await db_session.commit()
    await db_session.refresh(exam)
    return exam


@pytest.fixture
async def test_work_environment(db_session: AsyncSession):
    """Create test work environment"""
    env = WorkEnvironment(
        measurement_date=datetime.now(),
        location="테스트작업장",
        measurement_type="NOISE",
        measurement_agency="테스트기관",
        measured_value=85.0,
        measurement_unit="dB",
        standard_value=90.0,
        standard_unit="dB",
        result="PASS",
        report_number="TEST-001"
    )
    db_session.add(env)
    await db_session.commit()
    await db_session.refresh(env)
    return env


@pytest.fixture
async def test_health_education(db_session: AsyncSession):
    """Create test health education"""
    education = HealthEducation(
        education_date=datetime.now(),
        education_type="REGULAR_QUARTERLY",
        education_title="정기 안전교육",
        education_method="CLASSROOM",
        education_hours=4.0,
        instructor_name="이강사",
        required_by_law="Y"
    )
    db_session.add(education)
    await db_session.commit()
    await db_session.refresh(education)
    return education


@pytest.fixture
async def test_chemical_substance(db_session: AsyncSession):
    """Create test chemical substance"""
    chemical = ChemicalSubstance(
        korean_name="테스트화학물질",
        english_name="Test Chemical",
        cas_number="123-45-6",
        hazard_class="TOXIC",
        current_quantity=50.0,
        quantity_unit="L",
        minimum_quantity=10.0,
        maximum_quantity=100.0,
        storage_location="테스트보관실",
        manufacturer="테스트제조사"
    )
    db_session.add(chemical)
    await db_session.commit()
    await db_session.refresh(chemical)
    return chemical


@pytest.fixture
async def test_accident_report(db_session: AsyncSession, test_worker):
    """Create test accident report"""
    report = AccidentReport(
        accident_datetime=datetime.now(),
        report_datetime=datetime.now(),
        accident_location="테스트현장",
        worker_id=test_worker.id,
        accident_type="FALL",
        injury_type="BRUISE",
        severity="MINOR",
        accident_description="테스트 사고",
        investigation_status="REPORTED"
    )
    db_session.add(report)
    await db_session.commit()
    await db_session.refresh(report)
    return report


# 추가 헬퍼 함수들
@pytest.fixture
def sample_worker_data():
    """Sample worker data for testing"""
    return {
        "employee_id": "EMP001",
        "name": "홍길동",
        "birth_date": "1985-03-15",
        "gender": "male",
        "employment_type": "regular",
        "work_type": "construction",
        "hire_date": "2024-01-01",
        "health_status": "normal",
        "phone": "010-1234-5678",
        "department": "건설팀"
    }


@pytest.fixture
def sample_health_exam_data(test_worker):
    """Sample health exam data for testing"""
    return {
        "worker_id": test_worker.id,
        "exam_date": datetime.now().isoformat(),
        "exam_type": "GENERAL",
        "exam_agency": "서울의료원",
        "doctor_name": "김의사"
    }