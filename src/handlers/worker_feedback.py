"""
근로자 피드백 API 핸들러
Worker feedback API handlers
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..models.worker_feedback import WorkerFeedback
from ..schemas.worker_feedback import (
    WorkerFeedbackCreate,
    WorkerFeedbackList,
    WorkerFeedbackResponse,
    WorkerFeedbackUpdate,
)
from ..utils.auth_deps import CurrentUserId

router = APIRouter(prefix="/api/v1/worker-feedbacks", tags=["worker-feedbacks"])


@router.post("/", response_model=WorkerFeedbackResponse)
async def create_feedback(
    worker_id: int = Form(...),
    content: str = Form(...),
    created_by: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None),
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    """근로자 피드백 생성"""
    # 파일 업로드 처리
    photo_url = None
    if photo:
        import os
        import uuid
        from datetime import datetime
        
        # 업로드 디렉토리 생성
        upload_dir = "uploads/feedbacks"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 파일명 생성
        file_extension = os.path.splitext(photo.filename)[1]
        file_name = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(upload_dir, file_name)
        
        # 파일 저장
        with open(file_path, "wb") as f:
            content_bytes = await photo.read()
            f.write(content_bytes)
        
        photo_url = f"/{file_path}"
    
    # 피드백 생성
    feedback = WorkerFeedback(
        worker_id=worker_id,
        content=content,
        photo_url=photo_url,
        created_by=created_by or current_user_id,
    )
    
    db.add(feedback)
    await db.commit()
    await db.refresh(feedback)
    
    return feedback


@router.get("/worker/{worker_id}", response_model=WorkerFeedbackList)
async def get_worker_feedbacks(
    worker_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """특정 근로자의 피드백 목록 조회"""
    # 쿼리 실행
    result = await db.execute(
        select(WorkerFeedback)
        .where(WorkerFeedback.worker_id == worker_id)
        .order_by(WorkerFeedback.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    feedbacks = result.scalars().all()
    
    # 총 개수 조회
    count_result = await db.execute(
        select(WorkerFeedback).where(WorkerFeedback.worker_id == worker_id)
    )
    total = len(count_result.scalars().all())
    
    return {
        "items": feedbacks,
        "total": total,
    }


@router.get("/{feedback_id}", response_model=WorkerFeedbackResponse)
async def get_feedback(
    feedback_id: int,
    db: AsyncSession = Depends(get_db),
):
    """피드백 상세 조회"""
    result = await db.execute(
        select(WorkerFeedback).where(WorkerFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="피드백을 찾을 수 없습니다")
    
    return feedback


@router.put("/{feedback_id}", response_model=WorkerFeedbackResponse)
async def update_feedback(
    feedback_id: int,
    feedback_update: WorkerFeedbackUpdate,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    """피드백 수정"""
    result = await db.execute(
        select(WorkerFeedback).where(WorkerFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="피드백을 찾을 수 없습니다")
    
    # 업데이트
    for field, value in feedback_update.model_dump(exclude_unset=True).items():
        setattr(feedback, field, value)
    
    await db.commit()
    await db.refresh(feedback)
    
    return feedback


@router.delete("/{feedback_id}")
async def delete_feedback(
    feedback_id: int,
    current_user_id: str = CurrentUserId,
    db: AsyncSession = Depends(get_db),
):
    """피드백 삭제"""
    result = await db.execute(
        select(WorkerFeedback).where(WorkerFeedback.id == feedback_id)
    )
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="피드백을 찾을 수 없습니다")
    
    await db.delete(feedback)
    await db.commit()
    
    return {"message": "피드백이 삭제되었습니다"}