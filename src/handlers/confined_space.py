"""
밀폐공간 작업 관리 API 핸들러
Confined space work management API handlers
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
import json

from src.config.database import get_db
from src.models import confined_space as models
from src.schemas import confined_space as schemas
from src.utils.auth_deps import CurrentUserId
from src.services.cache import CacheService, get_cache_service
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1/confined-spaces", tags=["밀폐공간관리"])


# 밀폐공간 관리
@router.get("/", response_model=List[schemas.ConfinedSpaceResponse])
async def get_confined_spaces(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_active: Optional[bool] = None,
    space_type: Optional[str] = None,
    location: Optional[str] = None,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """밀폐공간 목록 조회"""
    cache_key = f"confined_spaces:{skip}:{limit}:{is_active}:{space_type}:{location}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    query = select(models.ConfinedSpace)
    
    # 필터 적용
    if is_active is not None:
        query = query.where(models.ConfinedSpace.is_active == is_active)
    if space_type:
        query = query.where(models.ConfinedSpace.type == space_type)
    if location:
        query = query.where(models.ConfinedSpace.location.ilike(f"%{location}%"))
    
    query = query.offset(skip).limit(limit).order_by(models.ConfinedSpace.created_at.desc())
    
    result = await db.execute(query)
    spaces = result.scalars().all()
    
    response = [schemas.ConfinedSpaceResponse.from_orm(space) for space in spaces]
    await cache.set(cache_key, response, ttl=300)
    
    return response


@router.post("/", response_model=schemas.ConfinedSpaceResponse)
async def create_confined_space(
    space_data: schemas.ConfinedSpaceCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """밀폐공간 등록"""
    # 중복 확인
    existing = await db.execute(
        select(models.ConfinedSpace).where(
            and_(
                models.ConfinedSpace.name == space_data.name,
                models.ConfinedSpace.location == space_data.location
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="동일한 이름과 위치의 밀폐공간이 이미 존재합니다"
        )
    
    # 밀폐공간 생성
    new_space = models.ConfinedSpace(
        **space_data.dict(),
        created_by=current_user_id
    )
    
    db.add(new_space)
    await db.commit()
    await db.refresh(new_space)
    
    logger.info(f"밀폐공간 등록: {new_space.name} by {current_user_id}")
    
    return schemas.ConfinedSpaceResponse.from_orm(new_space)


# 통계
@router.get("/statistics", response_model=schemas.ConfinedSpaceStatistics)
async def get_statistics(
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """밀폐공간 관리 통계"""
    cache_key = "confined_space_statistics"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # 전체 밀폐공간 수
    total_result = await db.execute(
        select(func.count(models.ConfinedSpace.id))
    )
    total_spaces = total_result.scalar() or 0
    
    # 사용 중인 밀폐공간 수
    active_result = await db.execute(
        select(func.count(models.ConfinedSpace.id))
        .where(models.ConfinedSpace.is_active == True)
    )
    active_spaces = active_result.scalar() or 0
    
    # 오늘 작업 허가
    today = datetime.now().date()
    today_result = await db.execute(
        select(func.count(models.ConfinedSpaceWorkPermit.id))
        .where(
            and_(
                func.date(models.ConfinedSpaceWorkPermit.scheduled_start) <= today,
                func.date(models.ConfinedSpaceWorkPermit.scheduled_end) >= today
            )
        )
    )
    permits_today = today_result.scalar() or 0
    
    # 이번 달 작업 허가
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    month_result = await db.execute(
        select(func.count(models.ConfinedSpaceWorkPermit.id))
        .where(models.ConfinedSpaceWorkPermit.created_at >= month_start)
    )
    permits_this_month = month_result.scalar() or 0
    
    # 승인 대기 중
    pending_result = await db.execute(
        select(func.count(models.ConfinedSpaceWorkPermit.id))
        .where(models.ConfinedSpaceWorkPermit.status == models.WorkPermitStatus.SUBMITTED)
    )
    pending_approvals = pending_result.scalar() or 0
    
    # 점검 기한 초과
    overdue_date = datetime.now() - timedelta(days=30)
    overdue_result = await db.execute(
        select(func.count(models.ConfinedSpace.id))
        .where(
            or_(
                models.ConfinedSpace.last_inspection_date == None,
                models.ConfinedSpace.last_inspection_date < overdue_date
            )
        )
    )
    overdue_inspections = overdue_result.scalar() or 0
    
    # 유형별 통계
    type_result = await db.execute(
        select(models.ConfinedSpace.type, func.count(models.ConfinedSpace.id))
        .group_by(models.ConfinedSpace.type)
    )
    by_type = {str(t): c for t, c in type_result.all()}
    
    # 위험 요인별 통계 (JSON 필드이므로 복잡한 쿼리 대신 Python에서 처리)
    all_spaces = await db.execute(
        select(models.ConfinedSpace.hazards).where(models.ConfinedSpace.hazards != None)
    )
    hazard_count = {}
    for (hazards,) in all_spaces:
        if hazards:
            for hazard in hazards:
                hazard_count[hazard] = hazard_count.get(hazard, 0) + 1
    
    statistics = schemas.ConfinedSpaceStatistics(
        total_spaces=total_spaces,
        active_spaces=active_spaces,
        permits_today=permits_today,
        permits_this_month=permits_this_month,
        pending_approvals=pending_approvals,
        overdue_inspections=overdue_inspections,
        by_type=by_type,
        by_hazard=hazard_count,
        recent_incidents=0  # 추후 사고 관리 기능 연동
    )
    
    await cache.set(cache_key, statistics.dict(), ttl=600)
    
    return statistics


@router.get("/{space_id}", response_model=schemas.ConfinedSpaceResponse)
async def get_confined_space(
    space_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """밀폐공간 상세 정보 조회"""
    space = await db.get(models.ConfinedSpace, space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="밀폐공간을 찾을 수 없습니다"
        )
    
    return schemas.ConfinedSpaceResponse.from_orm(space)


@router.put("/{space_id}", response_model=schemas.ConfinedSpaceResponse)
async def update_confined_space(
    space_id: UUID,
    space_data: schemas.ConfinedSpaceUpdate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """밀폐공간 정보 수정"""
    space = await db.get(models.ConfinedSpace, space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="밀폐공간을 찾을 수 없습니다"
        )
    
    # 업데이트
    update_data = space_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(space, field, value)
    
    await db.commit()
    await db.refresh(space)
    
    return schemas.ConfinedSpaceResponse.from_orm(space)


@router.delete("/{space_id}")
async def delete_confined_space(
    space_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """밀폐공간 삭제 (비활성화)"""
    space = await db.get(models.ConfinedSpace, space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="밀폐공간을 찾을 수 없습니다"
        )
    
    # 진행 중인 작업이 있는지 확인
    active_permits = await db.execute(
        select(models.ConfinedSpaceWorkPermit).where(
            and_(
                models.ConfinedSpaceWorkPermit.confined_space_id == space_id,
                models.ConfinedSpaceWorkPermit.status.in_([
                    models.WorkPermitStatus.APPROVED,
                    models.WorkPermitStatus.IN_PROGRESS
                ])
            )
        )
    )
    if active_permits.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="진행 중인 작업이 있어 삭제할 수 없습니다"
        )
    
    # 비활성화
    space.is_active = False
    await db.commit()
    
    return {"message": "밀폐공간이 비활성화되었습니다"}


# 작업 허가서 관리
@router.get("/permits/", response_model=List[schemas.WorkPermitResponse])
async def get_work_permits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    space_id: Optional[UUID] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 허가서 목록 조회"""
    query = select(models.ConfinedSpaceWorkPermit).options(
        selectinload(models.ConfinedSpaceWorkPermit.confined_space)
    )
    
    # 필터 적용
    if space_id:
        query = query.where(models.ConfinedSpaceWorkPermit.confined_space_id == space_id)
    if status:
        query = query.where(models.ConfinedSpaceWorkPermit.status == status)
    if date_from:
        query = query.where(models.ConfinedSpaceWorkPermit.scheduled_start >= date_from)
    if date_to:
        query = query.where(models.ConfinedSpaceWorkPermit.scheduled_end <= date_to)
    
    query = query.offset(skip).limit(limit).order_by(
        models.ConfinedSpaceWorkPermit.created_at.desc()
    )
    
    result = await db.execute(query)
    permits = result.scalars().all()
    
    return [schemas.WorkPermitResponse.from_orm(permit) for permit in permits]


@router.post("/permits/", response_model=schemas.WorkPermitResponse)
async def create_work_permit(
    permit_data: schemas.WorkPermitCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 허가서 생성"""
    # 밀폐공간 확인
    space = await db.get(models.ConfinedSpace, permit_data.confined_space_id)
    if not space or not space.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="유효한 밀폐공간을 찾을 수 없습니다"
        )
    
    # 중복 작업 확인 (같은 시간대)
    overlapping = await db.execute(
        select(models.ConfinedSpaceWorkPermit).where(
            and_(
                models.ConfinedSpaceWorkPermit.confined_space_id == permit_data.confined_space_id,
                models.ConfinedSpaceWorkPermit.status.in_([
                    models.WorkPermitStatus.APPROVED,
                    models.WorkPermitStatus.IN_PROGRESS
                ]),
                or_(
                    and_(
                        models.ConfinedSpaceWorkPermit.scheduled_start <= permit_data.scheduled_start,
                        models.ConfinedSpaceWorkPermit.scheduled_end > permit_data.scheduled_start
                    ),
                    and_(
                        models.ConfinedSpaceWorkPermit.scheduled_start < permit_data.scheduled_end,
                        models.ConfinedSpaceWorkPermit.scheduled_end >= permit_data.scheduled_end
                    )
                )
            )
        )
    )
    if overlapping.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="해당 시간대에 이미 작업이 예정되어 있습니다"
        )
    
    # 허가서 번호 생성
    today = datetime.now().strftime("%Y%m%d")
    count_result = await db.execute(
        select(func.count(models.ConfinedSpaceWorkPermit.id)).where(
            models.ConfinedSpaceWorkPermit.permit_number.like(f"CS-{today}-%")
        )
    )
    count = count_result.scalar() or 0
    permit_number = f"CS-{today}-{count + 1:03d}"
    
    # 작업 허가서 생성
    new_permit = models.ConfinedSpaceWorkPermit(
        **permit_data.dict(),
        permit_number=permit_number,
        submitted_by=current_user_id,
        submitted_at=datetime.now(),
        status=models.WorkPermitStatus.SUBMITTED
    )
    
    db.add(new_permit)
    await db.commit()
    await db.refresh(new_permit)
    
    logger.info(f"작업 허가서 생성: {permit_number} by {current_user_id}")
    
    return schemas.WorkPermitResponse.from_orm(new_permit)


@router.get("/permits/{permit_id}", response_model=schemas.WorkPermitResponse)
async def get_work_permit(
    permit_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 허가서 상세 정보 조회"""
    permit = await db.execute(
        select(models.ConfinedSpaceWorkPermit)
        .options(
            selectinload(models.ConfinedSpaceWorkPermit.confined_space),
            selectinload(models.ConfinedSpaceWorkPermit.gas_measurements)
        )
        .where(models.ConfinedSpaceWorkPermit.id == permit_id)
    )
    permit = permit.scalar_one_or_none()
    
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업 허가서를 찾을 수 없습니다"
        )
    
    return schemas.WorkPermitResponse.from_orm(permit)


