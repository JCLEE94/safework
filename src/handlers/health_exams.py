from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models import HealthExam, LabResult, VitalSigns, Worker
from src.schemas.health_exam import (HealthExamCreate, HealthExamListResponse,
                                     HealthExamResponse, HealthExamUpdate,
                                     LabResultCreate, VitalSignsCreate)
from src.utils.auth_deps import get_current_user_id

router = APIRouter(prefix="/api/v1/health-exams", tags=["health-exams"])


@router.post("/", response_model=HealthExamResponse)
async def create_health_exam(
    exam_data: HealthExamCreate, db: AsyncSession = Depends(get_db)
):
    """건강진단 기록 생성"""
    # Check if worker exists
    worker = await db.get(Worker, exam_data.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")

    # Create health exam
    exam = HealthExam(**exam_data.model_dump(exclude={"vital_signs", "lab_results"}))
    db.add(exam)
    await db.flush()

    # Create vital signs if provided
    if exam_data.vital_signs:
        vital_signs = VitalSigns(exam_id=exam.id, **exam_data.vital_signs.model_dump())
        db.add(vital_signs)

    # Create lab results if provided
    if exam_data.lab_results:
        for lab_result_data in exam_data.lab_results:
            lab_result = LabResult(exam_id=exam.id, **lab_result_data.model_dump())
            db.add(lab_result)

    await db.commit()
    await db.refresh(exam)

    # Load relationships
    result = await db.execute(
        select(HealthExam)
        .options(selectinload(HealthExam.vital_signs))
        .options(selectinload(HealthExam.lab_results))
        .where(HealthExam.id == exam.id)
    )
    return result.scalar_one()


@router.get("/", response_model=HealthExamListResponse)
async def list_health_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    worker_id: Optional[int] = None,
    exam_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
):
    """건강진단 기록 목록 조회"""
    query = select(HealthExam).options(
        selectinload(HealthExam.vital_signs), selectinload(HealthExam.lab_results)
    )

    # Apply filters
    conditions = []
    if worker_id:
        conditions.append(HealthExam.worker_id == worker_id)
    if exam_type:
        conditions.append(HealthExam.exam_type == exam_type)
    if start_date:
        conditions.append(HealthExam.exam_date >= start_date)
    if end_date:
        conditions.append(HealthExam.exam_date <= end_date)

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count()).select_from(HealthExam)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(HealthExam.exam_date.desc())

    result = await db.execute(query)
    items = result.scalars().all()

    return HealthExamListResponse(
        items=items, total=total, page=page, pages=(total + size - 1) // size, size=size
    )


@router.get("/due-soon")
async def get_exams_due_soon(
    days: int = Query(30, description="일수 이내"), db: AsyncSession = Depends(get_db)
):
    """건강진단 예정자 목록 조회"""
    # Get workers with their latest exam
    subquery = (
        select(
            HealthExam.worker_id,
            func.max(HealthExam.exam_date).label("latest_exam_date"),
        )
        .group_by(HealthExam.worker_id)
        .subquery()
    )

    # Calculate next exam date (1 year for general, 6 months for special)
    query = (
        select(Worker, subquery.c.latest_exam_date)
        .join(subquery, Worker.id == subquery.c.worker_id)
        .where(
            or_(
                subquery.c.latest_exam_date + timedelta(days=365)
                <= datetime.utcnow() + timedelta(days=days),
                subquery.c.latest_exam_date + timedelta(days=180)
                <= datetime.utcnow() + timedelta(days=days),
            )
        )
    )

    result = await db.execute(query)
    due_workers = []

    for worker, latest_exam_date in result:
        # Check if special exam is needed (simplified logic)
        next_exam_date = latest_exam_date + timedelta(days=365)
        days_until_due = (next_exam_date - datetime.utcnow()).days

        due_workers.append(
            {
                "worker_id": worker.id,
                "worker_name": worker.name,
                "employee_number": worker.employee_number,
                "latest_exam_date": latest_exam_date,
                "next_exam_date": next_exam_date,
                "days_until_due": days_until_due,
            }
        )

    return {"total": len(due_workers), "workers": due_workers}


