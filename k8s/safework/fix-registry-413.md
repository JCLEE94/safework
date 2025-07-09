# Registry 413 Error 해결 방안

## 문제점
- Docker Registry가 413 "Request Entity Too Large" 에러 발생
- 이미지 크기: 약 500MB
- Cloudflare 프록시를 통해 registry.jclee.me 접근 시 업로드 크기 제한

## 해결 방안

### 1. 즉시 적용 가능한 방안

#### A. Cloudflare 설정 변경
```bash
# Cloudflare Dashboard에서:
# 1. registry.jclee.me 도메인 선택
# 2. Page Rules 또는 Configuration Rules 추가
# 3. URL: registry.jclee.me/*
# 4. Settings:
#    - Disable Performance
#    - Cache Level: Bypass
#    - 또는 Orange Cloud를 Gray Cloud로 변경 (프록시 비활성화)
```

#### B. 직접 IP 사용 (임시)
```yaml
# .github/workflows/deploy.yml
env:
  REGISTRY_URL: 192.168.50.200:5000  # 실제 레지스트리 서버 IP
```

### 2. 이미지 크기 최적화

#### A. Multi-stage 빌드 개선
```dockerfile
# Alpine 베이스 이미지 사용
FROM python:3.11-alpine AS production

# 불필요한 패키지 제거
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache \
    && find /usr/local -name "*.pyc" -delete \
    && find /usr/local -name "__pycache__" -delete
```

#### B. 레이어 최적화
```dockerfile
# 자주 변경되지 않는 레이어를 먼저
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 자주 변경되는 소스 코드는 나중에
COPY src/ ./src/
```

### 3. 대체 레지스트리 사용

#### A. GitHub Container Registry (ghcr.io)
```yaml
# .github/workflows/deploy.yml
env:
  REGISTRY_URL: ghcr.io
  REGISTRY_USERNAME: ${{ github.actor }}
  REGISTRY_PASSWORD: ${{ secrets.GITHUB_TOKEN }}
  IMAGE_NAME: ghcr.io/${{ github.repository_owner }}/safework
```

#### B. Docker Hub (무료 계정도 가능)
```yaml
env:
  REGISTRY_URL: docker.io
  REGISTRY_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
  REGISTRY_PASSWORD: ${{ secrets.DOCKERHUB_TOKEN }}
  IMAGE_NAME: ${{ secrets.DOCKERHUB_USERNAME }}/safework
```

### 4. 레지스트리 서버 설정 변경

#### nginx.conf (레지스트리 앞단)
```nginx
server {
    listen 443 ssl;
    server_name registry.jclee.me;
    
    # 파일 업로드 크기 제한 증가
    client_max_body_size 1000M;
    proxy_read_timeout 600;
    proxy_connect_timeout 600;
    proxy_send_timeout 600;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 청크 전송 활성화
        proxy_request_buffering off;
        proxy_buffering off;
    }
}
```

## 권장 순서

1. **즉시**: Cloudflare 프록시 비활성화 (Orange → Gray Cloud)
2. **단기**: GitHub Container Registry로 전환
3. **장기**: 이미지 크기 최적화 (현재 500MB → 300MB 목표)

## CI/CD 복구 절차

1. 레지스트리 문제 해결 후:
```bash
# GitHub Actions 재실행
gh run rerun <run-id>

# 또는 새 커밋으로 트리거
git commit --allow-empty -m "fix: trigger CI/CD pipeline"
git push
```

2. ArgoCD 동기화:
```bash
# ArgoCD CLI로 수동 동기화
argocd app sync safework

# 또는 웹 UI에서 Sync 버튼 클릭
```