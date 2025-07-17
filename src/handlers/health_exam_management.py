# 건강검진 관리 시스템 API 핸들러
"""
건강검진 관리 시스템 API 엔드포인트
- 건강검진 계획
- 예약 관리 개선
- 차트 관리
- 결과 추적
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import json

from src.models.database import get_db
from src.models import health_exam_management as models
from src.models.worker import Worker
from src.schemas import health_exam_management as schemas
from src.utils.auth_deps import CurrentUserId
from src.services.cache import CacheService, get_cache_service
from src.services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/health-exam-management", tags=["health-exam-management"])


# 건강검진 계획 관리
@router.post("/plans/", response_model=schemas.HealthExamPlanResponse)
async def create_exam_plan(
    plan: schemas.HealthExamPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강검진 계획 생성"""
    # 동일 연도 계획 중복 확인
    existing_plan = await db.execute(
        select(models.HealthExamPlan).where(
            and_(
                models.HealthExamPlan.plan_year == plan.plan_year,
                models.HealthExamPlan.plan_status != schemas.ExamPlanStatus.CANCELLED
            )
        )
    )
    if existing_plan.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"{plan.plan_year}년도 계획이 이미 존재합니다")
    
    db_plan = models.HealthExamPlan(**plan.model_dump())
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    
    return db_plan


@router.get("/plans/", response_model=List[schemas.HealthExamPlanResponse])
async def get_exam_plans(
    year: Optional[int] = None,
    status: Optional[schemas.ExamPlanStatus] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강검진 계획 목록 조회"""
    query = select(models.HealthExamPlan)
    
    if year:
        query = query.where(models.HealthExamPlan.plan_year == year)
    
    if status:
        query = query.where(models.HealthExamPlan.plan_status == status)
    
    query = query.order_by(desc(models.HealthExamPlan.plan_year))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    return plans


@router.get("/plans/{plan_id}", response_model=schemas.HealthExamPlanResponse)
async def get_exam_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """특정 건강검진 계획 조회"""
    plan = await db.get(models.HealthExamPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="검진 계획을 찾을 수 없습니다")
    
    return plan


@router.put("/plans/{plan_id}", response_model=schemas.HealthExamPlanResponse)
async def update_exam_plan(
    plan_id: int,
    plan_update: schemas.HealthExamPlanUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강검진 계획 수정"""
    plan = await db.get(models.HealthExamPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="검진 계획을 찾을 수 없습니다")
    
    if plan.plan_status == schemas.ExamPlanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="완료된 계획은 수정할 수 없습니다")
    
    update_data = plan_update.model_dump(exclude_unset=True)
    
    # 승인 처리
    if update_data.get("plan_status") == schemas.ExamPlanStatus.APPROVED:
        update_data["approved_by"] = current_user_id
        update_data["approved_at"] = datetime.utcnow()
    
    for key, value in update_data.items():
        setattr(plan, key, value)
    
    plan.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(plan)
    
    return plan


