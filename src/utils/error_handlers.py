"""
전역 에러 핸들러
Global error handlers for the health management system
"""

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import traceback
from typing import Union

from .logger import logger, ErrorHandler


async def database_error_handler(request: Request, exc: SQLAlchemyError):
    """데이터베이스 에러 핸들러"""
    error_message = ErrorHandler.handle_database_error(
        error=exc,
        operation=f"{request.method} {request.url.path}",
        table=getattr(exc, 'table', None)
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": error_message,
            "error_type": "database_error",
            "timestamp": logger.logger.handlers[0].formatter.formatTime(
                logger.logger.makeRecord(
                    name="error", level=40, fn="", lno=0, 
                    msg="", args=(), exc_info=None
                )
            )
        }
    )


async def validation_error_handler(request: Request, exc: Union[RequestValidationError, ValidationError]):
    """검증 에러 핸들러"""
    # 상세한 에러 정보 추출
    error_details = []
    if hasattr(exc, 'errors'):
        for error in exc.errors():
            error_details.append({
                "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
                "message": error.get("msg", ""),
                "type": error.get("type", "")
            })
    
    logger.warning(
        "Validation error",
        endpoint=str(request.url.path),
        method=request.method,
        validation_errors=error_details
    )
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": "입력 데이터 검증에 실패했습니다.",
            "validation_errors": error_details,
            "error_type": "validation_error"
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP 예외 핸들러"""
    logger.warning(
        f"HTTP Exception: {exc.status_code}",
        endpoint=str(request.url.path),
        method=request.method,
        status_code=exc.status_code,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error_type": "http_error",
            "status_code": exc.status_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """일반 예외 핸들러"""
    logger.error(
        "Unhandled exception",
        error=exc,
        endpoint=str(request.url.path),
        method=request.method,
        traceback=traceback.format_exc()
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "서버 내부 오류가 발생했습니다.",
            "error_type": "internal_error",
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """데이터 무결성 에러 핸들러"""
    error_message = "데이터 무결성 제약 조건을 위반했습니다."
    
    # 구체적인 에러 메시지 생성
    if "duplicate key" in str(exc.orig).lower():
        error_message = "이미 존재하는 데이터입니다."
    elif "foreign key" in str(exc.orig).lower():
        error_message = "참조하는 데이터가 존재하지 않습니다."
    elif "not null" in str(exc.orig).lower():
        error_message = "필수 입력 항목이 누락되었습니다."
    
    logger.error(
        "Database integrity error",
        error=exc,
        endpoint=str(request.url.path),
        method=request.method
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "detail": error_message,
            "error_type": "integrity_error"
        }
    )


# 에러 핸들러 매핑
ERROR_HANDLERS = {
    SQLAlchemyError: database_error_handler,
    IntegrityError: integrity_error_handler,
    RequestValidationError: validation_error_handler,
    ValidationError: validation_error_handler,
    HTTPException: http_exception_handler,
    Exception: general_exception_handler,
}