@router.put("/permits/{permit_id}", response_model=schemas.WorkPermitResponse)
async def update_work_permit(
    permit_id: UUID,
    permit_data: schemas.WorkPermitUpdate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 허가서 수정"""
    permit = await db.get(models.ConfinedSpaceWorkPermit, permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업 허가서를 찾을 수 없습니다"
        )
    
    # 승인된 허가서는 일부 필드만 수정 가능
    if permit.status in [models.WorkPermitStatus.APPROVED, models.WorkPermitStatus.IN_PROGRESS]:
        allowed_fields = ['actual_start', 'actual_end', 'gas_test_results', 'workers']
        update_data = {k: v for k, v in permit_data.dict(exclude_unset=True).items() 
                      if k in allowed_fields}
    else:
        update_data = permit_data.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(permit, field, value)
    
    await db.commit()
    await db.refresh(permit)
    
    return schemas.WorkPermitResponse.from_orm(permit)


@router.post("/permits/{permit_id}/approve", response_model=schemas.WorkPermitResponse)
async def approve_work_permit(
    permit_id: UUID,
    approval: schemas.WorkPermitApproval,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 허가서 승인/반려"""
    permit = await db.get(models.ConfinedSpaceWorkPermit, permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업 허가서를 찾을 수 없습니다"
        )
    
    if permit.status != models.WorkPermitStatus.SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="제출된 상태의 허가서만 승인할 수 있습니다"
        )
    
    if approval.approved:
        permit.status = models.WorkPermitStatus.APPROVED
        permit.approved_by = current_user_id
        permit.approved_at = datetime.now()
    else:
        permit.status = models.WorkPermitStatus.CANCELLED
        if approval.comments:
            permit.safety_measures = permit.safety_measures or []
            permit.safety_measures.append(f"반려 사유: {approval.comments}")
    
    await db.commit()
    await db.refresh(permit)
    
    logger.info(f"작업 허가서 {'승인' if approval.approved else '반려'}: {permit.permit_number} by {current_user_id}")
    
    return schemas.WorkPermitResponse.from_orm(permit)


