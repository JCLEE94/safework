# 보건관리실 API 핸들러
"""
보건관리실 기능을 위한 API 엔드포인트
- 약품관리
- 측정기록
- 체성분분석
- 일반업무
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, date, timedelta

from src.models.database import get_db
from src.models import health_room as models
from src.schemas import health_room as schemas
from src.utils.auth_deps import CurrentUserId
from src.services.cache import CacheService, get_cache_service

router = APIRouter(prefix="/api/v1/health-room", tags=["health-room"])


# 약품 관리 엔드포인트
@router.get("/medications/", response_model=List[schemas.MedicationResponse])
async def get_medications(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    low_stock: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """약품 목록 조회"""
    query = select(models.Medication)
    
    if active_only:
        query = query.where(models.Medication.is_active == True)
    
    if low_stock:
        # 최소 재고 이하인 약품만
        query = query.where(
            models.Medication.current_stock <= models.Medication.minimum_stock
        )
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    medications = result.scalars().all()
    
    return medications


@router.post("/medications/", response_model=schemas.MedicationResponse)
async def create_medication(
    medication: schemas.MedicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """약품 등록"""
    db_medication = models.Medication(**medication.model_dump())
    
    db.add(db_medication)
    await db.commit()
    await db.refresh(db_medication)
    
    return db_medication


@router.get("/medications/{medication_id}", response_model=schemas.MedicationResponse)
async def get_medication(
    medication_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
    cache: CacheService = Depends(get_cache_service),
):
    """특정 약품 상세 조회"""
    cache_key = f"medication:{medication_id}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    query = select(models.Medication).where(models.Medication.id == medication_id)
    result = await db.execute(query)
    medication = result.scalar_one_or_none()
    
    if not medication:
        raise HTTPException(status_code=404, detail="약품을 찾을 수 없습니다")
    
    await cache.set(cache_key, medication, ttl=300)
    return medication


@router.put("/medications/{medication_id}", response_model=schemas.MedicationResponse)
async def update_medication(
    medication_id: int,
    medication_update: schemas.MedicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """약품 정보 수정"""
    query = select(models.Medication).where(models.Medication.id == medication_id)
    result = await db.execute(query)
    medication = result.scalar_one_or_none()
    
    if not medication:
        raise HTTPException(status_code=404, detail="약품을 찾을 수 없습니다")
    
    update_data = medication_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(medication, key, value)
    
    medication.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(medication)
    
    return medication


# 약품 불출 관리
@router.post("/medications/dispense/", response_model=schemas.MedicationDispensingResponse)
async def dispense_medication(
    dispensing: schemas.MedicationDispensingCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """약품 불출"""
    # 약품 확인
    medication_query = select(models.Medication).where(
        models.Medication.id == dispensing.medication_id
    )
    result = await db.execute(medication_query)
    medication = result.scalar_one_or_none()
    
    if not medication:
        raise HTTPException(status_code=404, detail="약품을 찾을 수 없습니다")
    
    if medication.current_stock < dispensing.quantity:
        raise HTTPException(status_code=400, detail="재고가 부족합니다")
    
    # 불출 기록 생성
    db_dispensing = models.MedicationDispensing(**dispensing.model_dump())
    db.add(db_dispensing)
    
    # 재고 차감
    medication.current_stock -= dispensing.quantity
    
    # 재고 변동 기록
    inventory_log = models.MedicationInventory(
        medication_id=medication.id,
        transaction_type="출고",
        quantity_change=-dispensing.quantity,
        quantity_after=medication.current_stock,
        reason=f"불출: {dispensing.reason or '일반 불출'}",
        created_by=dispensing.dispensed_by or current_user_id,
    )
    db.add(inventory_log)
    
    await db.commit()
    await db.refresh(db_dispensing)
    
    # medication 정보 포함해서 반환
    db_dispensing.medication = medication
    
    return db_dispensing


@router.get("/medications/dispensing/history", response_model=List[schemas.MedicationDispensingResponse])
async def get_dispensing_history(
    worker_id: Optional[int] = None,
    medication_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """약품 불출 이력 조회"""
    query = select(models.MedicationDispensing).options(
        selectinload(models.MedicationDispensing.medication)
    )
    
    if worker_id:
        query = query.where(models.MedicationDispensing.worker_id == worker_id)
    
    if medication_id:
        query = query.where(models.MedicationDispensing.medication_id == medication_id)
    
    if start_date:
        query = query.where(models.MedicationDispensing.dispensed_at >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.where(models.MedicationDispensing.dispensed_at <= end_datetime)
    
    query = query.order_by(desc(models.MedicationDispensing.dispensed_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    dispensing_records = result.scalars().all()
    
    return dispensing_records


# 재고 관리
@router.post("/medications/inventory/", response_model=schemas.MedicationInventoryResponse)
async def update_inventory(
    inventory: schemas.MedicationInventoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """재고 입출고 처리"""
    # 약품 확인
    medication_query = select(models.Medication).where(
        models.Medication.id == inventory.medication_id
    )
    result = await db.execute(medication_query)
    medication = result.scalar_one_or_none()
    
    if not medication:
        raise HTTPException(status_code=404, detail="약품을 찾을 수 없습니다")
    
    # 재고 업데이트
    new_stock = medication.current_stock + inventory.quantity_change
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="재고가 음수가 될 수 없습니다")
    
    medication.current_stock = new_stock
    
    # 재고 변동 기록
    db_inventory = models.MedicationInventory(
        **inventory.model_dump(),
        quantity_after=new_stock,
        created_by=inventory.created_by or current_user_id,
    )
    db.add(db_inventory)
    
    await db.commit()
    await db.refresh(db_inventory)
    
    db_inventory.medication = medication
    
    return db_inventory


@router.get("/medications/stock-alerts/", response_model=List[schemas.MedicationStockAlert])
async def get_stock_alerts(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """재고 부족 및 유효기간 임박 알림"""
    alerts = []
    
    # 재고 부족 약품
    low_stock_query = select(models.Medication).where(
        and_(
            models.Medication.is_active == True,
            models.Medication.current_stock <= models.Medication.minimum_stock
        )
    )
    result = await db.execute(low_stock_query)
    low_stock_meds = result.scalars().all()
    
    for med in low_stock_meds:
        stock_percentage = (med.current_stock / med.minimum_stock * 100) if med.minimum_stock > 0 else 0
        days_until_exp = None
        
        if med.expiration_date:
            days_until_exp = (med.expiration_date - date.today()).days
        
        alerts.append(schemas.MedicationStockAlert(
            medication=med,
            stock_percentage=stock_percentage,
            days_until_expiration=days_until_exp
        ))
    
    # 유효기간 30일 이내 약품
    expiry_date = date.today() + timedelta(days=30)
    expiry_query = select(models.Medication).where(
        and_(
            models.Medication.is_active == True,
            models.Medication.expiration_date != None,
            models.Medication.expiration_date <= expiry_date
        )
    )
    result = await db.execute(expiry_query)
    expiring_meds = result.scalars().all()
    
    for med in expiring_meds:
        if med not in low_stock_meds:  # 중복 제거
            days_until_exp = (med.expiration_date - date.today()).days
            stock_percentage = (med.current_stock / med.minimum_stock * 100) if med.minimum_stock > 0 else 100
            
            alerts.append(schemas.MedicationStockAlert(
                medication=med,
                stock_percentage=stock_percentage,
                days_until_expiration=days_until_exp
            ))
    
    return alerts


# 건강 측정 관리
@router.post("/measurements/", response_model=schemas.HealthMeasurementResponse)
async def create_measurement(
    measurement: schemas.HealthMeasurementCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강 측정 기록 생성"""
    db_measurement = models.HealthMeasurement(**measurement.model_dump())
    
    # 정상 범위 자동 판정 (측정 유형에 따라)
    if measurement.measurement_type == schemas.MeasurementType.BLOOD_PRESSURE:
        values = measurement.values
        systolic = values.get("systolic", 0)
        diastolic = values.get("diastolic", 0)
        
        # 고혈압 기준: 수축기 140 이상 또는 이완기 90 이상
        if systolic >= 140 or diastolic >= 90:
            db_measurement.is_normal = False
            db_measurement.abnormal_findings = f"고혈압 의심 (수축기: {systolic}, 이완기: {diastolic})"
    
    elif measurement.measurement_type == schemas.MeasurementType.BLOOD_SUGAR:
        value = measurement.values.get("value", 0)
        timing = measurement.values.get("timing", "공복")
        
        # 당뇨 기준: 공복 126 이상, 식후 200 이상
        if (timing == "공복" and value >= 126) or (timing == "식후" and value >= 200):
            db_measurement.is_normal = False
            db_measurement.abnormal_findings = f"당뇨 의심 ({timing} 혈당: {value})"
    
    db.add(db_measurement)
    await db.commit()
    await db.refresh(db_measurement)
    
    return db_measurement


