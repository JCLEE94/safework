"""
건강관리실 API 핸들러

이 모듈은 건강관리실 관련 기능의 API 엔드포인트를 제공합니다.
- 투약 기록 관리
- 생체 신호 측정 관리
- 인바디 측정 관리
- 건강관리실 방문 기록
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from typing import List, Optional
from datetime import datetime, timedelta

from ..models.database import get_db
from ..models.health_room import (
    MedicationRecord, VitalSignRecord, InBodyRecord, HealthRoomVisit
)
from ..models.worker import Worker
from ..schemas.health_room import (
    MedicationRecordCreate, MedicationRecordUpdate, MedicationRecordResponse,
    VitalSignRecordCreate, VitalSignRecordUpdate, VitalSignRecordResponse,
    InBodyRecordCreate, InBodyRecordUpdate, InBodyRecordResponse,
    HealthRoomVisitCreate, HealthRoomVisitUpdate, HealthRoomVisitResponse,
    HealthRoomStats, WorkerHealthSummary
)
from ..utils.auth_deps import CurrentUserId
from ..utils.logger import logger

router = APIRouter(prefix="/api/v1/health-room", tags=["건강관리실"])


# 투약 기록 관리
@router.post("/medications", response_model=MedicationRecordResponse)
async def create_medication_record(
    record: MedicationRecordCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """투약 기록 생성"""
    try:
        # 근로자 확인
        worker = await db.get(Worker, record.worker_id)
        if not worker:
            raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
        
        # 투약 기록 생성
        new_record = MedicationRecord(**record.dict())
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        
        logger.info(f"투약 기록 생성: Worker {record.worker_id}, 약품 {record.medication_name}")
        return new_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"투약 기록 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="투약 기록 생성 중 오류가 발생했습니다")


@router.get("/medications", response_model=List[MedicationRecordResponse])
async def get_medication_records(
    worker_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    follow_up_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """투약 기록 조회"""
    query = select(MedicationRecord)
    
    if worker_id:
        query = query.where(MedicationRecord.worker_id == worker_id)
    if start_date:
        query = query.where(MedicationRecord.administered_at >= start_date)
    if end_date:
        query = query.where(MedicationRecord.administered_at <= end_date)
    if follow_up_only:
        query = query.where(MedicationRecord.follow_up_required == True)
    
    query = query.order_by(desc(MedicationRecord.administered_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# 생체 신호 측정 관리
@router.post("/vital-signs", response_model=VitalSignRecordResponse)
async def create_vital_sign_record(
    record: VitalSignRecordCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """생체 신호 측정 기록 생성"""
    try:
        # 근로자 확인
        worker = await db.get(Worker, record.worker_id)
        if not worker:
            raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
        
        # 상태 자동 평가
        new_record = VitalSignRecord(**record.dict())
        new_record.status = evaluate_vital_signs(record)
        
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        
        logger.info(f"생체 신호 측정 기록 생성: Worker {record.worker_id}")
        return new_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"생체 신호 측정 기록 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="측정 기록 생성 중 오류가 발생했습니다")


def evaluate_vital_signs(record: VitalSignRecordCreate) -> str:
    """생체 신호 상태 평가"""
    status = "정상"
    
    # 혈압 평가
    if record.systolic_bp and record.diastolic_bp:
        if record.systolic_bp >= 140 or record.diastolic_bp >= 90:
            status = "위험"
        elif record.systolic_bp >= 130 or record.diastolic_bp >= 80:
            status = "주의"
    
    # 혈당 평가
    if record.blood_sugar:
        if record.blood_sugar_type == "공복":
            if record.blood_sugar >= 126:
                status = "위험"
            elif record.blood_sugar >= 100:
                status = "주의" if status == "정상" else status
        else:  # 식후
            if record.blood_sugar >= 200:
                status = "위험"
            elif record.blood_sugar >= 140:
                status = "주의" if status == "정상" else status
    
    # 심박수 평가
    if record.heart_rate:
        if record.heart_rate > 100 or record.heart_rate < 60:
            status = "주의" if status == "정상" else status
    
    return status


@router.get("/vital-signs", response_model=List[VitalSignRecordResponse])
async def get_vital_sign_records(
    worker_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """생체 신호 측정 기록 조회"""
    query = select(VitalSignRecord)
    
    if worker_id:
        query = query.where(VitalSignRecord.worker_id == worker_id)
    if status:
        query = query.where(VitalSignRecord.status == status)
    if start_date:
        query = query.where(VitalSignRecord.measured_at >= start_date)
    if end_date:
        query = query.where(VitalSignRecord.measured_at <= end_date)
    
    query = query.order_by(desc(VitalSignRecord.measured_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# 인바디 측정 관리
@router.post("/inbody", response_model=InBodyRecordResponse)
async def create_inbody_record(
    record: InBodyRecordCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """인바디 측정 기록 생성"""
    try:
        # 근로자 확인
        worker = await db.get(Worker, record.worker_id)
        if not worker:
            raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
        
        # BMI 자동 계산
        if not record.bmi:
            record.bmi = record.weight / ((record.height / 100) ** 2)
        
        new_record = InBodyRecord(**record.dict())
        db.add(new_record)
        await db.commit()
        await db.refresh(new_record)
        
        logger.info(f"인바디 측정 기록 생성: Worker {record.worker_id}")
        return new_record
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"인바디 측정 기록 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="인바디 기록 생성 중 오류가 발생했습니다")


@router.get("/inbody", response_model=List[InBodyRecordResponse])
async def get_inbody_records(
    worker_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """인바디 측정 기록 조회"""
    query = select(InBodyRecord)
    
    if worker_id:
        query = query.where(InBodyRecord.worker_id == worker_id)
    if start_date:
        query = query.where(InBodyRecord.measured_at >= start_date)
    if end_date:
        query = query.where(InBodyRecord.measured_at <= end_date)
    
    query = query.order_by(desc(InBodyRecord.measured_at))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/inbody/{worker_id}/latest", response_model=InBodyRecordResponse)
async def get_latest_inbody_record(
    worker_id: int,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """최신 인바디 측정 기록 조회"""
    query = select(InBodyRecord).where(
        InBodyRecord.worker_id == worker_id
    ).order_by(desc(InBodyRecord.measured_at)).limit(1)
    
    result = await db.execute(query)
    record = result.scalar_one_or_none()
    
    if not record:
        raise HTTPException(status_code=404, detail="인바디 측정 기록이 없습니다")
    
    return record


# 건강관리실 방문 기록
@router.post("/visits", response_model=HealthRoomVisitResponse)
async def create_health_room_visit(
    visit: HealthRoomVisitCreate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """건강관리실 방문 기록 생성"""
    try:
        # 근로자 확인
        worker = await db.get(Worker, visit.worker_id)
        if not worker:
            raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
        
        new_visit = HealthRoomVisit(**visit.dict())
        db.add(new_visit)
        await db.commit()
        await db.refresh(new_visit)
        
        logger.info(f"건강관리실 방문 기록 생성: Worker {visit.worker_id}")
        return new_visit
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"방문 기록 생성 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="방문 기록 생성 중 오류가 발생했습니다")


@router.get("/visits", response_model=List[HealthRoomVisitResponse])
async def get_health_room_visits(
    worker_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    follow_up_only: bool = False,
    referral_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """건강관리실 방문 기록 조회"""
    query = select(HealthRoomVisit)
    
    if worker_id:
        query = query.where(HealthRoomVisit.worker_id == worker_id)
    if start_date:
        query = query.where(HealthRoomVisit.visit_date >= start_date)
    if end_date:
        query = query.where(HealthRoomVisit.visit_date <= end_date)
    if follow_up_only:
        query = query.where(HealthRoomVisit.follow_up_required == True)
    if referral_only:
        query = query.where(HealthRoomVisit.referral_required == True)
    
    query = query.order_by(desc(HealthRoomVisit.visit_date))
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    return result.scalars().all()


# 통계 및 대시보드
@router.get("/stats", response_model=HealthRoomStats)
async def get_health_room_stats(
    start_date: Optional[datetime] = Query(None, description="시작일"),
    end_date: Optional[datetime] = Query(None, description="종료일"),
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """건강관리실 통계 조회"""
    # 기본 기간 설정 (최근 30일)
    if not end_date:
        end_date = datetime.now()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    # 방문 통계
    visit_query = select(func.count(HealthRoomVisit.id)).where(
        and_(
            HealthRoomVisit.visit_date >= start_date,
            HealthRoomVisit.visit_date <= end_date
        )
    )
    total_visits = (await db.execute(visit_query)).scalar() or 0
    
    # 투약 통계
    medication_query = select(func.count(MedicationRecord.id)).where(
        and_(
            MedicationRecord.administered_at >= start_date,
            MedicationRecord.administered_at <= end_date
        )
    )
    total_medications = (await db.execute(medication_query)).scalar() or 0
    
    # 측정 통계
    measurement_query = select(func.count(VitalSignRecord.id)).where(
        and_(
            VitalSignRecord.measured_at >= start_date,
            VitalSignRecord.measured_at <= end_date
        )
    )
    total_measurements = (await db.execute(measurement_query)).scalar() or 0
    
    # 인바디 통계
    inbody_query = select(func.count(InBodyRecord.id)).where(
        and_(
            InBodyRecord.measured_at >= start_date,
            InBodyRecord.measured_at <= end_date
        )
    )
    total_inbody_records = (await db.execute(inbody_query)).scalar() or 0
    
    # 방문 사유별 통계
    visit_reason_query = select(
        HealthRoomVisit.visit_reason,
        func.count(HealthRoomVisit.id)
    ).where(
        and_(
            HealthRoomVisit.visit_date >= start_date,
            HealthRoomVisit.visit_date <= end_date
        )
    ).group_by(HealthRoomVisit.visit_reason)
    
    visit_reason_result = await db.execute(visit_reason_query)
    visits_by_reason = {reason: count for reason, count in visit_reason_result}
    
    # 자주 사용된 약품
    common_meds_query = select(
        MedicationRecord.medication_name,
        func.count(MedicationRecord.id).label('count')
    ).where(
        and_(
            MedicationRecord.administered_at >= start_date,
            MedicationRecord.administered_at <= end_date
        )
    ).group_by(MedicationRecord.medication_name).order_by(
        desc('count')
    ).limit(10)
    
    common_meds_result = await db.execute(common_meds_query)
    common_medications = [
        {"name": name, "count": count} 
        for name, count in common_meds_result
    ]
    
    # 이상 측정값 수
    abnormal_query = select(func.count(VitalSignRecord.id)).where(
        and_(
            VitalSignRecord.measured_at >= start_date,
            VitalSignRecord.measured_at <= end_date,
            VitalSignRecord.status.in_(['주의', '위험'])
        )
    )
    abnormal_vital_signs = (await db.execute(abnormal_query)).scalar() or 0
    
    # 추적 관찰 필요 수
    follow_up_query = select(func.count(HealthRoomVisit.id)).where(
        and_(
            HealthRoomVisit.visit_date >= start_date,
            HealthRoomVisit.visit_date <= end_date,
            HealthRoomVisit.follow_up_required == True
        )
    )
    follow_up_required = (await db.execute(follow_up_query)).scalar() or 0
    
    return HealthRoomStats(
        total_visits=total_visits,
        total_medications=total_medications,
        total_measurements=total_measurements,
        total_inbody_records=total_inbody_records,
        visits_by_reason=visits_by_reason,
        common_medications=common_medications,
        abnormal_vital_signs=abnormal_vital_signs,
        follow_up_required=follow_up_required
    )


@router.get("/workers/{worker_id}/summary", response_model=WorkerHealthSummary)
async def get_worker_health_summary(
    worker_id: int,
    days: int = Query(30, description="조회 기간 (일)"),
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """근로자 건강 요약 정보 조회"""
    # 근로자 확인
    worker = await db.get(Worker, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    start_date = datetime.now() - timedelta(days=days)
    
    # 최근 방문 기록
    visits_query = select(HealthRoomVisit).where(
        and_(
            HealthRoomVisit.worker_id == worker_id,
            HealthRoomVisit.visit_date >= start_date
        )
    ).order_by(desc(HealthRoomVisit.visit_date)).limit(10)
    
    visits = (await db.execute(visits_query)).scalars().all()
    
    # 최근 투약 기록
    medications_query = select(MedicationRecord).where(
        and_(
            MedicationRecord.worker_id == worker_id,
            MedicationRecord.administered_at >= start_date
        )
    ).order_by(desc(MedicationRecord.administered_at)).limit(10)
    
    medications = (await db.execute(medications_query)).scalars().all()
    
    # 최근 측정 기록
    vital_signs_query = select(VitalSignRecord).where(
        and_(
            VitalSignRecord.worker_id == worker_id,
            VitalSignRecord.measured_at >= start_date
        )
    ).order_by(desc(VitalSignRecord.measured_at)).limit(10)
    
    vital_signs = (await db.execute(vital_signs_query)).scalars().all()
    
    # 최신 인바디 기록
    inbody_query = select(InBodyRecord).where(
        InBodyRecord.worker_id == worker_id
    ).order_by(desc(InBodyRecord.measured_at)).limit(1)
    
    latest_inbody = (await db.execute(inbody_query)).scalar_one_or_none()
    
    return WorkerHealthSummary(
        worker_id=worker_id,
        worker_name=worker.name,
        recent_visits=[HealthRoomVisitResponse.from_orm(v) for v in visits],
        recent_medications=[MedicationRecordResponse.from_orm(m) for m in medications],
        recent_vital_signs=[VitalSignRecordResponse.from_orm(v) for v in vital_signs],
        latest_inbody=InBodyRecordResponse.from_orm(latest_inbody) if latest_inbody else None
    )


if __name__ == "__main__":
    print("✅ 건강관리실 API 핸들러 정의 완료")
    print("📝 API 엔드포인트:")
    print("  - POST /api/v1/health-room/medications - 투약 기록 생성")
    print("  - GET /api/v1/health-room/medications - 투약 기록 조회")
    print("  - POST /api/v1/health-room/vital-signs - 생체 신호 측정 기록 생성")
    print("  - GET /api/v1/health-room/vital-signs - 생체 신호 측정 기록 조회")
    print("  - POST /api/v1/health-room/inbody - 인바디 측정 기록 생성")
    print("  - GET /api/v1/health-room/inbody - 인바디 측정 기록 조회")
    print("  - POST /api/v1/health-room/visits - 건강관리실 방문 기록 생성")
    print("  - GET /api/v1/health-room/visits - 건강관리실 방문 기록 조회")
    print("  - GET /api/v1/health-room/stats - 건강관리실 통계")
    print("  - GET /api/v1/health-room/workers/{worker_id}/summary - 근로자 건강 요약")