@router.get("/statistics")
async def get_exam_statistics(db: AsyncSession = Depends(get_db)):
    """건강진단 통계 조회"""
    # Total exams by type
    type_stats = await db.execute(
        select(HealthExam.exam_type, func.count(HealthExam.id).label("count")).group_by(
            HealthExam.exam_type
        )
    )

    # Results distribution
    result_stats = await db.execute(
        select(
            HealthExam.exam_result, func.count(HealthExam.id).label("count")
        ).group_by(HealthExam.exam_result)
    )

    # Exams this year
    current_year = datetime.utcnow().year
    yearly_count = await db.scalar(
        select(func.count(HealthExam.id)).where(
            func.extract("year", HealthExam.exam_date) == current_year
        )
    )

    # Workers with followup required
    followup_count = await db.scalar(
        select(func.count(HealthExam.id)).where(HealthExam.followup_required == "Y")
    )

    return {
        "by_type": {row[0].value: row[1] for row in type_stats},
        "by_result": {row[0].value: row[1] for row in result_stats},
        "total_this_year": yearly_count,
        "followup_required": followup_count,
    }


@router.get("/worker/{worker_id}/latest", response_model=HealthExamResponse)
async def get_latest_exam_for_worker(
    worker_id: int, db: AsyncSession = Depends(get_db)
):
    """근로자의 최신 건강진단 기록 조회"""
    result = await db.execute(
        select(HealthExam)
        .options(selectinload(HealthExam.vital_signs))
        .options(selectinload(HealthExam.lab_results))
        .where(HealthExam.worker_id == worker_id)
        .order_by(HealthExam.exam_date.desc())
        .limit(1)
    )
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="건강진단 기록이 없습니다")

    return exam


@router.get("/{exam_id}", response_model=HealthExamResponse)
async def get_health_exam(exam_id: int, db: AsyncSession = Depends(get_db)):
    """건강진단 기록 조회"""
    result = await db.execute(
        select(HealthExam)
        .options(selectinload(HealthExam.vital_signs))
        .options(selectinload(HealthExam.lab_results))
        .where(HealthExam.id == exam_id)
    )
    exam = result.scalar_one_or_none()

    if not exam:
        raise HTTPException(status_code=404, detail="건강진단 기록을 찾을 수 없습니다")

    return exam


@router.put("/{exam_id}", response_model=HealthExamResponse)
async def update_health_exam(
    exam_id: int, exam_update: HealthExamUpdate, db: AsyncSession = Depends(get_db)
):
    """건강진단 기록 수정"""
    exam = await db.get(HealthExam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="건강진단 기록을 찾을 수 없습니다")

    # Update fields
    update_data = exam_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(exam, field, value)

    exam.updated_at = datetime.utcnow()
    await db.commit()

    # Load relationships
    result = await db.execute(
        select(HealthExam)
        .options(selectinload(HealthExam.vital_signs))
        .options(selectinload(HealthExam.lab_results))
        .where(HealthExam.id == exam_id)
    )
    return result.scalar_one()


@router.delete("/{exam_id}")
async def delete_health_exam(exam_id: int, db: AsyncSession = Depends(get_db)):
    """건강진단 기록 삭제"""
    exam = await db.get(HealthExam, exam_id)
    if not exam:
        raise HTTPException(status_code=404, detail="건강진단 기록을 찾을 수 없습니다")

    await db.delete(exam)
    await db.commit()

    return {"message": "건강진단 기록이 삭제되었습니다"}


# =============================================================================
# INTEGRATION TESTS (Rust-style inline tests)
# =============================================================================

