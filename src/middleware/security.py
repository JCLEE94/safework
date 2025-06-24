"""
보안 강화 미들웨어
Security enhancement middleware
"""

import hashlib
import hmac
import secrets
import time
from typing import Optional, Dict, List, Set
from datetime import datetime, timedelta
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import json
import re
from urllib.parse import urlparse

from ..utils.logger import logger
from ..services.cache import cache_service


class CSRFProtectionMiddleware(BaseHTTPMiddleware):
    """
    CSRF 보호 미들웨어
    Cross-Site Request Forgery protection middleware
    """
    
    def __init__(self, app, secret_key: str = None):
        super().__init__(app)
        # Use a default secret key to avoid circular imports
        self.secret_key = secret_key or "default-csrf-secret-key-change-in-production"
        self.token_lifetime = 3600  # 1 hour
        self.safe_methods = {"GET", "HEAD", "OPTIONS"}
        
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for safe methods
        if request.method in self.safe_methods:
            return await call_next(request)
            
        # Skip for API endpoints (they should use API keys)
        if request.url.path.startswith("/api/"):
            return await call_next(request)
            
        # Get CSRF token from header or form
        csrf_token = request.headers.get("X-CSRF-Token") or \
                    request.headers.get("X-XSRF-Token")
        
        if not csrf_token:
            # Try to get from form data
            if request.method == "POST":
                form = await request.form()
                csrf_token = form.get("csrf_token")
                
        # Validate CSRF token
        if not self._validate_csrf_token(csrf_token):
            logger.warning(f"Invalid CSRF token from {request.client.host}")
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token validation failed"}
            )
            
        response = await call_next(request)
        
        # Add new CSRF token to response
        new_token = self._generate_csrf_token()
        response.headers["X-CSRF-Token"] = new_token
        
        return response
        
    def _generate_csrf_token(self) -> str:
        """Generate CSRF token"""
        timestamp = str(int(time.time()))
        message = f"{timestamp}:{secrets.token_urlsafe(16)}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{message}:{signature}"
        
    def _validate_csrf_token(self, token: Optional[str]) -> bool:
        """Validate CSRF token"""
        if not token:
            return False
            
        try:
            parts = token.split(":")
            if len(parts) != 3:
                return False
                
            timestamp, nonce, signature = parts
            
            # Check token age
            token_age = int(time.time()) - int(timestamp)
            if token_age > self.token_lifetime:
                return False
                
            # Verify signature
            message = f"{timestamp}:{nonce}"
            expected_signature = hmac.new(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"CSRF token validation error: {e}")
            return False


class XSSProtectionMiddleware(BaseHTTPMiddleware):
    """
    XSS 보호 미들웨어
    Cross-Site Scripting protection middleware
    """
    
    def __init__(self, app):
        super().__init__(app)
        # Dangerous patterns to detect
        self.xss_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
            re.compile(r'javascript:', re.IGNORECASE),
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
            re.compile(r'<iframe[^>]*>', re.IGNORECASE),
            re.compile(r'<object[^>]*>', re.IGNORECASE),
            re.compile(r'<embed[^>]*>', re.IGNORECASE),
            re.compile(r'<link[^>]*>', re.IGNORECASE),
            re.compile(r'<meta[^>]*>', re.IGNORECASE)
        ]
        
    async def dispatch(self, request: Request, call_next):
        # Check request body for XSS
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    # Check for XSS in JSON body
                    if request.headers.get("content-type", "").startswith("application/json"):
                        data = json.loads(body)
                        if self._contains_xss(data):
                            logger.warning(f"XSS attempt detected from {request.client.host}")
                            return JSONResponse(
                                status_code=400,
                                content={"detail": "Potential XSS detected in request"}
                            )
                except Exception:
                    pass
                    
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response
        
    def _contains_xss(self, data) -> bool:
        """Check if data contains XSS patterns"""
        if isinstance(data, str):
            for pattern in self.xss_patterns:
                if pattern.search(data):
                    return True
        elif isinstance(data, dict):
            for value in data.values():
                if self._contains_xss(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._contains_xss(item):
                    return True
        return False


class SQLInjectionProtectionMiddleware(BaseHTTPMiddleware):
    """
    SQL 인젝션 보호 미들웨어
    SQL Injection protection middleware
    """
    
    def __init__(self, app):
        super().__init__(app)
        # SQL injection patterns
        self.sql_patterns = [
            re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|CREATE|ALTER|EXEC|EXECUTE)\b)", re.IGNORECASE),
            re.compile(r"(--|\#|\/\*|\*\/)", re.IGNORECASE),  # SQL comments
            re.compile(r"(\bOR\b\s*\d+\s*=\s*\d+)", re.IGNORECASE),  # OR 1=1
            re.compile(r"(\bAND\b\s*\d+\s*=\s*\d+)", re.IGNORECASE),  # AND 1=1
            re.compile(r"(;|'|\")\s*(SELECT|INSERT|UPDATE|DELETE)", re.IGNORECASE),
            re.compile(r"xp_cmdshell", re.IGNORECASE),
            re.compile(r"(\bWAITFOR\s+DELAY\b)", re.IGNORECASE)
        ]
        
    async def dispatch(self, request: Request, call_next):
        # Check URL parameters
        if request.query_params:
            for key, value in request.query_params.items():
                if self._contains_sql_injection(str(value)):
                    logger.warning(f"SQL injection attempt in query params from {request.client.host}")
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid characters in query parameters"}
                    )
                    
        # Check request body
        if request.method in ["POST", "PUT", "PATCH"]:
            body = await request.body()
            if body:
                try:
                    if request.headers.get("content-type", "").startswith("application/json"):
                        data = json.loads(body)
                        if self._check_json_for_sql(data):
                            logger.warning(f"SQL injection attempt in body from {request.client.host}")
                            return JSONResponse(
                                status_code=400,
                                content={"detail": "Invalid characters in request body"}
                            )
                except Exception:
                    pass
                    
        return await call_next(request)
        
    def _contains_sql_injection(self, text: str) -> bool:
        """Check if text contains SQL injection patterns"""
        for pattern in self.sql_patterns:
            if pattern.search(text):
                return True
        return False
        
    def _check_json_for_sql(self, data) -> bool:
        """Recursively check JSON data for SQL injection"""
        if isinstance(data, str):
            return self._contains_sql_injection(data)
        elif isinstance(data, dict):
            for value in data.values():
                if self._check_json_for_sql(value):
                    return True
        elif isinstance(data, list):
            for item in data:
                if self._check_json_for_sql(item):
                    return True
        return False


