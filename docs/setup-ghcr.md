# GitHub Container Registry 설정 가이드

## 개요
Docker Registry 413 에러를 해결하기 위해 GitHub Container Registry (ghcr.io)를 사용합니다.

## 설정 단계

### 1. GitHub Personal Access Token 생성

1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 권한 선택:
   - `write:packages` - 패키지 업로드
   - `read:packages` - 패키지 다운로드
   - `delete:packages` - 패키지 삭제 (선택사항)
4. 토큰 저장 (한 번만 표시됨)

### 2. Kubernetes Secret 생성

```bash
# 토큰을 사용해 docker login
echo YOUR_GITHUB_TOKEN | docker login ghcr.io -u YOUR_GITHUB_USERNAME --password-stdin

# Secret 생성
kubectl create secret docker-registry ghcr-secret \
  --docker-server=ghcr.io \
  --docker-username=YOUR_GITHUB_USERNAME \
  --docker-password=YOUR_GITHUB_TOKEN \
  --docker-email=YOUR_EMAIL \
  -n safework

# 또는 기존 docker config 사용
kubectl create secret generic ghcr-secret \
  --from-file=.dockerconfigjson=$HOME/.docker/config.json \
  --type=kubernetes.io/dockerconfigjson \
  -n safework
```

### 3. GitHub Actions 설정

Repository Settings → Secrets and variables → Actions에서:
- `GHCR_USERNAME`: GitHub 사용자명
- `GHCR_TOKEN`: Personal Access Token

### 4. 배포 확인

```bash
# 새 워크플로우 실행
gh workflow run deploy-ghcr.yml

# 이미지 확인
docker pull ghcr.io/jclee94/safework:latest

# Pod 재시작
kubectl rollout restart deployment/safework -n safework
```

## 장점

1. **무료**: Public 저장소는 무제한 무료
2. **통합**: GitHub Actions와 완벽 통합
3. **권한 관리**: GitHub 권한 시스템 활용
4. **대용량 지원**: 이미지 크기 제한 없음

## 마이그레이션 체크리스트

- [ ] GitHub Token 생성
- [ ] K8s Secret 생성
- [ ] deployment.yaml 업데이트
- [ ] kustomization.yaml 업데이트
- [ ] ArgoCD 앱 동기화
- [ ] 기존 registry.jclee.me에서 이미지 삭제 (선택사항)

## 롤백 방법

문제 발생 시 기존 레지스트리로 복구:
```bash
# kustomization.yaml 수정
kubectl edit kustomization -n safework

# 이미지 이름을 다시 registry.jclee.me/safework로 변경
```