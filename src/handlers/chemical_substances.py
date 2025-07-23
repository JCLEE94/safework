import os
import shutil
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import Integer, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.config.settings import get_settings
from src.models import ChemicalSubstance, ChemicalUsageRecord, Worker
from src.schemas.chemical_substance import (ChemicalStatistics,
                                            ChemicalSubstanceCreate,
                                            ChemicalSubstanceListResponse,
                                            ChemicalSubstanceResponse,
                                            ChemicalSubstanceUpdate,
                                            ChemicalUsageCreate,
                                            ChemicalWithUsageResponse)
from src.utils.auth_deps import get_current_user_id

router = APIRouter(prefix="/api/v1/chemical-substances", tags=["chemical-substances"])


@router.post("/", response_model=ChemicalSubstanceResponse)
async def create_chemical_substance(
    chemical_data: ChemicalSubstanceCreate, db: AsyncSession = Depends(get_db)
):
    """화학물질 등록"""
    # Check for duplicate CAS number
    if chemical_data.cas_number:
        existing = await db.scalar(
            select(ChemicalSubstance).where(
                ChemicalSubstance.cas_number == chemical_data.cas_number
            )
        )
        if existing:
            raise HTTPException(status_code=400, detail="이미 등록된 CAS 번호입니다")

    chemical = ChemicalSubstance(**chemical_data.model_dump())
    chemical.created_by = current_user_id  # TODO: Should come from auth
    db.add(chemical)
    await db.commit()
    await db.refresh(chemical)

    return chemical


@router.get("/", response_model=ChemicalSubstanceListResponse)
async def list_chemical_substances(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    hazard_class: Optional[str] = None,
    status: Optional[str] = None,
    special_management: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """화학물질 목록 조회"""
    query = select(ChemicalSubstance)

    # Apply filters
    conditions = []
    if search:
        conditions.append(
            or_(
                ChemicalSubstance.korean_name.contains(search),
                ChemicalSubstance.english_name.contains(search),
                ChemicalSubstance.cas_number.contains(search),
            )
        )
    if hazard_class:
        conditions.append(ChemicalSubstance.hazard_class == hazard_class)
    if status:
        conditions.append(ChemicalSubstance.status == status)
    if special_management is not None:
        conditions.append(
            ChemicalSubstance.special_management_material
            == ("Y" if special_management else "N")
        )

    if conditions:
        query = query.where(and_(*conditions))

    # Get total count
    count_query = select(func.count()).select_from(ChemicalSubstance)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)

    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(ChemicalSubstance.korean_name)

    result = await db.execute(query)
    items = result.scalars().all()

    return ChemicalSubstanceListResponse(
        items=items, total=total, page=page, pages=(total + size - 1) // size, size=size
    )


