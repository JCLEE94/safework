# Cloudflare Service Token Usage Guide

**Date**: 2025-07-09  
**Version**: 1.0.0  
**Audience**: Developers, DevOps Engineers, Security Teams

## Overview

This guide provides practical instructions for using Cloudflare service tokens with SafeWork Pro. Service tokens enable secure machine-to-machine authentication without relying on user credentials.

## Quick Start

### 1. Setup Service Tokens

```bash
# Run the setup script
./scripts/setup-cloudflare-service-tokens.sh

# Or manually create tokens at:
# https://one.dash.cloudflare.com/ → Access → Service Tokens
```

### 2. Configure Environment

```bash
# Set environment variables
export CLOUDFLARE_TEAM_DOMAIN="your-team"
export CF_SERVICE_TOKEN_API_CLIENT_ID="your-api-client-id"
export CF_SERVICE_TOKEN_API_CLIENT_SECRET="your-api-client-secret"
```

### 3. Test Authentication

```bash
# Test API endpoint with service token
curl -H "CF-Access-Client-Id: your-client-id" \
     -H "CF-Access-Client-Secret: your-client-secret" \
     https://safework.jclee.me/api/v1/workers
```

## Service Token Types

### API Service Token (`safework-api`)
- **Purpose**: General API access
- **Endpoints**: `/api/v1/*`
- **Rate Limit**: 1000 requests/hour
- **Expiry**: 1 year

**Usage Example:**
```bash
curl -H "CF-Access-Client-Id: $CF_SERVICE_TOKEN_API_CLIENT_ID" \
     -H "CF-Access-Client-Secret: $CF_SERVICE_TOKEN_API_CLIENT_SECRET" \
     -H "Content-Type: application/json" \
     -X POST https://safework.jclee.me/api/v1/workers \
     -d '{"name": "김철수", "employee_id": "EMP001"}'
```

### Registry Service Token (`safework-registry`)
- **Purpose**: Docker registry access
- **Endpoints**: `/v2/*`
- **Rate Limit**: 500 requests/hour
- **Expiry**: 1 year

**Usage Example:**
```bash
# Docker login
echo "$CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET" | \
  docker login registry.jclee.me -u _token --password-stdin
```

### CI/CD Service Token (`safework-cicd`)
- **Purpose**: CI/CD pipeline authentication
- **Endpoints**: `/api/v1/pipeline/*`
- **Rate Limit**: 100 requests/hour
- **Expiry**: 6 months

**Usage Example:**
```bash
# Deploy via API
curl -H "CF-Access-Client-Id: $CF_SERVICE_TOKEN_CICD_CLIENT_ID" \
     -H "CF-Access-Client-Secret: $CF_SERVICE_TOKEN_CICD_CLIENT_SECRET" \
     -X POST https://safework.jclee.me/api/v1/pipeline/deploy \
     -d '{"version": "v1.2.3"}'
```

### Monitoring Service Token (`safework-monitoring`)
- **Purpose**: Health checks and monitoring
- **Endpoints**: `/health`, `/api/v1/monitoring/*`
- **Rate Limit**: 2000 requests/hour
- **Expiry**: 1 year

**Usage Example:**
```bash
# Health check
curl -H "CF-Access-Client-Id: $CF_SERVICE_TOKEN_MONITORING_CLIENT_ID" \
     -H "CF-Access-Client-Secret: $CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET" \
     https://safework.jclee.me/health
```

## Programming Examples

### Python Client

```python
import httpx
import asyncio
from typing import Dict, Any

class SafeWorkClient:
    def __init__(self, base_url: str, client_id: str, client_secret: str):
        self.base_url = base_url
        self.headers = {
            'CF-Access-Client-Id': client_id,
            'CF-Access-Client-Secret': client_secret,
            'Content-Type': 'application/json'
        }
    
    async def get_workers(self) -> Dict[str, Any]:
        """Get all workers"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/workers",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
    
    async def create_worker(self, worker_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new worker"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/api/v1/workers",
                headers=self.headers,
                json=worker_data
            )
            response.raise_for_status()
            return response.json()

# Usage
async def main():
    client = SafeWorkClient(
        base_url="https://safework.jclee.me",
        client_id="your-client-id",
        client_secret="your-client-secret"
    )
    
    # Get workers
    workers = await client.get_workers()
    print(f"Found {len(workers.get('items', []))} workers")
    
    # Create worker
    new_worker = await client.create_worker({
        "name": "김영희",
        "employee_id": "EMP002",
        "department": "안전관리팀"
    })
    print(f"Created worker: {new_worker}")

if __name__ == "__main__":
    asyncio.run(main())
```

### JavaScript/Node.js Client

