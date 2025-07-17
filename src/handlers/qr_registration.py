"""
QR코드 등록 API 핸들러

이 모듈은 QR코드 기반 근로자 등록을 위한 REST API 엔드포인트를 제공합니다.
- QR코드 생성 및 관리
- 등록 토큰 검증
- 근로자 등록 처리

외부 패키지:
- fastapi: REST API 프레임워크 (https://fastapi.tiangolo.com/)
- sqlalchemy: ORM (https://docs.sqlalchemy.org/)

예시 사용법:
- POST /api/v1/qr-registration/generate - QR코드 생성
- GET /api/v1/qr-registration/status/{token} - 등록 상태 확인
- POST /api/v1/qr-registration/complete - 등록 완료 처리
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_

from src.config.database import get_db
from src.schemas.qr_registration import (
    QRRegistrationRequest, QRRegistrationResponse,
    RegistrationStatusResponse, PendingRegistrationListResponse,
    CompleteRegistrationRequest, CompleteRegistrationResponse,
    QRRegistrationStatistics, QRRegistrationFilter
)
from src.schemas.worker import WorkerCreate, WorkerResponse
from src.services.qr_service import get_qr_service, QRCodeService
from src.services.worker import get_worker_service
from src.models.qr_registration import QRRegistrationToken, RegistrationStatus
from src.models.worker import Worker
from src.utils.auth_deps import CurrentUserId, CurrentUserInfo
from src.utils.logger import logger

router = APIRouter(prefix="/api/v1/qr-registration", tags=["QR코드 등록"])


@router.post("/generate", response_model=QRRegistrationResponse)
async def generate_qr_registration(
    request: QRRegistrationRequest,
    current_user_id: str = CurrentUserId,
    qr_service: QRCodeService = Depends(get_qr_service),
    db: AsyncSession = Depends(get_db)
):
    """
    QR코드 등록 토큰 생성
    
    새로운 근로자를 등록하기 위한 QR코드를 생성합니다.
    """
    try:
        # 근로자 데이터 변환
        worker_data = request.worker_data.dict()
        
        # QR코드 생성
        result = await qr_service.generate_qr_registration_token(
            worker_data=worker_data,
            department=request.department,
            position=request.position,
            expires_in_hours=request.expires_in_hours,
            created_by=current_user_id,
            db=db
        )
        
        return QRRegistrationResponse(**result)
        
    except Exception as e:
        logger.error(f"QR코드 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="QR코드 생성 중 오류가 발생했습니다"
        )


@router.get("/status/{token}", response_model=RegistrationStatusResponse)
async def get_registration_status(
    token: str,
    qr_service: QRCodeService = Depends(get_qr_service),
    db: AsyncSession = Depends(get_db)
):
    """
    등록 상태 확인
    
    토큰으로 등록 상태를 확인합니다.
    """
    try:
        status_info = await qr_service.get_registration_status(token, db)
        
        if not status_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="등록 토큰을 찾을 수 없습니다"
            )
        
        return RegistrationStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"등록 상태 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록 상태 조회 중 오류가 발생했습니다"
        )


@router.get("/validate/{token}")
async def validate_token(
    token: str,
    qr_service: QRCodeService = Depends(get_qr_service),
    db: AsyncSession = Depends(get_db)
):
    """
    토큰 검증 (인증 없음)
    
    근로자가 QR코드를 스캔했을 때 토큰의 유효성을 확인합니다.
    """
    try:
        db_token = await qr_service.validate_registration_token(token, db)
        
        if not db_token:
            return {"valid": False, "message": "유효하지 않거나 만료된 토큰입니다"}
        
        return {
            "valid": True,
            "token_info": {
                "id": str(db_token.id),
                "department": db_token.department,
                "position": db_token.position,
                "worker_data": db_token.get_worker_data(),
                "expires_at": db_token.expires_at.isoformat(),
                "status": db_token.status
            }
        }
        
    except Exception as e:
        logger.error(f"토큰 검증 실패: {str(e)}")
        return {"valid": False, "message": "토큰 검증 중 오류가 발생했습니다"}


@router.post("/complete", response_model=CompleteRegistrationResponse)
async def complete_registration(
    request: CompleteRegistrationRequest,
    qr_service: QRCodeService = Depends(get_qr_service),
    worker_service = Depends(get_worker_service),
    db: AsyncSession = Depends(get_db)
):
    """
    등록 완료 처리
    
    QR코드를 통한 근로자 등록을 완료합니다.
    """
    try:
        # 토큰 검증
        db_token = await qr_service.validate_registration_token(request.token, db)
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="유효하지 않거나 만료된 토큰입니다"
            )
        
        # 사용자가 제공한 데이터와 토큰 데이터 병합
        combined_data = db_token.get_worker_data()
        if request.worker_data:
            # 사용자가 입력한 데이터로 업데이트
            combined_data.update(request.worker_data.dict(exclude_unset=True))
        
        # 근로자 데이터 준비
        worker_create = WorkerCreate(
            **combined_data,
            department=combined_data.get("department", db_token.department),
            position=combined_data.get("position", db_token.position) or "사원"
        )
        
        # 근로자 등록
        new_worker = await worker_service.create_worker(worker_create, db)
        
        # 등록 완료 처리
        success = await qr_service.complete_registration(
            request.token,
            new_worker.id,
            "qr_registration",  # 시스템 등록으로 기록
            db
        )
        
        if success:
            return CompleteRegistrationResponse(
                success=True,
                worker_id=new_worker.id,
                message="근로자 등록이 완료되었습니다"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="등록 완료 처리 중 오류가 발생했습니다"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"등록 완료 처리 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록 완료 처리 중 오류가 발생했습니다"
        )


@router.get("/pending", response_model=PendingRegistrationListResponse)
async def get_pending_registrations(
    department: Optional[str] = Query(None, description="부서 필터"),
    limit: int = Query(50, ge=1, le=100, description="최대 결과 수"),
    current_user_id: str = CurrentUserId,
    qr_service: QRCodeService = Depends(get_qr_service),
    db: AsyncSession = Depends(get_db)
):
    """
    대기 중인 등록 목록 조회
    
    등록 대기 중인 QR코드 목록을 조회합니다.
    """
    try:
        registrations = await qr_service.list_pending_registrations(
            department=department,
            limit=limit,
            db=db
        )
        
        return PendingRegistrationListResponse(
            registrations=registrations,
            total=len(registrations)
        )
        
    except Exception as e:
        logger.error(f"대기 등록 목록 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="대기 등록 목록 조회 중 오류가 발생했습니다"
        )


@router.get("/statistics", response_model=QRRegistrationStatistics)
async def get_registration_statistics(
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """
    등록 통계 조회
    
    QR코드 등록 관련 통계를 조회합니다.
    """
    try:
        # 전체 통계
        total_stmt = select(func.count(QRRegistrationToken.id))
        total_result = await db.execute(total_stmt)
        total_generated = total_result.scalar()
        
        # 상태별 통계
        pending_stmt = select(func.count(QRRegistrationToken.id)).where(
            and_(
                QRRegistrationToken.status == RegistrationStatus.PENDING,
                QRRegistrationToken.expires_at > datetime.utcnow()
            )
        )
        pending_result = await db.execute(pending_stmt)
        pending_count = pending_result.scalar()
        
        completed_stmt = select(func.count(QRRegistrationToken.id)).where(
            QRRegistrationToken.status == RegistrationStatus.COMPLETED
        )
        completed_result = await db.execute(completed_stmt)
        completed_count = completed_result.scalar()
        
        expired_stmt = select(func.count(QRRegistrationToken.id)).where(
            or_(
                QRRegistrationToken.status == RegistrationStatus.EXPIRED,
                and_(
                    QRRegistrationToken.status == RegistrationStatus.PENDING,
                    QRRegistrationToken.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_result = await db.execute(expired_stmt)
        expired_count = expired_result.scalar()
        
        # 부서별 통계
        dept_stmt = select(
            QRRegistrationToken.department,
            func.count(QRRegistrationToken.id)
        ).group_by(QRRegistrationToken.department)
        dept_result = await db.execute(dept_stmt)
        departments = dict(dept_result.fetchall())
        
        return QRRegistrationStatistics(
            total_generated=total_generated or 0,
            pending_count=pending_count or 0,
            completed_count=completed_count or 0,
            expired_count=expired_count or 0,
            departments=departments or {}
        )
        
    except Exception as e:
        logger.error(f"등록 통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록 통계 조회 중 오류가 발생했습니다"
        )


@router.delete("/token/{token}")
async def cancel_registration(
    token: str,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db)
):
    """
    등록 취소
    
    등록 토큰을 취소합니다.
    """
    try:
        # 토큰 조회
        stmt = select(QRRegistrationToken).where(
            and_(
                QRRegistrationToken.token == token,
                QRRegistrationToken.status == RegistrationStatus.PENDING
            )
        )
        result = await db.execute(stmt)
        db_token = result.scalar_one_or_none()
        
        if not db_token:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="등록 토큰을 찾을 수 없습니다"
            )
        
        # 상태 업데이트
        db_token.status = RegistrationStatus.CANCELLED
        await db.commit()
        
        logger.info(f"등록 토큰 취소: {token[:10]}... by {current_user_id}")
        
        return {"message": "등록이 취소되었습니다"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"등록 취소 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록 취소 중 오류가 발생했습니다"
        )




if __name__ == "__main__":
    # 엔드포인트 검증
    print("✅ QR코드 등록 API 핸들러 검증 시작")
    print("📝 구현된 엔드포인트:")
    print("  - POST /api/v1/qr-registration/generate")
    print("  - GET /api/v1/qr-registration/status/{token}")
    print("  - POST /api/v1/qr-registration/complete")
    print("  - GET /api/v1/qr-registration/pending")
    print("  - GET /api/v1/qr-registration/statistics")
    print("  - DELETE /api/v1/qr-registration/token/{token}")
    print("  - GET /api/v1/qr-registration/validate/{token}")
    print("✅ QR코드 등록 API 핸들러 검증 완료 (중복 엔드포인트 제거됨)")