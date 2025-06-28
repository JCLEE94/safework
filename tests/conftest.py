import pytest
import pytest_asyncio
from datetime import datetime, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from src.app import create_app
from src.models import (
    Base, Worker, HealthExam, VitalSigns, LabResult,
    WorkEnvironment, HealthEducation, ChemicalSubstance, AccidentReport
)
from src.config.database import get_db


# Test database URL - using NullPool to avoid connection issues
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def engine():
    """Create test engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,  # Important for SQLite
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(engine):
    """Create test database session"""
    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(engine):
    """Create test client"""
    app = create_app()
    
    # Override the database dependency
    async def override_get_db():
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        async with async_session_maker() as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture(scope="function")  
async def test_worker(async_session):
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
    async_session.add(worker)
    await async_session.commit()
    await async_session.refresh(worker)
    return worker


@pytest_asyncio.fixture(scope="function")
async def test_health_exam(async_session, test_worker):
    """Create test health exam"""
    exam = HealthExam(
        worker_id=test_worker.id,
        exam_date=datetime.now(),
        exam_type="GENERAL",
        exam_result="NORMAL",
        exam_agency="테스트의료원",
        doctor_name="김의사",
        blood_pressure_sys=120,
        blood_pressure_dia=80,
        height=170.0,
        weight=70.0,
        bmi=24.2
    )
    async_session.add(exam)
    await async_session.commit()
    await async_session.refresh(exam)
    return exam


@pytest_asyncio.fixture(scope="function")
async def test_work_environment(async_session):
    """Create test work environment measurement"""
    env = WorkEnvironment(
        measurement_date=datetime.now(),
        location="A동 3층",
        measurement_type="NOISE",
        measurement_value=75.5,
        measurement_unit="dB",
        standard_value=90.0,
        measurement_agency="테스트측정업체",
        inspector_name="박측정원",
        exceeds_standard=False
    )
    async_session.add(env)
    await async_session.commit()
    await async_session.refresh(env)
    return env


@pytest_asyncio.fixture(scope="function")
async def test_health_education(async_session):
    """Create test health education"""
    education = HealthEducation(
        education_date=datetime.now(),
        education_type="REGULAR",
        topic="산업안전보건교육",
        instructor="안전강사",
        duration_hours=3,
        location="교육장",
        target_audience="전체 근로자"
    )
    async_session.add(education)
    await async_session.commit()
    await async_session.refresh(education)
    return education


@pytest_asyncio.fixture(scope="function")
async def test_chemical_substance(async_session):
    """Create test chemical substance"""
    chemical = ChemicalSubstance(
        korean_name="테스트화학물질",
        english_name="Test Chemical",
        cas_number="123-45-6",
        hazard_class="TOXIC",
        hazard_statement="유해함",
        signal_word="경고",
        physical_state="액체",
        storage_location="보관소 A",
        current_quantity=50.0,
        quantity_unit="L"
    )
    async_session.add(chemical)
    await async_session.commit()
    await async_session.refresh(chemical)
    return chemical


@pytest_asyncio.fixture(scope="function")
async def test_accident_report(async_session, test_worker):
    """Create test accident report"""
    report = AccidentReport(
        accident_datetime=datetime.now(),
        report_datetime=datetime.now(),
        accident_location="작업장",
        worker_id=test_worker.id,
        accident_type="FALL",
        injury_type="BRUISE",
        severity="MINOR",
        accident_description="사고 설명"
    )
    async_session.add(report)
    await async_session.commit()
    await async_session.refresh(report)
    return report