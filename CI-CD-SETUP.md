# CI/CD Setup Guide for SafeWork Pro

## 현재 상태 (2025-06-29)

### 작동하는 워크플로우
- **docker-build.yml** - Docker 컨테이너 기반 빌드 및 배포 (권장)
- **quick-deploy.yml** - 빠른 배포 (테스트 스킵)

### 문제가 있는 워크플로우
- **build-deploy.yml** - Self-hosted runner 권한 문제
- **test.yml** - Self-hosted runner 권한 문제
- **emergency-deploy.yml** - 권한 문제
- **direct-deploy.yml** - 권한 문제

## 권한 문제 해결 방법

### 1. 임시 해결책 (권장)
```bash
# Docker 컨테이너 기반 워크플로우 사용
gh workflow run docker-build.yml
```

### 2. 수동 배포
```bash
# 로컬에서 직접 빌드 및 푸시
docker login registry.jclee.me
docker build -f deployment/Dockerfile.prod -t registry.jclee.me/safework:latest .
docker push registry.jclee.me/safework:latest

# Watchtower 트리거
curl -X POST https://watchtower.jclee.me/v1/update \
  -H "Authorization: Bearer MySuperSecretToken12345"
```

### 3. Self-hosted runner 권한 수정
```bash
# 권한 수정 스크립트 실행
./scripts/fix-runner-permissions.sh

# 또는 수동으로
sudo chown -R $USER:$USER /home/jclee/github_runner/
sudo rm -rf /home/jclee/github_runner/github-runners/runner-*/_work/safework
```

## 배포 프로세스

### 자동 배포 흐름
1. `git push` → GitHub
2. GitHub Actions 트리거
3. Docker 이미지 빌드
4. registry.jclee.me에 푸시
5. Watchtower 자동 감지 및 배포
6. 프로덕션 서버 업데이트

### 프로덕션 서버 정보
- URL: http://192.168.50.215:3001
- 헬스체크: http://192.168.50.215:3001/health
- 로그 뷰어: http://192.168.50.200:5555/log/safework

## GitHub Secrets 설정

필수 시크릿:
- `DOCKER_USERNAME` - Docker Hub 사용자명
- `DOCKER_PASSWORD` - Docker Hub 비밀번호
- `REGISTRY_USERNAME` - Private registry 사용자명
- `REGISTRY_PASSWORD` - Private registry 비밀번호
- `GITHUB_TOKEN` - 자동 생성됨

## 향후 개선사항

1. **Self-hosted runner 대체**
   - GitHub-hosted runner로 전환 고려
   - 또는 Docker-in-Docker 전용 runner 구성

2. **테스트 환경 개선**
   - 테스트를 Docker 컨테이너에서 실행
   - 테스트 데이터베이스 격리

3. **모니터링 강화**
   - 배포 상태 실시간 알림
   - 자동 롤백 메커니즘

## 문제 해결

### "Permission denied" 에러
```bash
# Runner 작업 디렉토리 초기화
sudo rm -rf /home/jclee/github_runner/github-runners/runner-*/_work/safework
sudo systemctl restart actions.runner.*
```

### Docker 빌드 실패
```bash
# BuildKit 비활성화
export DOCKER_BUILDKIT=0
docker build ...
```

### Watchtower가 업데이트하지 않음
```bash
# 수동으로 컨테이너 재시작
docker pull registry.jclee.me/safework:latest
docker stop safework
docker rm safework
docker run -d --name safework ... registry.jclee.me/safework:latest
```