class ContentSecurityPolicyMiddleware(BaseHTTPMiddleware):
    """
    콘텐츠 보안 정책 미들웨어
    Content Security Policy middleware
    """
    
    def __init__(self, app, policy: Optional[Dict[str, str]] = None):
        super().__init__(app)
        self.policy = policy or {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self'",
            "connect-src": "'self'",
            "media-src": "'self'",
            "object-src": "'none'",
            "frame-ancestors": "'none'",
            "base-uri": "'self'",
            "form-action": "'self'",
            "upgrade-insecure-requests": ""
        }
        
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Build CSP header
        csp_directives = []
        for directive, value in self.policy.items():
            if value:
                csp_directives.append(f"{directive} {value}")
            else:
                csp_directives.append(directive)
                
        csp_header = "; ".join(csp_directives)
        response.headers["Content-Security-Policy"] = csp_header
        
        # Additional security headers
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    API 키 인증 미들웨어
    API Key authentication middleware
    """
    
    def __init__(self, app, api_keys: Optional[Set[str]] = None):
        super().__init__(app)
        self.api_keys = api_keys or set()
        self.rate_limits: Dict[str, List[float]] = {}
        self.rate_limit_window = 60  # 1 minute
        self.rate_limit_max = 100  # Max requests per window
        
    async def dispatch(self, request: Request, call_next):
        # Skip auth for public endpoints
        public_paths = ["/health", "/api/docs", "/api/redoc", "/openapi.json"]
        if request.url.path in public_paths or not request.url.path.startswith("/api/"):
            return await call_next(request)
            
        # Get API key from header
        api_key = request.headers.get("X-API-Key")
        
        if not api_key or api_key not in self.api_keys:
            # Check for JWT token as fallback
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                logger.warning(f"Missing or invalid API key from {request.client.host}")
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing API key"}
                )
            # If JWT token exists, let it pass through for JWT middleware to handle
            return await call_next(request)
            
        # Rate limiting per API key
        now = time.time()
        if api_key not in self.rate_limits:
            self.rate_limits[api_key] = []
            
        # Clean old requests
        self.rate_limits[api_key] = [
            timestamp for timestamp in self.rate_limits[api_key]
            if now - timestamp < self.rate_limit_window
        ]
        
        # Check rate limit
        if len(self.rate_limits[api_key]) >= self.rate_limit_max:
            return JSONResponse(
                status_code=429,
                content={"detail": "API rate limit exceeded"}
            )
            
        # Add current request
        self.rate_limits[api_key].append(now)
        
        # Add API key info to request state
        request.state.api_key = api_key
        
        return await call_next(request)


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP 화이트리스트 미들웨어
    IP whitelist middleware for additional security
    """
    
    def __init__(self, app, whitelist: Optional[Set[str]] = None, enabled: bool = False):
        super().__init__(app)
        self.whitelist = whitelist or {"127.0.0.1", "::1", "localhost"}
        self.enabled = enabled
        
    async def dispatch(self, request: Request, call_next):
        if not self.enabled:
            return await call_next(request)
            
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if IP is whitelisted
        if client_ip not in self.whitelist:
            # Check X-Forwarded-For header for proxy situations
            forwarded_for = request.headers.get("X-Forwarded-For")
            if forwarded_for:
                # Get the first IP in the chain
                real_ip = forwarded_for.split(",")[0].strip()
                if real_ip not in self.whitelist:
                    logger.warning(f"Blocked request from non-whitelisted IP: {real_ip}")
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Access denied"}
                    )
            else:
                logger.warning(f"Blocked request from non-whitelisted IP: {client_ip}")
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Access denied"}
                )
                
        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    종합 보안 헤더 미들웨어
    Comprehensive security headers middleware
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Remove server information
        if "Server" in response.headers:
            del response.headers["Server"]
        if "X-Powered-By" in response.headers:
            del response.headers["X-Powered-By"]
        
        # Add comprehensive security headers
        response.headers.update({
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Permitted-Cross-Domain-Policies": "none",
            "X-Download-Options": "noopen",
            "X-DNS-Prefetch-Control": "off"
        })
        
        return response