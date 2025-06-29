"""
대시보드 핸들러
Dashboard handler for SafeWork Pro
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from src.config.database import get_db
from src.models import (
    Worker, HealthExam, WorkEnvironment, 
    HealthEducation, AccidentReport, ChemicalSubstance
)

router = APIRouter(prefix="/api/v1", tags=["Dashboard"])

@router.get("/dashboard")
async def get_dashboard_data(db: Session = Depends(get_db)):
    """대시보드 데이터 조회"""
    
    # 현재 날짜
    now = datetime.now()
    thirty_days_ago = now - timedelta(days=30)
    
    # 근로자 통계
    total_workers = db.query(Worker).count()
    active_workers = db.query(Worker).filter(Worker.employment_status == "재직").count()
    on_leave_workers = db.query(Worker).filter(Worker.employment_status == "휴직").count()
    health_risk_workers = db.query(Worker).filter(Worker.health_status == "주의").count()
    
    # 건강진단 통계
    completed_this_month = db.query(HealthExam).filter(
        HealthExam.exam_date >= thirty_days_ago,
        HealthExam.exam_date <= now
    ).count()
    
    pending_exams = db.query(HealthExam).filter(
        HealthExam.exam_result == "pending"
    ).count()
    
    overdue_exams = db.query(HealthExam).filter(
        HealthExam.next_exam_date < now
    ).count()
    
    # 다음 예정된 검진
    next_exam = db.query(HealthExam).filter(
        HealthExam.next_exam_date >= now
    ).order_by(HealthExam.next_exam_date).first()
    
    # 작업환경 측정
    last_measurement = db.query(WorkEnvironment).order_by(
        WorkEnvironment.measurement_date.desc()
    ).first()
    
    # 교육 통계
    total_education = db.query(HealthEducation).count()
    completed_education = db.query(HealthEducation).filter(
        HealthEducation.completion_status == True
    ).count()
    completion_rate = (completed_education / total_education * 100) if total_education > 0 else 0
    
    # 사고 통계
    accidents_this_month = db.query(AccidentReport).filter(
        AccidentReport.accident_date >= thirty_days_ago
    ).count()
    
    # 화학물질 통계
    total_chemicals = db.query(ChemicalSubstance).count()
    hazardous_chemicals = db.query(ChemicalSubstance).filter(
        ChemicalSubstance.hazard_class.in_(["급성독성", "발암성"])
    ).count()
    
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