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
