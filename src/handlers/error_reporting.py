"""
에러 리포팅 API 핸들러
Error reporting API handlers for frontend error collection
"""

from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from src.services.github_issues import github_issues_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/error-reporting", tags=["error-reporting"])

class FrontendErrorReport(BaseModel):
    """프론트엔드 에러 리포트 모델"""
    message: str
    name: Optional[str] = None
    stack: Optional[str] = None
    filename: Optional[str] = None
    lineno: Optional[int] = None
    colno: Optional[int] = None
    url: Optional[str] = None
    userAgent: Optional[str] = None
    userId: Optional[str] = None
    severity: Optional[str] = "error"
    component: str = "frontend"
    customData: Optional[Dict[str, Any]] = None

class ManualErrorReport(BaseModel):
    """수동 에러 리포트 모델"""
    title: str
    description: str
    steps_to_reproduce: Optional[str] = None
    expected_behavior: Optional[str] = None
    actual_behavior: Optional[str] = None
    severity: Optional[str] = "error"
    component: Optional[str] = "general"
    environment: Optional[str] = "production"
    browser_info: Optional[str] = None
    user_id: Optional[str] = None

@router.post("/frontend-error")
async def report_frontend_error(
    error_report: FrontendErrorReport,
    request: Request,
    background_tasks: BackgroundTasks
):
    """프론트엔드 에러 리포트 수집"""
    try:
        # 클라이언트 정보 추가
        error_data = error_report.dict()
        error_data["clientIp"] = _get_client_ip(request)
        error_data["timestamp"] = datetime.now().isoformat()
        
        # User Agent가 없으면 헤더에서 추출
        if not error_data.get("userAgent"):
            error_data["userAgent"] = request.headers.get("user-agent")
        
        # 백그라운드에서 GitHub 이슈 생성
        background_tasks.add_task(
            github_issues_service.report_frontend_error,
            error_data
        )
        
        logger.info(f"Frontend error reported: {error_report.message}")
        
        return {
            "status": "success",
            "message": "에러가 성공적으로 리포트되었습니다",
            "error_id": str(hash(error_report.message))[:8]
        }
        
    except Exception as e:
        logger.error(f"Failed to report frontend error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="에러 리포트 전송에 실패했습니다"
        )

@router.post("/manual-report")
async def create_manual_report(
    report: ManualErrorReport,
    request: Request,
    background_tasks: BackgroundTasks
):
    """수동 에러/버그 리포트 생성"""
    try:
        # 수동 리포트를 GitHub 이슈로 변환
        error_data = {
            "message": report.title,
            "name": "ManualReport",
            "stack": f"""## 문제 설명
{report.description}

## 재현 단계
{report.steps_to_reproduce or '정보 없음'}

## 예상 동작
{report.expected_behavior or '정보 없음'}

## 실제 동작
{report.actual_behavior or '정보 없음'}

## 브라우저 정보
{report.browser_info or '정보 없음'}""",
            "url": str(request.url),
            "userAgent": request.headers.get("user-agent"),
            "userId": report.user_id,
            "severity": report.severity,
            "component": report.component,
            "environment": report.environment,
            "clientIp": _get_client_ip(request),
            "timestamp": datetime.now().isoformat()
        }
        
        # 백그라운드에서 GitHub 이슈 생성
        background_tasks.add_task(
            github_issues_service.report_frontend_error,
            error_data
        )
        
        logger.info(f"Manual report submitted: {report.title}")
        
        return {
            "status": "success",
            "message": "리포트가 성공적으로 제출되었습니다",
            "report_id": str(hash(report.title))[:8]
        }
        
    except Exception as e:
        logger.error(f"Failed to create manual report: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="리포트 제출에 실패했습니다"
        )

@router.get("/status")
async def get_reporting_status():
    """에러 리포팅 시스템 상태 확인"""
    try:
        # GitHub API 연결 상태 확인
        has_token = bool(github_issues_service.github_token)
        
        return {
            "status": "active" if has_token else "disabled",
            "github_integration": has_token,
            "repo": f"{github_issues_service.repo_owner}/{github_issues_service.repo_name}",
            "cache_size": len(github_issues_service.issue_cache),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get reporting status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="상태 확인에 실패했습니다"
        )

def _get_client_ip(request: Request) -> str:
    """클라이언트 IP 추출"""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip
        
    return request.client.host if request.client else "unknown"