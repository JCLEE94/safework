# 요관리대상자 관리 API 핸들러
"""
요관리대상자 관리 시스템 API 엔드포인트
- 유소견자 관리
- 직업병 의심자 관리
- 특별관리 대상자
- 추적관찰 대상자
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, update
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta

from src.models.database import get_db
from src.models import at_risk_employee as models
from src.models.worker import Worker
from src.models.health import HealthExam
from src.schemas import at_risk_employee as schemas
from src.utils.auth_deps import CurrentUserId
from src.services.cache import CacheService, get_cache_service
from src.services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/at-risk-employees", tags=["at-risk-employees"])


# 요관리대상자 등록 및 관리
@router.post("/", response_model=schemas.AtRiskEmployeeResponse)
async def register_at_risk_employee(
    employee: schemas.AtRiskEmployeeCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """요관리대상자 등록"""
    # 중복 확인 (활성 상태인 동일 근로자)
    existing = await db.execute(
        select(models.AtRiskEmployee).where(
            and_(
                models.AtRiskEmployee.worker_id == employee.worker_id,
                models.AtRiskEmployee.is_active == True
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 등록된 요관리대상자입니다")
    
    # risk_factors 변환
    risk_factors_data = None
    if employee.risk_factors:
        risk_factors_data = employee.risk_factors.model_dump()
    
    db_employee = models.AtRiskEmployee(
        **employee.model_dump(exclude={"risk_factors"}),
        risk_factors=risk_factors_data,
        registered_by=employee.registered_by or current_user_id,
        registration_date=date.today()
    )
    
    db.add(db_employee)
    await db.commit()
    await db.refresh(db_employee)
    
    return db_employee


@router.get("/", response_model=List[schemas.AtRiskEmployeeResponse])
async def get_at_risk_employees(
    is_active: Optional[bool] = True,
    risk_category: Optional[schemas.RiskCategory] = None,
    management_level: Optional[schemas.ManagementLevel] = None,
    worker_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """요관리대상자 목록 조회"""
    query = select(models.AtRiskEmployee).options(
        selectinload(models.AtRiskEmployee.worker)
    )
    
    if is_active is not None:
        query = query.where(models.AtRiskEmployee.is_active == is_active)
    
    if risk_category:
        query = query.where(models.AtRiskEmployee.primary_risk_category == risk_category)
    
    if management_level:
        query = query.where(models.AtRiskEmployee.management_level == management_level)
    
    if worker_id:
        query = query.where(models.AtRiskEmployee.worker_id == worker_id)
    
    query = query.order_by(desc(models.AtRiskEmployee.severity_score))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    return employees


@router.get("/{employee_id}", response_model=schemas.AtRiskEmployeeResponse)
async def get_at_risk_employee(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """특정 요관리대상자 조회"""
    employee = await db.get(models.AtRiskEmployee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="요관리대상자를 찾을 수 없습니다")
    
    return employee


@router.put("/{employee_id}", response_model=schemas.AtRiskEmployeeResponse)
async def update_at_risk_employee(
    employee_id: int,
    employee_update: schemas.AtRiskEmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """요관리대상자 정보 수정"""
    employee = await db.get(models.AtRiskEmployee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="요관리대상자를 찾을 수 없습니다")
    
    update_data = employee_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(employee, key, value)
    
    employee.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(employee)
    
    return employee


@router.post("/{employee_id}/resolve")
async def resolve_at_risk_employee(
    employee_id: int,
    resolution_reason: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """요관리대상자 해제"""
    employee = await db.get(models.AtRiskEmployee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="요관리대상자를 찾을 수 없습니다")
    
    if not employee.is_active:
        raise HTTPException(status_code=400, detail="이미 해제된 대상자입니다")
    
    employee.is_active = False
    employee.current_status = "resolved"
    employee.resolution_date = date.today()
    employee.resolution_reason = resolution_reason
    
    await db.commit()
    
    return {"message": "요관리대상자가 해제되었습니다"}


# 관리 계획
@router.post("/management-plans/", response_model=schemas.RiskManagementPlanResponse)
async def create_management_plan(
    plan: schemas.RiskManagementPlanCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """관리 계획 생성"""
    # 대상자 확인
    employee = await db.get(models.AtRiskEmployee, plan.at_risk_employee_id)
    if not employee or not employee.is_active:
        raise HTTPException(status_code=404, detail="활성 요관리대상자를 찾을 수 없습니다")
    
    # 기존 활성 계획 확인
    existing = await db.execute(
        select(models.RiskManagementPlan).where(
            and_(
                models.RiskManagementPlan.at_risk_employee_id == plan.at_risk_employee_id,
                models.RiskManagementPlan.status == "active"
            )
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 활성 관리 계획이 있습니다")
    
    # JSON 필드 변환
    plan_data = plan.model_dump()
    if plan_data.get("planned_interventions"):
        plan_data["planned_interventions"] = [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in plan_data["planned_interventions"]
        ]
    if plan_data.get("monitoring_schedule"):
        plan_data["monitoring_schedule"] = plan_data["monitoring_schedule"].model_dump() if hasattr(plan_data["monitoring_schedule"], "model_dump") else plan_data["monitoring_schedule"]
    
    db_plan = models.RiskManagementPlan(**plan_data)
    
    db.add(db_plan)
    await db.commit()
    await db.refresh(db_plan)
    
    return db_plan


@router.get("/management-plans/", response_model=List[schemas.RiskManagementPlanResponse])
async def get_management_plans(
    at_risk_employee_id: Optional[int] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """관리 계획 목록 조회"""
    query = select(models.RiskManagementPlan)
    
    if at_risk_employee_id:
        query = query.where(models.RiskManagementPlan.at_risk_employee_id == at_risk_employee_id)
    
    if status:
        query = query.where(models.RiskManagementPlan.status == status)
    
    query = query.order_by(desc(models.RiskManagementPlan.created_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    plans = result.scalars().all()
    
    return plans


@router.put("/management-plans/{plan_id}/approve")
async def approve_management_plan(
    plan_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """관리 계획 승인"""
    plan = await db.get(models.RiskManagementPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="관리 계획을 찾을 수 없습니다")
    
    plan.approved_by = current_user_id
    plan.approved_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "관리 계획이 승인되었습니다"}


# 개입 활동
@router.post("/interventions/", response_model=schemas.RiskInterventionResponse)
async def create_intervention(
    intervention: schemas.RiskInterventionCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """개입 활동 기록"""
    # 대상자 확인
    employee = await db.get(models.AtRiskEmployee, intervention.at_risk_employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="요관리대상자를 찾을 수 없습니다")
    
    db_intervention = models.RiskIntervention(**intervention.model_dump())
    
    db.add(db_intervention)
    await db.commit()
    await db.refresh(db_intervention)
    
    # 후속조치 알림 예약
    if intervention.followup_required and intervention.followup_date:
        background_tasks.add_task(
            schedule_followup_reminder,
            employee.worker_id,
            intervention.followup_date,
            intervention.followup_notes
        )
    
    return db_intervention


@router.get("/interventions/", response_model=List[schemas.RiskInterventionResponse])
async def get_interventions(
    at_risk_employee_id: Optional[int] = None,
    intervention_type: Optional[schemas.InterventionType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    followup_required: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """개입 활동 목록 조회"""
    query = select(models.RiskIntervention)
    
    if at_risk_employee_id:
        query = query.where(models.RiskIntervention.at_risk_employee_id == at_risk_employee_id)
    
    if intervention_type:
        query = query.where(models.RiskIntervention.intervention_type == intervention_type)
    
    if start_date:
        query = query.where(models.RiskIntervention.intervention_date >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.where(models.RiskIntervention.intervention_date <= end_datetime)
    
    if followup_required is not None:
        query = query.where(models.RiskIntervention.followup_required == followup_required)
    
    query = query.order_by(desc(models.RiskIntervention.intervention_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    interventions = result.scalars().all()
    
    return interventions


# 모니터링
@router.post("/monitoring/", response_model=schemas.RiskMonitoringResponse)
async def create_monitoring_record(
    monitoring: schemas.RiskMonitoringCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """모니터링 기록 생성"""
    # JSON 필드 변환
    monitoring_data = monitoring.model_dump()
    if monitoring_data.get("health_indicators"):
        monitoring_data["health_indicators"] = monitoring_data["health_indicators"].model_dump() if hasattr(monitoring_data["health_indicators"], "model_dump") else monitoring_data["health_indicators"]
    if monitoring_data.get("lifestyle_factors"):
        monitoring_data["lifestyle_factors"] = monitoring_data["lifestyle_factors"].model_dump() if hasattr(monitoring_data["lifestyle_factors"], "model_dump") else monitoring_data["lifestyle_factors"]
    
    db_monitoring = models.RiskMonitoring(**monitoring_data)
    
    db.add(db_monitoring)
    await db.commit()
    await db.refresh(db_monitoring)
    
    # 상태 업데이트
    employee = await db.get(models.AtRiskEmployee, monitoring.at_risk_employee_id)
    if employee and monitoring.improvement_status:
        employee.updated_at = datetime.utcnow()
        await db.commit()
    
    return db_monitoring


@router.get("/monitoring/", response_model=List[schemas.RiskMonitoringResponse])
async def get_monitoring_records(
    at_risk_employee_id: Optional[int] = None,
    monitoring_type: Optional[str] = None,
    improvement_status: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """모니터링 기록 조회"""
    query = select(models.RiskMonitoring)
    
    if at_risk_employee_id:
        query = query.where(models.RiskMonitoring.at_risk_employee_id == at_risk_employee_id)
    
    if monitoring_type:
        query = query.where(models.RiskMonitoring.monitoring_type == monitoring_type)
    
    if improvement_status:
        query = query.where(models.RiskMonitoring.improvement_status == improvement_status)
    
    if start_date:
        query = query.where(models.RiskMonitoring.monitoring_date >= start_date)
    
    if end_date:
        query = query.where(models.RiskMonitoring.monitoring_date <= end_date)
    
    query = query.order_by(desc(models.RiskMonitoring.monitoring_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    records = result.scalars().all()
    
    return records


@router.get("/monitoring/overdue", response_model=List[Dict[str, Any]])
async def get_overdue_monitoring(
    days_overdue: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """모니터링 지연 대상자 조회"""
    cutoff_date = date.today() - timedelta(days=days_overdue)
    
    # 최근 모니터링 기록 서브쿼리
    latest_monitoring = select(
        models.RiskMonitoring.at_risk_employee_id,
        func.max(models.RiskMonitoring.monitoring_date).label("last_date")
    ).group_by(models.RiskMonitoring.at_risk_employee_id).subquery()
    
    # 지연된 대상자 조회
    query = select(
        models.AtRiskEmployee,
        latest_monitoring.c.last_date
    ).join(
        latest_monitoring,
        models.AtRiskEmployee.id == latest_monitoring.c.at_risk_employee_id
    ).where(
        and_(
            models.AtRiskEmployee.is_active == True,
            latest_monitoring.c.last_date < cutoff_date
        )
    )
    
    result = await db.execute(query)
    overdue_list = []
    
    for employee, last_date in result:
        overdue_list.append({
            "employee_id": employee.id,
            "worker_id": employee.worker_id,
            "risk_category": employee.primary_risk_category,
            "management_level": employee.management_level,
            "last_monitoring_date": last_date.isoformat() if last_date else None,
            "days_overdue": (date.today() - last_date).days if last_date else None
        })
    
    return overdue_list


# 통계 및 대시보드
@router.get("/statistics/{year}", response_model=schemas.RiskEmployeeStatisticsResponse)
async def get_statistics(
    year: int,
    month: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
    cache: CacheService = Depends(get_cache_service),
):
    """요관리대상자 통계"""
    cache_key = f"at_risk_stats:{year}:{month or 'all'}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # 기본 통계 계산
    if month:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    
    # 전체 요관리대상자
    total_query = select(func.count(models.AtRiskEmployee.id)).where(
        and_(
            models.AtRiskEmployee.registration_date <= end_date,
            or_(
                models.AtRiskEmployee.resolution_date == None,
                models.AtRiskEmployee.resolution_date >= start_date
            )
        )
    )
    total_at_risk = (await db.execute(total_query)).scalar() or 0
    
    # 신규 등록
    new_query = select(func.count(models.AtRiskEmployee.id)).where(
        and_(
            models.AtRiskEmployee.registration_date >= start_date,
            models.AtRiskEmployee.registration_date <= end_date
        )
    )
    new_registrations = (await db.execute(new_query)).scalar() or 0
    
    # 해제 건수
    resolved_query = select(func.count(models.AtRiskEmployee.id)).where(
        and_(
            models.AtRiskEmployee.resolution_date >= start_date,
            models.AtRiskEmployee.resolution_date <= end_date
        )
    )
    resolved_cases = (await db.execute(resolved_query)).scalar() or 0
    
    # 카테고리별 분류
    category_query = select(
        models.AtRiskEmployee.primary_risk_category,
        func.count(models.AtRiskEmployee.id)
    ).where(
        models.AtRiskEmployee.is_active == True
    ).group_by(models.AtRiskEmployee.primary_risk_category)
    
    category_result = await db.execute(category_query)
    category_breakdown = {row[0]: row[1] for row in category_result}
    
    # 관리 수준별 분류
    level_query = select(
        models.AtRiskEmployee.management_level,
        func.count(models.AtRiskEmployee.id)
    ).where(
        models.AtRiskEmployee.is_active == True
    ).group_by(models.AtRiskEmployee.management_level)
    
    level_result = await db.execute(level_query)
    management_level_breakdown = {row[0]: row[1] for row in level_result}
    
    # 개입 통계
    intervention_query = select(func.count(models.RiskIntervention.id)).where(
        and_(
            models.RiskIntervention.intervention_date >= datetime.combine(start_date, datetime.min.time()),
            models.RiskIntervention.intervention_date <= datetime.combine(end_date, datetime.max.time())
        )
    )
    total_interventions = (await db.execute(intervention_query)).scalar() or 0
    
    # 개선율 계산 (간단한 버전)
    improvement_query = select(func.count(models.RiskMonitoring.id)).where(
        and_(
            models.RiskMonitoring.monitoring_date >= start_date,
            models.RiskMonitoring.monitoring_date <= end_date,
            models.RiskMonitoring.improvement_status == "개선"
        )
    )
    improved_count = (await db.execute(improvement_query)).scalar() or 0
    
    total_monitoring_query = select(func.count(models.RiskMonitoring.id)).where(
        and_(
            models.RiskMonitoring.monitoring_date >= start_date,
            models.RiskMonitoring.monitoring_date <= end_date
        )
    )
    total_monitoring = (await db.execute(total_monitoring_query)).scalar() or 0
    
    improvement_rate = (improved_count / total_monitoring * 100) if total_monitoring > 0 else 0
    
    statistics = schemas.RiskEmployeeStatisticsResponse(
        id=0,  # Dummy ID
        year=year,
        month=month,
        total_at_risk=total_at_risk,
        new_registrations=new_registrations,
        resolved_cases=resolved_cases,
        category_breakdown=category_breakdown,
        management_level_breakdown=management_level_breakdown,
        total_interventions=total_interventions,
        improvement_rate=improvement_rate,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await cache.set(cache_key, statistics, ttl=3600)
    
    return statistics


@router.get("/dashboard/", response_model=schemas.AtRiskDashboard)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """요관리대상자 대시보드"""
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # 현재 활성 대상자
    active_query = select(func.count(models.AtRiskEmployee.id)).where(
        models.AtRiskEmployee.is_active == True
    )
    total_active = (await db.execute(active_query)).scalar() or 0
    
    # 관리 수준별
    level_query = select(
        models.AtRiskEmployee.management_level,
        func.count(models.AtRiskEmployee.id)
    ).where(
        models.AtRiskEmployee.is_active == True
    ).group_by(models.AtRiskEmployee.management_level)
    
    level_result = await db.execute(level_query)
    by_management_level = {row[0]: row[1] for row in level_result}
    
    # 위험 카테고리별
    category_query = select(
        models.AtRiskEmployee.primary_risk_category,
        func.count(models.AtRiskEmployee.id)
    ).where(
        models.AtRiskEmployee.is_active == True
    ).group_by(models.AtRiskEmployee.primary_risk_category)
    
    category_result = await db.execute(category_query)
    by_risk_category = {row[0]: row[1] for row in category_result}
    
    # 이번 달 신규
    new_query = select(func.count(models.AtRiskEmployee.id)).where(
        models.AtRiskEmployee.registration_date >= month_start
    )
    new_this_month = (await db.execute(new_query)).scalar() or 0
    
    # 이번 달 해제
    resolved_query = select(func.count(models.AtRiskEmployee.id)).where(
        models.AtRiskEmployee.resolution_date >= month_start
    )
    resolved_this_month = (await db.execute(resolved_query)).scalar() or 0
    
    # 이번 달 개입
    intervention_query = select(func.count(models.RiskIntervention.id)).where(
        models.RiskIntervention.intervention_date >= datetime.combine(month_start, datetime.min.time())
    )
    interventions_this_month = (await db.execute(intervention_query)).scalar() or 0
    
    # 모니터링 지연 (7일 이상)
    overdue_monitoring = await get_overdue_monitoring(7, db, current_user_id)
    
    # 고위험 사례 (severity_score >= 8)
    high_severity_query = select(
        models.AtRiskEmployee.id,
        models.AtRiskEmployee.worker_id,
        models.AtRiskEmployee.primary_risk_category,
        models.AtRiskEmployee.severity_score
    ).where(
        and_(
            models.AtRiskEmployee.is_active == True,
            models.AtRiskEmployee.severity_score >= 8
        )
    ).limit(10)
    
    high_severity_result = await db.execute(high_severity_query)
    high_severity_cases = [
        {
            "id": row[0],
            "worker_id": row[1],
            "risk_category": row[2],
            "severity_score": row[3]
        }
        for row in high_severity_result
    ]
    
    # 미처리 후속조치
    pending_followups_query = select(
        models.RiskIntervention.id,
        models.RiskIntervention.at_risk_employee_id,
        models.RiskIntervention.followup_date,
        models.RiskIntervention.followup_notes
    ).where(
        and_(
            models.RiskIntervention.followup_required == True,
            models.RiskIntervention.followup_date <= today
        )
    ).limit(10)
    
    pending_result = await db.execute(pending_followups_query)
    pending_followups = [
        {
            "intervention_id": row[0],
            "at_risk_employee_id": row[1],
            "followup_date": row[2].isoformat() if row[2] else None,
            "notes": row[3]
        }
        for row in pending_result
    ]
    
    # 월간 개선율
    monthly_improvement_rate = 0  # TODO: 실제 계산
    
    # 평균 관리 기간
    avg_duration_query = select(
        func.avg(
            func.extract('day', models.AtRiskEmployee.resolution_date - models.AtRiskEmployee.registration_date)
        )
    ).where(
        models.AtRiskEmployee.resolution_date != None
    )
    avg_duration_result = await db.execute(avg_duration_query)
    average_management_duration = avg_duration_result.scalar() or 0
    
    dashboard = schemas.AtRiskDashboard(
        total_active=total_active,
        by_management_level=by_management_level,
        by_risk_category=by_risk_category,
        new_this_month=new_this_month,
        resolved_this_month=resolved_this_month,
        interventions_this_month=interventions_this_month,
        overdue_monitoring=overdue_monitoring[:10],  # 상위 10개만
        high_severity_cases=high_severity_cases,
        pending_followups=pending_followups,
        monthly_improvement_rate=monthly_improvement_rate,
        average_management_duration=average_management_duration,
        intervention_effectiveness={}  # TODO: 개입 효과성 계산
    )
    
    return dashboard


@router.get("/{employee_id}/summary", response_model=schemas.AtRiskEmployeeSummary)
async def get_employee_summary(
    employee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """요관리대상자 종합 요약"""
    # 기본 정보
    employee = await db.get(models.AtRiskEmployee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="요관리대상자를 찾을 수 없습니다")
    
    # 현재 활성 계획
    plan_query = select(models.RiskManagementPlan).where(
        and_(
            models.RiskManagementPlan.at_risk_employee_id == employee_id,
            models.RiskManagementPlan.status == "active"
        )
    )
    plan_result = await db.execute(plan_query)
    current_plan = plan_result.scalar_one_or_none()
    
    # 최근 개입 활동 (5개)
    interventions_query = select(models.RiskIntervention).where(
        models.RiskIntervention.at_risk_employee_id == employee_id
    ).order_by(desc(models.RiskIntervention.intervention_date)).limit(5)
    
    interventions_result = await db.execute(interventions_query)
    recent_interventions = interventions_result.scalars().all()
    
    # 최신 모니터링
    monitoring_query = select(models.RiskMonitoring).where(
        models.RiskMonitoring.at_risk_employee_id == employee_id
    ).order_by(desc(models.RiskMonitoring.monitoring_date)).limit(1)
    
    monitoring_result = await db.execute(monitoring_query)
    latest_monitoring = monitoring_result.scalar_one_or_none()
    
    # 개선 추세 분석
    trend_query = select(models.RiskMonitoring.improvement_status).where(
        models.RiskMonitoring.at_risk_employee_id == employee_id
    ).order_by(desc(models.RiskMonitoring.monitoring_date)).limit(3)
    
    trend_result = await db.execute(trend_query)
    recent_trends = [row[0] for row in trend_result]
    
    if len(recent_trends) >= 2:
        if all(t == "개선" for t in recent_trends[:2]):
            improvement_trend = "개선중"
        elif all(t == "악화" for t in recent_trends[:2]):
            improvement_trend = "악화"
        else:
            improvement_trend = "정체"
    else:
        improvement_trend = "평가중"
    
    # 다음 조치사항
    next_actions = []
    
    # 예정된 모니터링
    if latest_monitoring and latest_monitoring.next_monitoring_date:
        next_actions.append({
            "type": "monitoring",
            "date": latest_monitoring.next_monitoring_date.isoformat(),
            "description": latest_monitoring.next_monitoring_focus or "정기 모니터링"
        })
    
    # 예정된 후속조치
    followup_query = select(models.RiskIntervention).where(
        and_(
            models.RiskIntervention.at_risk_employee_id == employee_id,
            models.RiskIntervention.followup_required == True,
            models.RiskIntervention.followup_date >= date.today()
        )
    ).order_by(models.RiskIntervention.followup_date).limit(3)
    
    followup_result = await db.execute(followup_query)
    for intervention in followup_result.scalars():
        next_actions.append({
            "type": "followup",
            "date": intervention.followup_date.isoformat(),
            "description": intervention.followup_notes or "후속 조치"
        })
    
    summary = schemas.AtRiskEmployeeSummary(
        employee=employee,
        current_plan=current_plan,
        recent_interventions=recent_interventions,
        latest_monitoring=latest_monitoring,
        improvement_trend=improvement_trend,
        next_actions=next_actions
    )
    
    return summary


# 백그라운드 태스크
async def schedule_followup_reminder(worker_id: int, followup_date: date, notes: str):
    """후속조치 알림 예약"""
    # TODO: 실제 알림 서비스 구현
    pass