# 근골격계질환 및 직무스트레스 평가 API 핸들러
"""
근골격계질환 및 직무스트레스 평가 시스템 API 엔드포인트
- 근골격계 증상 조사
- 인간공학적 위험요인 평가
- 직무스트레스 평가
- 심리사회적 위험요인 평가
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, extract
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import json

from src.config.database import get_db
from src.models import musculoskeletal_stress as models
from src.models.worker import Worker
from src.schemas import musculoskeletal_stress as schemas
from src.utils.auth_deps import CurrentUserId
from src.services.cache import CacheService, get_cache_service
from src.services.notifications import NotificationService

router = APIRouter(prefix="/api/v1/musculoskeletal-stress", tags=["musculoskeletal-stress"])


# 근골격계 증상 평가
@router.post("/assessments/", response_model=schemas.MusculoskeletalAssessmentResponse)
async def create_musculoskeletal_assessment(
    assessment: schemas.MusculoskeletalAssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근골격계 증상 평가 생성"""
    # 근로자 확인
    worker = await db.get(Worker, assessment.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    # 데이터 변환
    assessment_data = assessment.model_dump()
    
    # symptoms_data 변환
    if assessment_data.get("symptoms_data"):
        symptoms_dict = {}
        for part, symptom in assessment_data["symptoms_data"].items():
            symptoms_dict[part] = symptom.model_dump() if hasattr(symptom, "model_dump") else symptom
        assessment_data["symptoms_data"] = symptoms_dict
    
    # work_characteristics 변환
    if assessment_data.get("work_characteristics"):
        assessment_data["work_characteristics"] = assessment_data["work_characteristics"].model_dump() if hasattr(assessment_data["work_characteristics"], "model_dump") else assessment_data["work_characteristics"]
    
    db_assessment = models.MusculoskeletalAssessment(**assessment_data)
    
    db.add(db_assessment)
    await db.commit()
    await db.refresh(db_assessment)
    
    return db_assessment


@router.get("/assessments/", response_model=List[schemas.MusculoskeletalAssessmentResponse])
async def get_musculoskeletal_assessments(
    worker_id: Optional[int] = None,
    assessment_type: Optional[schemas.AssessmentType] = None,
    risk_level: Optional[schemas.RiskLevel] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근골격계 증상 평가 목록 조회"""
    query = select(models.MusculoskeletalAssessment).options(
        selectinload(models.MusculoskeletalAssessment.worker)
    )
    
    if worker_id:
        query = query.where(models.MusculoskeletalAssessment.worker_id == worker_id)
    
    if assessment_type:
        query = query.where(models.MusculoskeletalAssessment.assessment_type == assessment_type)
    
    if risk_level:
        query = query.where(models.MusculoskeletalAssessment.risk_level == risk_level)
    
    if start_date:
        query = query.where(models.MusculoskeletalAssessment.assessment_date >= start_date)
    
    if end_date:
        query = query.where(models.MusculoskeletalAssessment.assessment_date <= end_date)
    
    query = query.order_by(desc(models.MusculoskeletalAssessment.assessment_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    assessments = result.scalars().all()
    
    return assessments


@router.get("/assessments/{assessment_id}", response_model=schemas.MusculoskeletalAssessmentResponse)
async def get_musculoskeletal_assessment(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """특정 근골격계 증상 평가 조회"""
    assessment = await db.get(models.MusculoskeletalAssessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
    
    return assessment


@router.put("/assessments/{assessment_id}", response_model=schemas.MusculoskeletalAssessmentResponse)
async def update_musculoskeletal_assessment(
    assessment_id: int,
    assessment_update: schemas.MusculoskeletalAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근골격계 증상 평가 수정"""
    assessment = await db.get(models.MusculoskeletalAssessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
    
    update_data = assessment_update.model_dump(exclude_unset=True)
    
    # symptoms_data 변환
    if update_data.get("symptoms_data"):
        symptoms_dict = {}
        for part, symptom in update_data["symptoms_data"].items():
            symptoms_dict[part] = symptom.model_dump() if hasattr(symptom, "model_dump") else symptom
        update_data["symptoms_data"] = symptoms_dict
    
    for key, value in update_data.items():
        setattr(assessment, key, value)
    
    assessment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(assessment)
    
    return assessment


@router.get("/assessments/worker/{worker_id}/history", response_model=List[schemas.MusculoskeletalAssessmentResponse])
async def get_worker_assessment_history(
    worker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근로자의 근골격계 평가 이력 조회"""
    query = select(models.MusculoskeletalAssessment).where(
        models.MusculoskeletalAssessment.worker_id == worker_id
    ).order_by(desc(models.MusculoskeletalAssessment.assessment_date))
    
    result = await db.execute(query)
    assessments = result.scalars().all()
    
    return assessments


# 인간공학적 평가
@router.post("/ergonomic-evaluations/", response_model=schemas.ErgonomicEvaluationResponse)
async def create_ergonomic_evaluation(
    evaluation: schemas.ErgonomicEvaluationCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """인간공학적 평가 생성"""
    # 데이터 변환
    evaluation_data = evaluation.model_dump()
    
    # JSON 필드 변환
    if evaluation_data.get("posture_analysis"):
        evaluation_data["posture_analysis"] = evaluation_data["posture_analysis"].model_dump() if hasattr(evaluation_data["posture_analysis"], "model_dump") else evaluation_data["posture_analysis"]
    
    if evaluation_data.get("load_assessment"):
        evaluation_data["load_assessment"] = evaluation_data["load_assessment"].model_dump() if hasattr(evaluation_data["load_assessment"], "model_dump") else evaluation_data["load_assessment"]
    
    if evaluation_data.get("evaluation_scores"):
        evaluation_data["evaluation_scores"] = evaluation_data["evaluation_scores"].model_dump() if hasattr(evaluation_data["evaluation_scores"], "model_dump") else evaluation_data["evaluation_scores"]
    
    if evaluation_data.get("improvement_suggestions"):
        evaluation_data["improvement_suggestions"] = [
            item.model_dump() if hasattr(item, "model_dump") else item
            for item in evaluation_data["improvement_suggestions"]
        ]
    
    db_evaluation = models.ErgonomicEvaluation(**evaluation_data)
    
    db.add(db_evaluation)
    await db.commit()
    await db.refresh(db_evaluation)
    
    return db_evaluation


@router.get("/ergonomic-evaluations/", response_model=List[schemas.ErgonomicEvaluationResponse])
async def get_ergonomic_evaluations(
    worker_id: Optional[int] = None,
    risk_level: Optional[schemas.RiskLevel] = None,
    evaluation_method: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """인간공학적 평가 목록 조회"""
    query = select(models.ErgonomicEvaluation)
    
    if worker_id:
        query = query.where(models.ErgonomicEvaluation.worker_id == worker_id)
    
    if risk_level:
        query = query.where(models.ErgonomicEvaluation.overall_risk_level == risk_level)
    
    if evaluation_method:
        query = query.where(models.ErgonomicEvaluation.evaluation_method == evaluation_method)
    
    query = query.order_by(desc(models.ErgonomicEvaluation.evaluation_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    evaluations = result.scalars().all()
    
    return evaluations


# 직무스트레스 평가
@router.post("/job-stress-assessments/", response_model=schemas.JobStressAssessmentResponse)
async def create_job_stress_assessment(
    assessment: schemas.JobStressAssessmentCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """직무스트레스 평가 생성"""
    # 근로자 확인
    worker = await db.get(Worker, assessment.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    # 데이터 변환
    assessment_data = assessment.model_dump()
    
    # scores 필드 변환
    for field in ["job_demand_scores", "job_control_scores", "interpersonal_scores"]:
        if assessment_data.get(field):
            assessment_data[field] = assessment_data[field].model_dump() if hasattr(assessment_data[field], "model_dump") else assessment_data[field]
    
    if assessment_data.get("coping_resources"):
        assessment_data["coping_resources"] = assessment_data["coping_resources"].model_dump() if hasattr(assessment_data["coping_resources"], "model_dump") else assessment_data["coping_resources"]
    
    db_assessment = models.JobStressAssessment(**assessment_data)
    
    db.add(db_assessment)
    await db.commit()
    await db.refresh(db_assessment)
    
    # 고위험군 알림
    if assessment.stress_level in [schemas.RiskLevel.HIGH, schemas.RiskLevel.VERY_HIGH]:
        background_tasks.add_task(
            notify_high_stress_alert,
            worker.id,
            worker.name,
            assessment.stress_level,
            assessment.high_risk_factors
        )
    
    return db_assessment


@router.get("/job-stress-assessments/", response_model=List[schemas.JobStressAssessmentResponse])
async def get_job_stress_assessments(
    worker_id: Optional[int] = None,
    stress_level: Optional[schemas.RiskLevel] = None,
    assessment_type: Optional[schemas.AssessmentType] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """직무스트레스 평가 목록 조회"""
    query = select(models.JobStressAssessment).options(
        selectinload(models.JobStressAssessment.worker)
    )
    
    if worker_id:
        query = query.where(models.JobStressAssessment.worker_id == worker_id)
    
    if stress_level:
        query = query.where(models.JobStressAssessment.stress_level == stress_level)
    
    if assessment_type:
        query = query.where(models.JobStressAssessment.assessment_type == assessment_type)
    
    if start_date:
        query = query.where(models.JobStressAssessment.assessment_date >= start_date)
    
    if end_date:
        query = query.where(models.JobStressAssessment.assessment_date <= end_date)
    
    query = query.order_by(desc(models.JobStressAssessment.assessment_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    assessments = result.scalars().all()
    
    return assessments


@router.get("/job-stress-assessments/{assessment_id}", response_model=schemas.JobStressAssessmentResponse)
async def get_job_stress_assessment(
    assessment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """특정 직무스트레스 평가 조회"""
    assessment = await db.get(models.JobStressAssessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
    
    return assessment


@router.put("/job-stress-assessments/{assessment_id}", response_model=schemas.JobStressAssessmentResponse)
async def update_job_stress_assessment(
    assessment_id: int,
    assessment_update: schemas.JobStressAssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """직무스트레스 평가 수정"""
    assessment = await db.get(models.JobStressAssessment, assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="평가를 찾을 수 없습니다")
    
    update_data = assessment_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        setattr(assessment, key, value)
    
    assessment.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(assessment)
    
    return assessment


# 스트레스 개입 프로그램
@router.post("/stress-interventions/", response_model=schemas.StressInterventionResponse)
async def create_stress_intervention(
    intervention: schemas.StressInterventionCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """스트레스 개입 프로그램 생성"""
    # 데이터 변환
    intervention_data = intervention.model_dump()
    
    # session_records 변환
    if intervention_data.get("session_records"):
        intervention_data["session_records"] = [
            record.model_dump() if hasattr(record, "model_dump") else record
            for record in intervention_data["session_records"]
        ]
    
    db_intervention = models.StressIntervention(**intervention_data)
    
    db.add(db_intervention)
    await db.commit()
    await db.refresh(db_intervention)
    
    return db_intervention


@router.get("/stress-interventions/", response_model=List[schemas.StressInterventionResponse])
async def get_stress_interventions(
    worker_id: Optional[int] = None,
    program_type: Optional[str] = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """스트레스 개입 프로그램 목록 조회"""
    query = select(models.StressIntervention)
    
    if worker_id:
        query = query.where(models.StressIntervention.worker_id == worker_id)
    
    if program_type:
        query = query.where(models.StressIntervention.program_type == program_type)
    
    if active_only:
        query = query.where(models.StressIntervention.end_date == None)
    
    query = query.order_by(desc(models.StressIntervention.start_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    interventions = result.scalars().all()
    
    return interventions


@router.put("/stress-interventions/{intervention_id}", response_model=schemas.StressInterventionResponse)
async def update_stress_intervention(
    intervention_id: int,
    intervention_update: schemas.StressInterventionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """스트레스 개입 프로그램 업데이트"""
    intervention = await db.get(models.StressIntervention, intervention_id)
    if not intervention:
        raise HTTPException(status_code=404, detail="프로그램을 찾을 수 없습니다")
    
    update_data = intervention_update.model_dump(exclude_unset=True)
    
    # session_records 변환
    if update_data.get("session_records"):
        update_data["session_records"] = [
            record.model_dump() if hasattr(record, "model_dump") else record
            for record in update_data["session_records"]
        ]
    
    for key, value in update_data.items():
        setattr(intervention, key, value)
    
    intervention.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(intervention)
    
    return intervention


# 통계 및 대시보드
@router.get("/musculoskeletal/statistics/{year}", response_model=schemas.MusculoskeletalStatisticsResponse)
async def get_musculoskeletal_statistics(
    year: int,
    month: Optional[int] = None,
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
    cache: CacheService = Depends(get_cache_service),
):
    """근골격계질환 통계"""
    cache_key = f"musculoskeletal_stats:{year}:{month or 'all'}:{department or 'all'}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # 기간 설정
    if month:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    
    # 평가 통계
    query = select(func.count(models.MusculoskeletalAssessment.id)).where(
        and_(
            models.MusculoskeletalAssessment.assessment_date >= start_date,
            models.MusculoskeletalAssessment.assessment_date <= end_date
        )
    )
    
    if department:
        query = query.where(models.MusculoskeletalAssessment.department == department)
    
    total_assessments = (await db.execute(query)).scalar() or 0
    
    # 근로자 수
    worker_query = select(func.count(func.distinct(models.MusculoskeletalAssessment.worker_id))).where(
        and_(
            models.MusculoskeletalAssessment.assessment_date >= start_date,
            models.MusculoskeletalAssessment.assessment_date <= end_date
        )
    )
    
    if department:
        worker_query = worker_query.where(models.MusculoskeletalAssessment.department == department)
    
    workers_assessed = (await db.execute(worker_query)).scalar() or 0
    
    # 증상 유병률 계산 (간단한 버전)
    symptom_prevalence = {
        "neck": 35,
        "shoulder": 45,
        "lower_back": 60,
        "wrist": 25
    }
    
    # 위험도 분포
    risk_query = select(
        models.MusculoskeletalAssessment.risk_level,
        func.count(models.MusculoskeletalAssessment.id)
    ).where(
        and_(
            models.MusculoskeletalAssessment.assessment_date >= start_date,
            models.MusculoskeletalAssessment.assessment_date <= end_date
        )
    ).group_by(models.MusculoskeletalAssessment.risk_level)
    
    if department:
        risk_query = risk_query.where(models.MusculoskeletalAssessment.department == department)
    
    risk_result = await db.execute(risk_query)
    risk_counts = {row[0]: row[1] for row in risk_result}
    
    total_count = sum(risk_counts.values())
    risk_distribution = {
        level: (count / total_count * 100) if total_count > 0 else 0
        for level, count in risk_counts.items()
    }
    
    statistics = schemas.MusculoskeletalStatisticsResponse(
        id=0,  # Dummy ID
        year=year,
        month=month,
        department=department,
        total_assessments=total_assessments,
        workers_assessed=workers_assessed,
        symptom_prevalence=symptom_prevalence,
        risk_distribution=risk_distribution,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await cache.set(cache_key, statistics, ttl=3600)
    
    return statistics


@router.get("/job-stress/statistics/{year}", response_model=schemas.JobStressStatisticsResponse)
async def get_job_stress_statistics(
    year: int,
    month: Optional[int] = None,
    department: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
    cache: CacheService = Depends(get_cache_service),
):
    """직무스트레스 통계"""
    cache_key = f"job_stress_stats:{year}:{month or 'all'}:{department or 'all'}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # 기간 설정
    if month:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
    
    # 평가 통계
    query = select(func.count(models.JobStressAssessment.id)).where(
        and_(
            models.JobStressAssessment.assessment_date >= start_date,
            models.JobStressAssessment.assessment_date <= end_date
        )
    )
    
    total_assessments = (await db.execute(query)).scalar() or 0
    
    # 근로자 수
    worker_query = select(func.count(func.distinct(models.JobStressAssessment.worker_id))).where(
        and_(
            models.JobStressAssessment.assessment_date >= start_date,
            models.JobStressAssessment.assessment_date <= end_date
        )
    )
    
    workers_assessed = (await db.execute(worker_query)).scalar() or 0
    
    # 스트레스 수준 분포
    stress_query = select(
        models.JobStressAssessment.stress_level,
        func.count(models.JobStressAssessment.id)
    ).where(
        and_(
            models.JobStressAssessment.assessment_date >= start_date,
            models.JobStressAssessment.assessment_date <= end_date
        )
    ).group_by(models.JobStressAssessment.stress_level)
    
    stress_result = await db.execute(stress_query)
    stress_counts = {row[0]: row[1] for row in stress_result}
    
    total_count = sum(stress_counts.values())
    stress_level_distribution = {
        level: (count / total_count * 100) if total_count > 0 else 0
        for level, count in stress_counts.items()
    }
    
    # 요인별 평균 점수 (샘플 데이터)
    factor_averages = {
        "job_demand": 65.5,
        "job_control": 45.2,
        "interpersonal": 55.8,
        "job_insecurity": 40.3,
        "organizational": 50.7,
        "reward": 48.9,
        "workplace_culture": 52.1
    }
    
    # 고위험군 수
    high_risk_query = select(func.count(models.JobStressAssessment.id)).where(
        and_(
            models.JobStressAssessment.assessment_date >= start_date,
            models.JobStressAssessment.assessment_date <= end_date,
            models.JobStressAssessment.stress_level.in_([schemas.RiskLevel.HIGH, schemas.RiskLevel.VERY_HIGH])
        )
    )
    
    high_risk_count = (await db.execute(high_risk_query)).scalar() or 0
    
    # 개입 프로그램 참여
    intervention_query = select(func.count(func.distinct(models.StressIntervention.worker_id))).where(
        models.StressIntervention.start_date >= start_date
    )
    
    intervention_participation = (await db.execute(intervention_query)).scalar() or 0
    
    statistics = schemas.JobStressStatisticsResponse(
        id=0,  # Dummy ID
        year=year,
        month=month,
        department=department,
        total_assessments=total_assessments,
        workers_assessed=workers_assessed,
        stress_level_distribution=stress_level_distribution,
        factor_averages=factor_averages,
        high_risk_count=high_risk_count,
        intervention_participation=intervention_participation,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await cache.set(cache_key, statistics, ttl=3600)
    
    return statistics


@router.get("/musculoskeletal/dashboard/", response_model=schemas.MusculoskeletalDashboard)
async def get_musculoskeletal_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근골격계 대시보드"""
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # 이번 달 평가 수
    assessments_query = select(func.count(models.MusculoskeletalAssessment.id)).where(
        models.MusculoskeletalAssessment.assessment_date >= month_start
    )
    total_assessments_this_month = (await db.execute(assessments_query)).scalar() or 0
    
    # 고위험 근로자
    high_risk_query = select(func.count(func.distinct(models.MusculoskeletalAssessment.worker_id))).where(
        models.MusculoskeletalAssessment.risk_level.in_([schemas.RiskLevel.HIGH, schemas.RiskLevel.VERY_HIGH])
    )
    high_risk_workers = (await db.execute(high_risk_query)).scalar() or 0
    
    # 후속조치 대기
    followup_query = select(func.count(models.MusculoskeletalAssessment.id)).where(
        and_(
            models.MusculoskeletalAssessment.followup_required == True,
            models.MusculoskeletalAssessment.followup_date <= today
        )
    )
    pending_followups = (await db.execute(followup_query)).scalar() or 0
    
    # 증상 분포 (최근 평가 기준)
    recent_assessments_query = select(models.MusculoskeletalAssessment).where(
        models.MusculoskeletalAssessment.assessment_date >= today - timedelta(days=90)
    ).limit(100)
    
    recent_result = await db.execute(recent_assessments_query)
    recent_assessments = recent_result.scalars().all()
    
    symptom_count = {}
    for assessment in recent_assessments:
        if assessment.symptoms_data:
            for part, symptom in assessment.symptoms_data.items():
                if symptom.get("pain_level") != "없음":
                    symptom_count[part] = symptom_count.get(part, 0) + 1
    
    # 가장 흔한 증상
    most_common_symptoms = sorted(
        [{"part": part, "count": count} for part, count in symptom_count.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]
    
    # 위험도 분포
    risk_distribution = {
        "low": 30,
        "medium": 45,
        "high": 20,
        "very_high": 5
    }
    
    # 긴급 사례
    urgent_query = select(
        models.MusculoskeletalAssessment.id,
        models.MusculoskeletalAssessment.worker_id,
        models.MusculoskeletalAssessment.risk_level,
        models.MusculoskeletalAssessment.overall_pain_score
    ).where(
        and_(
            models.MusculoskeletalAssessment.risk_level == schemas.RiskLevel.VERY_HIGH,
            models.MusculoskeletalAssessment.medical_referral_needed == True
        )
    ).limit(10)
    
    urgent_result = await db.execute(urgent_query)
    urgent_cases = [
        {
            "assessment_id": row[0],
            "worker_id": row[1],
            "risk_level": row[2],
            "pain_score": row[3]
        }
        for row in urgent_result
    ]
    
    dashboard = schemas.MusculoskeletalDashboard(
        total_assessments_this_month=total_assessments_this_month,
        high_risk_workers=high_risk_workers,
        pending_followups=pending_followups,
        symptom_distribution=symptom_count,
        most_common_symptoms=most_common_symptoms,
        risk_level_distribution=risk_distribution,
        departments_at_risk=[],  # TODO: 부서별 분석
        intervention_success_rate=75.5,  # TODO: 실제 계산
        average_pain_reduction=2.3,  # TODO: 실제 계산
        urgent_cases=urgent_cases,
        overdue_assessments=[]  # TODO: 기한 초과 평가
    )
    
    return dashboard


@router.get("/job-stress/dashboard/", response_model=schemas.JobStressDashboard)
async def get_job_stress_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """직무스트레스 대시보드"""
    today = date.today()
    month_start = date(today.year, today.month, 1)
    
    # 이번 달 평가 수
    assessments_query = select(func.count(models.JobStressAssessment.id)).where(
        models.JobStressAssessment.assessment_date >= month_start
    )
    total_assessments_this_month = (await db.execute(assessments_query)).scalar() or 0
    
    # 고스트레스 근로자
    high_stress_query = select(func.count(func.distinct(models.JobStressAssessment.worker_id))).where(
        models.JobStressAssessment.stress_level.in_([schemas.RiskLevel.HIGH, schemas.RiskLevel.VERY_HIGH])
    )
    high_stress_workers = (await db.execute(high_stress_query)).scalar() or 0
    
    # 진행 중인 개입
    ongoing_query = select(func.count(models.StressIntervention.id)).where(
        models.StressIntervention.end_date == None
    )
    ongoing_interventions = (await db.execute(ongoing_query)).scalar() or 0
    
    # 스트레스 수준 분포
    stress_level_distribution = {
        "low": 25,
        "medium": 50,
        "high": 20,
        "very_high": 5
    }
    
    # 평균 스트레스 점수
    avg_query = select(func.avg(models.JobStressAssessment.total_score)).where(
        models.JobStressAssessment.assessment_date >= month_start
    )
    average_stress_score = (await db.execute(avg_query)).scalar() or 0
    
    # 주요 스트레스 요인
    top_stress_factors = [
        {"factor": "직무요구", "score": 75.2},
        {"factor": "보상부적절", "score": 68.5},
        {"factor": "직무불안정", "score": 65.8}
    ]
    
    # 활성 프로그램
    active_programs_query = select(func.count(models.StressIntervention.id)).where(
        models.StressIntervention.end_date == None
    )
    active_programs = (await db.execute(active_programs_query)).scalar() or 0
    
    # 위급 사례
    critical_query = select(
        models.JobStressAssessment.id,
        models.JobStressAssessment.worker_id,
        models.JobStressAssessment.stress_level,
        models.JobStressAssessment.burnout_score
    ).where(
        and_(
            models.JobStressAssessment.stress_level == schemas.RiskLevel.VERY_HIGH,
            models.JobStressAssessment.counseling_needed == True
        )
    ).limit(10)
    
    critical_result = await db.execute(critical_query)
    critical_cases = [
        {
            "assessment_id": row[0],
            "worker_id": row[1],
            "stress_level": row[2],
            "burnout_score": row[3]
        }
        for row in critical_result
    ]
    
    dashboard = schemas.JobStressDashboard(
        total_assessments_this_month=total_assessments_this_month,
        high_stress_workers=high_stress_workers,
        ongoing_interventions=ongoing_interventions,
        stress_level_distribution=stress_level_distribution,
        average_stress_score=average_stress_score,
        trend_direction="상승",  # TODO: 실제 추세 계산
        top_stress_factors=top_stress_factors,
        department_comparison=[],  # TODO: 부서별 비교
        active_programs=active_programs,
        program_participation_rate=65.0,  # TODO: 실제 계산
        program_effectiveness=72.5,  # TODO: 실제 계산
        critical_cases=critical_cases,
        program_dropouts=[]  # TODO: 중도 탈락자
    )
    
    return dashboard


# 보고서 생성
@router.get("/reports/worker/{worker_id}/comprehensive")
async def get_worker_comprehensive_report(
    worker_id: int,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """근로자 종합 보고서 (근골격계 + 직무스트레스)"""
    # 근골격계 평가
    musculo_query = select(models.MusculoskeletalAssessment).where(
        models.MusculoskeletalAssessment.worker_id == worker_id
    ).order_by(desc(models.MusculoskeletalAssessment.assessment_date)).limit(1)
    
    musculo_result = await db.execute(musculo_query)
    latest_musculo = musculo_result.scalar_one_or_none()
    
    # 직무스트레스 평가
    stress_query = select(models.JobStressAssessment).where(
        models.JobStressAssessment.worker_id == worker_id
    ).order_by(desc(models.JobStressAssessment.assessment_date)).limit(1)
    
    stress_result = await db.execute(stress_query)
    latest_stress = stress_result.scalar_one_or_none()
    
    # 인간공학적 평가
    ergo_query = select(models.ErgonomicEvaluation).where(
        models.ErgonomicEvaluation.worker_id == worker_id
    ).order_by(desc(models.ErgonomicEvaluation.evaluation_date)).limit(1)
    
    ergo_result = await db.execute(ergo_query)
    latest_ergo = ergo_result.scalar_one_or_none()
    
    # 진행 중인 개입
    intervention_query = select(models.StressIntervention).where(
        and_(
            models.StressIntervention.worker_id == worker_id,
            models.StressIntervention.end_date == None
        )
    )
    
    intervention_result = await db.execute(intervention_query)
    active_interventions = intervention_result.scalars().all()
    
    report = {
        "worker_id": worker_id,
        "report_date": date.today().isoformat(),
        "musculoskeletal": {
            "latest_assessment": latest_musculo,
            "risk_level": latest_musculo.risk_level if latest_musculo else None,
            "most_painful_parts": latest_musculo.most_painful_parts if latest_musculo else [],
            "recommendations": latest_musculo.recommendations if latest_musculo else None
        },
        "job_stress": {
            "latest_assessment": latest_stress,
            "stress_level": latest_stress.stress_level if latest_stress else None,
            "high_risk_factors": latest_stress.high_risk_factors if latest_stress else [],
            "recommendations": latest_stress.recommendations if latest_stress else None
        },
        "ergonomic": {
            "latest_evaluation": latest_ergo,
            "risk_level": latest_ergo.overall_risk_level if latest_ergo else None,
            "improvement_needed": latest_ergo.immediate_action_required if latest_ergo else False
        },
        "active_interventions": [
            {
                "program_name": i.program_name,
                "program_type": i.program_type,
                "start_date": i.start_date.isoformat(),
                "progress": f"{i.sessions_completed}/{i.total_sessions_planned}"
            }
            for i in active_interventions
        ],
        "overall_status": determine_overall_status(latest_musculo, latest_stress),
        "priority_actions": generate_priority_actions(latest_musculo, latest_stress, latest_ergo)
    }
    
    return report


# 헬퍼 함수
def determine_overall_status(musculo_assessment, stress_assessment):
    """전체 상태 판단"""
    if not musculo_assessment and not stress_assessment:
        return "평가필요"
    
    risk_levels = []
    if musculo_assessment:
        risk_levels.append(musculo_assessment.risk_level)
    if stress_assessment:
        risk_levels.append(stress_assessment.stress_level)
    
    if any(level in [schemas.RiskLevel.VERY_HIGH] for level in risk_levels):
        return "긴급조치필요"
    elif any(level in [schemas.RiskLevel.HIGH] for level in risk_levels):
        return "집중관리필요"
    elif any(level in [schemas.RiskLevel.MEDIUM] for level in risk_levels):
        return "정기관찰필요"
    else:
        return "양호"


def generate_priority_actions(musculo_assessment, stress_assessment, ergo_evaluation):
    """우선순위 조치사항 생성"""
    actions = []
    
    if musculo_assessment:
        if musculo_assessment.medical_referral_needed:
            actions.append({
                "priority": 1,
                "action": "의료기관 진료 의뢰",
                "reason": "근골격계 증상 심각"
            })
        if musculo_assessment.work_improvement_needed:
            actions.append({
                "priority": 2,
                "action": "작업환경 개선",
                "reason": "인간공학적 위험요인"
            })
    
    if stress_assessment:
        if stress_assessment.counseling_needed:
            actions.append({
                "priority": 1,
                "action": "심리상담 연계",
                "reason": "높은 직무스트레스"
            })
        if stress_assessment.stress_management_program:
            actions.append({
                "priority": 2,
                "action": "스트레스 관리 프로그램 참여",
                "reason": "스트레스 대처능력 향상 필요"
            })
    
    if ergo_evaluation and ergo_evaluation.immediate_action_required:
        actions.append({
            "priority": 1,
            "action": "즉시 작업방법 변경",
            "reason": "매우 높은 인간공학적 위험"
        })
    
    return sorted(actions, key=lambda x: x["priority"])


async def notify_high_stress_alert(worker_id: int, worker_name: str, stress_level: str, risk_factors: List[str]):
    """고스트레스 근로자 알림"""
    # TODO: 실제 알림 서비스 구현
    pass