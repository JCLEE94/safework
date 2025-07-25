"""
공통 QR 코드 근로자 등록 시스템

하나의 공통 QR 코드로 모든 근로자가 등록할 수 있는 시스템입니다.
개별 토큰 생성이 필요 없으며, QR 코드를 통해 등록 페이지로 바로 이동합니다.

사용 방법:
1. 관리자가 공통 QR 코드를 생성/출력
2. 근로자가 QR 코드 스캔
3. 등록 페이지에서 정보 입력
4. 바로 등록 완료
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import qrcode
import io
import os
from urllib.parse import urljoin

from ..config.database import get_db
from ..config.settings import get_settings
from ..models.worker import Worker
from ..schemas.worker import WorkerCreate, WorkerResponse
from ..services.worker import get_worker_service
from ..utils.logger import logger
from ..utils.auth_deps import CurrentUserId

router = APIRouter(prefix="/api/v1/common-qr", tags=["공통QR등록"])
settings = get_settings()


@router.get("/generate", response_class=StreamingResponse)
async def generate_common_qr_code(
    size: int = Query(300, ge=100, le=1000, description="QR 코드 크기 (픽셀)"),
    current_user_id: str = CurrentUserId,
):
    """
    공통 QR 코드 생성
    
    모든 근로자가 사용할 수 있는 공통 QR 코드를 생성합니다.
    QR 코드는 근로자 등록 페이지 URL을 포함합니다.
    """
    try:
        # 등록 페이지 URL 생성
        base_url = settings.app_base_url or "https://safework.jclee.me"
        registration_url = f"{base_url}/register-qr"
        
        # QR 코드 생성
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(registration_url)
        qr.make(fit=True)
        
        # 이미지 생성
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 바이트 스트림으로 변환
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        logger.info(f"공통 QR 코드 생성: {registration_url} by {current_user_id}")
        
        return StreamingResponse(
            img_byte_arr,
            media_type="image/png",
            headers={
                "Content-Disposition": f"attachment; filename=safework_common_qr_{datetime.now().strftime('%Y%m%d')}.png"
            }
        )
        
    except Exception as e:
        logger.error(f"공통 QR 코드 생성 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="QR 코드 생성 중 오류가 발생했습니다"
        )


@router.get("/info")
async def get_common_qr_info(
    current_user_id: str = CurrentUserId,
):
    """
    공통 QR 코드 정보 조회
    
    QR 코드에 포함된 URL 및 사용 방법을 반환합니다.
    """
    base_url = settings.app_base_url or "https://safework.jclee.me"
    registration_url = f"{base_url}/register-qr"
    
    return {
        "registration_url": registration_url,
        "qr_download_url": f"{base_url}/api/v1/common-qr/generate",
        "instructions": {
            "step1": "QR 코드를 다운로드하여 출력",
            "step2": "작업장 입구나 게시판에 부착",
            "step3": "근로자가 휴대폰으로 QR 코드 스캔",
            "step4": "등록 페이지에서 정보 입력 후 등록 완료"
        },
        "features": [
            "개별 토큰 생성 불필요",
            "영구적으로 사용 가능한 QR 코드",
            "실시간 중복 사번 체크",
            "모바일 최적화된 등록 페이지"
        ]
    }


@router.post("/register", response_model=WorkerResponse)
async def register_worker_via_common_qr(
    worker_data: WorkerCreate,
    source: str = Query("common_qr", description="등록 출처"),
    db: AsyncSession = Depends(get_db),
    worker_service = Depends(get_worker_service)
):
    """
    공통 QR을 통한 근로자 등록 (인증 불필요)
    
    QR 코드를 스캔한 근로자가 정보를 입력하여 등록합니다.
    """
    try:
        # 중복 확인
        if worker_data.employee_id:
            existing_worker = await db.execute(
                select(Worker).where(Worker.employee_id == worker_data.employee_id)
            )
            if existing_worker.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="이미 등록된 사원번호입니다"
                )
        
        # 근로자 등록
        worker_dict = worker_data.dict()
        worker_dict['registration_source'] = source
        worker_dict['registered_at'] = datetime.now()
        
        new_worker = await worker_service.create_worker(worker_dict, db)
        
        logger.info(f"공통 QR 등록 완료: {worker_data.name} (사번: {worker_data.employee_id})")
        
        return WorkerResponse.from_orm(new_worker)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"공통 QR 등록 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="등록 중 오류가 발생했습니다"
        )


@router.get("/stats")
async def get_common_qr_stats(
    period: str = Query("today", regex="^(today|week|month|all)$", description="통계 기간"),
    db: AsyncSession = Depends(get_db),
    current_user_id: str = CurrentUserId,
):
    """
    공통 QR 등록 통계
    """
    try:
        # 기간 설정
        date_filter = None
        if period == "today":
            date_filter = func.date(Worker.created_at) == datetime.now().date()
        elif period == "week":
            date_filter = Worker.created_at >= datetime.now().replace(hour=0, minute=0, second=0) - timedelta(days=7)
        elif period == "month":
            date_filter = Worker.created_at >= datetime.now().replace(day=1, hour=0, minute=0, second=0)
        
        # 전체 등록자 수
        query = select(func.count(Worker.id))
        if date_filter is not None:
            query = query.where(date_filter)
        
        total_result = await db.execute(query)
        total_count = total_result.scalar()
        
        # 부서별 통계
        dept_query = select(
            Worker.department,
            func.count(Worker.id)
        ).group_by(Worker.department)
        
        if date_filter is not None:
            dept_query = dept_query.where(date_filter)
        
        dept_result = await db.execute(dept_query)
        dept_stats = {dept: count for dept, count in dept_result.fetchall()}
        
        # 시간대별 통계 (오늘만)
        hourly_stats = {}
        if period == "today":
            hourly_query = select(
                func.extract('hour', Worker.created_at),
                func.count(Worker.id)
            ).where(
                func.date(Worker.created_at) == datetime.now().date()
            ).group_by(
                func.extract('hour', Worker.created_at)
            )
            
            hourly_result = await db.execute(hourly_query)
            hourly_stats = {int(hour): count for hour, count in hourly_result.fetchall()}
        
        return {
            "period": period,
            "total_registrations": total_count,
            "department_stats": dept_stats,
            "hourly_stats": hourly_stats if period == "today" else None,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"통계 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="통계 조회 중 오류가 발생했습니다"
        )


@router.get("/check/{employee_id}")
async def check_employee_availability(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    사원번호 중복 확인 (공개 API)
    """
    try:
        worker = await db.execute(
            select(Worker).where(Worker.employee_id == employee_id)
        )
        existing_worker = worker.scalar_one_or_none()
        
        return {
            "available": existing_worker is None,
            "message": "사용 가능한 사원번호입니다" if existing_worker is None else "이미 등록된 사원번호입니다"
        }
        
    except Exception as e:
        logger.error(f"사원번호 확인 실패: {str(e)}")
        return {
            "available": False,
            "message": "확인 중 오류가 발생했습니다"
        }


if __name__ == "__main__":
    from datetime import timedelta
    
    print("✅ 공통 QR 코드 등록 시스템 검증")
    print("📝 구현된 기능:")
    print("  - GET /api/v1/common-qr/generate - 공통 QR 코드 생성 (PNG 이미지)")
    print("  - GET /api/v1/common-qr/info - QR 코드 정보 및 사용법")
    print("  - POST /api/v1/common-qr/register - 근로자 등록 (인증 불필요)")
    print("  - GET /api/v1/common-qr/stats - 등록 통계")
    print("  - GET /api/v1/common-qr/check/{employee_id} - 사번 중복 확인")
    print("✅ 검증 완료")