@router.get("/statistics", response_model=ChemicalStatistics)
async def get_chemical_statistics(db: AsyncSession = Depends(get_db)):
    """화학물질 통계 조회"""
    # Total chemicals
    total = await db.scalar(select(func.count(ChemicalSubstance.id)))

    # By status
    status_stats = await db.execute(
        select(
            ChemicalSubstance.status, func.count(ChemicalSubstance.id).label("count")
        ).group_by(ChemicalSubstance.status)
    )
    status_counts = {row[0].value: row[1] for row in status_stats}

    # Special chemicals
    special_counts = await db.execute(
        select(
            func.sum(
                func.cast(ChemicalSubstance.special_management_material == "Y", Integer)
            ).label("special"),
            func.sum(func.cast(ChemicalSubstance.carcinogen == "Y", Integer)).label(
                "carcinogen"
            ),
        )
    )
    special_row = special_counts.one()

    # By hazard class
    hazard_stats = await db.execute(
        select(
            ChemicalSubstance.hazard_class,
            func.count(ChemicalSubstance.id).label("count"),
        ).group_by(ChemicalSubstance.hazard_class)
    )

    # Low stock items
    low_stock_query = await db.execute(
        select(ChemicalSubstance)
        .where(
            and_(
                ChemicalSubstance.current_quantity < ChemicalSubstance.minimum_quantity,
                ChemicalSubstance.status == "IN_USE",
            )
        )
        .limit(get_settings().max_recent_items)
    )
    low_stock_items = []
    for item in low_stock_query.scalars():
        low_stock_items.append(
            {
                "id": item.id,
                "korean_name": item.korean_name,
                "current_quantity": item.current_quantity,
                "minimum_quantity": item.minimum_quantity,
                "unit": item.quantity_unit,
            }
        )

    # Expired MSDS
    settings = get_settings()
    one_year_ago = datetime.utcnow().date() - timedelta(
        days=settings.health_exam_interval_days
    )
    expired_msds_query = await db.execute(
        select(ChemicalSubstance)
        .where(
            or_(
                ChemicalSubstance.msds_revision_date < one_year_ago,
                ChemicalSubstance.msds_file_path.is_(None),
            )
        )
        .limit(settings.max_recent_items)
    )
    expired_msds = []
    for item in expired_msds_query.scalars():
        expired_msds.append(
            {
                "id": item.id,
                "korean_name": item.korean_name,
                "msds_revision_date": (
                    item.msds_revision_date.isoformat()
                    if item.msds_revision_date
                    else None
                ),
                "has_msds": bool(item.msds_file_path),
            }
        )

    return ChemicalStatistics(
        total_chemicals=total,
        in_use_count=status_counts.get("사용중", 0),
        expired_count=status_counts.get("유효기간만료", 0),
        special_management_count=special_row.special or 0,
        carcinogen_count=special_row.carcinogen or 0,
        low_stock_items=low_stock_items,
        expired_msds=expired_msds,
        by_hazard_class={row[0].value: row[1] for row in hazard_stats},
    )


@router.get("/inventory-check")
async def check_inventory_status(db: AsyncSession = Depends(get_db)):
    """재고 점검 현황"""
    # Items below minimum stock
    below_minimum = await db.execute(
        select(ChemicalSubstance).where(
            and_(
                ChemicalSubstance.current_quantity < ChemicalSubstance.minimum_quantity,
                ChemicalSubstance.status == "IN_USE",
            )
        )
    )

    # Items above maximum stock
    above_maximum = await db.execute(
        select(ChemicalSubstance).where(
            and_(
                ChemicalSubstance.current_quantity > ChemicalSubstance.maximum_quantity,
                ChemicalSubstance.status == "IN_USE",
            )
        )
    )

    # Expired items
    expired = await db.execute(
        select(ChemicalSubstance).where(ChemicalSubstance.status == "EXPIRED")
    )

    return {
        "below_minimum": [
            {
                "id": item.id,
                "name": item.korean_name,
                "current": item.current_quantity,
                "minimum": item.minimum_quantity,
                "shortage": item.minimum_quantity - item.current_quantity,
            }
            for item in below_minimum.scalars()
        ],
        "above_maximum": [
            {
                "id": item.id,
                "name": item.korean_name,
                "current": item.current_quantity,
                "maximum": item.maximum_quantity,
                "excess": item.current_quantity - item.maximum_quantity,
            }
            for item in above_maximum.scalars()
        ],
        "expired": [
            {"id": item.id, "name": item.korean_name, "quantity": item.current_quantity}
            for item in expired.scalars()
        ],
    }


@router.get("/{chemical_id}", response_model=ChemicalWithUsageResponse)
async def get_chemical_substance(chemical_id: int, db: AsyncSession = Depends(get_db)):
    """화학물질 상세 조회"""
    result = await db.execute(
        select(ChemicalSubstance)
        .options(selectinload(ChemicalSubstance.usage_records))
        .where(ChemicalSubstance.id == chemical_id)
    )
    chemical = result.scalar_one_or_none()

    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")

    return chemical


@router.put("/{chemical_id}", response_model=ChemicalSubstanceResponse)
async def update_chemical_substance(
    chemical_id: int,
    chemical_update: ChemicalSubstanceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """화학물질 정보 수정"""
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")

    # Update fields
    update_data = chemical_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chemical, field, value)

    chemical.updated_at = datetime.utcnow()
    chemical.updated_by = current_user_id  # Should come from auth
    await db.commit()
    await db.refresh(chemical)

    return chemical


