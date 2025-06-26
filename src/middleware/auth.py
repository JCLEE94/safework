"""
인증 미들웨어
Authentication middleware for JWT token validation
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from jose import JWTError, jwt
import json
import time

from ..config.settings import get_settings
from ..utils.logger import logger
from ..services.cache import cache_service


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """
    JWT 인증 미들웨어
    JWT authentication middleware for API security
    """
    
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.secret_key = settings.jwt_secret
        self.algorithm = settings.algorithm
        self.access_token_expire_minutes = settings.access_token_expire_minutes
        
        # Public endpoints that don't require authentication
        self.public_paths = {
            "/health",
            "/api/docs",
            "/api/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh"
        }
        
        # Paths that require authentication
        self.protected_path_prefixes = [
            "/api/v1/workers",
            "/api/v1/health-exams",
            "/api/v1/work-environments",
            "/api/v1/health-education",
            "/api/v1/chemical-substances",
            "/api/v1/accident-reports",
            "/api/v1/documents",
            "/api/v1/monitoring"
        ]
        
    async def dispatch(self, request: Request, call_next):
        # Skip authentication if disabled in settings (development mode)
        settings = get_settings()
        if getattr(settings, 'disable_auth', False):
            return await call_next(request)
            
        # Skip authentication for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)
            
        # Skip authentication for non-API paths (static files)
        if not any(request.url.path.startswith(prefix) for prefix in self.protected_path_prefixes):
            return await call_next(request)
            
        # TEMPORARY: Skip authentication for all endpoints in development/demo mode
        # TODO: Remove this in production
        logger.info(f"Skipping authentication for {request.url.path} - development mode")
        return await call_next(request)
            
        # Get token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Missing authentication token"}
            )
            
        token = auth_header.split(" ")[1]
        
        # Validate token
        try:
            # Check token blacklist in cache
            if await self._is_token_blacklisted(token):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has been revoked"}
                )
                
            # Decode and validate token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp) < datetime.utcnow():
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Token has expired"}
                )
                
            # Add user info to request state
            request.state.user_id = payload.get("sub")
            request.state.user_email = payload.get("email")
            request.state.user_role = payload.get("role", "user")
            request.state.token_jti = payload.get("jti")  # JWT ID for revocation
            
        except JWTError as e:
            logger.warning(f"JWT validation error: {e}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid authentication token"}
            )
            
        # Process request
        response = await call_next(request)
        
        # Add token refresh hint if close to expiration
        if hasattr(request.state, "token_exp"):
            time_until_exp = request.state.token_exp - datetime.utcnow()
            if time_until_exp < timedelta(minutes=5):
                response.headers["X-Token-Refresh-Hint"] = "true"
                
        return response
        
    async def _is_token_blacklisted(self, token: str) -> bool:
        """Check if token is in blacklist"""
        if not cache_service.redis_client:
            return False
            
        try:
            # Get JTI (JWT ID) from token without full validation
            unverified_payload = jwt.get_unverified_claims(token)
            jti = unverified_payload.get("jti")
            
            if not jti:
                return False
                
            # Check if JTI is in blacklist
            blacklisted = await cache_service.redis_client.get(f"blacklist:token:{jti}")
            return blacklisted is not None
            
        except Exception as e:
            logger.error(f"Error checking token blacklist: {e}")
            return False


class RoleBasedAccessMiddleware(BaseHTTPMiddleware):
    """
    역할 기반 접근 제어 미들웨어
    Role-based access control middleware
    """
    
    def __init__(self, app):
        super().__init__(app)
        
        # Define role permissions
        self.role_permissions = {
            "admin": {
                "read": True,
                "write": True,
                "delete": True,
                "admin": True
            },
            "manager": {
                "read": True,
                "write": True,
                "delete": False,
                "admin": False
            },
            "user": {
                "read": True,
                "write": False,
                "delete": False,
                "admin": False
            },
            "guest": {
                "read": True,
                "write": False,
                "delete": False,
                "admin": False
            }
        }
        
        # Define endpoint permissions
        self.endpoint_permissions = {
            # Workers endpoints
            "GET:/api/v1/workers": "read",
            "POST:/api/v1/workers": "write",
            "PUT:/api/v1/workers": "write",
            "DELETE:/api/v1/workers": "delete",
            
            # Health exams endpoints
            "GET:/api/v1/health-exams": "read",
            "POST:/api/v1/health-exams": "write",
            "PUT:/api/v1/health-exams": "write",
            "DELETE:/api/v1/health-exams": "delete",
            
            # Admin endpoints
            "GET:/api/v1/admin": "admin",
            "POST:/api/v1/admin": "admin",
            
            # Monitoring endpoints (manager and above)
            "GET:/api/v1/monitoring": "write",
            "POST:/api/v1/monitoring": "admin"
        }
        
    async def dispatch(self, request: Request, call_next):
        # Skip if no user role in request state
        if not hasattr(request.state, "user_role"):
            return await call_next(request)
            
        # Get user role
        user_role = request.state.user_role or "guest"
        
        # Check endpoint permission
        endpoint_key = f"{request.method}:{request.url.path}"
        
        # Find matching permission pattern
        required_permission = None
        for pattern, permission in self.endpoint_permissions.items():
            method, path_pattern = pattern.split(":")
            if request.method == method and request.url.path.startswith(path_pattern):
                required_permission = permission
                break
                
        # If permission required, check user role
        if required_permission:
            role_perms = self.role_permissions.get(user_role, {})
            if not role_perms.get(required_permission, False):
                logger.warning(
                    f"Access denied for user role '{user_role}' to {endpoint_key}"
                )
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Insufficient permissions"}
                )
                
        # Add role info to response headers
        response = await call_next(request)
        response.headers["X-User-Role"] = user_role
        
        return response


class SessionManagementMiddleware(BaseHTTPMiddleware):
    """
    세션 관리 미들웨어
    Session management middleware for enhanced security
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.session_timeout = 1800  # 30 minutes
        self.max_concurrent_sessions = 5
        
    async def dispatch(self, request: Request, call_next):
        # Get user ID from request state
        user_id = getattr(request.state, "user_id", None)
        
        if user_id:
            # Check concurrent sessions
            session_count = await self._get_active_session_count(user_id)
            
            if session_count >= self.max_concurrent_sessions:
                # Invalidate oldest session
                await self._invalidate_oldest_session(user_id)
                
            # Update session activity
            await self._update_session_activity(user_id, request)
            
        response = await call_next(request)
        
        # Add session info to response
        if user_id:
            response.headers["X-Session-Timeout"] = str(self.session_timeout)
            
        return response
        
    async def _get_active_session_count(self, user_id: str) -> int:
        """Get number of active sessions for user"""
        if not cache_service.redis_client:
            return 0
            
        try:
            sessions = await cache_service.redis_client.keys(f"session:{user_id}:*")
            return len(sessions)
        except Exception as e:
            logger.error(f"Error getting session count: {e}")
            return 0
            
    async def _invalidate_oldest_session(self, user_id: str):
        """Invalidate the oldest session for user"""
        if not cache_service.redis_client:
            return
            
        try:
            # Get all sessions
            sessions = await cache_service.redis_client.keys(f"session:{user_id}:*")
            
            if sessions:
                # Get session timestamps
                session_times = []
                for session_key in sessions:
                    data = await cache_service.redis_client.get(session_key)
                    if data:
                        session_data = json.loads(data)
                        session_times.append((session_key, session_data.get("last_activity", 0)))
                        
                # Sort by timestamp and remove oldest
                session_times.sort(key=lambda x: x[1])
                if session_times:
                    oldest_key = session_times[0][0]
                    await cache_service.redis_client.delete(oldest_key)
                    logger.info(f"Invalidated oldest session for user {user_id}")
                    
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            
    async def _update_session_activity(self, user_id: str, request: Request):
        """Update session last activity time"""
        if not cache_service.redis_client:
            return
            
        try:
            session_id = getattr(request.state, "token_jti", "default")
            session_key = f"session:{user_id}:{session_id}"
            
            session_data = {
                "user_id": user_id,
                "last_activity": time.time(),
                "ip_address": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown")
            }
            
            await cache_service.redis_client.setex(
                session_key,
                self.session_timeout,
                json.dumps(session_data)
            )
            
        except Exception as e:
            logger.error(f"Error updating session activity: {e}")