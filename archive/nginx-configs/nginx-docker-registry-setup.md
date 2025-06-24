# Nginx Proxy Manager - Docker Registry 설정 가이드

## registry.jclee.me를 Docker Registry로 재설정하기

### 1. 기존 설정 삭제
1. Nginx Proxy Manager 웹 콘솔 접속
2. Proxy Hosts 목록에서 registry.jclee.me 찾기
3. 우측 Actions에서 Delete 클릭
4. 확인 후 삭제

### 2. 새로운 Proxy Host 생성
1. "Add Proxy Host" 버튼 클릭

### 3. Details 탭 설정
- **Domain Names**: registry.jclee.me
- **Scheme**: http
- **Forward Hostname / IP**: 192.168.50.215
- **Forward Port**: 1234
- **Cache Assets**: ❌ OFF (체크 해제)
- **Block Common Exploits**: ❌ OFF (체크 해제)
- **Websockets Support**: ✅ ON (체크)
- **Access List**: Publicly Accessible

### 4. Custom Nginx Configuration 탭
아래 내용을 정확히 복사해서 붙여넣기:

```nginx
# Docker Registry v2 API 설정
client_max_body_size 0;
chunked_transfer_encoding on;

# 프록시 헤더 설정
proxy_set_header Host $http_host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header Authorization $http_authorization;
proxy_set_header Docker-Content-Digest $http_docker_content_digest;

# 버퍼링 비활성화 (중요!)
proxy_request_buffering off;
proxy_buffering off;

# HTTP 1.1 사용
proxy_http_version 1.1;

# 타임아웃 설정
proxy_read_timeout 900;
proxy_connect_timeout 900;
proxy_send_timeout 900;

# 리다이렉트 비활성화
proxy_redirect off;

# 모든 HTTP 메소드 허용
proxy_pass_request_headers on;
proxy_pass_request_body on;
```

### 5. SSL/TLS 탭 (선택사항)
- **SSL Certificate**: None (또는 Let's Encrypt)
- **Force SSL**: ❌ OFF (먼저 HTTP로 테스트)
- **HTTP/2 Support**: ❌ OFF
- **HSTS Enabled**: ❌ OFF
- **HSTS Subdomains**: ❌ OFF

### 6. Advanced 탭
- Custom Locations는 추가하지 않음
- 기본 설정 유지

### 7. 저장
"Save" 버튼 클릭

### 8. 테스트 명령어
```bash
# 1. Registry 엔드포인트 테스트
curl http://registry.jclee.me/v2/

# 2. Docker 로그인 (필요시)
docker login registry.jclee.me

# 3. 이미지 태그
docker tag health-management-system:latest registry.jclee.me/health:latest

# 4. 이미지 푸시
docker push registry.jclee.me/health:latest

# 5. 이미지 풀
docker pull registry.jclee.me/health:latest
```

### 문제 해결
만약 여전히 405 에러가 발생한다면:
1. Nginx Proxy Manager 컨테이너 재시작
2. 브라우저 캐시 삭제
3. DNS 캐시 플러시: `sudo systemctl restart systemd-resolved`

### 확인사항
- Forward Port가 1234인지 확인 (5000이 아님)
- Block Common Exploits가 OFF인지 확인
- Custom Nginx Configuration이 정확히 입력되었는지 확인