@router.post("/plans/{plan_id}/approve", response_model=schemas.HealthExamPlanResponse)
async def approve_exam_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강검진 계획 승인"""
    plan = await db.get(models.HealthExamPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="검진 계획을 찾을 수 없습니다")
    
    if plan.plan_status != schemas.ExamPlanStatus.DRAFT:
        raise HTTPException(status_code=400, detail="초안 상태의 계획만 승인할 수 있습니다")
    
    plan.plan_status = schemas.ExamPlanStatus.APPROVED
    plan.approved_by = current_user_id
    plan.approved_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(plan)
    
    return plan


# 검진 대상자 관리
@router.post("/targets/", response_model=schemas.HealthExamTargetResponse)
async def create_exam_target(
    target: schemas.HealthExamTargetCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 대상자 등록"""
    # 중복 확인
    existing = await db.execute(
        select(models.HealthExamTarget).where(
            and_(
                models.HealthExamTarget.plan_id == target.plan_id,
                models.HealthExamTarget.worker_id == target.worker_id
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 등록된 대상자입니다")
    
    db_target = models.HealthExamTarget(**target.model_dump())
    
    # 다음 검진 예정일 계산
    if target.last_exam_date:
        db_target.next_exam_due_date = target.last_exam_date + timedelta(days=30 * target.exam_cycle_months)
    
    db.add(db_target)
    await db.commit()
    await db.refresh(db_target)
    
    return db_target


@router.post("/targets/bulk", response_model=List[schemas.HealthExamTargetResponse])
async def create_exam_targets_bulk(
    plan_id: int,
    worker_ids: List[int],
    exam_categories: List[schemas.ExamCategory],
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 대상자 일괄 등록"""
    created_targets = []
    
    for worker_id in worker_ids:
        # 중복 체크
        existing = await db.execute(
            select(models.HealthExamTarget).where(
                and_(
                    models.HealthExamTarget.plan_id == plan_id,
                    models.HealthExamTarget.worker_id == worker_id
                )
            )
        )
        if existing.scalar_one_or_none():
            continue
        
        target = models.HealthExamTarget(
            plan_id=plan_id,
            worker_id=worker_id,
            exam_categories=exam_categories,
            general_exam_required=schemas.ExamCategory.GENERAL_REGULAR in exam_categories,
            special_exam_required=any(cat.startswith("특수") for cat in exam_categories),
            night_work_exam_required=schemas.ExamCategory.NIGHT_WORK in exam_categories,
        )
        
        db.add(target)
        created_targets.append(target)
    
    await db.commit()
    
    # Refresh all targets
    for target in created_targets:
        await db.refresh(target)
    
    return created_targets


@router.get("/targets/", response_model=List[schemas.HealthExamTargetResponse])
async def get_exam_targets(
    plan_id: Optional[int] = None,
    worker_id: Optional[int] = None,
    is_completed: Optional[bool] = None,
    exam_category: Optional[schemas.ExamCategory] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 대상자 목록 조회"""
    query = select(models.HealthExamTarget)
    
    if plan_id:
        query = query.where(models.HealthExamTarget.plan_id == plan_id)
    
    if worker_id:
        query = query.where(models.HealthExamTarget.worker_id == worker_id)
    
    if is_completed is not None:
        query = query.where(models.HealthExamTarget.is_completed == is_completed)
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    targets = result.scalars().all()
    
    # Filter by exam_category if provided (JSON field)
    if exam_category:
        targets = [t for t in targets if exam_category in (t.exam_categories or [])]
    
    return targets


# 검진 일정 관리
@router.post("/schedules/", response_model=schemas.HealthExamScheduleResponse)
async def create_exam_schedule(
    schedule: schemas.HealthExamScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 일정 생성"""
    db_schedule = models.HealthExamSchedule(
        **schedule.model_dump(),
        available_slots=schedule.total_capacity
    )
    
    db.add(db_schedule)
    await db.commit()
    await db.refresh(db_schedule)
    
    return db_schedule


@router.get("/schedules/", response_model=List[schemas.HealthExamScheduleResponse])
async def get_exam_schedules(
    plan_id: Optional[int] = None,
    institution_name: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 일정 목록 조회"""
    query = select(models.HealthExamSchedule)
    
    if plan_id:
        query = query.where(models.HealthExamSchedule.plan_id == plan_id)
    
    if institution_name:
        query = query.where(models.HealthExamSchedule.institution_name.contains(institution_name))
    
    if start_date:
        query = query.where(models.HealthExamSchedule.schedule_date >= start_date)
    
    if end_date:
        query = query.where(models.HealthExamSchedule.schedule_date <= end_date)
    
    if available_only:
        query = query.where(
            and_(
                models.HealthExamSchedule.is_active == True,
                models.HealthExamSchedule.is_full == False
            )
        )
    
    query = query.order_by(models.HealthExamSchedule.schedule_date)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    schedules = result.scalars().all()
    
    return schedules


# 검진 예약 관리
@router.post("/reservations/", response_model=schemas.HealthExamReservationResponse)
async def create_exam_reservation(
    reservation: schemas.HealthExamReservationCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 예약 생성"""
    # 일정 확인
    schedule = await db.get(models.HealthExamSchedule, reservation.schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail="검진 일정을 찾을 수 없습니다")
    
    if schedule.is_full:
        raise HTTPException(status_code=400, detail="해당 일정이 마감되었습니다")
    
    # 중복 예약 확인
    existing = await db.execute(
        select(models.HealthExamReservation).where(
            and_(
                models.HealthExamReservation.schedule_id == reservation.schedule_id,
                models.HealthExamReservation.worker_id == reservation.worker_id,
                models.HealthExamReservation.is_cancelled == False
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 예약이 존재합니다")
    
    # 예약번호 생성
    reservation_number = f"HE{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    
    db_reservation = models.HealthExamReservation(
        **reservation.model_dump(),
        reservation_number=reservation_number
    )
    
    # 일정 업데이트
    schedule.reserved_count += 1
    schedule.available_slots = schedule.total_capacity - schedule.reserved_count
    if schedule.available_slots <= 0:
        schedule.is_full = True
    
    db.add(db_reservation)
    await db.commit()
    await db.refresh(db_reservation)
    
    # 예약 확인 알림 발송 (백그라운드)
    if reservation.contact_email or reservation.contact_phone:
        background_tasks.add_task(
            send_reservation_confirmation,
            db_reservation,
            schedule
        )
    
    return db_reservation


@router.get("/reservations/", response_model=List[schemas.HealthExamReservationResponse])
async def get_exam_reservations(
    schedule_id: Optional[int] = None,
    worker_id: Optional[int] = None,
    status: Optional[str] = None,
    reservation_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 예약 목록 조회"""
    query = select(models.HealthExamReservation).options(
        selectinload(models.HealthExamReservation.schedule)
    )
    
    if schedule_id:
        query = query.where(models.HealthExamReservation.schedule_id == schedule_id)
    
    if worker_id:
        query = query.where(models.HealthExamReservation.worker_id == worker_id)
    
    if status:
        query = query.where(models.HealthExamReservation.status == status)
    
    query = query.where(models.HealthExamReservation.is_cancelled == False)
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    reservations = result.scalars().all()
    
    return reservations


@router.put("/reservations/{reservation_id}/cancel")
async def cancel_reservation(
    reservation_id: int,
    cancellation_reason: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """예약 취소"""
    reservation = await db.get(models.HealthExamReservation, reservation_id)
    if not reservation:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다")
    
    if reservation.is_cancelled:
        raise HTTPException(status_code=400, detail="이미 취소된 예약입니다")
    
    reservation.is_cancelled = True
    reservation.cancelled_at = datetime.utcnow()
    reservation.cancellation_reason = cancellation_reason
    reservation.status = "cancelled"
    
    # 일정 업데이트
    schedule = await db.get(models.HealthExamSchedule, reservation.schedule_id)
    if schedule:
        schedule.reserved_count -= 1
        schedule.available_slots = schedule.total_capacity - schedule.reserved_count
        schedule.is_full = False
    
    await db.commit()
    
    return {"message": "예약이 취소되었습니다"}


# 건강검진 차트 관리
@router.post("/charts/", response_model=schemas.HealthExamChartResponse)
async def create_exam_chart(
    chart: schemas.HealthExamChartCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강검진 차트 생성"""
    # 차트번호 생성
    chart_number = f"HC{datetime.now().strftime('%Y%m%d')}{uuid.uuid4().hex[:6].upper()}"
    
    # JSON 필드 직렬화
    chart_data = chart.model_dump()
    if chart_data.get("medical_history"):
        chart_data["medical_history"] = chart_data["medical_history"].model_dump() if hasattr(chart_data["medical_history"], "model_dump") else chart_data["medical_history"]
    if chart_data.get("lifestyle_habits"):
        chart_data["lifestyle_habits"] = chart_data["lifestyle_habits"].model_dump() if hasattr(chart_data["lifestyle_habits"], "model_dump") else chart_data["lifestyle_habits"]
    
    db_chart = models.HealthExamChart(
        **chart_data,
        chart_number=chart_number
    )
    
    db.add(db_chart)
    await db.commit()
    await db.refresh(db_chart)
    
    return db_chart


@router.get("/charts/worker/{worker_id}", response_model=List[schemas.HealthExamChartResponse])
async def get_worker_charts(
    worker_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근로자별 차트 목록 조회"""
    query = select(models.HealthExamChart).where(
        models.HealthExamChart.worker_id == worker_id
    ).order_by(desc(models.HealthExamChart.exam_date)).limit(limit)
    
    result = await db.execute(query)
    charts = result.scalars().all()
    
    return charts


@router.put("/charts/{chart_id}/sign")
async def sign_chart(
    chart_id: int,
    signature: str,  # Base64 encoded signature
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """차트 서명"""
    chart = await db.get(models.HealthExamChart, chart_id)
    if not chart:
        raise HTTPException(status_code=404, detail="차트를 찾을 수 없습니다")
    
    chart.worker_signature = signature
    chart.signed_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "서명이 완료되었습니다"}


# 검진 결과 관리
@router.post("/results/", response_model=schemas.HealthExamResultResponse)
async def create_exam_result(
    result: schemas.HealthExamResultCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 결과 등록"""
    # JSON 필드 처리
    result_data = result.model_dump()
    if result_data.get("abnormal_findings"):
        result_data["abnormal_findings"] = [
            finding.model_dump() if hasattr(finding, "model_dump") else finding
            for finding in result_data["abnormal_findings"]
        ]
    if result_data.get("health_guidance"):
        result_data["health_guidance"] = result_data["health_guidance"].model_dump() if hasattr(result_data["health_guidance"], "model_dump") else result_data["health_guidance"]
    
    db_result = models.HealthExamResult(**result_data)
    
    db.add(db_result)
    await db.commit()
    await db.refresh(db_result)
    
    # 대상자 완료 처리
    if result.worker_id:
        target = await db.execute(
            select(models.HealthExamTarget).where(
                models.HealthExamTarget.worker_id == result.worker_id
            ).order_by(desc(models.HealthExamTarget.created_at)).limit(1)
        )
        target_obj = target.scalar_one_or_none()
        if target_obj:
            target_obj.is_completed = True
            target_obj.completed_date = date.today()
    
    await db.commit()
    
    return db_result


@router.get("/results/", response_model=List[schemas.HealthExamResultResponse])
async def get_exam_results(
    worker_id: Optional[int] = None,
    overall_result: Optional[str] = None,
    followup_required: Optional[bool] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """검진 결과 목록 조회"""
    query = select(models.HealthExamResult)
    
    if worker_id:
        query = query.where(models.HealthExamResult.worker_id == worker_id)
    
    if overall_result:
        query = query.where(models.HealthExamResult.overall_result == overall_result)
    
    if followup_required is not None:
        query = query.where(models.HealthExamResult.followup_required == followup_required)
    
    if start_date:
        query = query.where(models.HealthExamResult.result_received_date >= start_date)
    
    if end_date:
        query = query.where(models.HealthExamResult.result_received_date <= end_date)
    
    query = query.order_by(desc(models.HealthExamResult.created_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    results = result.scalars().all()
    
    return results


@router.put("/results/{result_id}/confirm")
async def confirm_result(
    result_id: int,
    feedback: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근로자 결과 확인"""
    result = await db.get(models.HealthExamResult, result_id)
    if not result:
        raise HTTPException(status_code=404, detail="결과를 찾을 수 없습니다")
    
    result.worker_confirmed = True
    result.worker_confirmed_at = datetime.utcnow()
    if feedback:
        result.worker_feedback = feedback
    
    await db.commit()
    
    return {"message": "결과 확인이 완료되었습니다"}


# 통계 및 대시보드
@router.get("/statistics/{year}", response_model=schemas.HealthExamStatisticsResponse)
async def get_exam_statistics(
    year: int,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
    cache: CacheService = Depends(get_cache_service),
):
    """건강검진 통계 조회"""
    cache_key = f"health_exam_stats:{year}:{month or 'all'}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # 통계 계산 (간략화된 버전)
    query = select(models.HealthExamTarget).join(
        models.HealthExamPlan
    ).where(
        models.HealthExamPlan.plan_year == year
    )
    
    result = await db.execute(query)
    targets = result.scalars().all()
    
    total_targets = len(targets)
    completed_count = len([t for t in targets if t.is_completed])
    completion_rate = (completed_count / total_targets * 100) if total_targets > 0 else 0
    
    # 결과별 통계
    results_query = select(
        models.HealthExamResult.overall_result,
        func.count(models.HealthExamResult.id)
    ).group_by(models.HealthExamResult.overall_result)
    
    if month:
        results_query = results_query.where(
            func.extract('month', models.HealthExamResult.created_at) == month
        )
    
    results = await db.execute(results_query)
    result_counts = {row[0]: row[1] for row in results}
    
    statistics = schemas.HealthExamStatisticsResponse(
        id=0,  # Dummy ID for response
        year=year,
        month=month,
        total_targets=total_targets,
        completed_count=completed_count,
        completion_rate=completion_rate,
        result_a_count=result_counts.get('A', 0),
        result_b_count=result_counts.get('B', 0),
        result_c_count=result_counts.get('C', 0),
        result_d_count=result_counts.get('D', 0),
        result_r_count=result_counts.get('R', 0),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await cache.set(cache_key, statistics, ttl=3600)  # 1시간 캐시
    
    return statistics


@router.get("/dashboard/", response_model=schemas.HealthExamDashboard)
async def get_exam_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강검진 대시보드 데이터"""
    current_year = datetime.now().year
    
    # 현재 연도 계획
    plan_result = await db.execute(
        select(models.HealthExamPlan).where(
            models.HealthExamPlan.plan_year == current_year
        )
    )
    current_plan = plan_result.scalar_one_or_none()
    
    # 진행 현황
    targets_result = await db.execute(
        select(models.HealthExamTarget).join(
            models.HealthExamPlan
        ).where(
            models.HealthExamPlan.plan_year == current_year
        )
    )
    targets = targets_result.scalars().all()
    
    total_targets = len(targets)
    completed_count = len([t for t in targets if t.is_completed])
    pending_count = total_targets - completed_count
    
    # 이번달/다음달 예정
    today = date.today()
    next_month = today.replace(day=1) + timedelta(days=32)
    next_month = next_month.replace(day=1)
    
    this_month_query = select(func.count(models.HealthExamSchedule.id)).where(
        and_(
            func.extract('year', models.HealthExamSchedule.schedule_date) == today.year,
            func.extract('month', models.HealthExamSchedule.schedule_date) == today.month
        )
    )
    this_month_result = await db.execute(this_month_query)
    this_month_scheduled = this_month_result.scalar() or 0
    
    # 미검진자 목록 (상위 10명)
    overdue_query = select(
        models.HealthExamTarget.worker_id,
        models.HealthExamTarget.next_exam_due_date
    ).where(
        and_(
            models.HealthExamTarget.is_completed == False,
            models.HealthExamTarget.next_exam_due_date < today
        )
    ).limit(10)
    
    overdue_result = await db.execute(overdue_query)
    overdue_workers = [
        {
            "worker_id": row[0],
            "due_date": row[1].isoformat() if row[1] else None
        }
        for row in overdue_result
    ]
    
    dashboard = schemas.HealthExamDashboard(
        current_year_plan=current_plan,
        total_targets=total_targets,
        completed_count=completed_count,
        in_progress_count=0,  # TODO: 실제 진행중 계산
        pending_count=pending_count,
        this_month_scheduled=this_month_scheduled,
        next_month_scheduled=0,  # TODO: 다음달 계산
        completion_rate=(completed_count / total_targets * 100) if total_targets > 0 else 0,
        abnormal_rate=0,  # TODO: 이상소견율 계산
        followup_rate=0,  # TODO: 추적검사율 계산
        overdue_workers=overdue_workers,
        upcoming_deadlines=[],  # TODO: 구현
        pending_results=[]  # TODO: 구현
    )
    
    return dashboard


# 백그라운드 태스크
async def send_reservation_confirmation(reservation, schedule):
    """예약 확인 알림 발송"""
    # TODO: 실제 알림 서비스 구현
    pass