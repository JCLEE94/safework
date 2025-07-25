"""
인증 API 핸들러
Authentication API handlers for login, logout, and token management
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import (APIRouter, Depends, HTTPException, Request, Response,
                     status)
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..config.database import get_db
from ..services.cache import cache_service
from ..utils.logger import logger
from ..utils.security import PasswordHasher, PasswordValidator, TokenManager

router = APIRouter(prefix="/api/v1/auth", tags=["인증"])


# Pydantic models
class UserRegister(BaseModel):
    """사용자 등록 모델"""

    email: str = Field(..., description="이메일 주소 또는 사용자명")
    password: str = Field(..., min_length=8, description="비밀번호")
    name: str = Field(..., description="사용자 이름")
    department: Optional[str] = Field(None, description="부서")
    role: str = Field("user", description="사용자 역할")


class UserLogin(BaseModel):
    """사용자 로그인 모델"""

    email: str = Field(..., description="이메일 주소 또는 사용자명")
    password: str = Field(..., description="비밀번호")


class TokenResponse(BaseModel):
    """토큰 응답 모델"""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PasswordChange(BaseModel):
    """비밀번호 변경 모델"""

    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호")


class PasswordReset(BaseModel):
    """비밀번호 재설정 모델"""

    email: str = Field(..., description="이메일 주소 또는 사용자명")


# Initialize utilities
password_hasher = PasswordHasher()
token_manager = TokenManager()


@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """
    새 사용자 등록
    Register a new user
    """
    try:
        # Validate password strength
        is_valid, errors = PasswordValidator.validate(user_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "비밀번호가 보안 요구사항을 충족하지 않습니다",
                    "errors": errors,
                },
            )

        # Check if user already exists
        from sqlalchemy import select

        from ..models.user import User

        stmt = select(User).where(User.email == user_data.email)
        result = await db.execute(stmt)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="이미 등록된 이메일입니다"
            )

        # Create new user
        hashed_password = password_hasher.hash_password(user_data.password)

        new_user = User(
            email=user_data.email,
            password_hash=hashed_password,
            name=user_data.name,
            department=user_data.department,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow(),
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        # Generate tokens
        access_token = token_manager.create_access_token(
            data={
                "sub": str(new_user.id),
                "email": new_user.email,
                "role": new_user.role,
            }
        )

        refresh_token = token_manager.create_refresh_token(
            data={"sub": str(new_user.id)}
        )

        logger.info(f"New user registered: {new_user.email}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=token_manager.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="사용자 등록 중 오류가 발생했습니다",
        )


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    사용자 로그인
    User login
    """
    try:
        # Find user by email
        from sqlalchemy import select

        from ..models.user import User

        stmt = select(User).where(User.email == user_credentials.email)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
            )

        # Verify password
        if not password_hasher.verify_password(
            user_credentials.password, user.password_hash
        ):
            # Log failed attempt
            logger.warning(f"Failed login attempt for: {user_credentials.email}")

            # Track failed attempts in cache
            if cache_service.redis_client:
                failed_key = f"login:failed:{user_credentials.email}"
                try:
                    await cache_service.redis_client.incr(failed_key)
                    await cache_service.redis_client.expire(failed_key, 3600)  # 1 hour

                    # Check if account should be locked
                    failed_count = await cache_service.redis_client.get(failed_key)
                    if int(failed_count) >= 5:
                        user.is_active = False
                        await db.commit()
                        raise HTTPException(
                            status_code=status.HTTP_423_LOCKED,
                            detail="Too many failed attempts. Account locked.",
                        )
                except Exception as e:
                    logger.error(f"Cache error tracking failed login: {e}")

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="이메일 또는 비밀번호가 올바르지 않습니다",
            )

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="계정이 비활성화되었습니다",
            )

        # Update last login
        user.last_login = datetime.utcnow()
        await db.commit()

        # Clear failed attempts
        if cache_service.redis_client:
            try:
                await cache_service.redis_client.delete(
                    f"login:failed:{user_credentials.email}"
                )
            except Exception:
                pass

        # Generate tokens
        access_token = token_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        refresh_token = token_manager.create_refresh_token(data={"sub": str(user.id)})

        # Log successful login
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"User logged in: {user.email} from {client_ip}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=token_manager.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인 중 오류가 발생했습니다",
        )


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    사용자 로그아웃
    User logout
    """
    try:
        # Get token from request
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

            # Decode token to get JTI
            payload = token_manager.decode_token(token)
            if payload and "jti" in payload:
                # Add token to blacklist
                if cache_service.redis_client:
                    try:
                        # Calculate remaining TTL
                        exp = payload.get("exp")
                        if exp:
                            ttl = int(exp - datetime.utcnow().timestamp())
                            if ttl > 0:
                                await cache_service.redis_client.setex(
                                    f"blacklist:token:{payload['jti']}", ttl, "1"
                                )
                    except Exception as e:
                        logger.error(f"Error blacklisting token: {e}")

        # Clear any session data
        user_id = getattr(request.state, "user_id", None)
        if user_id and cache_service.redis_client:
            try:
                # Clear all user sessions
                sessions = await cache_service.redis_client.keys(f"session:{user_id}:*")
                if sessions:
                    await cache_service.redis_client.delete(*sessions)
            except Exception as e:
                logger.error(f"Error clearing sessions: {e}")

        logger.info(
            f"User logged out: {getattr(request.state, 'user_email', 'unknown')}"
        )

        return {"message": "로그아웃되었습니다"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        # Logout should always succeed
        return {"message": "로그아웃되었습니다"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """
    토큰 갱신
    Refresh access token using refresh token
    """
    try:
        # Decode refresh token
        payload = token_manager.decode_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user_id = payload.get("sub")

        # Get user from database
        from sqlalchemy import select

        from ..models.user import User

        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Generate new tokens
        new_access_token = token_manager.create_access_token(
            data={"sub": str(user.id), "email": user.email, "role": user.role}
        )

        # Optionally rotate refresh token
        new_refresh_token = token_manager.create_refresh_token(
            data={"sub": str(user.id)}
        )

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=token_manager.access_token_expire_minutes * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 갱신 중 오류가 발생했습니다",
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChange, request: Request, db: AsyncSession = Depends(get_db)
):
    """
    비밀번호 변경
    Change user password
    """
    try:
        # Get user ID from request state (set by JWT middleware)
        user_id = getattr(request.state, "user_id", None)

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="인증이 필요합니다"
            )

        # Get user from database
        from sqlalchemy import select

        from ..models.user import User

        stmt = select(User).where(User.id == int(user_id))
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="사용자를 찾을 수 없습니다",
            )

        # Verify current password
        if not password_hasher.verify_password(
            password_data.current_password, user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 올바르지 않습니다",
            )

        # Validate new password
        is_valid, errors = PasswordValidator.validate(password_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "새 비밀번호가 보안 요구사항을 충족하지 않습니다",
                    "errors": errors,
                },
            )

        # Hash and update password
        new_hash = password_hasher.hash_password(password_data.new_password)
        user.password_hash = new_hash
        user.password_changed_at = datetime.utcnow()

        await db.commit()

        logger.info(f"Password changed for user: {user.email}")

        return {"message": "비밀번호가 성공적으로 변경되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 변경 중 오류가 발생했습니다",
        )