@router.post("/permits/{permit_id}/start")
async def start_work(
    permit_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 시작"""
    permit = await db.get(models.ConfinedSpaceWorkPermit, permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업 허가서를 찾을 수 없습니다"
        )
    
    if permit.status != models.WorkPermitStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="승인된 허가서만 작업을 시작할 수 있습니다"
        )
    
    permit.status = models.WorkPermitStatus.IN_PROGRESS
    permit.actual_start = datetime.now()
    
    await db.commit()
    
    return {"message": "작업이 시작되었습니다", "started_at": permit.actual_start}


@router.post("/permits/{permit_id}/complete")
async def complete_work(
    permit_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 완료"""
    permit = await db.get(models.ConfinedSpaceWorkPermit, permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업 허가서를 찾을 수 없습니다"
        )
    
    if permit.status != models.WorkPermitStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="진행 중인 작업만 완료할 수 있습니다"
        )
    
    permit.status = models.WorkPermitStatus.COMPLETED
    permit.actual_end = datetime.now()
    
    await db.commit()
    
    return {"message": "작업이 완료되었습니다", "completed_at": permit.actual_end}


# 가스 측정 관리
@router.post("/gas-measurements/", response_model=schemas.GasMeasurementResponse)
async def create_gas_measurement(
    measurement_data: schemas.GasMeasurementCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """가스 측정 기록 생성"""
    # 작업 허가서 확인
    permit = await db.get(models.ConfinedSpaceWorkPermit, measurement_data.work_permit_id)
    if not permit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="작업 허가서를 찾을 수 없습니다"
        )
    
    if permit.status != models.WorkPermitStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="진행 중인 작업에만 가스 측정을 기록할 수 있습니다"
        )
    
    # 가스 측정 기록 생성
    new_measurement = models.ConfinedSpaceGasMeasurement(
        **measurement_data.dict(),
        is_safe=measurement_data.is_safe
    )
    
    db.add(new_measurement)
    
    # 허가서의 최신 측정 결과 업데이트
    if not permit.gas_test_results:
        permit.gas_test_results = []
    
    permit.gas_test_results.append({
        "time": new_measurement.measurement_time.isoformat(),
        "oxygen": new_measurement.oxygen_level,
        "carbon_monoxide": new_measurement.carbon_monoxide,
        "hydrogen_sulfide": new_measurement.hydrogen_sulfide,
        "methane": new_measurement.methane,
        "is_safe": new_measurement.is_safe
    })
    
    await db.commit()
    await db.refresh(new_measurement)
    
    # 안전하지 않은 경우 경고
    if not new_measurement.is_safe:
        logger.warning(f"위험한 가스 농도 감지: Permit {permit.permit_number}, O2: {new_measurement.oxygen_level}%")
    
    return schemas.GasMeasurementResponse.from_orm(new_measurement)


