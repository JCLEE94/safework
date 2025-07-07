from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.config.database import get_db
from src.models import WorkEnvironment, WorkEnvironmentWorkerExposure, Worker
from src.schemas.work_environment import (
    WorkEnvironmentCreate, WorkEnvironmentUpdate, WorkEnvironmentResponse,
    WorkEnvironmentListResponse, WorkEnvironmentWithExposuresResponse,
    WorkerExposureCreate, WorkEnvironmentStatistics
)
from src.utils.auth_deps import get_current_user_id

router = APIRouter(prefix="/api/v1/work-environments", tags=["work-environments"])


@router.post("/", response_model=WorkEnvironmentResponse)
async def create_work_environment(
    env_data: WorkEnvironmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """작업환경측정 기록 생성"""
    from src.models.work_environment import MeasurementType, MeasurementResult
    
    # Convert string values to enum objects
    data_dict = env_data.model_dump()
    
    # Find enum values by their value (Korean text)
    measurement_type_enum = None
    for enum_item in MeasurementType:
        if enum_item.value == data_dict["measurement_type"]:
            measurement_type_enum = enum_item
            break
    
    result_enum = None
    for enum_item in MeasurementResult:
        if enum_item.value == data_dict["result"]:
            result_enum = enum_item
            break
    
    if not measurement_type_enum or not result_enum:
        raise HTTPException(status_code=400, detail="잘못된 측정항목 또는 결과값입니다")
    
    # Replace string values with enum objects
    data_dict["measurement_type"] = measurement_type_enum
    data_dict["result"] = result_enum
    
    # Create work environment record
    work_env = WorkEnvironment(**data_dict)
    work_env.created_by = current_user_id  # Should come from auth
    db.add(work_env)
    await db.commit()
    await db.refresh(work_env)
    
    return work_env


@router.get("/", response_model=WorkEnvironmentListResponse)
async def list_work_environments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    measurement_type: Optional[str] = None,
    result: Optional[str] = None,
    location: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """작업환경측정 기록 목록 조회"""
    query = select(WorkEnvironment)
    
    # Apply filters
    conditions = []
    if measurement_type:
        conditions.append(WorkEnvironment.measurement_type == measurement_type)
    if result:
        conditions.append(WorkEnvironment.result == result)
    if location:
        conditions.append(WorkEnvironment.location.contains(location))
    if start_date:
        conditions.append(WorkEnvironment.measurement_date >= start_date)
    if end_date:
        conditions.append(WorkEnvironment.measurement_date <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Get total count
    count_query = select(func.count()).select_from(WorkEnvironment)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(WorkEnvironment.measurement_date.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return WorkEnvironmentListResponse(
        items=items,
        total=total,
        page=page,
        pages=(total + size - 1) // size,
        size=size
    )


@router.get("/statistics", response_model=WorkEnvironmentStatistics)
async def get_environment_statistics(db: AsyncSession = Depends(get_db)):
    """작업환경측정 통계 조회"""
    # Total measurements
    total = await db.scalar(select(func.count(WorkEnvironment.id)))
    
    # By result
    result_stats = await db.execute(
        select(
            WorkEnvironment.result,
            func.count(WorkEnvironment.id).label("count")
        )
        .group_by(WorkEnvironment.result)
    )
    
    result_counts = {row[0].value: row[1] for row in result_stats}
    
    # By type
    type_stats = await db.execute(
        select(
            WorkEnvironment.measurement_type,
            func.count(WorkEnvironment.id).label("count")
        )
        .group_by(WorkEnvironment.measurement_type)
    )
    
    # Re-measurement required
    re_measurement_count = await db.scalar(
        select(func.count(WorkEnvironment.id))
        .where(WorkEnvironment.re_measurement_required == 'Y')
    )
    
    # Recent failures
    recent_failures_query = await db.execute(
        select(WorkEnvironment)
        .where(WorkEnvironment.result == 'FAIL')
        .order_by(WorkEnvironment.measurement_date.desc())
        .limit(5)
    )
    recent_failures = []
    for failure in recent_failures_query.scalars():
        recent_failures.append({
            "id": failure.id,
            "location": failure.location,
            "measurement_type": failure.measurement_type.value,
            "measurement_date": failure.measurement_date.isoformat(),
            "measured_value": failure.measured_value,
            "standard_value": failure.standard_value
        })
    
    return WorkEnvironmentStatistics(
        total_measurements=total,
        pass_count=result_counts.get("적합", 0),
        fail_count=result_counts.get("부적합", 0),
        pending_count=result_counts.get("측정중", 0),
        re_measurement_required=re_measurement_count,
        by_type={row[0].value: row[1] for row in type_stats},
        recent_failures=recent_failures
    )


@router.get("/compliance-status")
async def get_compliance_status(db: AsyncSession = Depends(get_db)):
    """작업환경측정 법규 준수 현황"""
    # Get latest measurements by location and type
    six_months_ago = datetime.utcnow() - timedelta(days=180)
    
    # Locations that need measurement
    all_locations = await db.execute(
        select(WorkEnvironment.location).distinct()
    )
    locations = [loc[0] for loc in all_locations]
    
    compliance_status = []
    for location in locations:
        # Get latest measurement for each type at this location
        latest_measurements = await db.execute(
            select(
                WorkEnvironment.measurement_type,
                func.max(WorkEnvironment.measurement_date).label("latest_date"),
                func.max(WorkEnvironment.result).label("latest_result")
            )
            .where(WorkEnvironment.location == location)
            .group_by(WorkEnvironment.measurement_type)
        )
        
        location_status = {
            "location": location,
            "measurements": []
        }
        
        for measurement in latest_measurements:
            days_since = (datetime.utcnow() - measurement[1]).days
            is_overdue = days_since > 180  # 6 months
            
            location_status["measurements"].append({
                "type": measurement[0].value,
                "latest_date": measurement[1].isoformat(),
                "days_since": days_since,
                "is_overdue": is_overdue,
                "latest_result": measurement[2].value if measurement[2] else None
            })
        
        compliance_status.append(location_status)
    
    return {
        "locations": compliance_status,
        "total_locations": len(locations)
    }


@router.get("/{env_id}", response_model=WorkEnvironmentWithExposuresResponse)
async def get_work_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    """작업환경측정 기록 조회"""
    result = await db.execute(
        select(WorkEnvironment)
        .options(selectinload(WorkEnvironment.worker_exposures))
        .where(WorkEnvironment.id == env_id)
    )
    work_env = result.scalar_one_or_none()
    
    if not work_env:
        raise HTTPException(status_code=404, detail="작업환경측정 기록을 찾을 수 없습니다")
    
    return work_env


@router.put("/{env_id}", response_model=WorkEnvironmentResponse)
async def update_work_environment(
    env_id: int,
    env_update: WorkEnvironmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """작업환경측정 기록 수정"""
    work_env = await db.get(WorkEnvironment, env_id)
    if not work_env:
        raise HTTPException(status_code=404, detail="작업환경측정 기록을 찾을 수 없습니다")
    
    # Update fields
    update_data = env_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(work_env, field, value)
    
    work_env.updated_at = datetime.utcnow()
    work_env.updated_by = current_user_id  # Should come from auth
    await db.commit()
    await db.refresh(work_env)
    
    return work_env


@router.delete("/{env_id}")
async def delete_work_environment(env_id: int, db: AsyncSession = Depends(get_db)):
    """작업환경측정 기록 삭제"""
    work_env = await db.get(WorkEnvironment, env_id)
    if not work_env:
        raise HTTPException(status_code=404, detail="작업환경측정 기록을 찾을 수 없습니다")
    
    await db.delete(work_env)
    await db.commit()
    
    return {"message": "작업환경측정 기록이 삭제되었습니다"}


@router.post("/{env_id}/exposures", response_model=dict)
async def add_worker_exposures(
    env_id: int,
    exposures: List[WorkerExposureCreate],
    db: AsyncSession = Depends(get_db)
):
    """작업환경측정에 노출 근로자 추가"""
    # Check if environment exists
    work_env = await db.get(WorkEnvironment, env_id)
    if not work_env:
        raise HTTPException(status_code=404, detail="작업환경측정 기록을 찾을 수 없습니다")
    
    # Add exposures
    added_count = 0
    for exposure_data in exposures:
        # Check if worker exists
        worker = await db.get(Worker, exposure_data.worker_id)
        if not worker:
            continue
        
        # Check if exposure already exists
        existing = await db.scalar(
            select(WorkEnvironmentWorkerExposure)
            .where(
                and_(
                    WorkEnvironmentWorkerExposure.work_environment_id == env_id,
                    WorkEnvironmentWorkerExposure.worker_id == exposure_data.worker_id
                )
            )
        )
        if existing:
            continue
        
        exposure = WorkEnvironmentWorkerExposure(
            work_environment_id=env_id,
            **exposure_data.model_dump()
        )
        db.add(exposure)
        added_count += 1
    
    await db.commit()
    
    return {
        "message": f"{added_count}명의 노출 근로자가 추가되었습니다",
        "added_count": added_count
    }