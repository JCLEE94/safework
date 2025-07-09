"""
Cloudflare Service Token validation middleware
Implements service token authentication for machine-to-machine communication
"""

import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import httpx

from ..config.settings import get_settings
from ..utils.logger import logger
from ..services.cache import cache_service


class CloudflareServiceTokenMiddleware(BaseHTTPMiddleware):
    """
    Cloudflare Service Token validation middleware
    Validates service tokens for machine-to-machine authentication
    """
    
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.cloudflare_team_domain = settings.cloudflare_team_domain
        self.service_token_cache_ttl = settings.service_token_cache_ttl
        
        # Service token configuration
        self.service_tokens = {
            'safework-api': {
                'client_id': settings.cf_service_token_api_client_id,
                'client_secret': settings.cf_service_token_api_client_secret,
                'allowed_endpoints': ['/api/v1/'],
                'required_scopes': ['api:read', 'api:write'],
                'description': 'API access authentication'
            },
            'safework-registry': {
                'client_id': settings.cf_service_token_registry_client_id,
                'client_secret': settings.cf_service_token_registry_client_secret,
                'allowed_endpoints': ['/v2/'],
                'required_scopes': ['registry:read', 'registry:write'],
                'description': 'Docker registry access'
            },
            'safework-cicd': {
                'client_id': settings.cf_service_token_cicd_client_id,
                'client_secret': settings.cf_service_token_cicd_client_secret,
                'allowed_endpoints': ['/api/v1/pipeline'],
                'required_scopes': ['cicd:deploy'],
                'description': 'CI/CD pipeline authentication'
            },
            'safework-monitoring': {
                'client_id': settings.cf_service_token_monitoring_client_id,
                'client_secret': settings.cf_service_token_monitoring_client_secret,
                'allowed_endpoints': ['/health', '/api/v1/monitoring'],
                'required_scopes': ['monitoring:read'],
                'description': 'Monitoring and health checks'
            }
        }
        
        # Public endpoints that don't require service tokens
        self.public_endpoints = {
            '/health',
            '/api/docs',
            '/api/redoc',
            '/openapi.json',
            '/api/v1/auth/login',
            '/api/v1/auth/register'
        }
        
        # Skip service token validation if disabled
        self.enabled = settings.enable_service_token_validation
        
    async def dispatch(self, request: Request, call_next):
        # Skip if service token validation is disabled
        if not self.enabled:
            return await call_next(request)
            
        # Skip service token validation for public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)
        
        # Check for service token headers
        cf_access_client_id = request.headers.get('CF-Access-Client-Id')
        cf_access_client_secret = request.headers.get('CF-Access-Client-Secret')
        
        if cf_access_client_id and cf_access_client_secret:
            # Validate service token
            try:
                start_time = datetime.utcnow()
                
                token_info = await self._validate_service_token(
                    cf_access_client_id, 
                    cf_access_client_secret, 
                    request.url.path
                )
                
                validation_duration = (datetime.utcnow() - start_time).total_seconds()
                
                # Add service token info to request state
                request.state.service_token = token_info
                request.state.is_service_token = True
                request.state.validation_duration = validation_duration
                
                logger.info(
                    f"Service token validated successfully",
                    extra={
                        "token_name": token_info['name'],
                        "client_id": cf_access_client_id,
                        "endpoint": request.url.path,
                        "validation_duration": validation_duration
                    }
                )
                
                # Record metrics if available
                try:
                    from ..services.service_token_metrics import ServiceTokenMetrics
                    ServiceTokenMetrics.record_request(
                        token_info['name'], 
                        request.url.path, 
                        'success'
                    )
                    ServiceTokenMetrics.record_validation_duration(
                        token_info['name'], 
                        validation_duration
                    )
                except ImportError:
                    pass  # Metrics not available
                
            except HTTPException as e:
                logger.warning(
                    f"Service token validation failed",
                    extra={
                        "client_id": cf_access_client_id,
                        "endpoint": request.url.path,
                        "error": e.detail
                    }
                )
                
                # Record failure metrics if available
                try:
                    from ..services.service_token_metrics import ServiceTokenMetrics
                    ServiceTokenMetrics.record_request(
                        "unknown", 
                        request.url.path, 
                        'failure'
                    )
                except ImportError:
                    pass
                
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
        else:
            # No service token provided - check if JWT authentication is available
            auth_header = request.headers.get("Authorization")
            if not auth_header and not request.url.path.startswith("/api/v1/auth/"):
                logger.warning(
                    f"No authentication provided for protected endpoint",
                    extra={
                        "endpoint": request.url.path,
                        "client_ip": request.client.host if request.client else "unknown"
                    }
                )
        
        response = await call_next(request)
        
        # Add service token info to response headers for debugging
        if hasattr(request.state, 'service_token'):
            response.headers["X-Service-Token-Name"] = request.state.service_token['name']
            response.headers["X-Service-Token-Validation-Duration"] = str(request.state.validation_duration)
        
        return response
    
    async def _validate_service_token(
        self, 
        client_id: str, 
        client_secret: str, 
        endpoint: str
    ) -> Dict[str, Any]:
        """Validate Cloudflare service token"""
        
        # Find matching service token configuration
        token_config = None
        token_name = None
        
        for name, config in self.service_tokens.items():
            if config['client_id'] == client_id:
                token_config = config
                token_name = name
                break
        
        if not token_config:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token client ID"
            )
        
        # Validate client secret
        if not hmac.compare_digest(token_config['client_secret'], client_secret):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid service token client secret"
            )
        
        # Check endpoint permissions
        endpoint_allowed = any(
            endpoint.startswith(allowed_endpoint) 
            for allowed_endpoint in token_config['allowed_endpoints']
        )
        
        if not endpoint_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Service token '{token_name}' not authorized for endpoint '{endpoint}'"
            )
        
        # Check cache for token validation
        cache_key = f"service_token:{client_id}:validation"
        cached_result = await cache_service.get(cache_key)
        
        if cached_result:
            # Record cache hit
            try:
                from ..services.service_token_metrics import ServiceTokenMetrics
                ServiceTokenMetrics.record_cache_hit(token_name)
            except ImportError:
                pass
            
            logger.debug(f"Service token validation cache hit for {token_name}")
        else:
            # Validate with Cloudflare API
            is_valid = await self._validate_with_cloudflare(client_id, client_secret)
            
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Service token validation failed with Cloudflare"
                )
            
            # Cache successful validation
            await cache_service.set(
                cache_key, 
                {
                    "valid": True, 
                    "timestamp": datetime.utcnow().isoformat(),
                    "token_name": token_name
                },
                ttl=self.service_token_cache_ttl
            )
            
            logger.debug(f"Service token validation cached for {token_name}")
        
        return {
            "name": token_name,
            "client_id": client_id,
            "allowed_endpoints": token_config['allowed_endpoints'],
            "required_scopes": token_config['required_scopes'],
            "description": token_config['description'],
            "validated_at": datetime.utcnow().isoformat()
        }
    
    async def _validate_with_cloudflare(self, client_id: str, client_secret: str) -> bool:
        """Validate service token with Cloudflare API"""
        
        if not self.cloudflare_team_domain:
            logger.warning("Cloudflare team domain not configured, skipping API validation")
            return True  # Allow if not configured (for development)
        
        try:
            # Cloudflare service token validation endpoint
            url = f"https://{self.cloudflare_team_domain}.cloudflareaccess.com/cdn-cgi/access/login"
            
            headers = {
                'CF-Access-Client-Id': client_id,
                'CF-Access-Client-Secret': client_secret,
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    logger.debug("Cloudflare service token validation successful")
                    return True
                else:
                    logger.warning(f"Cloudflare validation failed: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error validating with Cloudflare: {e}")
            return False


class ServiceTokenRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for service tokens
    Provides different rate limits for different service token types
    """
    
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        
        # Rate limits configuration (requests per window)
        self.rate_limits = {
            'safework-api': {
                'requests': settings.service_token_api_rate_limit, 
                'window': settings.service_token_rate_limit_window
            },
            'safework-registry': {
                'requests': settings.service_token_registry_rate_limit, 
                'window': settings.service_token_rate_limit_window
            },
            'safework-cicd': {
                'requests': settings.service_token_cicd_rate_limit, 
                'window': settings.service_token_rate_limit_window
            },
            'safework-monitoring': {
                'requests': settings.service_token_monitoring_rate_limit, 
                'window': settings.service_token_rate_limit_window
            }
        }
        
        # Skip rate limiting if disabled
        self.enabled = settings.enable_service_token_rate_limiting
    
    async def dispatch(self, request: Request, call_next):
        # Skip if rate limiting is disabled
        if not self.enabled:
            return await call_next(request)
            
        # Check if request uses service token
        if hasattr(request.state, 'service_token'):
            service_token = request.state.service_token
            token_name = service_token['name']
            
            # Check rate limit
            if token_name in self.rate_limits:
                limit_config = self.rate_limits[token_name]
                
                is_within_limit = await self._check_rate_limit(
                    service_token['client_id'], 
                    limit_config['requests'], 
                    limit_config['window']
                )
                
                if not is_within_limit:
                    logger.warning(
                        f"Service token rate limit exceeded",
                        extra={
                            "token_name": token_name,
                            "client_id": service_token['client_id'],
                            "endpoint": request.url.path
                        }
                    )
                    
                    # Record rate limit metrics
                    try:
                        from ..services.service_token_metrics import ServiceTokenMetrics
                        ServiceTokenMetrics.record_request(
                            token_name, 
                            request.url.path, 
                            'rate_limited'
                        )
                    except ImportError:
                        pass
                    
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={
                            "detail": "Service token rate limit exceeded",
                            "retry_after": limit_config['window']
                        }
                    )
        
        return await call_next(request)
    
    async def _check_rate_limit(self, client_id: str, requests: int, window: int) -> bool:
        """Check rate limit for service token"""
        
        cache_key = f"service_token_rate_limit:{client_id}"
        
        try:
            current_count = await cache_service.get(cache_key)
            
            if current_count is None:
                current_count = 0
            
            if current_count >= requests:
                return False
            
            # Increment counter
            await cache_service.set(cache_key, current_count + 1, ttl=window)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if rate limit check fails


class ServiceTokenAuditMiddleware(BaseHTTPMiddleware):
    """
    Audit middleware for service token usage
    Logs all service token requests for security monitoring
    """
    
    def __init__(self, app):
        super().__init__(app)
        settings = get_settings()
        self.enabled = settings.enable_service_token_audit
        
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
        
        # Record request start
        start_time = datetime.utcnow()
        
        response = await call_next(request)
        
        # Record audit log if service token was used
        if hasattr(request.state, 'service_token'):
            service_token = request.state.service_token
            
            audit_data = {
                "timestamp": start_time.isoformat(),
                "token_name": service_token['name'],
                "client_id": service_token['client_id'],
                "endpoint": request.url.path,
                "method": request.method,
                "status_code": response.status_code,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "request_id": request.headers.get("X-Request-ID", "unknown")
            }
            
            logger.info(
                "Service token audit log",
                extra=audit_data
            )
            
            # Store in audit cache for monitoring
            audit_cache_key = f"service_token_audit:{service_token['client_id']}:{int(start_time.timestamp())}"
            await cache_service.set(audit_cache_key, audit_data, ttl=86400)  # 24 hours
        
        return response


# Helper functions for service token management
async def get_service_token_info(client_id: str) -> Optional[Dict[str, Any]]:
    """Get service token information by client ID"""
    
    settings = get_settings()
    service_tokens = {
        'safework-api': {
            'client_id': settings.cf_service_token_api_client_id,
            'name': 'safework-api',
            'description': 'API access authentication'
        },
        'safework-registry': {
            'client_id': settings.cf_service_token_registry_client_id,
            'name': 'safework-registry',
            'description': 'Docker registry access'
        },
        'safework-cicd': {
            'client_id': settings.cf_service_token_cicd_client_id,
            'name': 'safework-cicd',
            'description': 'CI/CD pipeline authentication'
        },
        'safework-monitoring': {
            'client_id': settings.cf_service_token_monitoring_client_id,
            'name': 'safework-monitoring',
            'description': 'Monitoring and health checks'
        }
    }
    
    for token_name, token_config in service_tokens.items():
        if token_config['client_id'] == client_id:
            return {
                'name': token_name,
                'description': token_config['description'],
                'client_id': client_id
            }
    
    return None


async def validate_service_token_permissions(
    client_id: str, 
    required_scopes: List[str]
) -> bool:
    """Validate service token has required scopes"""
    
    token_info = await get_service_token_info(client_id)
    if not token_info:
        return False
    
    # This would be extended to check actual scopes
    # For now, return True if token exists
    return True


# Dependency injection functions for FastAPI
def get_service_token_info_from_request(request: Request) -> Optional[Dict[str, Any]]:
    """Get service token info from request state"""
    return getattr(request.state, 'service_token', None)


def require_service_token_scope(required_scope: str):
    """Decorator to require specific service token scope"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # This would be implemented to check token scopes
            # For now, just pass through
            return await func(*args, **kwargs)
        return wrapper
    return decorator