@router.get("/gas-measurements/", response_model=List[schemas.GasMeasurementResponse])
async def get_gas_measurements(
    work_permit_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """작업 허가서의 가스 측정 기록 조회"""
    measurements = await db.execute(
        select(models.ConfinedSpaceGasMeasurement)
        .where(models.ConfinedSpaceGasMeasurement.work_permit_id == work_permit_id)
        .order_by(models.ConfinedSpaceGasMeasurement.measurement_time.desc())
    )
    measurements = measurements.scalars().all()
    
    return [schemas.GasMeasurementResponse.from_orm(m) for m in measurements]


# 안전 체크리스트
@router.post("/safety-checklists/", response_model=schemas.SafetyChecklistResponse)
async def create_safety_checklist(
    checklist_data: schemas.SafetyChecklistCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """안전 체크리스트 생성"""
    # 밀폐공간 확인
    space = await db.get(models.ConfinedSpace, checklist_data.confined_space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="밀폐공간을 찾을 수 없습니다"
        )
    
    # 체크리스트 생성
    new_checklist = models.ConfinedSpaceSafetyChecklist(
        **checklist_data.dict()
    )
    
    db.add(new_checklist)
    
    # 밀폐공간의 최근 점검일 업데이트
    space.last_inspection_date = new_checklist.inspection_date
    
    await db.commit()
    await db.refresh(new_checklist)
    
    return schemas.SafetyChecklistResponse.from_orm(new_checklist)


@router.get("/safety-checklists/", response_model=List[schemas.SafetyChecklistResponse])
async def get_safety_checklists(
    confined_space_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """밀폐공간의 안전 체크리스트 목록 조회"""
    checklists = await db.execute(
        select(models.ConfinedSpaceSafetyChecklist)
        .where(models.ConfinedSpaceSafetyChecklist.confined_space_id == confined_space_id)
        .offset(skip)
        .limit(limit)
        .order_by(models.ConfinedSpaceSafetyChecklist.inspection_date.desc())
    )
    checklists = checklists.scalars().all()
    
    return [schemas.SafetyChecklistResponse.from_orm(c) for c in checklists]


# 체크리스트 템플릿
@router.get("/checklist-template")
async def get_checklist_template(
    current_user_id: str = CurrentUserId
):
    """안전 체크리스트 템플릿 조회"""
    template = [
        {
            "category": "진입 전 조치",
            "items": [
                "작업 허가서 확인",
                "위험성 평가 실시",
                "안전 교육 실시",
                "감시인 배치",
                "비상 연락망 확인"
            ]
        },
        {
            "category": "환기 조치",
            "items": [
                "자연 환기 실시 (30분 이상)",
                "강제 환기 장비 설치",
                "환기 상태 확인",
                "환기구 막힘 확인"
            ]
        },
        {
            "category": "가스 측정",
            "items": [
                "산소 농도 측정 (18-23.5%)",
                "유해가스 농도 측정",
                "가연성 가스 측정",
                "측정 장비 교정 확인"
            ]
        },
        {
            "category": "안전 장비",
            "items": [
                "개인 보호구 착용",
                "안전대 및 구명줄 준비",
                "호흡용 보호구 준비",
                "비상 탈출 장비 준비",
                "통신 장비 준비"
            ]
        },
        {
            "category": "작업 중 조치",
            "items": [
                "연속 가스 모니터링",
                "정기적 휴식 및 교대",
                "비상 상황 대응 절차 숙지",
                "작업자 상태 지속 확인"
            ]
        }
    ]
    
    return {"template": template}