# ArgoCD Image Updater 설정 가이드

## 개요

ArgoCD Image Updater를 사용하여 Docker 이미지 업데이트를 자동화합니다. 
CI/CD 파이프라인에서 수동으로 K8s 매니페스트를 업데이트하는 대신, 
Image Updater가 레지스트리를 모니터링하고 자동으로 새 이미지를 배포합니다.

## 아키텍처

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│ Docker Build │────▶│  Registry   │
│   Actions   │     │   & Push     │     │ (jclee.me)  │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                 │
                                                 ▼
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│ Kubernetes  │◀────│    ArgoCD    │◀────│   Image     │
│  Cluster    │     │              │     │  Updater    │
└─────────────┘     └──────────────┘     └─────────────┘
```

## 설치

### 1. ArgoCD Image Updater 설치

```bash
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml
```

### 2. ConfigMap 적용

```bash
kubectl apply -f k8s/argocd/image-updater-configmap.yaml
```

### 3. Secret 생성 (GitHub Token 필요)

```bash
# GitHub Personal Access Token 생성 (repo 권한 필요)
# https://github.com/settings/tokens/new

# Secret 생성
kubectl create secret generic argocd-image-updater-secret \
  -n argocd \
  --from-literal=git-creds="https://x-access-token:${GITHUB_TOKEN}@github.com"
```

## 설정 구조

### 1. ArgoCD Application 어노테이션

```yaml
# k8s/argocd/application.yaml
annotations:
  # 모니터링할 이미지 목록
  argocd-image-updater.argoproj.io/image-list: safework=registry.jclee.me/safework
  
  # 업데이트 전략 (latest, semver, digest)
  argocd-image-updater.argoproj.io/safework.update-strategy: latest
  
  # 허용할 태그 패턴 (정규식)
  argocd-image-updater.argoproj.io/safework.allow-tags: "regexp:^prod-[0-9]{8}-[a-f0-9]{7}$"
  
  # Write-back 방법 (git, argocd)
  argocd-image-updater.argoproj.io/write-back-method: git
  
  # Git 브랜치
  argocd-image-updater.argoproj.io/git-branch: main
```

### 2. 이미지 태그 전략

```yaml
# Semantic Versioning 사용
tags:
  - type=raw,value=latest
  - type=raw,value=prod-{{date 'YYYYMMDD'}}-{{sha}}
  - type=raw,value=1.{{date 'YYYYMMDD'}}.{{env.GITHUB_RUN_NUMBER}}
```

### 3. Registry 설정

```yaml
# Public registry (인증 불필요)
registries:
- name: registry.jclee.me
  api_url: https://registry.jclee.me
  prefix: registry.jclee.me
  insecure: no
  default: true
```

## CI/CD 파이프라인 변경사항

### Before (수동 업데이트)
```yaml
- name: Update Kubernetes manifests
  run: |
    sed -i "s|newTag:.*|newTag: ${NEW_TAG}|g" k8s/safework/kustomization.yaml
    git add k8s/safework/kustomization.yaml
    git commit -m "chore: update image to ${NEW_TAG}"
    git push
```

### After (자동 업데이트)
```yaml
# 이미지 빌드 및 푸시만 수행
# ArgoCD Image Updater가 자동으로 감지하고 배포
```

## 모니터링

### 1. Image Updater 로그 확인

```bash
kubectl logs -n argocd deployment/argocd-image-updater -f
```

### 2. 업데이트 상태 확인

```bash
# Application 상태 확인
kubectl get application -n argocd safework -o yaml | grep -A 10 "status:"

# 최근 업데이트 확인
kubectl logs -n argocd deployment/argocd-image-updater | grep safework
```

### 3. ArgoCD UI에서 확인

```
https://argo.jclee.me/applications/safework
```

## 문제 해결

### 1. 이미지가 업데이트되지 않음

```bash
# Image Updater 재시작
kubectl rollout restart deployment/argocd-image-updater -n argocd

# 수동으로 스캔 트리거
argocd app get safework --refresh
```

### 2. Git write-back 실패

```bash
# Secret 확인
kubectl get secret -n argocd argocd-image-updater-secret -o yaml

# Git 권한 확인
curl -H "Authorization: token ${GITHUB_TOKEN}" https://api.github.com/user
```

### 3. Registry 연결 실패

```bash
# Registry 상태 확인
curl https://registry.jclee.me/v2/

# Image Updater에서 직접 테스트
kubectl exec -n argocd deployment/argocd-image-updater -- \
  argocd-image-updater test registry.jclee.me/safework
```

## 장점

1. **자동화**: 수동 커밋/푸시 불필요
2. **신속성**: 새 이미지 즉시 감지 및 배포
3. **안정성**: Git 충돌 방지
4. **추적성**: 모든 업데이트가 Git에 기록됨
5. **유연성**: 다양한 업데이트 전략 지원

## 주의사항

1. GitHub Token은 `repo` 권한 필요
2. Image tag 패턴을 정확히 설정해야 함
3. Registry가 공개되어 있거나 적절한 인증 설정 필요
4. Git write-back 시 커밋 메시지 커스터마이징 가능

## 참고 자료

- [ArgoCD Image Updater 공식 문서](https://argocd-image-updater.readthedocs.io/)
- [Update Strategies](https://argocd-image-updater.readthedocs.io/en/stable/basics/update-strategies/)
- [Configuration](https://argocd-image-updater.readthedocs.io/en/stable/configuration/)