```javascript
const axios = require('axios');

class SafeWorkClient {
  constructor(baseUrl, clientId, clientSecret) {
    this.baseUrl = baseUrl;
    this.headers = {
      'CF-Access-Client-Id': clientId,
      'CF-Access-Client-Secret': clientSecret,
      'Content-Type': 'application/json'
    };
  }

  async getWorkers() {
    const response = await axios.get(`${this.baseUrl}/api/v1/workers`, {
      headers: this.headers
    });
    return response.data;
  }

  async createWorker(workerData) {
    const response = await axios.post(`${this.baseUrl}/api/v1/workers`, workerData, {
      headers: this.headers
    });
    return response.data;
  }
}

// Usage
const client = new SafeWorkClient(
  'https://safework.jclee.me',
  process.env.CF_SERVICE_TOKEN_API_CLIENT_ID,
  process.env.CF_SERVICE_TOKEN_API_CLIENT_SECRET
);

client.getWorkers()
  .then(workers => console.log(`Found ${workers.items.length} workers`))
  .catch(error => console.error('Error:', error));
```

### Shell Script Integration

```bash
#!/bin/bash

# SafeWork Pro API wrapper using service tokens
SAFEWORK_API_URL="https://safework.jclee.me/api/v1"

# Function to make authenticated API calls
safework_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    curl -s -X "$method" \
        -H "CF-Access-Client-Id: $CF_SERVICE_TOKEN_API_CLIENT_ID" \
        -H "CF-Access-Client-Secret: $CF_SERVICE_TOKEN_API_CLIENT_SECRET" \
        -H "Content-Type: application/json" \
        ${data:+-d "$data"} \
        "$SAFEWORK_API_URL$endpoint"
}

# Get workers
echo "Fetching workers..."
safework_api GET "/workers" | jq '.items[] | .name'

# Create worker
echo "Creating worker..."
safework_api POST "/workers" '{
    "name": "박민수",
    "employee_id": "EMP003",
    "department": "건설팀"
}'
```

## Token Management

### Check Token Expiry

```bash
# Use the rotation script
python3 scripts/rotate-service-tokens.py check-expiry

# Output example:
# 📅 Service Token Expiry Status:
# ========================================
# ✅ OK safework-api:
#    Expires: 2025-12-31T23:59:59Z
#    Days until expiry: 145
#    Client ID: abc123...
```

### Rotate Tokens

```bash
# Rotate all tokens
python3 scripts/rotate-service-tokens.py rotate-all

# Rotate specific token
python3 scripts/rotate-service-tokens.py rotate safework-api
```

### Manual Token Rotation

```bash
# 1. Create new token in Cloudflare Zero Trust
# 2. Update Kubernetes secret
kubectl patch secret cloudflare-service-tokens -n safework \
  --type='json' \
  -p='[{"op": "replace", "path": "/data/CF_SERVICE_TOKEN_API_CLIENT_ID", "value": "new-client-id-base64"}]'

# 3. Update GitHub secrets
gh secret set CF_SERVICE_TOKEN_API_CLIENT_ID --body "new-client-id"
gh secret set CF_SERVICE_TOKEN_API_CLIENT_SECRET --body "new-client-secret"

# 4. Restart deployment
kubectl rollout restart deployment safework -n safework
```

## Monitoring and Troubleshooting

### Check Service Token Status

```bash
# Check middleware logs
kubectl logs -n safework deployment/safework | grep "service_token"

# Check token validation
kubectl exec -n safework deployment/safework -- \
  curl -H "CF-Access-Client-Id: $CLIENT_ID" \
       -H "CF-Access-Client-Secret: $CLIENT_SECRET" \
       http://localhost:8000/health
```

### Common Issues

#### 1. Invalid Token Error
```
Error: Invalid service token client ID
```
**Solution**: Verify client ID is correct and token exists in Cloudflare.

#### 2. Forbidden Access Error
```
Error: Service token 'safework-api' not authorized for endpoint '/admin'
```
**Solution**: Check endpoint permissions in middleware configuration.

#### 3. Rate Limit Exceeded
```
Error: Service token rate limit exceeded
```
**Solution**: Reduce request frequency or increase rate limits.

#### 4. Token Expired
```
Error: Service token validation failed with Cloudflare
```
**Solution**: Rotate the expired token.

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Test with curl
curl -v -H "CF-Access-Client-Id: $CLIENT_ID" \
        -H "CF-Access-Client-Secret: $CLIENT_SECRET" \
        https://safework.jclee.me/api/v1/workers
