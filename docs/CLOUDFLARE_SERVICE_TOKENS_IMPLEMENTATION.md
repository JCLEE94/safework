# Cloudflare Service Tokens Implementation Guide

**Date**: 2025-07-09  
**Version**: 1.0.0  
**Scope**: Implementation of Cloudflare service tokens for enhanced security  
**Reference**: [Cloudflare Service Tokens Documentation](https://developers.cloudflare.com/cloudflare-one/identity/service-tokens/)

## 1. Overview

This document outlines the implementation of Cloudflare service tokens for SafeWork Pro to enhance security through machine-to-machine authentication. Service tokens provide a secure way to authenticate services without relying on user credentials.

### 1.1 Current State Analysis

**Existing Cloudflare Integration:**
- Cloudflare Access for Docker Registry authentication
- Cloudflare Tunnel for secure connectivity
- CF_ACCESS_TOKEN already used for registry access

**Service Token Benefits:**
- Enhanced security for API-to-API communication
- Reduced dependency on user tokens
- Better audit trails and access control
- Programmatic access management

## 2. Implementation Strategy

### 2.1 Service Token Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 Cloudflare Service Tokens                   │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    │
│  │   CI/CD     │    │   Registry  │    │   External  │    │
│  │  Pipeline   │    │   Access    │    │   Services  │    │
│  └─────────────┘    └─────────────┘    └─────────────┘    │
│         │                   │                   │         │
│         ▼                   ▼                   ▼         │
│  ┌─────────────────────────────────────────────────────────┐│
│  │            Service Token Validation             │    ││
│  │                                                │    ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ││
│  │  │    API      │  │  Middleware │  │  Services   │  ││
│  │  │   Gateway   │  │  Validation │  │    Auth     │  ││
│  │  └─────────────┘  └─────────────┘  └─────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 2.2 Implementation Phases

1. **Phase 1**: Service token creation and basic validation
2. **Phase 2**: Middleware integration for API authentication
3. **Phase 3**: CI/CD pipeline integration
4. **Phase 4**: External service integration
5. **Phase 5**: Token rotation and lifecycle management

## 3. Service Token Configuration

### 3.1 Token Types and Purposes

| Token Name | Purpose | Scope | Expiration |
|------------|---------|-------|------------|
| `safework-api` | API access authentication | All API endpoints | 1 year |
| `safework-registry` | Docker registry access | Registry operations | 1 year |
| `safework-cicd` | CI/CD pipeline authentication | Build and deploy | 6 months |
| `safework-monitoring` | Monitoring and health checks | Health endpoints | 1 year |
| `safework-external` | External service integration | Third-party APIs | 3 months |

### 3.2 Token Creation Process

1. **Create Service Tokens in Cloudflare Zero Trust:**
   - Navigate to Cloudflare Zero Trust Dashboard
   - Go to Access → Service Tokens
   - Create tokens for each service type
   - Configure appropriate policies

2. **Store Tokens Securely:**
   - Use Kubernetes secrets for production
   - Use GitHub secrets for CI/CD
   - Implement proper token rotation

## 4. Middleware Implementation

### 4.1 Service Token Validation Middleware

```python
# src/middleware/cloudflare_service_tokens.py
"""
Cloudflare Service Token validation middleware
"""

import hmac
import hashlib
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import jwt
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
        self.service_token_cache_ttl = 300  # 5 minutes
        
        # Service token configuration
        self.service_tokens = {
            'safework-api': {
                'client_id': settings.cf_service_token_api_client_id,
                'client_secret': settings.cf_service_token_api_client_secret,
                'allowed_endpoints': ['/api/v1/'],
                'required_scopes': ['api:read', 'api:write']
            },
            'safework-registry': {
                'client_id': settings.cf_service_token_registry_client_id,
                'client_secret': settings.cf_service_token_registry_client_secret,
                'allowed_endpoints': ['/v2/'],
                'required_scopes': ['registry:read', 'registry:write']
            },
            'safework-cicd': {
                'client_id': settings.cf_service_token_cicd_client_id,
                'client_secret': settings.cf_service_token_cicd_client_secret,
                'allowed_endpoints': ['/api/v1/pipeline'],
                'required_scopes': ['cicd:deploy']
            },
            'safework-monitoring': {
                'client_id': settings.cf_service_token_monitoring_client_id,
                'client_secret': settings.cf_service_token_monitoring_client_secret,
                'allowed_endpoints': ['/health', '/api/v1/monitoring'],
                'required_scopes': ['monitoring:read']
            }
        }
        
        # Public endpoints that don't require service tokens
        self.public_endpoints = {
            '/health',
            '/api/docs',
            '/api/redoc',
            '/openapi.json'
        }
    
    async def dispatch(self, request: Request, call_next):
        # Skip service token validation for public endpoints
        if request.url.path in self.public_endpoints:
            return await call_next(request)
        
        # Check for service token headers
        cf_access_client_id = request.headers.get('CF-Access-Client-Id')
        cf_access_client_secret = request.headers.get('CF-Access-Client-Secret')
        
        if cf_access_client_id and cf_access_client_secret:
            # Validate service token
            try:
                token_info = await self._validate_service_token(
                    cf_access_client_id, 
                    cf_access_client_secret, 
                    request.url.path
                )
                
                # Add service token info to request state
                request.state.service_token = token_info
                request.state.is_service_token = True
                
                logger.info(f"Service token validated: {token_info['name']}")
                
            except HTTPException as e:
                logger.warning(f"Service token validation failed: {e.detail}")
                return JSONResponse(
                    status_code=e.status_code,
                    content={"detail": e.detail}
                )
        
        return await call_next(request)
    
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
        
        if not cached_result:
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
                {"valid": True, "timestamp": datetime.utcnow().isoformat()},
                ttl=self.service_token_cache_ttl
            )
        
        return {
            "name": token_name,
            "client_id": client_id,
            "allowed_endpoints": token_config['allowed_endpoints'],
            "required_scopes": token_config['required_scopes'],
            "validated_at": datetime.utcnow().isoformat()
        }
    
    async def _validate_with_cloudflare(self, client_id: str, client_secret: str) -> bool:
        """Validate service token with Cloudflare API"""
        
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
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.rate_limits = {
            'safework-api': {'requests': 1000, 'window': 3600},     # 1000 req/hour
            'safework-registry': {'requests': 500, 'window': 3600}, # 500 req/hour
            'safework-cicd': {'requests': 100, 'window': 3600},     # 100 req/hour
            'safework-monitoring': {'requests': 2000, 'window': 3600}, # 2000 req/hour
        }
    
    async def dispatch(self, request: Request, call_next):
        # Check if request uses service token
        if hasattr(request.state, 'service_token'):
            service_token = request.state.service_token
            token_name = service_token['name']
            
            # Check rate limit
            if token_name in self.rate_limits:
                limit_config = self.rate_limits[token_name]
                
                if not await self._check_rate_limit(
                    service_token['client_id'], 
                    limit_config['requests'], 
                    limit_config['window']
                ):
                    return JSONResponse(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        content={"detail": "Service token rate limit exceeded"}
                    )
        
        return await call_next(request)
    
    async def _check_rate_limit(self, client_id: str, requests: int, window: int) -> bool:
        """Check rate limit for service token"""
        
        cache_key = f"service_token_rate_limit:{client_id}"
        
        try:
            current_count = await cache_service.get(cache_key) or 0
            
            if current_count >= requests:
                return False
            
            # Increment counter
            await cache_service.set(cache_key, current_count + 1, ttl=window)
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if rate limit check fails
```

### 4.2 Settings Configuration

```python
# src/config/settings.py - Additional settings for service tokens

class Settings(BaseSettings):
    # ... existing settings ...
    
    # Cloudflare Service Token Settings
    cloudflare_team_domain: str = Field(default="", env="CLOUDFLARE_TEAM_DOMAIN")
    
    # Service Token Client IDs and Secrets
    cf_service_token_api_client_id: str = Field(default="", env="CF_SERVICE_TOKEN_API_CLIENT_ID")
    cf_service_token_api_client_secret: str = Field(default="", env="CF_SERVICE_TOKEN_API_CLIENT_SECRET")
    
    cf_service_token_registry_client_id: str = Field(default="", env="CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID")
    cf_service_token_registry_client_secret: str = Field(default="", env="CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET")
    
    cf_service_token_cicd_client_id: str = Field(default="", env="CF_SERVICE_TOKEN_CICD_CLIENT_ID")
    cf_service_token_cicd_client_secret: str = Field(default="", env="CF_SERVICE_TOKEN_CICD_CLIENT_SECRET")
    
    cf_service_token_monitoring_client_id: str = Field(default="", env="CF_SERVICE_TOKEN_MONITORING_CLIENT_ID")
    cf_service_token_monitoring_client_secret: str = Field(default="", env="CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET")
    
    # Service Token Configuration
    enable_service_token_validation: bool = Field(default=True, env="ENABLE_SERVICE_TOKEN_VALIDATION")
    service_token_cache_ttl: int = Field(default=300, env="SERVICE_TOKEN_CACHE_TTL")
```

## 5. Deployment Configuration Updates

### 5.1 Kubernetes Secrets

```yaml
# k8s/secrets/cloudflare-service-tokens.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloudflare-service-tokens
  namespace: safework
type: Opaque
stringData:
  CLOUDFLARE_TEAM_DOMAIN: "your-team-domain"
  CF_SERVICE_TOKEN_API_CLIENT_ID: "api-client-id"
  CF_SERVICE_TOKEN_API_CLIENT_SECRET: "api-client-secret"
  CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID: "registry-client-id"
  CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET: "registry-client-secret"
  CF_SERVICE_TOKEN_CICD_CLIENT_ID: "cicd-client-id"
  CF_SERVICE_TOKEN_CICD_CLIENT_SECRET: "cicd-client-secret"
  CF_SERVICE_TOKEN_MONITORING_CLIENT_ID: "monitoring-client-id"
  CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET: "monitoring-client-secret"
```

### 5.2 Application Integration

```python
# src/app.py - Add service token middleware

from .middleware.cloudflare_service_tokens import (
    CloudflareServiceTokenMiddleware,
    ServiceTokenRateLimitMiddleware
)

def create_app() -> FastAPI:
    app = FastAPI(...)
    
    # Add middleware stack in correct order
    app.add_middleware(ServiceTokenRateLimitMiddleware)
    app.add_middleware(CloudflareServiceTokenMiddleware)
    
    # ... rest of middleware stack ...
    
    return app
```

## 6. CI/CD Pipeline Integration

### 6.1 GitHub Actions Configuration

```yaml
# .github/workflows/deploy.yml - Add service token usage

    - name: Setup Cloudflare Service Token
      run: |
        echo "CF_ACCESS_CLIENT_ID=${{ secrets.CF_SERVICE_TOKEN_CICD_CLIENT_ID }}" >> $GITHUB_ENV
        echo "CF_ACCESS_CLIENT_SECRET=${{ secrets.CF_SERVICE_TOKEN_CICD_CLIENT_SECRET }}" >> $GITHUB_ENV
    
    - name: Deploy with Service Token
      run: |
        curl -X POST "https://safework.jclee.me/api/v1/pipeline/deploy" \
          -H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" \
          -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET" \
          -H "Content-Type: application/json" \
          -d '{"version": "${{ github.sha }}"}'
```

### 6.2 Docker Registry Authentication

```bash
# scripts/docker-login-service-token.sh
#!/bin/bash

# Login to Docker registry using service token
docker login registry.jclee.me \
  -u "_token" \
  -p "$CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET"
```

## 7. External Service Integration

### 7.1 API Client Example

```python
# examples/service_token_client.py
"""
Example client using Cloudflare service tokens
"""

import httpx
from typing import Dict, Any

class SafeWorkServiceClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        """Make authenticated request using service token"""
        
        headers = {
            'CF-Access-Client-Id': self.client_id,
            'CF-Access-Client-Secret': self.client_secret,
            'Content-Type': 'application/json'
        }
        
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        
        kwargs['headers'] = headers
        
        async with httpx.AsyncClient() as client:
            response = await client.request(method, f"{self.base_url}{endpoint}", **kwargs)
            response.raise_for_status()
            return response.json()
    
    async def get_workers(self) -> Dict[str, Any]:
        """Get workers list"""
        return await self._make_request('GET', '/api/v1/workers')
    
    async def create_worker(self, worker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new worker"""
        return await self._make_request('POST', '/api/v1/workers', json=worker_data)

# Usage example
async def main():
    client = SafeWorkServiceClient(
        base_url="https://safework.jclee.me",
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    workers = await client.get_workers()
    print(f"Found {len(workers['items'])} workers")
```

## 8. Token Management and Rotation

### 8.1 Token Rotation Script

```python
# scripts/rotate_service_tokens.py
"""
Service token rotation script
"""

import asyncio
import httpx
from datetime import datetime, timedelta
from typing import Dict, List

class ServiceTokenRotator:
    def __init__(self, cloudflare_api_token: str, account_id: str):
        self.api_token = cloudflare_api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        
    async def rotate_token(self, token_name: str) -> Dict[str, str]:
        """Rotate a service token"""
        
        # Get current token
        current_token = await self._get_service_token(token_name)
        
        if not current_token:
            raise ValueError(f"Service token '{token_name}' not found")
        
        # Create new token
        new_token = await self._create_service_token(token_name)
        
        # Update Kubernetes secrets
        await self._update_kubernetes_secret(token_name, new_token)
        
        # Wait for propagation
        await asyncio.sleep(30)
        
        # Delete old token
        await self._delete_service_token(current_token['id'])
        
        return new_token
    
    async def _get_service_token(self, token_name: str) -> Dict[str, Any]:
        """Get service token by name"""
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/accounts/{self.account_id}/access/service_tokens",
                headers=headers
            )
            response.raise_for_status()
            
            tokens = response.json()['result']
            return next((token for token in tokens if token['name'] == token_name), None)
    
    async def _create_service_token(self, token_name: str) -> Dict[str, str]:
        """Create new service token"""
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'name': token_name,
            'duration': '8760h'  # 1 year
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/accounts/{self.account_id}/access/service_tokens",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            return response.json()['result']
    
    async def _update_kubernetes_secret(self, token_name: str, token_data: Dict[str, str]):
        """Update Kubernetes secret with new token"""
        
        # This would integrate with kubectl or Kubernetes API
        # Implementation depends on your deployment environment
        pass
    
    async def _delete_service_token(self, token_id: str):
        """Delete old service token"""
        
        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/accounts/{self.account_id}/access/service_tokens/{token_id}",
                headers=headers
            )
            response.raise_for_status()

# Usage
async def main():
    rotator = ServiceTokenRotator(
        cloudflare_api_token="your-api-token",
        account_id="your-account-id"
    )
    
    # Rotate API token
    new_token = await rotator.rotate_token("safework-api")
    print(f"Rotated API token: {new_token['client_id']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 Automated Rotation with Cron Job

```yaml
# k8s/jobs/token-rotation-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: service-token-rotation
  namespace: safework
spec:
  schedule: "0 2 1 * *"  # Monthly at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: token-rotator
            image: python:3.11-slim
            command: ["/bin/sh"]
            args:
            - -c
            - |
              pip install httpx
              python /scripts/rotate_service_tokens.py
            env:
            - name: CLOUDFLARE_API_TOKEN
              valueFrom:
                secretKeyRef:
                  name: cloudflare-credentials
                  key: api-token
            - name: CLOUDFLARE_ACCOUNT_ID
              valueFrom:
                secretKeyRef:
                  name: cloudflare-credentials
                  key: account-id
            volumeMounts:
            - name: scripts
              mountPath: /scripts
          volumes:
          - name: scripts
            configMap:
              name: token-rotation-scripts
          restartPolicy: OnFailure
```

## 9. Monitoring and Alerting

### 9.1 Service Token Metrics

```python
# src/services/service_token_metrics.py
"""
Service token monitoring and metrics
"""

from prometheus_client import Counter, Histogram, Gauge
from typing import Dict, Any
import time

# Metrics
service_token_requests_total = Counter(
    'service_token_requests_total',
    'Total service token requests',
    ['token_name', 'endpoint', 'status']
)

service_token_validation_duration = Histogram(
    'service_token_validation_duration_seconds',
    'Service token validation duration',
    ['token_name']
)

service_token_cache_hits = Counter(
    'service_token_cache_hits_total',
    'Service token cache hits',
    ['token_name']
)

service_token_expiry_gauge = Gauge(
    'service_token_expiry_days',
    'Days until service token expiry',
    ['token_name']
)

class ServiceTokenMetrics:
    @staticmethod
    def record_request(token_name: str, endpoint: str, status: str):
        """Record service token request"""
        service_token_requests_total.labels(
            token_name=token_name,
            endpoint=endpoint,
            status=status
        ).inc()
    
    @staticmethod
    def record_validation_duration(token_name: str, duration: float):
        """Record validation duration"""
        service_token_validation_duration.labels(
            token_name=token_name
        ).observe(duration)
    
    @staticmethod
    def record_cache_hit(token_name: str):
        """Record cache hit"""
        service_token_cache_hits.labels(
            token_name=token_name
        ).inc()
    
    @staticmethod
    def update_expiry_gauge(token_name: str, days_until_expiry: int):
        """Update expiry gauge"""
        service_token_expiry_gauge.labels(
            token_name=token_name
        ).set(days_until_expiry)
```

### 9.2 Alerting Rules

```yaml
# monitoring/alerts/service-token-alerts.yaml
groups:
- name: service-token-alerts
  rules:
  - alert: ServiceTokenExpiryWarning
    expr: service_token_expiry_days < 30
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Service token expiring soon"
      description: "Service token {{ $labels.token_name }} expires in {{ $value }} days"
  
  - alert: ServiceTokenValidationFailure
    expr: rate(service_token_requests_total{status="failure"}[5m]) > 0.1
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "High service token validation failure rate"
      description: "Service token {{ $labels.token_name }} has high failure rate"
  
  - alert: ServiceTokenRateLimitExceeded
    expr: rate(service_token_requests_total{status="rate_limited"}[5m]) > 0.01
    for: 1m
    labels:
      severity: warning
    annotations:
      summary: "Service token rate limit exceeded"
      description: "Service token {{ $labels.token_name }} is hitting rate limits"
```

## 10. Security Best Practices

### 10.1 Token Security Guidelines

1. **Storage Security:**
   - Never store tokens in plaintext
   - Use Kubernetes secrets or external secret management
   - Implement proper RBAC for secret access

2. **Rotation Policy:**
   - Rotate tokens every 3-6 months
   - Implement automated rotation
   - Monitor token expiry dates

3. **Access Control:**
   - Implement least privilege principle
   - Use different tokens for different services
   - Monitor token usage patterns

4. **Audit and Logging:**
   - Log all token validation attempts
   - Monitor for suspicious usage patterns
   - Implement alerting for failures

### 10.2 Emergency Procedures

1. **Token Compromise:**
   - Immediately revoke compromised token
   - Generate new token
   - Update all systems using the token
   - Investigate usage logs

2. **Service Disruption:**
   - Implement fallback authentication
   - Have emergency access procedures
   - Monitor service health

## 11. Implementation Checklist

### 11.1 Development Phase

- [ ] Create service tokens in Cloudflare Zero Trust
- [ ] Implement service token validation middleware
- [ ] Add settings configuration for tokens
- [ ] Create unit tests for token validation
- [ ] Implement token metrics and monitoring

### 11.2 Testing Phase

- [ ] Test token validation with valid tokens
- [ ] Test token validation with invalid tokens
- [ ] Test rate limiting functionality
- [ ] Test endpoint access control
- [ ] Test token rotation procedures

### 11.3 Deployment Phase

- [ ] Create Kubernetes secrets for tokens
- [ ] Update deployment configurations
- [ ] Deploy middleware to staging
- [ ] Test end-to-end functionality
- [ ] Deploy to production

### 11.4 Monitoring Phase

- [ ] Set up token expiry monitoring
- [ ] Configure alerting rules
- [ ] Monitor token usage patterns
- [ ] Implement automated rotation
- [ ] Create operational runbooks

## 12. Conclusion

Implementing Cloudflare service tokens provides enhanced security for SafeWork Pro through:

- **Improved Authentication**: Machine-to-machine authentication without user credentials
- **Better Access Control**: Fine-grained permissions for different services
- **Enhanced Monitoring**: Detailed audit trails and usage metrics
- **Automated Management**: Token rotation and lifecycle management

This implementation aligns with security best practices and provides a robust foundation for secure service-to-service communication in the SafeWork Pro ecosystem.

---

**Next Steps:**
1. Begin with Phase 1 implementation (token creation and validation)
2. Integrate with existing authentication system
3. Deploy to staging environment for testing
4. Implement monitoring and alerting
5. Roll out to production with proper monitoring

**References:**
- [Cloudflare Service Tokens Documentation](https://developers.cloudflare.com/cloudflare-one/identity/service-tokens/)
- [Cloudflare Zero Trust API](https://developers.cloudflare.com/api/operations/zero-trust-service-tokens-create-service-token)
- [Kubernetes Secrets Management](https://kubernetes.io/docs/concepts/configuration/secret/)