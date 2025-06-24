# GitHub Actions 워크플로우

## 🚀 간소화된 CI/CD 파이프라인

### 배포 흐름
1. **Build & Push** (`build-push.yml`)
   - Docker 이미지 빌드
   - registry.jclee.me로 푸시
   - **끝** - Watchtower가 자동 배포 처리

2. **Test** (`test.yml`)
   - 백엔드/프론트엔드 테스트
   - 포트 충돌 방지 (15432, 16379)

3. **Security Scan** (`security.yml`)
   - Trivy 취약점 스캔
   - Docker 이미지 스캔
   - 의존성 체크

## ⚙️ 필수 GitHub Secrets
```yaml
REGISTRY_USERNAME: qws941
REGISTRY_PASSWORD: ****
```

## 🔄 Watchtower 자동 배포
운영 서버의 Watchtower가:
- 30초마다 registry.jclee.me 모니터링
- 새 이미지 자동 pull & 배포
- 이전 이미지 자동 정리

## ❌ 제거된 기능
- SSH 배포 스크립트
- 수동 docker-compose 명령
- 복잡한 배포 로직