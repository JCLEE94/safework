"""
근로자 관리 API 핸들러
Worker management API handlers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
import logging

from ..config.database import get_db
from ..models.worker import Worker, HealthConsultation
from ..schemas.worker import (
    WorkerCreate, WorkerUpdate, WorkerResponse, WorkerListResponse,
    HealthConsultationCreate, HealthConsultationResponse
)
from ..repositories.worker import worker_repository
from ..services.cache import cache_result, cache_query, CacheTTL, invalidate_worker_cache
from ..utils.db_optimization import DatabaseOptimizer

logger = logging.getLogger(__name__)

router = APIRouter()

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
    db: AsyncSession = Depends(get_db)
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
                filters['department'] = department
            if work_type:
                filters['work_type'] = work_type
            if employment_type:
                filters['employment_type'] = employment_type
            if health_status:
                filters['health_status'] = health_status
            if is_active is not None:
                filters['is_active'] = is_active
            
            workers, total = await worker_repository.get_multi(
                db, skip=skip, limit=limit, filters=filters
            )
        
        return WorkerListResponse(
            items=[WorkerResponse.model_validate(worker, from_attributes=True) for worker in workers],
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"근로자 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 목록 조회 중 오류가 발생했습니다."
        )

@router.post("/", response_model=WorkerResponse, status_code=status.HTTP_201_CREATED)
async def create_worker(
    worker_data: WorkerCreate,
    db: AsyncSession = Depends(get_db)
):
    """근로자 등록"""
    try:
        # 사번 중복 체크
        existing_worker = await worker_repository.get_by_employee_id(
            db, employee_id=worker_data.employee_id
        )
        
        if existing_worker:
            logger.warning(f"중복된 사번: {worker_data.employee_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 존재하는 사번입니다."
            )
        
        # 리포지토리를 통한 근로자 생성
        worker = await worker_repository.create(db, obj_in=worker_data)
        
        # 캐시 무효화
        await invalidate_worker_cache()
        
        return WorkerResponse.model_validate(worker, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근로자 생성 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 생성 중 오류가 발생했습니다."
        )

@router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: int,
    db: AsyncSession = Depends(get_db)
):
    """근로자 상세 조회"""
    try:
        worker = await worker_repository.get_by_id(db, id=worker_id)
        
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="근로자를 찾을 수 없습니다."
            )
        
        return WorkerResponse.model_validate(worker, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근로자 상세 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 조회 중 오류가 발생했습니다."
        )

@router.put("/{worker_id}", response_model=WorkerResponse)
async def update_worker(
    worker_id: int,
    worker_data: WorkerUpdate,
    db: AsyncSession = Depends(get_db)
):
    """근로자 정보 수정"""
    try:
        worker = await worker_repository.get_by_id(db, id=worker_id)
        
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="근로자를 찾을 수 없습니다."
            )
        
        updated_worker = await worker_repository.update(
            db, db_obj=worker, obj_in=worker_data
        )
        
        # 캐시 무효화
        await invalidate_worker_cache(worker_id)
        
        return WorkerResponse.model_validate(updated_worker, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근로자 수정 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 수정 중 오류가 발생했습니다."
        )

@router.delete("/{worker_id}")
async def delete_worker(
    worker_id: int,
    db: AsyncSession = Depends(get_db)
):
    """근로자 삭제 (비활성화)"""
    try:
        success = await worker_repository.delete(db, id=worker_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="근로자를 찾을 수 없습니다."
            )
        
        # 캐시 무효화
        await invalidate_worker_cache(worker_id)
        
        return {"message": "근로자가 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근로자 삭제 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="근로자 삭제 중 오류가 발생했습니다."
        )

@router.get("/{worker_id}/health-consultations", response_model=List[HealthConsultationResponse])
async def get_worker_consultations(
    worker_id: int,
    db: AsyncSession = Depends(get_db)
):
    """근로자 건강상담 기록 조회"""
    
    result = await db.execute(
        select(HealthConsultation)
        .where(HealthConsultation.worker_id == worker_id)
        .order_by(HealthConsultation.consultation_date.desc())
    )
    consultations = result.scalars().all()
    
    return [HealthConsultationResponse.model_validate(consultation) for consultation in consultations]

@router.post("/{worker_id}/health-consultations", response_model=HealthConsultationResponse)
async def create_health_consultation(
    worker_id: int,
    consultation_data: HealthConsultationCreate,
    db: AsyncSession = Depends(get_db)
):
    """건강상담 기록 등록"""
    
    # 근로자 존재 확인
    result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="근로자를 찾을 수 없습니다."
        )
    
    # 상담기록 생성
    consultation = HealthConsultation(
        worker_id=worker_id,
        **consultation_data.model_dump()
    )
    db.add(consultation)
    await db.commit()
    await db.refresh(consultation)
    
    return HealthConsultationResponse.model_validate(consultation)

@router.get("/statistics/dashboard")
@cache_result("worker_stats", CacheTTL.DASHBOARD)
async def get_worker_statistics(
    db: AsyncSession = Depends(get_db)
):
    """근로자 현황 통계"""
    try:
        stats = await worker_repository.get_statistics(db)
        return {
            "total_workers": stats["total"],
            "employment_type_distribution": stats["by_employment_type"],
            "work_type_distribution": stats["by_work_type"],
            "health_status_distribution": stats["by_health_status"],
            "gender_distribution": stats["by_gender"],
            "department_distribution": stats["by_department"],
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"근로자 통계 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="통계 조회 중 오류가 발생했습니다."
        )

@router.get("/debug/test")
async def test_endpoint():
    """테스트 엔드포인트"""
    return {"status": "ok", "message": "workers router working"}

@router.post("/debug/test-post")
async def test_post_endpoint(data: dict):
    """POST 테스트 엔드포인트"""
    return {"status": "ok", "received": data, "message": "POST working"}