if __name__ == "__main__":
    import asyncio
    import pytest
    import pytest_asyncio
    from httpx import AsyncClient
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from src.app import app
    from src.config.database import Base, get_db
    from src.models.worker import Worker, EmploymentType, WorkType, HealthStatus
    from src.models.health_exam import HealthExam, ExamType, ExamResult
    from src.models.vital_signs import VitalSigns
    from src.models.lab_result import LabResult

    # Test database setup
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_health_exams.db"
    test_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
    TestingSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )

    async def override_get_db():
        async with TestingSessionLocal() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db

    @pytest_asyncio.fixture
    async def async_client():
        """Test client fixture"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest_asyncio.fixture
    async def test_db():
        """Test database fixture"""
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        async with TestingSessionLocal() as session:
            yield session
        
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    @pytest_asyncio.fixture
    async def test_worker(test_db: AsyncSession):
        """Test worker fixture"""
        worker = Worker(
            name="테스트근로자",
            employee_id="T001",
            employment_type=EmploymentType.REGULAR,
            work_type=WorkType.CONSTRUCTION,
            health_status=HealthStatus.NORMAL,
            department="건설팀",
            company_name="테스트회사",
            work_category="건설공사",
            address="서울시 강남구"
        )
        test_db.add(worker)
        await test_db.commit()
        await test_db.refresh(worker)
        return worker

    async def test_health_exam_creation_integration(async_client: AsyncClient, test_worker: Worker):
        """
        통합 테스트: 건강진단 기록 생성 전체 플로우
        - API 요청 → 검증 → DB 저장 → 관련 데이터 저장 → 응답
        """
        # Given: 건강진단 생성 데이터
        exam_data = {
            "worker_id": test_worker.id,
            "exam_date": "2024-01-15",
            "exam_type": "general",
            "exam_result": "normal",
            "medical_institution": "서울의료원",
            "doctor_name": "김의사",
            "vital_signs": {
                "height": 175.5,
                "weight": 70.2,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "heart_rate": 72,
                "body_temperature": 36.5
            },
            "lab_results": [
                {
                    "test_name": "혈당검사",
                    "test_value": "95",
                    "reference_range": "70-100",
                    "unit": "mg/dL",
                    "result_status": "normal"
                }
            ]
        }

        # When: 건강진단 기록 생성 API 호출
        response = await async_client.post("/api/v1/health-exams/", json=exam_data)

        # Then: 성공 응답 확인
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["worker_id"] == test_worker.id
        assert response_data["exam_type"] == "general"
        assert response_data["exam_result"] == "normal"
        assert response_data["doctor_name"] == "김의사"

        # Then: 바이탈 사인 저장 확인
        assert response_data["vital_signs"] is not None
        vital_signs = response_data["vital_signs"]
        assert vital_signs["height"] == 175.5
        assert vital_signs["blood_pressure_systolic"] == 120

        # Then: 검사 결과 저장 확인
        assert len(response_data["lab_results"]) == 1
        lab_result = response_data["lab_results"][0]
        assert lab_result["test_name"] == "혈당검사"
        assert lab_result["result_status"] == "normal"

    async def test_health_exam_list_with_filters_integration(async_client: AsyncClient, test_worker: Worker, test_db: AsyncSession):
        """
        통합 테스트: 건강진단 목록 조회 및 필터링
        """
        # Given: 테스트 건강진단 데이터 생성
        from datetime import datetime, date
        exams = [
            HealthExam(
                worker_id=test_worker.id,
                exam_date=date(2024, 1, 15),
                exam_type=ExamType.GENERAL,
                exam_result=ExamResult.NORMAL,
                medical_institution="서울의료원",
                doctor_name="김의사"
            ),
            HealthExam(
                worker_id=test_worker.id,
                exam_date=date(2024, 6, 15),
                exam_type=ExamType.SPECIAL,
                exam_result=ExamResult.ABNORMAL,
                medical_institution="부산의료원",
                doctor_name="박의사"
            )
        ]
        
        for exam in exams:
            test_db.add(exam)
        await test_db.commit()

        # When: 전체 목록 조회
        response = await async_client.get("/api/v1/health-exams/?page=1&size=10")
        
        # Then: 전체 데이터 확인
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

        # When: 검진 유형별 필터링
        response = await async_client.get("/api/v1/health-exams/?exam_type=general")
        
        # Then: 일반건강진단만 조회
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["exam_type"] == "general"

        # When: 근로자별 필터링
        response = await async_client.get(f"/api/v1/health-exams/?worker_id={test_worker.id}")
        
        # Then: 해당 근로자의 모든 검진 기록 조회
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["worker_id"] == test_worker.id

    async def test_health_exam_due_soon_integration(async_client: AsyncClient, test_worker: Worker, test_db: AsyncSession):
        """
        통합 테스트: 건강진단 예정자 조회 기능
        """
        # Given: 1년 전 건강진단 기록 (곧 만료 예정)
        from datetime import datetime, date, timedelta
        old_exam_date = date.today() - timedelta(days=350)  # 350일 전
        
        old_exam = HealthExam(
            worker_id=test_worker.id,
            exam_date=old_exam_date,
            exam_type=ExamType.GENERAL,
            exam_result=ExamResult.NORMAL,
            medical_institution="서울의료원",
            doctor_name="김의사"
        )
        test_db.add(old_exam)
        await test_db.commit()

        # When: 30일 이내 건강진단 예정자 조회
        response = await async_client.get("/api/v1/health-exams/due-soon?days=30")

        # Then: 예정자 목록에 포함 확인
        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        
        # 해당 근로자가 예정자 목록에 있는지 확인
        worker_found = False
        for worker_info in data["workers"]:
            if worker_info["worker_id"] == test_worker.id:
                worker_found = True
                assert worker_info["worker_name"] == test_worker.name
                assert worker_info["days_until_due"] <= 30
                break
        assert worker_found, "근로자가 건강진단 예정자 목록에 없습니다"

    async def test_health_exam_statistics_integration(async_client: AsyncClient, test_worker: Worker, test_db: AsyncSession):
        """
        통합 테스트: 건강진단 통계 조회
        """
        # Given: 다양한 건강진단 기록 생성
        from datetime import datetime, date
        exams = [
            HealthExam(
                worker_id=test_worker.id,
                exam_date=date(2024, 1, 15),
                exam_type=ExamType.GENERAL,
                exam_result=ExamResult.NORMAL,
                followup_required="N"
            ),
            HealthExam(
                worker_id=test_worker.id,
                exam_date=date(2024, 6, 15),
                exam_type=ExamType.SPECIAL,
                exam_result=ExamResult.ABNORMAL,
                followup_required="Y"
            )
        ]
        
        for exam in exams:
            test_db.add(exam)
        await test_db.commit()

        # When: 통계 조회
        response = await async_client.get("/api/v1/health-exams/statistics")

        # Then: 통계 데이터 확인
        assert response.status_code == 200
        stats = response.json()
        
        # 검진 유형별 통계
        assert "by_type" in stats
        assert stats["by_type"]["general"] >= 1
        assert stats["by_type"]["special"] >= 1
        
        # 결과별 통계
        assert "by_result" in stats
        assert stats["by_result"]["normal"] >= 1
        assert stats["by_result"]["abnormal"] >= 1
        
        # 올해 검진 수
        assert "total_this_year" in stats
        assert stats["total_this_year"] >= 2
        
        # 추가 관리 필요자 수
        assert "followup_required" in stats
        assert stats["followup_required"] >= 1

    async def test_health_exam_latest_for_worker_integration(async_client: AsyncClient, test_worker: Worker, test_db: AsyncSession):
        """
        통합 테스트: 근로자별 최신 건강진단 기록 조회
        """
        # Given: 여러 건강진단 기록 (날짜 순으로)
        from datetime import date
        exams = [
            HealthExam(
                worker_id=test_worker.id,
                exam_date=date(2023, 1, 15),
                exam_type=ExamType.GENERAL,
                exam_result=ExamResult.NORMAL,
                doctor_name="구의사"
            ),
            HealthExam(
                worker_id=test_worker.id,
                exam_date=date(2024, 6, 15),  # 가장 최신
                exam_type=ExamType.SPECIAL,
                exam_result=ExamResult.CAUTION,
                doctor_name="신의사"
            )
        ]
        
        for exam in exams:
            test_db.add(exam)
        await test_db.commit()

        # When: 최신 건강진단 기록 조회
        response = await async_client.get(f"/api/v1/health-exams/worker/{test_worker.id}/latest")

        # Then: 가장 최신 기록 반환 확인
        assert response.status_code == 200
        data = response.json()
        assert data["worker_id"] == test_worker.id
        assert data["exam_date"] == "2024-06-15"  # 가장 최신 날짜
        assert data["doctor_name"] == "신의사"
        assert data["exam_result"] == "caution"

    # Run tests
    async def run_integration_tests():
        """건강진단 통합 테스트 실행"""
        print("🧪 건강진단 관리 통합 테스트 시작...")
        
        try:
            # Setup test database
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            async with TestingSessionLocal() as test_db:
                async with AsyncClient(app=app, base_url="http://test") as client:
                    print("✅ 테스트 환경 설정 완료")
                    
                    # Create test worker
                    test_worker = Worker(
                        name="테스트근로자",
                        employee_id="T001",
                        employment_type=EmploymentType.REGULAR,
                        work_type=WorkType.CONSTRUCTION,
                        health_status=HealthStatus.NORMAL,
                        department="건설팀",
                        company_name="테스트회사",
                        work_category="건설공사",
                        address="서울시 강남구"
                    )
                    test_db.add(test_worker)
                    await test_db.commit()
                    await test_db.refresh(test_worker)
                    
                    # Run individual tests
                    await test_health_exam_creation_integration(client, test_worker)
                    print("✅ 건강진단 기록 생성 통합 테스트 통과")
                    
                    await test_db.rollback()  # Reset for next test
                    
                    await test_health_exam_list_with_filters_integration(client, test_worker, test_db)
                    print("✅ 건강진단 목록 조회 및 필터링 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_health_exam_due_soon_integration(client, test_worker, test_db)
                    print("✅ 건강진단 예정자 조회 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_health_exam_statistics_integration(client, test_worker, test_db)
                    print("✅ 건강진단 통계 조회 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_health_exam_latest_for_worker_integration(client, test_worker, test_db)
                    print("✅ 근로자별 최신 건강진단 기록 조회 테스트 통과")
                    
            # Cleanup
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                
            print("🎉 모든 건강진단 관리 통합 테스트 통과!")
            
        except Exception as e:
            print(f"❌ 건강진단 통합 테스트 실패: {e}")
            raise

    # Execute tests when run directly
    if __name__ == "__main__":
        asyncio.run(run_integration_tests())
