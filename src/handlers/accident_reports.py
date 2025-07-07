from typing import Optional, List
from datetime import datetime, timedelta, date
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import os
import shutil
import json

from src.config.database import get_db
from src.config.settings import get_settings
from src.models import AccidentReport, Worker
from src.schemas.accident_report import (
    AccidentReportCreate, AccidentReportUpdate, AccidentReportResponse,
    AccidentReportListResponse, AccidentStatistics
)
from src.utils.auth_deps import get_current_user_id
)

router = APIRouter(prefix="/api/v1/accident-reports", tags=["accident-reports"])


@router.post("/", response_model=AccidentReportResponse)
async def create_accident_report(
    report_data: AccidentReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """산업재해 신고"""
    # Check if worker exists
    worker = await db.get(Worker, report_data.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    # Create accident report
    report = AccidentReport(**report_data.model_dump())
    report.created_by = current_user_id
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return report


@router.get("/", response_model=AccidentReportListResponse)
async def list_accident_reports(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    worker_id: Optional[int] = None,
    accident_type: Optional[str] = None,
    severity: Optional[str] = None,
    investigation_status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """산업재해 신고 목록 조회"""
    query = select(AccidentReport).options(selectinload(AccidentReport.worker))
    
    # Apply filters
    conditions = []
    if worker_id:
        conditions.append(AccidentReport.worker_id == worker_id)
    if accident_type:
        conditions.append(AccidentReport.accident_type == accident_type)
    if severity:
        conditions.append(AccidentReport.severity == severity)
    if investigation_status:
        conditions.append(AccidentReport.investigation_status == investigation_status)
    if start_date:
        conditions.append(AccidentReport.accident_datetime >= start_date)
    if end_date:
        conditions.append(AccidentReport.accident_datetime <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Get total count
    count_query = select(func.count()).select_from(AccidentReport)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(AccidentReport.accident_datetime.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return AccidentReportListResponse(
        items=items,
        total=total,
        page=page,
        pages=(total + size - 1) // size,
        size=size
    )


@router.get("/statistics", response_model=AccidentStatistics)
async def get_accident_statistics(db: AsyncSession = Depends(get_db)):
    """산업재해 통계 조회"""
    # Total accidents
    total_accidents = await db.scalar(select(func.count(AccidentReport.id)))
    
    # Total work days lost
    total_days_lost = await db.scalar(
        select(func.sum(AccidentReport.work_days_lost))
    ) or 0
    
    # Total cost
    total_cost_result = await db.execute(
        select(
            func.sum(AccidentReport.medical_cost + 
                    AccidentReport.compensation_cost + 
                    AccidentReport.other_cost).label("total")
        )
    )
    total_cost = total_cost_result.scalar() or 0
    
    # By type
    type_stats = await db.execute(
        select(
            AccidentReport.accident_type,
            func.count(AccidentReport.id).label("count")
        )
        .group_by(AccidentReport.accident_type)
    )
    
    # By severity
    severity_stats = await db.execute(
        select(
            AccidentReport.severity,
            func.count(AccidentReport.id).label("count")
        )
        .group_by(AccidentReport.severity)
    )
    
    # By month (last 12 months)
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    month_stats = await db.execute(
        select(
            func.date_trunc('month', AccidentReport.accident_datetime).label("month"),
            func.count(AccidentReport.id).label("count")
        )
        .where(AccidentReport.accident_datetime >= twelve_months_ago)
        .group_by("month")
        .order_by("month")
    )
    
    # Investigation pending
    investigation_pending = await db.scalar(
        select(func.count(AccidentReport.id))
        .where(AccidentReport.investigation_status.in_(['REPORTED', 'INVESTIGATING']))
    )
    
    # Actions pending
    actions_pending = await db.scalar(
        select(func.count(AccidentReport.id))
        .where(
            and_(
                AccidentReport.corrective_actions.isnot(None),
                AccidentReport.action_completion_date.is_(None)
            )
        )
    )
    
    # Recent accidents
    recent_query = await db.execute(
        select(AccidentReport)
        .options(selectinload(AccidentReport.worker))
        .order_by(AccidentReport.accident_datetime.desc())
        .limit(5)
    )
    recent_accidents = []
    for accident in recent_query.scalars():
        recent_accidents.append({
            "id": accident.id,
            "accident_date": accident.accident_datetime.isoformat(),
            "worker_name": accident.worker.name if accident.worker else "Unknown",
            "accident_type": accident.accident_type.value,
            "severity": accident.severity.value,
            "location": accident.accident_location
        })
    
    return AccidentStatistics(
        total_accidents=total_accidents,
        total_work_days_lost=total_days_lost,
        total_cost=float(total_cost),
        by_type={row[0].value: row[1] for row in type_stats},
        by_severity={row[0].value: row[1] for row in severity_stats},
        by_month={row[0].strftime("%Y-%m"): row[1] for row in month_stats},
        investigation_pending=investigation_pending,
        actions_pending=actions_pending,
        recent_accidents=recent_accidents
    )


@router.get("/safety-metrics")
async def get_safety_metrics(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """안전 성과 지표 조회"""
    if not year:
        year = datetime.utcnow().year
    
    # Calculate metrics for the year
    year_start = datetime(year, 1, 1)
    year_end = datetime(year, 12, 31, 23, 59, 59)
    
    # Total accidents this year
    year_accidents = await db.scalar(
        select(func.count(AccidentReport.id))
        .where(
            and_(
                AccidentReport.accident_datetime >= year_start,
                AccidentReport.accident_datetime <= year_end
            )
        )
    )
    
    # Lost time accidents
    lost_time_accidents = await db.scalar(
        select(func.count(AccidentReport.id))
        .where(
            and_(
                AccidentReport.accident_datetime >= year_start,
                AccidentReport.accident_datetime <= year_end,
                AccidentReport.work_days_lost > 0
            )
        )
    )
    
    # Total work days lost
    days_lost = await db.scalar(
        select(func.sum(AccidentReport.work_days_lost))
        .where(
            and_(
                AccidentReport.accident_datetime >= year_start,
                AccidentReport.accident_datetime <= year_end
            )
        )
    ) or 0
    
    # Fatalities
    fatalities = await db.scalar(
        select(func.count(AccidentReport.id))
        .where(
            and_(
                AccidentReport.accident_datetime >= year_start,
                AccidentReport.accident_datetime <= year_end,
                AccidentReport.severity == 'FATAL'
            )
        )
    )
    
    # Calculate frequency rate (accidents per 1M work hours)
    settings = get_settings()
    total_work_hours = settings.annual_work_days * settings.daily_work_hours * settings.default_worker_count
    frequency_rate = (year_accidents / total_work_hours) * 1000000 if total_work_hours > 0 else 0
    
    # Severity rate (days lost per 1000 work hours)
    severity_rate = (days_lost / total_work_hours) * 1000 if total_work_hours > 0 else 0
    
    # Compare with previous year
    prev_year_accidents = await db.scalar(
        select(func.count(AccidentReport.id))
        .where(
            and_(
                AccidentReport.accident_datetime >= datetime(year-1, 1, 1),
                AccidentReport.accident_datetime <= datetime(year-1, 12, 31, 23, 59, 59)
            )
        )
    )
    
    improvement_rate = ((prev_year_accidents - year_accidents) / prev_year_accidents * 100) if prev_year_accidents > 0 else 0
    
    return {
        "year": year,
        "total_accidents": year_accidents,
        "lost_time_accidents": lost_time_accidents,
        "total_days_lost": days_lost,
        "fatalities": fatalities,
        "frequency_rate": round(frequency_rate, 2),
        "severity_rate": round(severity_rate, 2),
        "previous_year_accidents": prev_year_accidents,
        "improvement_rate": round(improvement_rate, 2),
        "target_zero_days": 365 - year_accidents  # Days without accidents goal
    }


@router.get("/authority-reporting-required")
async def get_authority_reporting_required(db: AsyncSession = Depends(get_db)):
    """관계당국 신고 대상 사고 조회"""
    # Accidents that require authority reporting but haven't been reported
    unreported = await db.execute(
        select(AccidentReport)
        .options(selectinload(AccidentReport.worker))
        .where(
            and_(
                or_(
                    AccidentReport.severity.in_(['SEVERE', 'FATAL']),
                    AccidentReport.work_days_lost >= settings.work_days_lost_threshold  # 휴업일수 기준
                ),
                AccidentReport.reported_to_authorities == 'N'
            )
        )
        .order_by(AccidentReport.accident_datetime.desc())
    )
    
    unreported_list = []
    for accident in unreported.scalars():
        days_since = (datetime.utcnow() - accident.accident_datetime).days
        unreported_list.append({
            "id": accident.id,
            "accident_date": accident.accident_datetime.isoformat(),
            "worker_name": accident.worker.name if accident.worker else "Unknown",
            "severity": accident.severity.value,
            "work_days_lost": accident.work_days_lost,
            "days_since_accident": days_since,
            "reporting_deadline_passed": days_since * 24 > settings.accident_report_deadline_hours  # 신고 기한
        })
    
    return {
        "total_unreported": len(unreported_list),
        "accidents": unreported_list
    }


@router.get("/{report_id}", response_model=AccidentReportResponse)
async def get_accident_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """산업재해 신고서 조회"""
    result = await db.execute(
        select(AccidentReport)
        .options(selectinload(AccidentReport.worker))
        .where(AccidentReport.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="산업재해 신고서를 찾을 수 없습니다")
    
    return report


@router.put("/{report_id}", response_model=AccidentReportResponse)
async def update_accident_report(
    report_id: int,
    report_update: AccidentReportUpdate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """산업재해 신고서 수정"""
    report = await db.get(AccidentReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="산업재해 신고서를 찾을 수 없습니다")
    
    # Update fields
    update_data = report_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(report, field, value)
    
    report.updated_at = datetime.utcnow()
    report.updated_by = current_user_id
    await db.commit()
    await db.refresh(report)
    
    return report


@router.delete("/{report_id}")
async def delete_accident_report(report_id: int, db: AsyncSession = Depends(get_db)):
    """산업재해 신고서 삭제"""
    report = await db.get(AccidentReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="산업재해 신고서를 찾을 수 없습니다")
    
    await db.delete(report)
    await db.commit()
    
    return {"message": "산업재해 신고서가 삭제되었습니다"}


@router.post("/{report_id}/photos", response_model=dict)
async def upload_accident_photos(
    report_id: int,
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """사고 현장 사진 업로드"""
    report = await db.get(AccidentReport, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="산업재해 신고서를 찾을 수 없습니다")
    
    # Create upload directory
    settings = get_settings()
    upload_dir = os.path.join(settings.upload_dir, settings.accident_upload_subdir)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Get existing photos
    existing_photos = []
    if report.accident_photo_paths:
        try:
            existing_photos = json.loads(report.accident_photo_paths)
        except:
            existing_photos = []
    
    # Save files
    uploaded_paths = []
    for file in files:
        # Validate file type
        if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
            continue
        
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{report_id}_{timestamp}_{file.filename}"
        file_path = os.path.join(upload_dir, filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        uploaded_paths.append(file_path)
    
    # Update report record
    all_photos = existing_photos + uploaded_paths
    report.accident_photo_paths = json.dumps(all_photos)
    await db.commit()
    
    return {
        "message": f"{len(uploaded_paths)}개의 사진이 업로드되었습니다",
        "uploaded_count": len(uploaded_paths),
        "total_photos": len(all_photos)
    }