@router.get("/measurements/", response_model=List[schemas.HealthMeasurementResponse])
async def get_measurements(
    worker_id: Optional[int] = None,
    measurement_type: Optional[schemas.MeasurementType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    abnormal_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강 측정 기록 조회"""
    query = select(models.HealthMeasurement)
    
    if worker_id:
        query = query.where(models.HealthMeasurement.worker_id == worker_id)
    
    if measurement_type:
        query = query.where(models.HealthMeasurement.measurement_type == measurement_type)
    
    if start_date:
        query = query.where(models.HealthMeasurement.measured_at >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.where(models.HealthMeasurement.measured_at <= end_datetime)
    
    if abnormal_only:
        query = query.where(models.HealthMeasurement.is_normal == False)
    
    query = query.order_by(desc(models.HealthMeasurement.measured_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    measurements = result.scalars().all()
    
    return measurements


@router.put("/measurements/{measurement_id}", response_model=schemas.HealthMeasurementResponse)
async def update_measurement(
    measurement_id: int,
    measurement_update: schemas.HealthMeasurementUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """건강 측정 기록 수정"""
    query = select(models.HealthMeasurement).where(
        models.HealthMeasurement.id == measurement_id
    )
    result = await db.execute(query)
    measurement = result.scalar_one_or_none()
    
    if not measurement:
        raise HTTPException(status_code=404, detail="측정 기록을 찾을 수 없습니다")
    
    update_data = measurement_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(measurement, key, value)
    
    measurement.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(measurement)
    
    return measurement


# 체성분 분석
@router.post("/body-composition/", response_model=schemas.BodyCompositionResponse)
async def create_body_composition(
    body_comp: schemas.BodyCompositionCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """체성분 분석 기록 생성"""
    # BMI 자동 계산
    if not body_comp.bmi and body_comp.height and body_comp.weight:
        height_m = body_comp.height / 100
        body_comp.bmi = body_comp.weight / (height_m ** 2)
    
    db_body_comp = models.BodyCompositionAnalysis(**body_comp.model_dump())
    
    # 체성분 측정 기록도 함께 생성
    measurement = models.HealthMeasurement(
        worker_id=body_comp.worker_id,
        measurement_type=schemas.MeasurementType.BODY_COMPOSITION,
        values={
            "weight": body_comp.weight,
            "height": body_comp.height,
            "bmi": body_comp.bmi,
            "body_fat_percentage": body_comp.body_fat_percentage,
            "muscle_mass": body_comp.muscle_mass
        },
        measured_by=current_user_id,
        is_normal=True  # 체성분은 별도 평가
    )
    db.add(measurement)
    await db.flush()
    
    db_body_comp.measurement_id = measurement.id
    db.add(db_body_comp)
    
    await db.commit()
    await db.refresh(db_body_comp)
    
    return db_body_comp


@router.get("/body-composition/worker/{worker_id}", response_model=List[schemas.BodyCompositionResponse])
async def get_worker_body_composition_history(
    worker_id: int,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근로자 체성분 분석 이력 조회"""
    query = select(models.BodyCompositionAnalysis).where(
        models.BodyCompositionAnalysis.worker_id == worker_id
    ).order_by(desc(models.BodyCompositionAnalysis.measured_at)).limit(limit)
    
    result = await db.execute(query)
    body_comps = result.scalars().all()
    
    return body_comps


# 보건실 방문 관리
@router.post("/visits/", response_model=schemas.HealthRoomVisitResponse)
async def create_visit(
    visit: schemas.HealthRoomVisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """보건실 방문 기록 생성"""
    db_visit = models.HealthRoomVisit(
        **visit.model_dump(),
        treated_by=visit.treated_by or current_user_id
    )
    
    db.add(db_visit)
    await db.commit()
    await db.refresh(db_visit)
    
    return db_visit


@router.get("/visits/", response_model=List[schemas.HealthRoomVisitResponse])
async def get_visits(
    worker_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    work_related: Optional[bool] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """보건실 방문 기록 조회"""
    query = select(models.HealthRoomVisit)
    
    if worker_id:
        query = query.where(models.HealthRoomVisit.worker_id == worker_id)
    
    if start_date:
        query = query.where(models.HealthRoomVisit.visit_datetime >= start_date)
    
    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.where(models.HealthRoomVisit.visit_datetime <= end_datetime)
    
    if work_related is not None:
        query = query.where(models.HealthRoomVisit.work_related == work_related)
    
    query = query.order_by(desc(models.HealthRoomVisit.visit_datetime))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    visits = result.scalars().all()
    
    return visits


# 통계 및 대시보드
@router.get("/statistics/", response_model=schemas.HealthRoomStatistics)
async def get_health_room_statistics(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
    cache: CacheService = Depends(get_cache_service),
):
    """보건실 통계 조회"""
    cache_key = "health_room_statistics"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    today = date.today()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # 방문 통계
    today_visits_query = select(func.count(models.HealthRoomVisit.id)).where(
        func.date(models.HealthRoomVisit.visit_datetime) == today
    )
    week_visits_query = select(func.count(models.HealthRoomVisit.id)).where(
        models.HealthRoomVisit.visit_datetime >= week_ago
    )
    month_visits_query = select(func.count(models.HealthRoomVisit.id)).where(
        models.HealthRoomVisit.visit_datetime >= month_ago
    )
    
    today_visits = (await db.execute(today_visits_query)).scalar() or 0
    week_visits = (await db.execute(week_visits_query)).scalar() or 0
    month_visits = (await db.execute(month_visits_query)).scalar() or 0
    
    # 주요 호소 증상 (최근 30일)
    complaints_query = select(
        models.HealthRoomVisit.chief_complaint,
        func.count(models.HealthRoomVisit.id).label("count")
    ).where(
        and_(
            models.HealthRoomVisit.visit_datetime >= month_ago,
            models.HealthRoomVisit.chief_complaint != None
        )
    ).group_by(
        models.HealthRoomVisit.chief_complaint
    ).order_by(
        desc("count")
    ).limit(10)
    
    complaints_result = await db.execute(complaints_query)
    common_complaints = [
        {"complaint": row[0], "count": row[1]}
        for row in complaints_result
    ]
    
    # 약품 사용량 (최근 30일)
    medication_query = select(
        models.Medication.name,
        models.Medication.type,
        func.sum(models.MedicationDispensing.quantity).label("total_quantity")
    ).join(
        models.MedicationDispensing,
        models.Medication.id == models.MedicationDispensing.medication_id
    ).where(
        models.MedicationDispensing.dispensed_at >= month_ago
    ).group_by(
        models.Medication.id,
        models.Medication.name,
        models.Medication.type
    ).order_by(
        desc("total_quantity")
    ).limit(10)
    
    medication_result = await db.execute(medication_query)
    medication_usage = [
        {
            "name": row[0],
            "type": row[1],
            "total_quantity": row[2]
        }
        for row in medication_result
    ]
    
    # 측정 유형별 건수 (최근 30일)
    measurement_query = select(
        models.HealthMeasurement.measurement_type,
        func.count(models.HealthMeasurement.id).label("count")
    ).where(
        models.HealthMeasurement.measured_at >= month_ago
    ).group_by(
        models.HealthMeasurement.measurement_type
    )
    
    measurement_result = await db.execute(measurement_query)
    measurement_summary = {
        row[0]: row[1]
        for row in measurement_result
    }
    
    statistics = schemas.HealthRoomStatistics(
        total_visits_today=today_visits,
        total_visits_week=week_visits,
        total_visits_month=month_visits,
        common_complaints=common_complaints,
        medication_usage=medication_usage,
        measurement_summary=measurement_summary
    )
    
    await cache.set(cache_key, statistics, ttl=300)  # 5분 캐시
    
    return statistics