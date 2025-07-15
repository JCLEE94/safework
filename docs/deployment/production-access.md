# SafeWork Production Access Information

## External URLs

### Domain Access
- **URL**: https://safework.jclee.me
- **Type**: HTTPS with Let's Encrypt certificate
- **Ingress**: Nginx Ingress Controller

### NodePort Access (Direct)
- **URL**: http://192.168.50.110:32301
- **Type**: NodePort Service
- **Port**: 32301
- **Protocol**: HTTP

## ArgoCD Configuration

### Server
- **URL**: https://argo.jclee.me
- **Application**: safework
- **Namespace**: safework

### Current Image
- **Repository**: registry.jclee.me/safework
- **Tag**: prod-20250715-63d57ad (with Redis port fix)

### Helm Parameters
```yaml
image:
  repository: registry.jclee.me/safework
  tag: prod-20250715-63d57ad
service:
  type: NodePort
  port: 3001
  nodePort: 32301
ingress:
  enabled: true
  hosts:
    - host: safework.jclee.me
      paths:
        - path: /
          pathType: Prefix
```

## Health Check Endpoints
- https://safework.jclee.me/health
- http://192.168.50.110:32301/health

## Last Updated
- Date: 2025-07-15
- Status: Deployment Healthy
- Redis Port Issue: Fixed in commit 63d57ad