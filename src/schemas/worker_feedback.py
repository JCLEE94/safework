"""
근로자 피드백 스키마
Worker feedback Pydantic schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# Base schemas
class WorkerFeedbackBase(BaseModel):
    """피드백 기본 스키마"""
    content: str = Field(..., min_length=1, description="피드백 내용")
    photo_url: Optional[str] = Field(None, description="첨부 사진 URL")


class WorkerFeedbackCreate(WorkerFeedbackBase):
    """피드백 생성 스키마"""
    worker_id: int = Field(..., description="근로자 ID")
    created_by: Optional[str] = Field(None, description="작성자")


class WorkerFeedbackUpdate(BaseModel):
    """피드백 수정 스키마"""
    content: Optional[str] = Field(None, min_length=1, description="피드백 내용")
    photo_url: Optional[str] = Field(None, description="첨부 사진 URL")


class WorkerFeedbackResponse(WorkerFeedbackBase):
    """피드백 응답 스키마"""
    id: int
    worker_id: int
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkerFeedbackList(BaseModel):
    """피드백 목록 응답 스키마"""
    items: list[WorkerFeedbackResponse]
    total: int