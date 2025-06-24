# Nginx Proxy Manager Docker Registry 설정 수정 방법

## 문제
- GET 요청은 작동하지만 POST/PUT 요청이 405 에러 반환
- Docker push 시 실패

## 해결 방법

### 1. Nginx Proxy Manager 웹 콘솔 접속

### 2. registry.jclee.me Proxy Host 수정

#### Details 탭:
- Domain Names: registry.jclee.me
- Scheme: http (not https)
- Forward Hostname/IP: 192.168.50.215
- Forward Port: 1234
- **Cache Assets: OFF** ✅
- **Block Common Exploits: OFF** ✅
- **Websockets Support: ON** ✅

#### Custom Nginx Configuration 탭:
```nginx
# Docker Registry v2 설정
client_max_body_size 0;
chunked_transfer_encoding on;

# 프록시 헤더
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Authorization $http_authorization;
proxy_set_header Docker-Content-Digest $http_docker_content_digest;

# 버퍼링 비활성화
proxy_request_buffering off;
proxy_buffering off;
proxy_http_version 1.1;

# 타임아웃
proxy_read_timeout 900;
proxy_connect_timeout 900;
proxy_send_timeout 900;

# 모든 메소드 허용
proxy_pass_request_headers on;
proxy_pass_request_body on;

# 405 에러 우회
error_page 405 =200 @405;
location @405 {
    proxy_pass http://192.168.50.215:1234;
}
```

#### SSL/TLS 탭:
- SSL Certificate: None 또는 Let's Encrypt
- **Force SSL: OFF** (테스트 중)
- **HTTP/2 Support: OFF** (Docker와 호환성 문제 가능)
- **HSTS Enabled: OFF**

### 3. 저장 후 테스트

```bash
# 테스트
curl https://registry.jclee.me/v2/
docker push registry.jclee.me/health:latest
```

### 4. 만약 여전히 안되면

Nginx Proxy Manager 대신 직접 nginx 설정:

```nginx
server {
    listen 443 ssl;
    server_name registry.jclee.me;
    
    # SSL 설정...
    
    location / {
        proxy_pass http://192.168.50.215:1234;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Docker Registry 필수
        client_max_body_size 0;
        chunked_transfer_encoding on;
        proxy_request_buffering off;
        proxy_buffering off;
    }
}
```