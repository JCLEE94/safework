# Docker Registry Setup with Nginx Proxy Manager

## Problem
Getting 405 Method Not Allowed when pushing to Docker registry through nginx proxy manager.

## Solution

### 1. In Nginx Proxy Manager Web Console:

1. Go to your proxy host for `registry.jclee.me`
2. Click "Edit" 
3. Go to the "Custom Nginx Configuration" tab
4. Clear any existing configuration
5. Paste this complete configuration:

```nginx
# Docker Registry v2 API Configuration
client_max_body_size 0;
chunked_transfer_encoding on;

# Headers
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Docker-Content-Digest $http_docker_content_digest;
proxy_set_header Authorization $http_authorization;

# Disable buffering
proxy_request_buffering off;
proxy_buffering off;

# Timeouts
proxy_read_timeout 900;
proxy_connect_timeout 900;
proxy_send_timeout 900;

# HTTP 1.1
proxy_http_version 1.1;
proxy_redirect off;

# Fix 405 errors
if ($request_method !~ ^(GET|HEAD|POST|PUT|DELETE|PATCH)$) {
    return 405;
}
```

### 2. Remove Custom Location:

1. Go to "Custom Locations" tab
2. Delete the `/v2` location if it exists
3. The main proxy configuration should handle all paths

### 3. Main Settings:

- Domain: `registry.jclee.me`
- Forward Hostname/IP: `192.168.50.215`
- Forward Port: `1234`
- Cache Assets: OFF
- Block Common Exploits: OFF
- Websockets Support: ON

### 4. Save and Test:

After saving, test with:
```bash
# Test registry endpoint
curl https://registry.jclee.me/v2/

# Login to registry
docker login registry.jclee.me

# Tag and push
docker tag health-management-system:latest registry.jclee.me/health:latest
docker push registry.jclee.me/health:latest
```

## Alternative: Direct Push to IP:Port

If nginx proxy continues to have issues:
```bash
# Use direct IP:port instead
docker tag health-management-system:latest 192.168.50.215:1234/health:latest
docker push 192.168.50.215:1234/health:latest
```

## Troubleshooting

1. Check nginx error logs on the proxy server
2. Ensure Docker registry container is running: `docker ps | grep registry`
3. Test direct access: `curl http://192.168.50.215:1234/v2/`
4. Check if insecure-registries is configured in `/etc/docker/daemon.json`