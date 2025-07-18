"""
뇌심혈관계 관리 API 핸들러
Cardiovascular management API handlers
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta, date
from uuid import UUID
import math

from src.config.database import get_db
from src.models import cardiovascular as models
from src.schemas import cardiovascular as schemas
from src.utils.auth_deps import CurrentUserId
from src.services.cache import CacheService, get_cache_service
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1/cardiovascular", tags=["뇌심혈관계관리"])


# 위험도 계산 유틸리티
def calculate_cardiovascular_risk(
    age: int,
    gender: str,
    systolic_bp: int,
    cholesterol: float,
    smoking: bool = False,
    diabetes: bool = False,
    hypertension: bool = False
) -> dict:
    """Framingham Risk Score를 기반으로 한 심혈관 위험도 계산"""
    
    # 기본 점수 (나이)
    if gender.lower() == "male":
        if age < 35:
            age_score = -9
        elif age < 40:
            age_score = -4
        elif age < 45:
            age_score = 0
        elif age < 50:
            age_score = 3
        elif age < 55:
            age_score = 6
        elif age < 60:
            age_score = 8
        elif age < 65:
            age_score = 10
        elif age < 70:
            age_score = 11
        elif age < 75:
            age_score = 12
        else:
            age_score = 13
    else:  # female
        if age < 35:
            age_score = -7
        elif age < 40:
            age_score = -3
        elif age < 45:
            age_score = 0
        elif age < 50:
            age_score = 3
        elif age < 55:
            age_score = 6
        elif age < 60:
            age_score = 8
        elif age < 65:
            age_score = 10
        elif age < 70:
            age_score = 12
        elif age < 75:
            age_score = 14
        else:
            age_score = 16
    
    # 콜레스테롤 점수
    if cholesterol < 160:
        chol_score = 0
    elif cholesterol < 200:
        chol_score = 4
    elif cholesterol < 240:
        chol_score = 7
    elif cholesterol < 280:
        chol_score = 9
    else:
        chol_score = 11
    
    # 혈압 점수
    if systolic_bp < 120:
        bp_score = 0
    elif systolic_bp < 130:
        bp_score = 1
    elif systolic_bp < 140:
        bp_score = 2
    elif systolic_bp < 160:
        bp_score = 3
    else:
        bp_score = 4
    
    # 위험 요인 점수
    risk_score = age_score + chol_score + bp_score
    if smoking:
        risk_score += 4
    if diabetes:
        risk_score += 5
    if hypertension:
        risk_score += 2
    
    # 10년 위험도 계산 (근사치)
    if risk_score < 0:
        ten_year_risk = 1
    elif risk_score < 5:
        ten_year_risk = 2
    elif risk_score < 10:
        ten_year_risk = 5
    elif risk_score < 15:
        ten_year_risk = 10
    elif risk_score < 20:
        ten_year_risk = 20
    else:
        ten_year_risk = 30
    
    # 위험도 수준 결정 (Korean string values directly)
    if ten_year_risk < 5:
        risk_level = "낮음"
    elif ten_year_risk < 10:
        risk_level = "보통"
    elif ten_year_risk < 20:
        risk_level = "높음"
    else:
        risk_level = "매우높음"
    
    # 권고사항 생성
    recommendations = []
    if smoking:
        recommendations.append("금연")
    if systolic_bp >= 140:
        recommendations.append("혈압 관리")
    if cholesterol >= 240:
        recommendations.append("콜레스테롤 관리")
    if diabetes:
        recommendations.append("혈당 관리")
    
    recommendations.extend([
        "규칙적인 운동",
        "건강한 식단 유지",
        "정기적인 건강검진"
    ])
    
    # 다음 평가까지 기간 (개월)
    if risk_level == "매우높음":
        next_assessment_months = 3
    elif risk_level == "높음":
        next_assessment_months = 6
    else:
        next_assessment_months = 12
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "ten_year_risk": ten_year_risk,
        "recommendations": recommendations,
        "next_assessment_months": next_assessment_months
    }


# 위험도 계산 API
@router.post("/risk-calculation", response_model=schemas.RiskCalculationResponse)
async def calculate_risk(
    request: schemas.RiskCalculationRequest,
    current_user_id: str = CurrentUserId
):
    """심혈관 위험도 계산"""
    result = calculate_cardiovascular_risk(
        age=request.age,
        gender=request.gender,
        systolic_bp=request.systolic_bp,
        cholesterol=request.cholesterol,
        smoking=request.smoking,
        diabetes=request.diabetes,
        hypertension=request.hypertension
    )
    
    return schemas.RiskCalculationResponse(**result)


# 위험도 평가 관리
@router.get("/assessments/", response_model=List[schemas.CardiovascularRiskAssessmentResponse])
async def get_risk_assessments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    worker_id: Optional[str] = None,
    risk_level: Optional[str] = None,  # Changed from enum to string
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """위험도 평가 목록 조회"""
    cache_key = f"risk_assessments:{skip}:{limit}:{worker_id}:{risk_level}:{date_from}:{date_to}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    query = select(models.CardiovascularRiskAssessment)
    
    # 필터 적용
    if worker_id:
        query = query.where(models.CardiovascularRiskAssessment.worker_id == worker_id)
    if risk_level:
        query = query.where(models.CardiovascularRiskAssessment.risk_level == risk_level)
    if date_from:
        query = query.where(models.CardiovascularRiskAssessment.assessment_date >= date_from)
    if date_to:
        query = query.where(models.CardiovascularRiskAssessment.assessment_date <= date_to)
    
    query = query.offset(skip).limit(limit).order_by(
        models.CardiovascularRiskAssessment.assessment_date.desc()
    )
    
    result = await db.execute(query)
    assessments = result.scalars().all()
    
    response = [schemas.CardiovascularRiskAssessmentResponse.from_orm(assessment) 
               for assessment in assessments]
    await cache.set(cache_key, response, ttl=300)
    
    return response


@router.post("/assessments/", response_model=schemas.CardiovascularRiskAssessmentResponse)
async def create_risk_assessment(
    assessment_data: schemas.CardiovascularRiskAssessmentCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """위험도 평가 생성"""
    
    # 위험도 자동 계산
    if (assessment_data.age and assessment_data.gender and 
        assessment_data.systolic_bp and assessment_data.cholesterol):
        
        risk_calc = calculate_cardiovascular_risk(
            age=assessment_data.age,
            gender=assessment_data.gender,
            systolic_bp=assessment_data.systolic_bp,
            cholesterol=assessment_data.cholesterol,
            smoking=assessment_data.smoking,
            diabetes=assessment_data.diabetes,
            hypertension=assessment_data.hypertension
        )
        
        # 계산된 값 적용
        assessment_dict = assessment_data.model_dump()  # Use Pydantic v2 method
        assessment_dict.update({
            "risk_score": risk_calc["risk_score"],
            "risk_level": risk_calc["risk_level"],  # Now it's already a Korean string
            "ten_year_risk": risk_calc["ten_year_risk"],
            "recommendations": risk_calc["recommendations"],
            "assessed_by": current_user_id
        })
        
        # 다음 평가 예정일 설정
        next_months = risk_calc["next_assessment_months"]
        assessment_dict["follow_up_date"] = datetime.now() + timedelta(days=30 * next_months)
    else:
        assessment_dict = assessment_data.model_dump()
        assessment_dict["assessed_by"] = current_user_id
    
    # 평가 생성
    new_assessment = models.CardiovascularRiskAssessment(**assessment_dict)
    
    db.add(new_assessment)
    await db.commit()
    await db.refresh(new_assessment)
    
    logger.info(f"뇌심혈관 위험도 평가 생성: {assessment_data.worker_id} by {current_user_id}")
    
    return schemas.CardiovascularRiskAssessmentResponse.from_orm(new_assessment)


@router.get("/assessments/{assessment_id}", response_model=schemas.CardiovascularRiskAssessmentResponse)
async def get_risk_assessment(
    assessment_id: UUID,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """위험도 평가 상세 정보 조회"""
    assessment = await db.get(models.CardiovascularRiskAssessment, assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="위험도 평가를 찾을 수 없습니다"
        )
    
    return schemas.CardiovascularRiskAssessmentResponse.from_orm(assessment)


@router.put("/assessments/{assessment_id}", response_model=schemas.CardiovascularRiskAssessmentResponse)
async def update_risk_assessment(
    assessment_id: UUID,
    assessment_data: schemas.CardiovascularRiskAssessmentUpdate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """위험도 평가 수정"""
    assessment = await db.get(models.CardiovascularRiskAssessment, assessment_id)
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="위험도 평가를 찾을 수 없습니다"
        )
    
    # 업데이트
    update_data = assessment_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assessment, field, value)
    
    await db.commit()
    await db.refresh(assessment)
    
    return schemas.CardiovascularRiskAssessmentResponse.from_orm(assessment)


# 모니터링 관리
@router.get("/monitoring/", response_model=List[schemas.CardiovascularMonitoringResponse])
async def get_monitoring_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    worker_id: Optional[str] = None,
    monitoring_type: Optional[str] = None,  # Changed from enum to string
    is_completed: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """모니터링 스케줄 목록 조회"""
    query = select(models.CardiovascularMonitoring).options(
        selectinload(models.CardiovascularMonitoring.risk_assessment)
    )
    
    # 필터 적용
    if worker_id:
        query = query.where(models.CardiovascularMonitoring.worker_id == worker_id)
    if monitoring_type:
        query = query.where(models.CardiovascularMonitoring.monitoring_type == monitoring_type)
    if is_completed is not None:
        query = query.where(models.CardiovascularMonitoring.is_completed == is_completed)
    if date_from:
        query = query.where(models.CardiovascularMonitoring.scheduled_date >= date_from)
    if date_to:
        query = query.where(models.CardiovascularMonitoring.scheduled_date <= date_to)
    
    query = query.offset(skip).limit(limit).order_by(
        models.CardiovascularMonitoring.scheduled_date.desc()
    )
    
    result = await db.execute(query)
    monitoring_schedules = result.scalars().all()
    
    return [schemas.CardiovascularMonitoringResponse.from_orm(schedule) 
           for schedule in monitoring_schedules]


@router.post("/monitoring/", response_model=schemas.CardiovascularMonitoringResponse)
async def create_monitoring_schedule(
    monitoring_data: schemas.CardiovascularMonitoringCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """모니터링 스케줄 생성"""
    
    # 모니터링 스케줄 생성
    monitoring_dict = monitoring_data.dict()
    monitoring_dict["monitored_by"] = current_user_id
    
    new_monitoring = models.CardiovascularMonitoring(**monitoring_dict)
    
    db.add(new_monitoring)
    await db.commit()
    await db.refresh(new_monitoring)
    
    logger.info(f"뇌심혈관 모니터링 스케줄 생성: {monitoring_data.worker_id} by {current_user_id}")
    
    return schemas.CardiovascularMonitoringResponse.from_orm(new_monitoring)


@router.put("/monitoring/{monitoring_id}", response_model=schemas.CardiovascularMonitoringResponse)
async def update_monitoring_record(
    monitoring_id: UUID,
    monitoring_data: schemas.CardiovascularMonitoringUpdate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """모니터링 기록 업데이트"""
    monitoring = await db.get(models.CardiovascularMonitoring, monitoring_id)
    if not monitoring:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="모니터링 기록을 찾을 수 없습니다"
        )
    
    # 업데이트
    update_data = monitoring_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(monitoring, field, value)
    
    # 완료 처리시 실제 일시 자동 설정
    if monitoring_data.is_completed and not monitoring.actual_date:
        monitoring.actual_date = datetime.now()
    
    # 이상 소견 발생시 자동으로 정상 여부 설정
    if monitoring_data.abnormal_findings:
        monitoring.is_normal = False
        monitoring.action_required = True
    
    await db.commit()
    await db.refresh(monitoring)
    
    # 이상 소견이 있고 조치가 필요한 경우 로그 기록
    if monitoring.action_required and monitoring.abnormal_findings:
        logger.warning(f"뇌심혈관 모니터링 이상 소견: {monitoring.worker_id}, 소견: {monitoring.abnormal_findings}")
    
    return schemas.CardiovascularMonitoringResponse.from_orm(monitoring)


# 응급상황 대응
@router.get("/emergency/", response_model=List[schemas.EmergencyResponseResponse])
async def get_emergency_responses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    worker_id: Optional[str] = None,
    status: Optional[str] = None,  # Changed from enum to string
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """응급상황 대응 기록 목록 조회"""
    query = select(models.EmergencyResponse)
    
    # 필터 적용
    if worker_id:
        query = query.where(models.EmergencyResponse.worker_id == worker_id)
    if status:
        query = query.where(models.EmergencyResponse.status == status)
    if date_from:
        query = query.where(models.EmergencyResponse.incident_datetime >= date_from)
    if date_to:
        query = query.where(models.EmergencyResponse.incident_datetime <= date_to)
    
    query = query.offset(skip).limit(limit).order_by(
        models.EmergencyResponse.incident_datetime.desc()
    )
    
    result = await db.execute(query)
    responses = result.scalars().all()
    
    return [schemas.EmergencyResponseResponse.from_orm(response) for response in responses]


@router.post("/emergency/", response_model=schemas.EmergencyResponseResponse)
async def create_emergency_response(
    response_data: schemas.EmergencyResponseCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """응급상황 대응 기록 생성"""
    
    # 응급상황 대응 기록 생성
    response_dict = response_data.dict()
    response_dict["created_by"] = current_user_id
    response_dict["status"] = "활성화"  # Use Korean string directly
    
    new_response = models.EmergencyResponse(**response_dict)
    
    db.add(new_response)
    await db.commit()
    await db.refresh(new_response)
    
    logger.warning(f"뇌심혈관 응급상황 발생: {response_data.worker_id}, 장소: {response_data.incident_location}")
    
    return schemas.EmergencyResponseResponse.from_orm(new_response)


# 예방 교육
@router.get("/education/", response_model=List[schemas.PreventionEducationResponse])
async def get_prevention_education(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    is_completed: Optional[bool] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """예방 교육 프로그램 목록 조회"""
    query = select(models.PreventionEducation)
    
    # 필터 적용
    if is_completed is not None:
        query = query.where(models.PreventionEducation.is_completed == is_completed)
    if date_from:
        query = query.where(models.PreventionEducation.scheduled_date >= date_from)
    if date_to:
        query = query.where(models.PreventionEducation.scheduled_date <= date_to)
    
    query = query.offset(skip).limit(limit).order_by(
        models.PreventionEducation.scheduled_date.desc()
    )
    
    result = await db.execute(query)
    education_programs = result.scalars().all()
    
    return [schemas.PreventionEducationResponse.from_orm(program) 
           for program in education_programs]


@router.post("/education/", response_model=schemas.PreventionEducationResponse)
async def create_prevention_education(
    education_data: schemas.PreventionEducationCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """예방 교육 프로그램 생성"""
    
    new_education = models.PreventionEducation(**education_data.dict())
    
    db.add(new_education)
    await db.commit()
    await db.refresh(new_education)
    
    logger.info(f"뇌심혈관 예방 교육 프로그램 생성: {education_data.title} by {current_user_id}")
    
    return schemas.PreventionEducationResponse.from_orm(new_education)


# 통계
@router.get("/statistics", response_model=schemas.CardiovascularStatistics)
async def get_statistics(
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
    cache: CacheService = Depends(get_cache_service)
):
    """뇌심혈관계 관리 통계"""
    cache_key = "cardiovascular_statistics"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # 전체 평가 건수
    total_assessments = await db.scalar(
        select(func.count(models.CardiovascularRiskAssessment.id))
    ) or 0
    
    # 위험도별 분포 (Korean string values for PostgreSQL enum)
    high_risk_count = await db.scalar(
        select(func.count(models.CardiovascularRiskAssessment.id))
        .where(models.CardiovascularRiskAssessment.risk_level == "높음")
    ) or 0
    
    very_high_risk_count = await db.scalar(
        select(func.count(models.CardiovascularRiskAssessment.id))
        .where(models.CardiovascularRiskAssessment.risk_level == "매우높음")
    ) or 0
    
    moderate_risk_count = await db.scalar(
        select(func.count(models.CardiovascularRiskAssessment.id))
        .where(models.CardiovascularRiskAssessment.risk_level == "보통")
    ) or 0
    
    low_risk_count = await db.scalar(
        select(func.count(models.CardiovascularRiskAssessment.id))
        .where(models.CardiovascularRiskAssessment.risk_level == "낮음")
    ) or 0
    
    # 모니터링 통계
    active_monitoring = await db.scalar(
        select(func.count(models.CardiovascularMonitoring.id))
        .where(models.CardiovascularMonitoring.is_completed == False)
    ) or 0
    
    # 지연된 모니터링 (예정일이 지났지만 완료되지 않은 것)
    overdue_monitoring = await db.scalar(
        select(func.count(models.CardiovascularMonitoring.id))
        .where(and_(
            models.CardiovascularMonitoring.is_completed == False,
            models.CardiovascularMonitoring.scheduled_date < datetime.now()
        ))
    ) or 0
    
    # 이달 완료된 모니터링
    month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    completed_this_month = await db.scalar(
        select(func.count(models.CardiovascularMonitoring.id))
        .where(and_(
            models.CardiovascularMonitoring.is_completed == True,
            models.CardiovascularMonitoring.actual_date >= month_start
        ))
    ) or 0
    
    # 이달 응급상황 건수
    emergency_cases_this_month = await db.scalar(
        select(func.count(models.EmergencyResponse.id))
        .where(models.EmergencyResponse.incident_datetime >= month_start)
    ) or 0
    
    # 평균 대응시간
    emergency_response_time_avg = await db.scalar(
        select(func.avg(models.EmergencyResponse.response_time))
        .where(models.EmergencyResponse.response_time.isnot(None))
    )
    
    # 교육 통계
    scheduled_education = await db.scalar(
        select(func.count(models.PreventionEducation.id))
        .where(models.PreventionEducation.is_completed == False)
    ) or 0
    
    completed_education = await db.scalar(
        select(func.count(models.PreventionEducation.id))
        .where(models.PreventionEducation.is_completed == True)
    ) or 0
    
    # 교육 효과성 평균
    education_effectiveness_avg = await db.scalar(
        select(func.avg(models.PreventionEducation.effectiveness_score))
        .where(models.PreventionEducation.effectiveness_score.isnot(None))
    )
    
    statistics = schemas.CardiovascularStatistics(
        total_assessments=total_assessments,
        high_risk_count=high_risk_count + very_high_risk_count,  # 높음 + 매우높음
        moderate_risk_count=moderate_risk_count,
        low_risk_count=low_risk_count,
        active_monitoring=active_monitoring,
        overdue_monitoring=overdue_monitoring,
        completed_this_month=completed_this_month,
        emergency_cases_this_month=emergency_cases_this_month,
        emergency_response_time_avg=emergency_response_time_avg,
        scheduled_education=scheduled_education,
        completed_education=completed_education,
        education_effectiveness_avg=education_effectiveness_avg,
        by_risk_level={
            "매우높음": very_high_risk_count,
            "높음": high_risk_count,
            "보통": moderate_risk_count,
            "낮음": low_risk_count
        }
    )
    
    await cache.set(cache_key, statistics.dict(), ttl=600)
    
    return statistics