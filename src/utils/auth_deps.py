"""
인증 관련 의존성 주입 유틸리티
Authentication dependency injection utilities
"""

from typing import Any, Dict

from fastapi import Depends, Request

from ..services.auth_service import (get_current_user_id_from_request,
                                     get_current_user_info_from_request)


def get_current_user_id(request: Request) -> str:
    """현재 사용자 ID를 반환하는 의존성"""
    return get_current_user_id_from_request(request)


def get_current_user_info(request: Request) -> Dict[str, Any]:
    """현재 사용자 정보를 반환하는 의존성"""
    return get_current_user_info_from_request(request)


# FastAPI 의존성으로 사용할 함수들
CurrentUserId = Depends(get_current_user_id)
CurrentUserInfo = Depends(get_current_user_info)
