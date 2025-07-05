"""
대시보드 핸들러
Dashboard handler for SafeWork Pro
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from src.config.database import get_db
from src.models import (
    Worker, HealthExam, WorkEnvironment, 
    HealthEducation, AccidentReport, ChemicalSubstance
)

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])

@router.get("/dashboard")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    """대시보드 데이터 조회"""
    
    # 현재 날짜
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # 근로자 통계
    total_workers_result = await db.execute(select(func.count(Worker.id)))
    total_workers = total_workers_result.scalar()
    
    active_workers_result = await db.execute(select(func.count(Worker.id)).where(Worker.is_active == True))
    active_workers = active_workers_result.scalar()
    
    on_leave_workers_result = await db.execute(select(func.count(Worker.id)).where(Worker.is_active == False))
    on_leave_workers = on_leave_workers_result.scalar()
    
    health_risk_workers_result = await db.execute(select(func.count(Worker.id)).where(Worker.health_status == "caution"))
    health_risk_workers = health_risk_workers_result.scalar()
    
    # 건강진단 통계
    completed_this_month_result = await db.execute(
        select(func.count(HealthExam.id)).where(
            HealthExam.exam_date >= thirty_days_ago,
            HealthExam.exam_date <= now
        )
    )
    completed_this_month = completed_this_month_result.scalar()
    
    pending_exams_result = await db.execute(
        select(func.count(HealthExam.id)).where(HealthExam.exam_result == "pending")
    )
    pending_exams = pending_exams_result.scalar()
    
    overdue_exams_result = await db.execute(
        select(func.count(HealthExam.id)).where(HealthExam.next_exam_date < now)
    )
    overdue_exams = overdue_exams_result.scalar()
    
    # 다음 예정된 검진
    next_exam_result = await db.execute(
        select(HealthExam).where(HealthExam.next_exam_date >= now).order_by(HealthExam.next_exam_date)
    )
    next_exam = next_exam_result.scalar_one_or_none()
    
    # 작업환경 측정
    last_measurement_result = await db.execute(
        select(WorkEnvironment).order_by(WorkEnvironment.measurement_date.desc())
    )
    last_measurement = last_measurement_result.scalar_one_or_none()
    
    # 교육 통계
    total_education_result = await db.execute(select(func.count(HealthEducation.id)))
    total_education = total_education_result.scalar()
    
    completed_education_result = await db.execute(
        select(func.count(HealthEducation.id)).where(HealthEducation.completion_status == True)
    )
    completed_education = completed_education_result.scalar()
    completion_rate = (completed_education / total_education * 100) if total_education > 0 else 0
    
    # 사고 통계
    accidents_this_month_result = await db.execute(
        select(func.count(AccidentReport.id)).where(AccidentReport.accident_datetime >= thirty_days_ago)
    )
    accidents_this_month = accidents_this_month_result.scalar()
    
    # 화학물질 통계
    total_chemicals_result = await db.execute(select(func.count(ChemicalSubstance.id)))
    total_chemicals = total_chemicals_result.scalar()
    
    hazardous_chemicals_result = await db.execute(
        select(func.count(ChemicalSubstance.id)).where(ChemicalSubstance.hazard_class.in_(["급성독성", "발암성"]))
    )
    hazardous_chemicals = hazardous_chemicals_result.scalar()
    
    return {
        "workers": {
            "total": total_workers,
            "active": active_workers,
            "on_leave": on_leave_workers,
            "health_risk": health_risk_workers
        },
        "health_exams": {
            "completed_this_month": completed_this_month,
            "pending": pending_exams,
            "overdue": overdue_exams,
            "next_scheduled": next_exam.next_exam_date.isoformat() if next_exam else None
        },
        "work_environment": {
            "last_measurement": last_measurement.measurement_date.isoformat() if last_measurement else "",
            "next_due": (last_measurement.measurement_date + timedelta(days=180)).isoformat() if last_measurement else "",
            "status": "정상",
            "high_risk_areas": 0
        },
        "education": {
            "total_sessions": total_education,
            "completed": completed_education,
            "completion_rate": round(completion_rate, 1),
            "upcoming": 0
        },
        "accidents": {
            "this_month": accidents_this_month,
            "total_year": accidents_this_month * 12,  # 임시 계산
            "severity_trend": "감소",
            "lost_workdays": 0
        },
        "chemicals": {
            "total": total_chemicals,
            "hazardous": hazardous_chemicals,
            "inventory_alerts": 0,
            "msds_updates": 0
        }
    }