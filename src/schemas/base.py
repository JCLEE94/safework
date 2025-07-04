"""
기본 스키마 정의
Base schemas for API responses and common data structures
"""

from typing import Optional, Any, Dict, List
from pydantic import BaseModel
from datetime import datetime


class BaseResponse(BaseModel):
    """API 응답 기본 스키마"""
    success: bool = True
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(BaseResponse):
    """페이지네이션된 응답 스키마"""
    total: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0
    has_next: bool = False
    has_prev: bool = False


class ErrorResponse(BaseModel):
    """에러 응답 스키마"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class StatusResponse(BaseModel):
    """상태 응답 스키마"""
    status: str = "ok"
    service: str = "SafeWork Pro"
    version: str = "1.0.1"
    timestamp: datetime = datetime.now()
    components: Optional[Dict[str, str]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ListResponse(BaseModel):
    """목록 응답 기본 스키마"""
    items: List[Any] = []
    total: int = 0
    
    class Config:
        arbitrary_types_allowed = True


class CreateResponse(BaseModel):
    """생성 응답 스키마"""
    id: Any
    message: str = "성공적으로 생성되었습니다"
    created_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UpdateResponse(BaseModel):
    """업데이트 응답 스키마"""
    id: Any
    message: str = "성공적으로 업데이트되었습니다"
    updated_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DeleteResponse(BaseModel):
    """삭제 응답 스키마"""
    id: Any
    message: str = "성공적으로 삭제되었습니다"
    deleted_at: datetime = datetime.now()
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }