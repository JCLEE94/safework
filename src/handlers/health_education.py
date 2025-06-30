from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import os
import shutil

from src.config.database import get_db
from src.models import HealthEducation, HealthEducationAttendance, Worker
from src.schemas.health_education import (
    HealthEducationCreate, HealthEducationUpdate, HealthEducationResponse,
    HealthEducationListResponse, EducationWithAttendanceResponse,
    AttendanceCreate, AttendanceUpdate, EducationStatistics
)

router = APIRouter(prefix="/api/v1/health-education", tags=["health-education"])


@router.post("/", response_model=HealthEducationResponse)
async def create_health_education(
    education_data: HealthEducationCreate,
    db: AsyncSession = Depends(get_db)
):
    """보건교육 등록"""
    education = HealthEducation(**education_data.model_dump())
    education.created_by = "system"  # Should come from auth
    db.add(education)
    await db.commit()
    await db.refresh(education)
    
    return education


@router.get("/", response_model=HealthEducationListResponse)
async def list_health_education(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    education_type: Optional[str] = None,
    education_method: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """보건교육 목록 조회"""
    query = select(HealthEducation)
    
    # Apply filters
    conditions = []
    if education_type:
        conditions.append(HealthEducation.education_type == education_type)
    if education_method:
        conditions.append(HealthEducation.education_method == education_method)
    if start_date:
        conditions.append(HealthEducation.education_date >= start_date)
    if end_date:
        conditions.append(HealthEducation.education_date <= end_date)
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Get total count
    count_query = select(func.count()).select_from(HealthEducation)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(HealthEducation.education_date.desc())
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return HealthEducationListResponse(
        items=items,
        total=total,
        page=page,
        pages=(total + size - 1) // size,
        size=size
    )


@router.get("/statistics", response_model=EducationStatistics)
async def get_education_statistics(db: AsyncSession = Depends(get_db)):
    """보건교육 통계 조회"""
    # Total sessions
    total_sessions = await db.scalar(select(func.count(HealthEducation.id)))
    
    # Total hours
    total_hours = await db.scalar(
        select(func.sum(HealthEducation.education_hours))
    ) or 0
    
    # Total attendees
    total_attendees = await db.scalar(
        select(func.count(HealthEducationAttendance.id))
    )
    
    # By type
    type_stats = await db.execute(
        select(
            HealthEducation.education_type,
            func.count(HealthEducation.id).label("count")
        )
        .group_by(HealthEducation.education_type)
    )
    
    # By method
    method_stats = await db.execute(
        select(
            HealthEducation.education_method,
            func.count(HealthEducation.id).label("count")
        )
        .group_by(HealthEducation.education_method)
    )
    
    # Completion rate
    completed_attendances = await db.scalar(
        select(func.count(HealthEducationAttendance.id))
        .where(HealthEducationAttendance.status == 'COMPLETED')
    )
    completion_rate = (completed_attendances / total_attendees * 100) if total_attendees > 0 else 0
    
    # Upcoming sessions
    upcoming_query = await db.execute(
        select(HealthEducation)
        .where(HealthEducation.education_date > datetime.utcnow())
        .order_by(HealthEducation.education_date)
        .limit(5)
    )
    upcoming_sessions = []
    for session in upcoming_query.scalars():
        upcoming_sessions.append({
            "id": session.id,
            "title": session.education_title,
            "type": session.education_type.value,
            "date": session.education_date.isoformat(),
            "hours": session.education_hours
        })
    
    # Overdue trainings (workers who haven't completed required training)
    # This is simplified - in reality would need more complex logic
    overdue_trainings = []
    
    return EducationStatistics(
        total_sessions=total_sessions,
        total_hours=float(total_hours),
        total_attendees=total_attendees,
        by_type={row[0].value: row[1] for row in type_stats},
        by_method={row[0].value: row[1] for row in method_stats},
        completion_rate=completion_rate,
        upcoming_sessions=upcoming_sessions,
        overdue_trainings=overdue_trainings
    )


@router.get("/{education_id}", response_model=EducationWithAttendanceResponse)
async def get_health_education(education_id: int, db: AsyncSession = Depends(get_db)):
    """보건교육 상세 조회"""
    result = await db.execute(
        select(HealthEducation)
        .options(selectinload(HealthEducation.attendances))
        .where(HealthEducation.id == education_id)
    )
    education = result.scalar_one_or_none()
    
    if not education:
        raise HTTPException(status_code=404, detail="보건교육을 찾을 수 없습니다")
    
    # Calculate attendance stats
    total_attendees = len(education.attendances)
    completed_count = sum(1 for a in education.attendances if a.status.value == "완료")
    
    response = EducationWithAttendanceResponse.model_validate(education)
    response.total_attendees = total_attendees
    response.completed_count = completed_count
    
    return response


@router.put("/{education_id}", response_model=HealthEducationResponse)
async def update_health_education(
    education_id: int,
    education_update: HealthEducationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """보건교육 정보 수정"""
    education = await db.get(HealthEducation, education_id)
    if not education:
        raise HTTPException(status_code=404, detail="보건교육을 찾을 수 없습니다")
    
    # Update fields
    update_data = education_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(education, field, value)
    
    education.updated_at = datetime.utcnow()
    education.updated_by = "system"  # Should come from auth
    await db.commit()
    await db.refresh(education)
    
    return education


@router.delete("/{education_id}")
async def delete_health_education(education_id: int, db: AsyncSession = Depends(get_db)):
    """보건교육 삭제"""
    education = await db.get(HealthEducation, education_id)
    if not education:
        raise HTTPException(status_code=404, detail="보건교육을 찾을 수 없습니다")
    
    await db.delete(education)
    await db.commit()
    
    return {"message": "보건교육이 삭제되었습니다"}


@router.post("/{education_id}/attendance", response_model=dict)
async def add_attendance(
    education_id: int,
    attendance_list: List[AttendanceCreate],
    db: AsyncSession = Depends(get_db)
):
    """교육 참석자 등록"""
    # Check if education exists
    education = await db.get(HealthEducation, education_id)
    if not education:
        raise HTTPException(status_code=404, detail="보건교육을 찾을 수 없습니다")
    
    added_count = 0
    for attendance_data in attendance_list:
        # Check if worker exists
        worker = await db.get(Worker, attendance_data.worker_id)
        if not worker:
            continue
        
        # Check if already registered
        existing = await db.scalar(
            select(HealthEducationAttendance)
            .where(
                and_(
                    HealthEducationAttendance.education_id == education_id,
                    HealthEducationAttendance.worker_id == attendance_data.worker_id
                )
            )
        )
        if existing:
            continue
        
        attendance = HealthEducationAttendance(
            education_id=education_id,
            **attendance_data.model_dump()
        )
        attendance.created_by = "system"  # Should come from auth
        db.add(attendance)
        added_count += 1
    
    await db.commit()
    
    return {
        "message": f"{added_count}명의 참석자가 등록되었습니다",
        "added_count": added_count
    }


@router.put("/attendance/{attendance_id}", response_model=dict)
async def update_attendance(
    attendance_id: int,
    attendance_update: AttendanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """교육 참석 정보 수정"""
    attendance = await db.get(HealthEducationAttendance, attendance_id)
    if not attendance:
        raise HTTPException(status_code=404, detail="참석 정보를 찾을 수 없습니다")
    
    # Update fields
    update_data = attendance_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(attendance, field, value)
    
    await db.commit()
    
    return {"message": "참석 정보가 수정되었습니다"}


@router.get("/worker/{worker_id}/history")
async def get_worker_education_history(
    worker_id: int,
    db: AsyncSession = Depends(get_db)
):
    """근로자 교육 이력 조회"""
    # Check if worker exists
    worker = await db.get(Worker, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    # Get education history
    result = await db.execute(
        select(HealthEducationAttendance, HealthEducation)
        .join(HealthEducation)
        .where(HealthEducationAttendance.worker_id == worker_id)
        .order_by(HealthEducation.education_date.desc())
    )
    
    history = []
    total_hours = 0
    for attendance, education in result:
        history.append({
            "education_id": education.id,
            "title": education.education_title,
            "type": education.education_type.value,
            "date": education.education_date.isoformat(),
            "hours": education.education_hours,
            "status": attendance.status.value,
            "test_score": attendance.test_score,
            "certificate_number": attendance.certificate_number
        })
        
        if attendance.status.value == "완료":
            total_hours += education.education_hours
    
    # Calculate required hours for this year
    current_year = datetime.utcnow().year
    required_hours = 8 if worker.hire_date.year == current_year else 12  # New: 8hrs, Regular: 12hrs/year
    
    return {
        "worker_id": worker_id,
        "worker_name": worker.name,
        "total_hours_completed": total_hours,
        "required_hours_this_year": required_hours,
        "compliance_status": "준수" if total_hours >= required_hours else "미달",
        "education_history": history
    }


@router.post("/{education_id}/materials", response_model=dict)
async def upload_education_materials(
    education_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """교육 자료 업로드"""
    education = await db.get(HealthEducation, education_id)
    if not education:
        raise HTTPException(status_code=404, detail="보건교육을 찾을 수 없습니다")
    
    # Create upload directory
    upload_dir = "uploads/education"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{education_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update education record
    education.education_material_path = file_path
    await db.commit()
    
    return {
        "message": "교육 자료가 업로드되었습니다",
        "file_path": file_path
    }