@router.delete("/{chemical_id}")
async def delete_chemical_substance(
    chemical_id: int, db: AsyncSession = Depends(get_db)
):
    """화학물질 삭제"""
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")

    # Check if there are usage records
    usage_count = await db.scalar(
        select(func.count(ChemicalUsageRecord.id)).where(
            ChemicalUsageRecord.chemical_id == chemical_id
        )
    )

    if usage_count > 0:
        # Mark as disposed instead of deleting
        chemical.status = "DISPOSED"
        await db.commit()
        return {"message": "사용 기록이 있어 폐기 상태로 변경되었습니다"}

    await db.delete(chemical)
    await db.commit()

    return {"message": "화학물질이 삭제되었습니다"}


@router.post("/{chemical_id}/usage", response_model=dict)
async def record_chemical_usage(
    chemical_id: int,
    usage_data: ChemicalUsageCreate,
    db: AsyncSession = Depends(get_db),
):
    """화학물질 사용 기록"""
    # Check if chemical exists
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")

    # Check if worker exists
    worker = await db.get(Worker, usage_data.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")

    # Create usage record
    usage = ChemicalUsageRecord(chemical_id=chemical_id, **usage_data.model_dump())
    usage.created_by = current_user_id  # Should come from auth
    db.add(usage)

    # Update chemical quantity
    if chemical.current_quantity and usage_data.quantity_used:
        chemical.current_quantity -= usage_data.quantity_used
        if chemical.current_quantity < 0:
            chemical.current_quantity = 0

    await db.commit()

    return {
        "message": "사용 기록이 저장되었습니다",
        "remaining_quantity": chemical.current_quantity,
    }


@router.post("/{chemical_id}/msds", response_model=dict)
async def upload_msds(
    chemical_id: int, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    """MSDS 파일 업로드"""
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")

    # Validate file type
    if not file.filename.lower().endswith((".pdf", ".doc", ".docx")):
        raise HTTPException(status_code=400, detail="PDF, DOC, DOCX 파일만 허용됩니다")

    # Create upload directory
    settings = get_settings()
    upload_dir = os.path.join(settings.upload_dir, settings.msds_upload_subdir)
    os.makedirs(upload_dir, exist_ok=True)

    # Save file
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{chemical_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Update chemical record
    chemical.msds_file_path = file_path
    chemical.msds_revision_date = datetime.utcnow().date()
    await db.commit()

    return {"message": "MSDS 파일이 업로드되었습니다", "file_path": file_path}


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
    from src.models.chemical_substance import ChemicalSubstance, HazardClass, ChemicalStatus
    from src.models.chemical_usage_record import ChemicalUsageRecord

    # Test database setup
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_chemical_substances.db"
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

    async def test_chemical_substance_creation_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 화학물질 등록 전체 플로우
        - API 요청 → 검증 → DB 저장 → CAS 번호 중복 체크 → 응답
        """
        # Given: 화학물질 등록 데이터
        chemical_data = {
            "korean_name": "아세톤",
            "english_name": "Acetone",
            "cas_number": "67-64-1",
            "chemical_formula": "C3H6O",
            "hazard_class": "flammable",
            "usage_purpose": "청소용",
            "storage_location": "창고1-A구역",
            "supplier": "화학회사A",
            "minimum_quantity": 10.0,
            "maximum_quantity": 100.0,
            "current_quantity": 50.0,
            "unit": "L",
            "status": "IN_USE"
        }

        # When: 화학물질 등록 API 호출
        response = await async_client.post("/api/v1/chemical-substances/", json=chemical_data)

        # Then: 성공 응답 확인
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["korean_name"] == "아세톤"
        assert response_data["cas_number"] == "67-64-1"
        assert response_data["hazard_class"] == "flammable"
        assert response_data["current_quantity"] == 50.0

        # Then: DB에 저장 확인
        result = await test_db.execute(
            select(ChemicalSubstance).where(ChemicalSubstance.cas_number == "67-64-1")
        )
        saved_chemical = result.scalar_one_or_none()
        assert saved_chemical is not None
        assert saved_chemical.korean_name == "아세톤"
        assert saved_chemical.hazard_class == HazardClass.FLAMMABLE

    async def test_chemical_substance_duplicate_cas_validation(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: CAS 번호 중복 검증
        """
        # Given: 기존 화학물질 생성
        existing_chemical = ChemicalSubstance(
            korean_name="기존물질",
            cas_number="12345-67-8",
            hazard_class=HazardClass.TOXIC,
            storage_location="창고A",
            supplier="공급사A",
            unit="kg",
            status=ChemicalStatus.IN_USE
        )
        test_db.add(existing_chemical)
        await test_db.commit()

        # Given: 동일한 CAS 번호로 등록 시도
        duplicate_data = {
            "korean_name": "새물질",
            "cas_number": "12345-67-8",  # 중복된 CAS 번호
            "hazard_class": "corrosive",
            "storage_location": "창고B",
            "supplier": "공급사B",
            "unit": "L",
            "status": "IN_USE"
        }

        # When: 등록 시도
        response = await async_client.post("/api/v1/chemical-substances/", json=duplicate_data)

        # Then: 중복 오류 응답
        assert response.status_code == 400
        assert "이미 등록된 CAS 번호입니다" in response.json()["detail"]

    async def test_chemical_substance_list_with_filters_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 화학물질 목록 조회 및 필터링
        """
        # Given: 테스트 화학물질 데이터 생성
        chemicals = [
            ChemicalSubstance(
                korean_name="아세톤",
                cas_number="67-64-1",
                hazard_class=HazardClass.FLAMMABLE,
                storage_location="창고A",
                supplier="공급사A",
                unit="L",
                status=ChemicalStatus.IN_USE
            ),
            ChemicalSubstance(
                korean_name="염산",
                cas_number="7647-01-0",
                hazard_class=HazardClass.CORROSIVE,
                storage_location="창고B",
                supplier="공급사B",
                unit="L",
                status=ChemicalStatus.IN_USE
            ),
            ChemicalSubstance(
                korean_name="만료물질",
                cas_number="0000-00-0",
                hazard_class=HazardClass.TOXIC,
                storage_location="창고C",
                supplier="공급사C",
                unit="kg",
                status=ChemicalStatus.EXPIRED
            )
        ]
        
        for chemical in chemicals:
            test_db.add(chemical)
        await test_db.commit()

        # When: 전체 목록 조회
        response = await async_client.get("/api/v1/chemical-substances/?page=1&size=10")
        
        # Then: 전체 데이터 확인
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

        # When: 위험등급별 필터링
        response = await async_client.get("/api/v1/chemical-substances/?hazard_class=flammable")
        
        # Then: 가연성 물질만 조회
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["hazard_class"] == "flammable"

        # When: 상태별 필터링
        response = await async_client.get("/api/v1/chemical-substances/?status=EXPIRED")
        
        # Then: 만료된 물질만 조회
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "EXPIRED"

    async def test_chemical_usage_recording_integration(async_client: AsyncClient, test_worker: Worker, test_db: AsyncSession):
        """
        통합 테스트: 화학물질 사용 기록 및 재고 관리
        """
        # Given: 화학물질 생성
        chemical = ChemicalSubstance(
            korean_name="테스트화학물질",
            cas_number="TEST-001",
            hazard_class=HazardClass.FLAMMABLE,
            storage_location="창고A",
            supplier="공급사A",
            current_quantity=100.0,
            unit="L",
            status=ChemicalStatus.IN_USE
        )
        test_db.add(chemical)
        await test_db.commit()
        await test_db.refresh(chemical)

        # Given: 사용 기록 데이터
        usage_data = {
            "worker_id": test_worker.id,
            "quantity_used": 20.0,
            "usage_date": "2024-01-15",
            "usage_purpose": "청소작업",
            "work_location": "현장A"
        }

        # When: 사용 기록 등록 API 호출
        response = await async_client.post(f"/api/v1/chemical-substances/{chemical.id}/usage", json=usage_data)

        # Then: 성공 응답 확인
        assert response.status_code == 200
        response_data = response.json()
        assert "사용 기록이 저장되었습니다" in response_data["message"]
        assert response_data["remaining_quantity"] == 80.0  # 100 - 20

        # Then: DB에 사용 기록 저장 확인
        usage_result = await test_db.execute(
            select(ChemicalUsageRecord).where(
                and_(
                    ChemicalUsageRecord.chemical_id == chemical.id,
                    ChemicalUsageRecord.worker_id == test_worker.id
                )
            )
        )
        saved_usage = usage_result.scalar_one_or_none()
        assert saved_usage is not None
        assert saved_usage.quantity_used == 20.0
        assert saved_usage.usage_purpose == "청소작업"

        # Then: 화학물질 재고 업데이트 확인
        await test_db.refresh(chemical)
        assert chemical.current_quantity == 80.0

    async def test_chemical_inventory_check_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 재고 점검 현황 조회
        """
        # Given: 다양한 재고 상태의 화학물질 생성
        chemicals = [
            # 최소 재고 미달
            ChemicalSubstance(
                korean_name="부족물질",
                cas_number="LOW-001",
                hazard_class=HazardClass.FLAMMABLE,
                storage_location="창고A",
                supplier="공급사A",
                minimum_quantity=50.0,
                maximum_quantity=200.0,
                current_quantity=30.0,  # 최소 재고 미달
                unit="L",
                status=ChemicalStatus.IN_USE
            ),
            # 최대 재고 초과
            ChemicalSubstance(
                korean_name="과잉물질",
                cas_number="HIGH-001",
                hazard_class=HazardClass.CORROSIVE,
                storage_location="창고B",
                supplier="공급사B",
                minimum_quantity=10.0,
                maximum_quantity=100.0,
                current_quantity=150.0,  # 최대 재고 초과
                unit="kg",
                status=ChemicalStatus.IN_USE
            ),
            # 만료된 물질
            ChemicalSubstance(
                korean_name="만료물질",
                cas_number="EXP-001",
                hazard_class=HazardClass.TOXIC,
                storage_location="창고C",
                supplier="공급사C",
                current_quantity=25.0,
                unit="L",
                status=ChemicalStatus.EXPIRED
            )
        ]
        
        for chemical in chemicals:
            test_db.add(chemical)
        await test_db.commit()

        # When: 재고 점검 현황 조회
        response = await async_client.get("/api/v1/chemical-substances/inventory-check")

        # Then: 재고 현황 확인
        assert response.status_code == 200
        data = response.json()
        
        # 최소 재고 미달 항목 확인
        assert len(data["below_minimum"]) == 1
        below_min = data["below_minimum"][0]
        assert below_min["name"] == "부족물질"
        assert below_min["current"] == 30.0
        assert below_min["minimum"] == 50.0
        assert below_min["shortage"] == 20.0

        # 최대 재고 초과 항목 확인
        assert len(data["above_maximum"]) == 1
        above_max = data["above_maximum"][0]
        assert above_max["name"] == "과잉물질"
        assert above_max["current"] == 150.0
        assert above_max["maximum"] == 100.0
        assert above_max["excess"] == 50.0

        # 만료 항목 확인
        assert len(data["expired"]) == 1
        expired = data["expired"][0]
        assert expired["name"] == "만료물질"
        assert expired["quantity"] == 25.0

    async def test_chemical_statistics_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 화학물질 통계 조회
        """
        # Given: 다양한 화학물질 생성
        chemicals = [
            ChemicalSubstance(
                korean_name="가연성물질1",
                cas_number="FLM-001",
                hazard_class=HazardClass.FLAMMABLE,
                storage_location="창고A",
                supplier="공급사A",
                unit="L",
                status=ChemicalStatus.IN_USE
            ),
            ChemicalSubstance(
                korean_name="가연성물질2",
                cas_number="FLM-002",
                hazard_class=HazardClass.FLAMMABLE,
                storage_location="창고B",
                supplier="공급사B",
                unit="L",
                status=ChemicalStatus.IN_USE
            ),
            ChemicalSubstance(
                korean_name="부식성물질",
                cas_number="COR-001",
                hazard_class=HazardClass.CORROSIVE,
                storage_location="창고C",
                supplier="공급사C",
                unit="kg",
                status=ChemicalStatus.IN_USE
            )
        ]
        
        for chemical in chemicals:
            test_db.add(chemical)
        await test_db.commit()

        # When: 통계 조회
        response = await async_client.get("/api/v1/chemical-substances/statistics")

        # Then: 통계 데이터 확인
        assert response.status_code == 200
        stats = response.json()
        
        # 전체 개수 확인
        assert stats["total_substances"] == 3
        
        # 위험등급별 통계 확인
        assert "by_hazard_class" in stats
        assert stats["by_hazard_class"]["flammable"] == 2
        assert stats["by_hazard_class"]["corrosive"] == 1

    async def test_chemical_deletion_with_usage_records_integration(async_client: AsyncClient, test_worker: Worker, test_db: AsyncSession):
        """
        통합 테스트: 사용 기록이 있는 화학물질 삭제 처리
        """
        # Given: 화학물질 및 사용 기록 생성
        chemical = ChemicalSubstance(
            korean_name="삭제테스트물질",
            cas_number="DEL-001",
            hazard_class=HazardClass.FLAMMABLE,
            storage_location="창고A",
            supplier="공급사A",
            unit="L",
            status=ChemicalStatus.IN_USE
        )
        test_db.add(chemical)
        await test_db.commit()
        await test_db.refresh(chemical)

        # 사용 기록 생성
        usage_record = ChemicalUsageRecord(
            chemical_id=chemical.id,
            worker_id=test_worker.id,
            quantity_used=10.0,
            usage_purpose="테스트",
            work_location="현장A"
        )
        test_db.add(usage_record)
        await test_db.commit()

        # When: 화학물질 삭제 시도
        response = await async_client.delete(f"/api/v1/chemical-substances/{chemical.id}")

        # Then: 폐기 상태로 변경됨을 확인
        assert response.status_code == 200
        response_data = response.json()
        assert "폐기 상태로 변경되었습니다" in response_data["message"]

        # Then: DB에서 폐기 상태 확인
        await test_db.refresh(chemical)
        assert chemical.status == ChemicalStatus.DISPOSED

    # Run tests
    async def run_integration_tests():
        """화학물질 관리 통합 테스트 실행"""
        print("🧪 화학물질 관리 통합 테스트 시작...")
        
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
                    await test_chemical_substance_creation_integration(client, test_db)
                    print("✅ 화학물질 등록 통합 테스트 통과")
                    
                    await test_db.rollback()  # Reset for next test
                    
                    await test_chemical_substance_duplicate_cas_validation(client, test_db)
                    print("✅ CAS 번호 중복 검증 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_chemical_substance_list_with_filters_integration(client, test_db)
                    print("✅ 화학물질 목록 조회 및 필터링 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_chemical_usage_recording_integration(client, test_worker, test_db)
                    print("✅ 화학물질 사용 기록 및 재고 관리 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_chemical_inventory_check_integration(client, test_db)
                    print("✅ 재고 점검 현황 조회 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_chemical_statistics_integration(client, test_db)
                    print("✅ 화학물질 통계 조회 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_chemical_deletion_with_usage_records_integration(client, test_worker, test_db)
                    print("✅ 사용 기록이 있는 화학물질 삭제 처리 테스트 통과")
                    
            # Cleanup
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                
            print("🎉 모든 화학물질 관리 통합 테스트 통과!")
            
        except Exception as e:
            print(f"❌ 화학물질 통합 테스트 실패: {e}")
            raise

    # Execute tests when run directly
    if __name__ == "__main__":
        asyncio.run(run_integration_tests())
