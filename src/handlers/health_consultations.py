"""
보건상담 관리 API 핸들러
Health Consultation management API handlers
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import date, datetime
import logging

from ..config.database import get_db
from ..models.health_consultation import HealthConsultation, ConsultationFollowUp
from ..models.worker import Worker
from ..schemas.health_consultation import (
    HealthConsultationCreate, 
    HealthConsultationUpdate,
    HealthConsultationResponse, 
    HealthConsultationListResponse,
    ConsultationStatistics,
    ConsultationType,
    ConsultationStatus,
    HealthIssueCategory
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/health-consultations")

@router.get("/", response_model=HealthConsultationListResponse)
async def get_consultations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    worker_id: Optional[int] = Query(None, description="근로자 ID로 필터"),
    consultation_type: Optional[str] = Query(None, description="상담유형 필터"),
    start_date: Optional[date] = Query(None, description="시작일자"),
    end_date: Optional[date] = Query(None, description="종료일자"),
    search: Optional[str] = Query(None, description="근로자명 또는 상담내용으로 검색"),
    db: AsyncSession = Depends(get_db)
):
    """보건상담 목록 조회"""
    
    try:
        logger.info(f"보건상담 목록 조회 - skip: {skip}, limit: {limit}")
        
        # 근로자 정보와 함께 조회
        query = select(HealthConsultation).options(
            selectinload(HealthConsultation.worker)
        )
        
        # 필터 조건 구성
        conditions = []
        
        if worker_id:
            conditions.append(HealthConsultation.worker_id == worker_id)
        
        if consultation_type:
            conditions.append(HealthConsultation.consultation_type == consultation_type)
        
        if start_date:
            conditions.append(HealthConsultation.consultation_date >= start_date)
        
        if end_date:
            conditions.append(HealthConsultation.consultation_date <= end_date)
        
        if search:
            # 근로자명 또는 상담내용으로 검색
            query = query.join(Worker)
            conditions.append(
                or_(
                    Worker.name.ilike(f"%{search}%"),
                    HealthConsultation.consultation_content.ilike(f"%{search}%"),
                    HealthConsultation.recommendations.ilike(f"%{search}%")
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # 전체 개수 조회
        count_query = select(func.count()).select_from(HealthConsultation)
        if search:
            count_query = count_query.join(Worker)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        
        result = await db.execute(count_query)
        total = result.scalar()
        
        # 페이징 및 정렬
        query = query.offset(skip).limit(limit).order_by(
            HealthConsultation.consultation_date.desc()
        )
        
        result = await db.execute(query)
        consultations = result.scalars().all()
        
        # 응답 데이터에 근로자 정보 추가
        consultation_responses = []
        for consultation in consultations:
            consultation_data = {
                "id": consultation.id,
                "worker_id": consultation.worker_id,
                "consultation_date": consultation.consultation_date,
                "consultation_type": consultation.consultation_type,
                "symptoms": consultation.symptoms,
                "consultation_details": consultation.consultation_content,
                "action_taken": consultation.recommendations,
                "counselor_name": consultation.counselor_name or "미기재",
                "worker_name": consultation.worker.name if consultation.worker else None,
                "worker_employee_id": consultation.worker.employee_id if consultation.worker else None,
                "created_at": consultation.created_at,
                "updated_at": consultation.updated_at
            }
            consultation_responses.append(HealthConsultationResponse(**consultation_data))
        
        return HealthConsultationListResponse(
            items=consultation_responses,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error(f"보건상담 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="보건상담 목록을 조회하는 중 오류가 발생했습니다."
        )

@router.post("/", response_model=HealthConsultationResponse, status_code=status.HTTP_201_CREATED)
async def create_consultation(
    consultation_data: HealthConsultationCreate,
    db: AsyncSession = Depends(get_db)
):
    """보건상담 등록"""
    
    try:
        logger.info(f"보건상담 등록 - 근로자 ID: {consultation_data.worker_id}")
        
        # 근로자 존재 확인
        worker_query = select(Worker).where(
            and_(Worker.id == consultation_data.worker_id, Worker.is_active == True)
        )
        result = await db.execute(worker_query)
        worker = result.scalar_one_or_none()
        
        if not worker:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 근로자를 찾을 수 없습니다."
            )
        
        # 보건상담 생성
        consultation = HealthConsultation(**consultation_data.model_dump())
        db.add(consultation)
        await db.commit()
        await db.refresh(consultation)
        
        # 근로자 정보와 함께 조회
        consultation_query = select(HealthConsultation).options(
            selectinload(HealthConsultation.worker)
        ).where(HealthConsultation.id == consultation.id)
        
        result = await db.execute(consultation_query)
        consultation_with_worker = result.scalar_one()
        
        logger.info(f"보건상담 등록 완료 - ID: {consultation.id}")
        return HealthConsultationResponse.model_validate(consultation_with_worker, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보건상담 등록 오류: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="보건상담을 등록하는 중 오류가 발생했습니다."
        )

@router.get("/{consultation_id}", response_model=HealthConsultationResponse)
async def get_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """특정 보건상담 조회"""
    
    try:
        logger.info(f"보건상담 조회 - ID: {consultation_id}")
        
        query = select(HealthConsultation).options(
            selectinload(HealthConsultation.worker)
        ).where(HealthConsultation.id == consultation_id)
        
        result = await db.execute(query)
        consultation = result.scalar_one_or_none()
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 보건상담을 찾을 수 없습니다."
            )
        
        return HealthConsultationResponse.model_validate(consultation, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보건상담 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="보건상담을 조회하는 중 오류가 발생했습니다."
        )

@router.put("/{consultation_id}", response_model=HealthConsultationResponse)
async def update_consultation(
    consultation_id: int,
    consultation_data: HealthConsultationUpdate,
    db: AsyncSession = Depends(get_db)
):
    """보건상담 수정"""
    
    try:
        logger.info(f"보건상담 수정 - ID: {consultation_id}")
        
        # 기존 상담 조회
        query = select(HealthConsultation).where(HealthConsultation.id == consultation_id)
        result = await db.execute(query)
        consultation = result.scalar_one_or_none()
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 보건상담을 찾을 수 없습니다."
            )
        
        # 수정된 필드만 업데이트
        update_data = consultation_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(consultation, field, value)
        
        await db.commit()
        await db.refresh(consultation)
        
        # 근로자 정보와 함께 조회
        consultation_query = select(HealthConsultation).options(
            selectinload(HealthConsultation.worker)
        ).where(HealthConsultation.id == consultation.id)
        
        result = await db.execute(consultation_query)
        consultation_with_worker = result.scalar_one()
        
        logger.info(f"보건상담 수정 완료 - ID: {consultation_id}")
        return HealthConsultationResponse.model_validate(consultation_with_worker, from_attributes=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보건상담 수정 오류: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="보건상담을 수정하는 중 오류가 발생했습니다."
        )

@router.delete("/{consultation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consultation(
    consultation_id: int,
    db: AsyncSession = Depends(get_db)
):
    """보건상담 삭제"""
    
    try:
        logger.info(f"보건상담 삭제 - ID: {consultation_id}")
        
        query = select(HealthConsultation).where(HealthConsultation.id == consultation_id)
        result = await db.execute(query)
        consultation = result.scalar_one_or_none()
        
        if not consultation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 보건상담을 찾을 수 없습니다."
            )
        
        await db.delete(consultation)
        await db.commit()
        
        logger.info(f"보건상담 삭제 완료 - ID: {consultation_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"보건상담 삭제 오류: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="보건상담을 삭제하는 중 오류가 발생했습니다."
        )

@router.get("/statistics/summary")
async def get_consultation_statistics(
    start_date: Optional[date] = Query(None, description="통계 시작일"),
    end_date: Optional[date] = Query(None, description="통계 종료일"),
    db: AsyncSession = Depends(get_db)
):
    """보건상담 통계"""
    
    try:
        logger.info("보건상담 통계 조회")
        
        # 기본 조건
        conditions = []
        if start_date:
            conditions.append(HealthConsultation.consultation_date >= start_date)
        if end_date:
            conditions.append(HealthConsultation.consultation_date <= end_date)
        
        # 전체 상담 수
        total_query = select(func.count()).select_from(HealthConsultation)
        if conditions:
            total_query = total_query.where(and_(*conditions))
        
        result = await db.execute(total_query)
        total_consultations = result.scalar()
        
        # 상담 유형별 통계
        type_query = select(
            HealthConsultation.consultation_type,
            func.count().label('count')
        ).group_by(HealthConsultation.consultation_type)
        
        if conditions:
            type_query = type_query.where(and_(*conditions))
        
        result = await db.execute(type_query)
        type_stats = {row.consultation_type: row.count for row in result}
        
        # 월별 상담 수
        monthly_query = select(
            func.extract('year', HealthConsultation.consultation_date).label('year'),
            func.extract('month', HealthConsultation.consultation_date).label('month'),
            func.count().label('count')
        ).group_by(
            func.extract('year', HealthConsultation.consultation_date),
            func.extract('month', HealthConsultation.consultation_date)
        ).order_by(
            func.extract('year', HealthConsultation.consultation_date),
            func.extract('month', HealthConsultation.consultation_date)
        )
        
        if conditions:
            monthly_query = monthly_query.where(and_(*conditions))
        
        result = await db.execute(monthly_query)
        monthly_stats = [
            {
                "year": int(row.year),
                "month": int(row.month),
                "count": row.count
            }
            for row in result
        ]
        
        return {
            "total_consultations": total_consultations,
            "consultation_types": type_stats,
            "monthly_statistics": monthly_stats,
            "period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }
        
    except Exception as e:
        logger.error(f"보건상담 통계 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="보건상담 통계를 조회하는 중 오류가 발생했습니다."
        )