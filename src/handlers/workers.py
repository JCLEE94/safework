"""
근로자 관리 API 핸들러
Worker management API handlers
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..models.health_consultation import HealthConsultation
from ..models.worker import Worker
from ..repositories.worker import worker_repository
from ..schemas.worker import (HealthConsultationCreate,
                              HealthConsultationResponse, WorkerCreate,
                              WorkerListResponse, WorkerResponse, WorkerUpdate)
from ..services.cache import (CacheTTL, cache_query, cache_result,
                              invalidate_worker_cache)
from ..utils.db_optimization import DatabaseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/public-registration", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
async def public_worker_registration(
    worker_data: WorkerCreate, 
    db: AsyncSession = Depends(get_db)
):
    """공개 근로자 등록 (인증 불필요)"""
    try:
        # 사번이 있는 경우 중복 체크
        if worker_data.employee_id:
            existing_worker = await worker_repository.get_by_employee_id(
                db, employee_id=worker_data.employee_id
            )
            if existing_worker:
                logger.warning(f"중복된 사번: {worker_data.employee_id}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 존재하는 사번입니다.",
                )

        # 근로자 생성
        worker = await worker_repository.create(db, obj_in=worker_data)
        
        # 캐시 무효화
        await invalidate_worker_cache()
        
        logger.info(f"공개 등록 완료: {worker.name} (ID: {worker.id})")
        
        return WorkerResponse.model_validate(worker, from_attributes=True)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"공개 근로자 등록 실패: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 등록 중 오류가 발생했습니다.",
        )


@router.get("/", response_model=WorkerListResponse)
async def get_workers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    search: Optional[str] = Query(None, description="이름, 사번으로 검색"),
    department: Optional[str] = Query(None, description="부서 필터"),
    work_type: Optional[str] = Query(None, description="작업유형 필터"),
    employment_type: Optional[str] = Query(None, description="고용형태 필터"),
    health_status: Optional[str] = Query(None, description="건강상태 필터"),
    is_active: Optional[bool] = Query(None, description="재직여부 필터"),
    db: AsyncSession = Depends(get_db),
):
    """근로자 목록 조회"""
    try:
        # 검색어가 있으면 검색 기능 사용
        if search:
            workers, total = await worker_repository.search_workers(
                db, search_term=search, skip=skip, limit=limit
            )
        else:
            # 필터 조건 구성
            filters = {}
            if department:
                filters["department"] = department
            if work_type:
                filters["work_type"] = work_type
            if employment_type:
                filters["employment_type"] = employment_type
            if health_status:
                filters["health_status"] = health_status
            if is_active is not None:
                filters["is_active"] = is_active

            workers, total = await worker_repository.get_multi_with_filters(
                db, skip=skip, limit=limit, **filters
            )

        return WorkerListResponse(
            items=[WorkerResponse.model_validate(worker, from_attributes=True) for worker in workers],
            total=total,
            page=skip // limit + 1,
            size=limit,
            pages=(total + limit - 1) // limit,
        )

    except Exception as e:
        logger.error(f"근로자 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 목록 조회 중 오류가 발생했습니다.",
        )


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
    from ..app import app
    from ..config.database import Base, get_db
    from ..models.worker import Worker, EmploymentType, WorkType, HealthStatus

    # Test database setup
    SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_workers.db"
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

    async def test_worker_registration_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 근로자 등록 전체 플로우
        - API 요청 → 검증 → DB 저장 → 캐시 무효화 → 응답
        """
        # Given: 근로자 등록 데이터
        worker_data = {
            "name": "김철수",
            "employee_id": "EMP001",
            "phone": "010-1234-5678",
            "email": "kimcs@example.com",
            "department": "건설팀",
            "position": "현장관리자",
            "employment_type": "regular",
            "work_type": "construction",
            "hire_date": "2024-01-01",
            "birth_date": "1985-03-15",
            "address": "서울시 강남구",
            "emergency_contact": "010-9876-5432",
            "health_status": "normal",
            "is_active": True
        }

        # When: 공개 등록 API 호출
        response = await async_client.post("/api/v1/workers/public-registration", json=worker_data)

        # Then: 성공 응답 확인
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["name"] == "김철수"
        assert response_data["employee_id"] == "EMP001"
        assert response_data["employment_type"] == "regular"

        # Then: DB에 저장 확인
        result = await test_db.execute(
            select(Worker).where(Worker.employee_id == "EMP001")
        )
        saved_worker = result.scalar_one_or_none()
        assert saved_worker is not None
        assert saved_worker.name == "김철수"
        assert saved_worker.employment_type == EmploymentType.REGULAR

    async def test_worker_registration_duplicate_employee_id(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 중복 사번 검증
        """
        # Given: 기존 근로자 생성
        existing_worker = Worker(
            name="기존근로자",
            employee_id="DUPLICATE001",
            employment_type=EmploymentType.REGULAR,
            work_type=WorkType.CONSTRUCTION,
            health_status=HealthStatus.NORMAL
        )
        test_db.add(existing_worker)
        await test_db.commit()

        # Given: 동일한 사번으로 등록 시도
        duplicate_data = {
            "name": "새근로자",
            "employee_id": "DUPLICATE001",
            "employment_type": "contract",
            "work_type": "electrical",
            "health_status": "normal"
        }

        # When: 등록 시도
        response = await async_client.post("/api/v1/workers/public-registration", json=duplicate_data)

        # Then: 중복 오류 응답
        assert response.status_code == 400
        assert "이미 존재하는 사번입니다" in response.json()["detail"]

    async def test_worker_list_with_filters_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 근로자 목록 조회 및 필터링
        """
        # Given: 테스트 데이터 생성
        workers = [
            Worker(name="김건설", employee_id="C001", department="건설팀", 
                  employment_type=EmploymentType.REGULAR, work_type=WorkType.CONSTRUCTION,
                  health_status=HealthStatus.NORMAL, is_active=True),
            Worker(name="박전기", employee_id="E001", department="전기팀",
                  employment_type=EmploymentType.CONTRACT, work_type=WorkType.ELECTRICAL,
                  health_status=HealthStatus.CAUTION, is_active=True),
            Worker(name="이배관", employee_id="P001", department="배관팀",
                  employment_type=EmploymentType.TEMPORARY, work_type=WorkType.PLUMBING,
                  health_status=HealthStatus.NORMAL, is_active=False),
        ]
        
        for worker in workers:
            test_db.add(worker)
        await test_db.commit()

        # When: 부서별 필터링 조회
        response = await async_client.get("/api/v1/workers/?department=건설팀")
        
        # Then: 필터링된 결과 확인
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "김건설"

        # When: 고용형태별 필터링 조회
        response = await async_client.get("/api/v1/workers/?employment_type=contract")
        
        # Then: 계약직 근로자만 조회
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["employment_type"] == "contract"

        # When: 재직 상태 필터링
        response = await async_client.get("/api/v1/workers/?is_active=false")
        
        # Then: 퇴직자만 조회
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["is_active"] == False

    async def test_worker_search_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 근로자 검색 기능
        """
        # Given: 테스트 데이터
        workers = [
            Worker(name="김철수", employee_id="K001", employment_type=EmploymentType.REGULAR, 
                  work_type=WorkType.CONSTRUCTION, health_status=HealthStatus.NORMAL),
            Worker(name="박영희", employee_id="P001", employment_type=EmploymentType.CONTRACT,
                  work_type=WorkType.ELECTRICAL, health_status=HealthStatus.NORMAL),
            Worker(name="이민수", employee_id="L001", employment_type=EmploymentType.TEMPORARY,
                  work_type=WorkType.PLUMBING, health_status=HealthStatus.CAUTION),
        ]
        
        for worker in workers:
            test_db.add(worker)
        await test_db.commit()

        # When: 이름으로 검색
        response = await async_client.get("/api/v1/workers/?search=김철수")
        
        # Then: 검색 결과 확인
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "김철수"

        # When: 사번으로 검색
        response = await async_client.get("/api/v1/workers/?search=P001")
        
        # Then: 사번 검색 결과 확인
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["employee_id"] == "P001"
        assert data["items"][0]["name"] == "박영희"

    async def test_worker_cache_invalidation_integration(async_client: AsyncClient, test_db: AsyncSession):
        """
        통합 테스트: 캐시 무효화 검증
        이 테스트는 Redis 캐시가 설정되어 있을 때 실행됩니다.
        """
        # Given: 근로자 등록 (캐시 생성)
        worker_data = {
            "name": "캐시테스트",
            "employee_id": "CACHE001",
            "employment_type": "regular",
            "work_type": "construction",
            "health_status": "normal"
        }

        # When: 첫 번째 등록 (캐시 생성)
        response1 = await async_client.post("/api/v1/workers/public-registration", json=worker_data)
        assert response1.status_code == 201

        # When: 목록 조회 (캐시 사용)
        list_response1 = await async_client.get("/api/v1/workers/")
        initial_count = list_response1.json()["total"]

        # When: 두 번째 근로자 등록 (캐시 무효화 발생)
        worker_data2 = {
            "name": "캐시테스트2",
            "employee_id": "CACHE002", 
            "employment_type": "contract",
            "work_type": "electrical",
            "health_status": "normal"
        }
        response2 = await async_client.post("/api/v1/workers/public-registration", json=worker_data2)
        assert response2.status_code == 201

        # Then: 목록 조회 시 캐시가 무효화되어 새로운 데이터 반영
        list_response2 = await async_client.get("/api/v1/workers/")
        updated_count = list_response2.json()["total"]
        assert updated_count == initial_count + 1

    # Run tests
    async def run_integration_tests():
        """통합 테스트 실행"""
        print("🧪 근로자 관리 통합 테스트 시작...")
        
        try:
            # Setup test database
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            async with TestingSessionLocal() as test_db:
                async with AsyncClient(app=app, base_url="http://test") as client:
                    print("✅ 테스트 환경 설정 완료")
                    
                    # Run individual tests
                    await test_worker_registration_integration(client, test_db)
                    print("✅ 근로자 등록 통합 테스트 통과")
                    
                    await test_db.rollback()  # Reset for next test
                    
                    await test_worker_registration_duplicate_employee_id(client, test_db)
                    print("✅ 중복 사번 검증 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_worker_list_with_filters_integration(client, test_db)
                    print("✅ 목록 조회 및 필터링 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_worker_search_integration(client, test_db)
                    print("✅ 검색 기능 테스트 통과")
                    
                    await test_db.rollback()
                    
                    await test_worker_cache_invalidation_integration(client, test_db)
                    print("✅ 캐시 무효화 테스트 통과")
                    
            # Cleanup
            async with test_engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                
            print("🎉 모든 근로자 관리 통합 테스트 통과!")
            
        except Exception as e:
            print(f"❌ 통합 테스트 실패: {e}")
            raise

    # Execute tests when run directly
    if __name__ == "__main__":
        asyncio.run(run_integration_tests())