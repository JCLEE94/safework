"""
건강진단 예약 관리 핸들러
Health Exam Appointment Management Handler
"""

from typing import Optional, List
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import json

from src.config.database import get_db
from src.models.health_exam_appointment import (
    HealthExamAppointment, AppointmentNotification,
    AppointmentStatus, NotificationType
)
from src.models.worker import Worker
from src.schemas.health_exam_appointment import (
    HealthExamAppointmentCreate, HealthExamAppointmentUpdate,
    HealthExamAppointmentResponse, AppointmentListResponse,
    HealthExamAppointmentStatusUpdate, AppointmentReminderRequest,
    AppointmentStatistics, BulkAppointmentCreate
)
from src.utils.auth_deps import get_current_user_id
from src.services.notifications import NotificationService
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1/health-exam-appointments", tags=["health-exam-appointments"])


@router.post("/", response_model=HealthExamAppointmentResponse)
async def create_appointment(
    appointment_data: HealthExamAppointmentCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """건강진단 예약 생성"""
    # 근로자 확인
    worker = await db.get(Worker, appointment_data.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    # 중복 예약 확인
    existing = await db.execute(
        select(HealthExamAppointment).where(
            and_(
                HealthExamAppointment.worker_id == appointment_data.worker_id,
                HealthExamAppointment.scheduled_date == appointment_data.scheduled_date,
                HealthExamAppointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )
        )
    )
    if existing.scalar():
        raise HTTPException(status_code=400, detail="해당 날짜에 이미 예약이 있습니다")
    
    # 예약 생성
    appointment = HealthExamAppointment(
        **appointment_data.model_dump(exclude={"notification_methods", "exam_items"}),
        notification_methods=json.dumps([m.value for m in appointment_data.notification_methods]),
        exam_items=json.dumps(appointment_data.exam_items or []),
        created_by=current_user_id
    )
    
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    
    # 응답 데이터 준비
    response = HealthExamAppointmentResponse.from_orm(appointment)
    response.worker_name = worker.name
    response.worker_employee_number = worker.employee_number
    
    return response


@router.get("/", response_model=AppointmentListResponse)
async def get_appointments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    worker_id: Optional[int] = None,
    status: Optional[AppointmentStatus] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    medical_institution: Optional[str] = None,
    exam_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """건강진단 예약 목록 조회"""
    query = select(HealthExamAppointment).options(selectinload(HealthExamAppointment.worker))
    
    # 필터링
    if worker_id:
        query = query.where(HealthExamAppointment.worker_id == worker_id)
    if status:
        query = query.where(HealthExamAppointment.status == status)
    if date_from:
        query = query.where(HealthExamAppointment.scheduled_date >= date_from)
    if date_to:
        query = query.where(HealthExamAppointment.scheduled_date <= date_to)
    if medical_institution:
        query = query.where(HealthExamAppointment.medical_institution.contains(medical_institution))
    if exam_type:
        query = query.where(HealthExamAppointment.exam_type == exam_type)
    
    # 정렬
    query = query.order_by(HealthExamAppointment.scheduled_date.desc())
    
    # 전체 개수
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar()
    
    # 페이징
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    # 응답 데이터 준비
    items = []
    for appointment in appointments:
        response = HealthExamAppointmentResponse.from_orm(appointment)
        if appointment.worker:
            response.worker_name = appointment.worker.name
            response.worker_employee_number = appointment.worker.employee_number
        items.append(response)
    
    return AppointmentListResponse(total=total, items=items)


@router.get("/statistics", response_model=AppointmentStatistics)
async def get_appointment_statistics(
    date_from: Optional[date] = Query(None, description="시작일"),
    date_to: Optional[date] = Query(None, description="종료일"),
    db: AsyncSession = Depends(get_db)
):
    """예약 통계 조회"""
    today = date.today()
    
    # 기본 날짜 범위 설정
    if not date_from:
        date_from = today - timedelta(days=365)
    if not date_to:
        date_to = today + timedelta(days=365)
    
    # 상태별 통계
    status_stats = await db.execute(
        select(
            HealthExamAppointment.status,
            func.count(HealthExamAppointment.id)
        ).where(
            and_(
                HealthExamAppointment.scheduled_date >= date_from,
                HealthExamAppointment.scheduled_date <= date_to
            )
        ).group_by(HealthExamAppointment.status)
    )
    
    stats = {
        "total_scheduled": 0,
        "total_confirmed": 0,
        "total_completed": 0,
        "total_cancelled": 0,
        "total_no_show": 0
    }
    
    for status, count in status_stats:
        if status == AppointmentStatus.SCHEDULED:
            stats["total_scheduled"] = count
        elif status == AppointmentStatus.CONFIRMED:
            stats["total_confirmed"] = count
        elif status == AppointmentStatus.COMPLETED:
            stats["total_completed"] = count
        elif status == AppointmentStatus.CANCELLED:
            stats["total_cancelled"] = count
        elif status == AppointmentStatus.NO_SHOW:
            stats["total_no_show"] = count
    
    # 예정된 예약
    upcoming_7_result = await db.execute(
        select(func.count(HealthExamAppointment.id)).where(
            and_(
                HealthExamAppointment.scheduled_date >= today,
                HealthExamAppointment.scheduled_date <= today + timedelta(days=7),
                HealthExamAppointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )
        )
    )
    stats["upcoming_7_days"] = upcoming_7_result.scalar() or 0
    
    upcoming_30_result = await db.execute(
        select(func.count(HealthExamAppointment.id)).where(
            and_(
                HealthExamAppointment.scheduled_date >= today,
                HealthExamAppointment.scheduled_date <= today + timedelta(days=30),
                HealthExamAppointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )
        )
    )
    stats["upcoming_30_days"] = upcoming_30_result.scalar() or 0
    
    # 기한 초과
    overdue_result = await db.execute(
        select(func.count(HealthExamAppointment.id)).where(
            and_(
                HealthExamAppointment.scheduled_date < today,
                HealthExamAppointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )
        )
    )
    stats["overdue"] = overdue_result.scalar() or 0
    
    # 비율 계산
    total = sum([stats["total_completed"], stats["total_cancelled"], stats["total_no_show"]])
    stats["completion_rate"] = (stats["total_completed"] / total * 100) if total > 0 else 0
    stats["no_show_rate"] = (stats["total_no_show"] / total * 100) if total > 0 else 0
    
    # 검진 유형별 통계
    type_stats = await db.execute(
        select(
            HealthExamAppointment.exam_type,
            func.count(HealthExamAppointment.id)
        ).where(
            and_(
                HealthExamAppointment.scheduled_date >= date_from,
                HealthExamAppointment.scheduled_date <= date_to
            )
        ).group_by(HealthExamAppointment.exam_type)
    )
    stats["by_exam_type"] = {exam_type: count for exam_type, count in type_stats}
    
    # 기관별 통계
    institution_stats = await db.execute(
        select(
            HealthExamAppointment.medical_institution,
            func.count(HealthExamAppointment.id)
        ).where(
            and_(
                HealthExamAppointment.scheduled_date >= date_from,
                HealthExamAppointment.scheduled_date <= date_to
            )
        ).group_by(HealthExamAppointment.medical_institution)
    )
    stats["by_institution"] = {institution: count for institution, count in institution_stats}
    
    return AppointmentStatistics(**stats)


@router.get("/{appointment_id}", response_model=HealthExamAppointmentResponse)
async def get_appointment(
    appointment_id: int,
    db: AsyncSession = Depends(get_db)
):
    """특정 예약 조회"""
    appointment = await db.get(HealthExamAppointment, appointment_id, options=[selectinload(HealthExamAppointment.worker)])
    if not appointment:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다")
    
    response = HealthExamAppointmentResponse.from_orm(appointment)
    if appointment.worker:
        response.worker_name = appointment.worker.name
        response.worker_employee_number = appointment.worker.employee_number
    
    return response


@router.put("/{appointment_id}", response_model=HealthExamAppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: HealthExamAppointmentUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """예약 정보 수정"""
    appointment = await db.get(HealthExamAppointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다")
    
    # 완료된 예약은 수정 불가
    if appointment.status == AppointmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="완료된 예약은 수정할 수 없습니다")
    
    # 업데이트
    update_data = appointment_data.model_dump(exclude_unset=True)
    if "notification_methods" in update_data:
        update_data["notification_methods"] = json.dumps([m.value for m in update_data["notification_methods"]])
    if "exam_items" in update_data:
        update_data["exam_items"] = json.dumps(update_data["exam_items"])
    
    for field, value in update_data.items():
        setattr(appointment, field, value)
    
    appointment.updated_by = current_user_id
    appointment.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(appointment)
    
    # Worker 정보 로드
    await db.refresh(appointment, ["worker"])
    
    response = HealthExamAppointmentResponse.from_orm(appointment)
    if appointment.worker:
        response.worker_name = appointment.worker.name
        response.worker_employee_number = appointment.worker.employee_number
    
    return response


@router.patch("/{appointment_id}/status", response_model=HealthExamAppointmentResponse)
async def update_appointment_status(
    appointment_id: int,
    status_update: HealthExamAppointmentStatusUpdate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """예약 상태 변경"""
    appointment = await db.get(HealthExamAppointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다")
    
    # 이전 상태 저장
    previous_status = appointment.status
    
    # 상태 변경
    appointment.status = status_update.status
    appointment.updated_by = current_user_id
    appointment.updated_at = datetime.now()
    
    # 상태별 추가 처리
    if status_update.status == AppointmentStatus.CONFIRMED:
        appointment.confirmed_at = datetime.now()
    elif status_update.status == AppointmentStatus.COMPLETED:
        appointment.completed_at = datetime.now()
    elif status_update.status == AppointmentStatus.CANCELLED:
        appointment.cancelled_at = datetime.now()
        appointment.cancellation_reason = status_update.reason
    elif status_update.status == AppointmentStatus.RESCHEDULED:
        # 재예약 시 새 예약 생성 필요
        appointment.cancelled_at = datetime.now()
        appointment.cancellation_reason = f"재예약: {status_update.reason}"
    
    await db.commit()
    await db.refresh(appointment, ["worker"])
    
    response = HealthExamAppointmentResponse.from_orm(appointment)
    if appointment.worker:
        response.worker_name = appointment.worker.name
        response.worker_employee_number = appointment.worker.employee_number
    
    logger.info(f"예약 상태 변경: {appointment_id} - {previous_status} -> {status_update.status}")
    
    return response


@router.post("/bulk", response_model=List[HealthExamAppointmentResponse])
async def create_bulk_appointments(
    bulk_data: BulkAppointmentCreate,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """대량 예약 생성"""
    # 근로자 확인
    workers_result = await db.execute(
        select(Worker).where(Worker.id.in_(bulk_data.worker_ids))
    )
    workers = {w.id: w for w in workers_result.scalars().all()}
    
    if len(workers) != len(bulk_data.worker_ids):
        raise HTTPException(status_code=400, detail="일부 근로자를 찾을 수 없습니다")
    
    # 시간대별 할당
    appointments = []
    worker_index = 0
    
    for time_slot in bulk_data.time_slots:
        for _ in range(bulk_data.workers_per_slot):
            if worker_index >= len(bulk_data.worker_ids):
                break
            
            worker_id = bulk_data.worker_ids[worker_index]
            
            appointment = HealthExamAppointment(
                worker_id=worker_id,
                exam_type=bulk_data.exam_type,
                scheduled_date=bulk_data.scheduled_date,
                scheduled_time=time_slot,
                medical_institution=bulk_data.medical_institution,
                institution_address=bulk_data.institution_address,
                institution_phone=bulk_data.institution_phone,
                notification_methods=json.dumps([m.value for m in bulk_data.notification_methods]),
                special_instructions=bulk_data.special_instructions,
                created_by=current_user_id
            )
            
            db.add(appointment)
            appointments.append(appointment)
            worker_index += 1
    
    await db.commit()
    
    # 응답 준비
    responses = []
    for appointment in appointments:
        await db.refresh(appointment)
        response = HealthExamAppointmentResponse.from_orm(appointment)
        worker = workers.get(appointment.worker_id)
        if worker:
            response.worker_name = worker.name
            response.worker_employee_number = worker.employee_number
        responses.append(response)
    
    return responses


@router.post("/reminders/send")
async def send_appointment_reminders(
    reminder_request: AppointmentReminderRequest,
    background_tasks: BackgroundTasks,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """예약 알림 발송"""
    today = date.today()
    
    # 알림 대상 조회
    query = select(HealthExamAppointment).options(selectinload(HealthExamAppointment.worker))
    
    if reminder_request.appointment_ids:
        query = query.where(HealthExamAppointment.id.in_(reminder_request.appointment_ids))
    else:
        # 특정 예약이 지정되지 않은 경우, 조건에 맞는 예약 조회
        days_before = reminder_request.days_before or 3
        target_date = today + timedelta(days=days_before)
        
        query = query.where(
            and_(
                HealthExamAppointment.scheduled_date == target_date,
                HealthExamAppointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.CONFIRMED])
            )
        )
        
        if not reminder_request.force_send:
            query = query.where(HealthExamAppointment.reminder_sent == False)
    
    result = await db.execute(query)
    appointments = result.scalars().all()
    
    # 백그라운드에서 알림 발송
    background_tasks.add_task(
        send_notifications_task,
        appointments,
        current_user_id
    )
    
    return {
        "message": f"{len(appointments)}건의 알림 발송을 시작했습니다",
        "appointment_count": len(appointments)
    }


async def send_notifications_task(appointments: List[HealthExamAppointment], user_id: str):
    """백그라운드 알림 발송 작업"""
    notification_service = NotificationService()
    
    for appointment in appointments:
        try:
            # 알림 메시지 생성
            message = f"""
[건강진단 예약 안내]
{appointment.worker.name}님, 건강진단 예약을 안내드립니다.

📅 일시: {appointment.scheduled_date} {appointment.scheduled_time or ''}
🏥 장소: {appointment.medical_institution}
📍 주소: {appointment.institution_address or ''}
📞 연락처: {appointment.institution_phone or ''}

{appointment.special_instructions or ''}

예약 변경이 필요하신 경우 보건관리자에게 연락주세요.
            """.strip()
            
            # 알림 발송 (실제 구현은 notification_service에서)
            if appointment.notification_methods:
                methods = json.loads(appointment.notification_methods)
                for method in methods:
                    # 실제 알림 발송 로직
                    logger.info(f"알림 발송: {method} - {appointment.worker.name}")
            
            # 발송 완료 표시
            appointment.reminder_sent = True
            appointment.reminder_sent_at = datetime.now()
            
        except Exception as e:
            logger.error(f"알림 발송 실패 - 예약 ID: {appointment.id}, 오류: {str(e)}")


@router.delete("/{appointment_id}")
async def delete_appointment(
    appointment_id: int,
    current_user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """예약 삭제"""
    appointment = await db.get(HealthExamAppointment, appointment_id)
    if not appointment:
        raise HTTPException(status_code=404, detail="예약을 찾을 수 없습니다")
    
    # 완료된 예약은 삭제 불가
    if appointment.status == AppointmentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="완료된 예약은 삭제할 수 없습니다")
    
    await db.delete(appointment)
    await db.commit()
    
    return {"message": "예약이 삭제되었습니다"}