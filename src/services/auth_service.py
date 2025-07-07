"""
사용자 인증 서비스
Authentication and authorization service
"""

from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..config.settings import get_settings
from ..models.database import get_db
from ..utils.logger import get_logger

settings = get_settings()
logger = get_logger(__name__)
security = HTTPBearer()


class AuthService:
    """인증 서비스 클래스"""
    
    def __init__(self):
        self.jwt_secret = settings.jwt_secret
        self.jwt_algorithm = "HS256"
        self.jwt_expiration_hours = 24
        
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """JWT 액세스 토큰 생성"""
        try:
            payload = {
                "user_id": user_data.get("id"),
                "username": user_data.get("username"),
                "role": user_data.get("role", "user"),
                "exp": datetime.utcnow() + timedelta(hours=self.jwt_expiration_hours),
                "iat": datetime.utcnow(),
                "type": "access"
            }
            
            token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
            logger.info(f"Created access token for user: {user_data.get('username')}")
            return token
            
        except Exception as e:
            logger.error(f"Token creation failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="토큰 생성에 실패했습니다"
            )
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """JWT 토큰 검증 및 페이로드 반환"""
        try:
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.jwt_algorithm]
            )
            
            # 토큰 타입 확인
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="잘못된 토큰 타입입니다"
                )
            
            # 토큰 만료 확인
            if datetime.utcnow() > datetime.fromtimestamp(payload["exp"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="토큰이 만료되었습니다"
                )
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="토큰이 만료되었습니다"
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="유효하지 않은 토큰입니다"
            )
    
    def get_current_user_id(self, request: Request) -> str:
        """요청에서 현재 사용자 ID 추출"""
        try:
            # Authorization 헤더에서 토큰 추출
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                # 개발 모드에서는 기본 사용자 반환
                if settings.environment == "development":
                    return "dev_user"
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증 토큰이 필요합니다"
                )
            
            token = auth_header.split(" ")[1]
            payload = self.verify_token(token)
            return payload.get("user_id", "anonymous")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User ID extraction failed: {str(e)}")
            # 개발 모드에서는 기본 사용자 반환
            if settings.environment == "development":
                return "dev_user"
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자 인증에 실패했습니다"
            )
    
    def get_current_user_info(self, request: Request) -> Dict[str, Any]:
        """요청에서 현재 사용자 정보 추출"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                # 개발 모드에서는 기본 사용자 정보 반환
                if settings.environment == "development":
                    return {
                        "user_id": "dev_user",
                        "username": "developer",
                        "role": "admin"
                    }
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="인증 토큰이 필요합니다"
                )
            
            token = auth_header.split(" ")[1]
            payload = self.verify_token(token)
            
            return {
                "user_id": payload.get("user_id"),
                "username": payload.get("username"),
                "role": payload.get("role", "user")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User info extraction failed: {str(e)}")
            # 개발 모드에서는 기본 사용자 정보 반환
            if settings.environment == "development":
                return {
                    "user_id": "dev_user", 
                    "username": "developer",
                    "role": "admin"
                }
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="사용자 인증에 실패했습니다"
            )
    
    def hash_password(self, password: str) -> str:
        """비밀번호 해시 생성"""
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


# 글로벌 인증 서비스 인스턴스
auth_service = AuthService()


def get_auth_service() -> AuthService:
    """인증 서비스 의존성 주입"""
    return auth_service


def get_current_user_id_from_request(request: Request) -> str:
    """FastAPI 의존성으로 사용할 사용자 ID 추출 함수"""
    return auth_service.get_current_user_id(request)


def get_current_user_info_from_request(request: Request) -> Dict[str, Any]:
    """FastAPI 의존성으로 사용할 사용자 정보 추출 함수"""
    return auth_service.get_current_user_info(request)