```

## Security Best Practices

### 1. Token Storage
- ✅ Store tokens in Kubernetes secrets
- ✅ Use GitHub secrets for CI/CD
- ❌ Never commit tokens to version control
- ❌ Avoid storing tokens in plain text files

### 2. Access Control
- ✅ Use different tokens for different services
- ✅ Implement least privilege access
- ✅ Regular token rotation
- ❌ Don't share tokens between environments

### 3. Monitoring
- ✅ Monitor token usage patterns
- ✅ Set up expiry alerts
- ✅ Log authentication attempts
- ❌ Don't ignore failed authentication logs

### 4. Incident Response
- ✅ Have token rotation procedures ready
- ✅ Monitor for suspicious activity
- ✅ Implement emergency revocation
- ❌ Don't delay token rotation after incidents

## CI/CD Integration

### GitHub Actions Example

```yaml
name: API Integration Test
on: [push]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Test API with Service Token
        env:
          CF_SERVICE_TOKEN_API_CLIENT_ID: ${{ secrets.CF_SERVICE_TOKEN_API_CLIENT_ID }}
          CF_SERVICE_TOKEN_API_CLIENT_SECRET: ${{ secrets.CF_SERVICE_TOKEN_API_CLIENT_SECRET }}
        run: |
          response=$(curl -s -H "CF-Access-Client-Id: $CF_SERVICE_TOKEN_API_CLIENT_ID" \
                          -H "CF-Access-Client-Secret: $CF_SERVICE_TOKEN_API_CLIENT_SECRET" \
                          https://safework.jclee.me/health)
          echo "Health check response: $response"
```

### Jenkins Pipeline Example

```groovy
pipeline {
    agent any
    
    environment {
        CF_SERVICE_TOKEN_API_CLIENT_ID = credentials('cf-service-token-api-client-id')
        CF_SERVICE_TOKEN_API_CLIENT_SECRET = credentials('cf-service-token-api-client-secret')
    }
    
    stages {
        stage('API Test') {
            steps {
                script {
                    def response = sh(
                        script: """
                            curl -s -H "CF-Access-Client-Id: ${CF_SERVICE_TOKEN_API_CLIENT_ID}" \
                                   -H "CF-Access-Client-Secret: ${CF_SERVICE_TOKEN_API_CLIENT_SECRET}" \
                                   https://safework.jclee.me/api/v1/workers
                        """,
                        returnStdout: true
                    )
                    echo "API Response: ${response}"
                }
            }
        }
    }
}
```

## Environment Configuration

### Development Environment

```bash
# .env.development
CLOUDFLARE_TEAM_DOMAIN=mycompany-dev
CF_SERVICE_TOKEN_API_CLIENT_ID=dev-api-client-id
CF_SERVICE_TOKEN_API_CLIENT_SECRET=dev-api-client-secret
ENABLE_SERVICE_TOKEN_VALIDATION=true
SERVICE_TOKEN_CACHE_TTL=60
```

### Production Environment

```bash
# .env.production
CLOUDFLARE_TEAM_DOMAIN=mycompany
CF_SERVICE_TOKEN_API_CLIENT_ID=prod-api-client-id
CF_SERVICE_TOKEN_API_CLIENT_SECRET=prod-api-client-secret
ENABLE_SERVICE_TOKEN_VALIDATION=true
SERVICE_TOKEN_CACHE_TTL=300
```

## Metrics and Monitoring

### Prometheus Metrics

```yaml
# Service token metrics
service_token_requests_total{token_name="safework-api", status="success"} 1250
service_token_validation_duration_seconds{token_name="safework-api"} 0.045
service_token_cache_hits_total{token_name="safework-api"} 890
service_token_expiry_days{token_name="safework-api"} 145
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "Service Token Metrics",
    "panels": [
      {
        "title": "Token Requests",
        "targets": [
          {
            "expr": "rate(service_token_requests_total[5m])",
            "legendFormat": "{{token_name}} - {{status}}"
          }
        ]
      },
      {
        "title": "Token Expiry",
        "targets": [
          {
            "expr": "service_token_expiry_days",
            "legendFormat": "{{token_name}}"
          }
        ]
      }
    ]
  }
}
```

## Troubleshooting Checklist

### Pre-deployment Checklist
- [ ] Service tokens created in Cloudflare Zero Trust
- [ ] Kubernetes secrets configured
- [ ] GitHub secrets configured (if using CI/CD)
- [ ] Middleware enabled in application
- [ ] Rate limits configured appropriately
- [ ] Monitoring and alerting set up

### Post-deployment Checklist
- [ ] Health check passes with service token
- [ ] API endpoints accessible
- [ ] Rate limiting working correctly
- [ ] Audit logs being generated
- [ ] Metrics being collected
- [ ] Alerts configured for token expiry

### Emergency Procedures
1. **Token Compromise**: 
   - Revoke token immediately in Cloudflare
   - Generate new token
   - Update secrets in Kubernetes and GitHub
   - Restart application

2. **Service Unavailable**:
   - Check token expiry
   - Verify Cloudflare service status
   - Check rate limits
   - Review middleware configuration

## FAQ

### Q: Can I use the same service token for multiple environments?
A: No, use separate tokens for each environment (dev, staging, prod) for better security isolation.

### Q: How often should I rotate service tokens?
A: Recommended rotation schedule:
- API tokens: Every 6-12 months
- Registry tokens: Every 6-12 months
- CI/CD tokens: Every 3-6 months
- Monitoring tokens: Every 6-12 months

### Q: What happens if a service token expires?
A: The service will fail authentication. Set up monitoring alerts for tokens expiring within 30 days.

### Q: Can I disable service token validation?
A: Yes, set `ENABLE_SERVICE_TOKEN_VALIDATION=false`, but this is not recommended for production.

### Q: How do I test service token integration locally?
A: Use the development environment configuration with test tokens, or temporarily disable validation for local testing.

---

**Support**: For additional help, see the [implementation guide](CLOUDFLARE_SERVICE_TOKENS_IMPLEMENTATION.md) or contact the development team.

**Last Updated**: 2025-07-09  
**Version**: 1.0.0