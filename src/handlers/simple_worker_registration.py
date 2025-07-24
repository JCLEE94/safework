"""
간단한 근로자 등록 시스템

근로자가 휴대폰으로 직접 등록할 수 있는 간단한 시스템을 제공합니다.
복잡한 QR 코드 생성/토큰 관리 없이 바로 등록 가능합니다.

URL: https://safework.jclee.me/register
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config.database import get_db
from ..models.worker import Worker
from ..schemas.worker import WorkerCreate, WorkerResponse
from ..services.worker import get_worker_service
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/simple-registration", tags=["간단등록"])


@router.post("/worker", response_model=WorkerResponse)
async def register_worker_directly(
    worker_data: WorkerCreate,
    db: AsyncSession = Depends(get_db),
    worker_service = Depends(get_worker_service)
):
    """
    근로자 직접 등록
    
    QR 코드나 토큰 없이 근로자가 직접 등록할 수 있습니다.
    """
    try:
        # 중복 확인 (employee_id 기준)
        existing_worker = await db.execute(
            select(Worker).where(Worker.employee_id == worker_data.employee_id)
        )
        if existing_worker.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="이미 등록된 사원번호입니다"
            )
        
        # 근로자 등록
        new_worker = await worker_service.create_worker(worker_data.dict(), db)
        
        logger.info(f"근로자 직접 등록 완료: {worker_data.name} (ID: {worker_data.employee_id})")
        
        return WorkerResponse.from_orm(new_worker)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"근로자 직접 등록 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록 중 오류가 발생했습니다"
        )


@router.get("/check/{employee_id}")
async def check_worker_exists(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    근로자 등록 여부 확인
    """
    try:
        worker = await db.execute(
            select(Worker).where(Worker.employee_id == employee_id)
        )
        existing_worker = worker.scalar_one_or_none()
        
        return {
            "exists": existing_worker is not None,
            "worker_info": {
                "name": existing_worker.name,
                "department": existing_worker.department,
                "registered_at": existing_worker.created_at.isoformat()
            } if existing_worker else None
        }
        
    except Exception as e:
        logger.error(f"근로자 확인 실패: {str(e)}")
        return {"exists": False, "error": "확인 중 오류가 발생했습니다"}


@router.get("/stats")
async def get_registration_stats(db: AsyncSession = Depends(get_db)):
    """
    등록 통계
    """
    try:
        from sqlalchemy import func
        
        # 총 등록자 수
        total_workers = await db.execute(select(func.count(Worker.id)))
        total_count = total_workers.scalar()
        
        # 오늘 등록자 수
        today_workers = await db.execute(
            select(func.count(Worker.id)).where(
                func.date(Worker.created_at) == datetime.now().date()
            )
        )
        today_count = today_workers.scalar()
        
        # 부서별 통계
        dept_stats = await db.execute(
            select(Worker.department, func.count(Worker.id))
            .group_by(Worker.department)
        )
        department_counts = {dept: count for dept, count in dept_stats.fetchall()}
        
        return {
            "total_workers": total_count,
            "today_registrations": today_count,
            "department_counts": department_counts,
            "updated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        return {
            "total_workers": 0,
            "today_registrations": 0,
            "department_counts": {},
            "error": "통계 조회 중 오류가 발생했습니다"
        }