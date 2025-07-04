# SafeWork ArgoCD 자동 배포 가이드

ArgoCD를 사용한 SafeWork Pro의 GitOps 기반 자동 배포 설정입니다.

## 📋 구성 요소

### 🏗️ GitOps 아키텍처
```
┌─────────────────────────────────────────────────────┐
│                 GitOps Pipeline                     │
│                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐ │
│  │ Developer   │    │ GitHub      │    │ ArgoCD   │ │
│  │ Push Code   │───▶│ Actions     │───▶│ Deploy   │ │
│  └─────────────┘    │ Build Image │    │ to K8s   │ │
│                     └─────────────┘    └──────────┘ │
│                                             │       │
│                                             ▼       │
│                     ┌─────────────────────────────┐ │
│                     │    Kubernetes Cluster      │ │
│                     │                             │ │
│                     │  ┌─────────┐  ┌─────────┐   │ │
│                     │  │Frontend │  │Backend  │   │ │
│                     │  │Pod×2    │  │Pod×2    │   │ │
│                     │  └─────────┘  └─────────┘   │ │
│                     │                             │ │
│                     │  ┌─────────┐  ┌─────────┐   │ │
│                     │  │PostgreSQL│  │Redis   │   │ │
│                     │  │Pod×1    │  │Pod×1    │   │ │
│                     │  └─────────┘  └─────────┘   │ │
│                     └─────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

## 🚀 빠른 설정

### 1. ArgoCD 설치 및 설정
```bash
cd k8s/argocd
./deploy-argocd.sh install
```

### 2. GitHub Secrets 설정
Repository > Settings > Secrets and variables > Actions에서 다음 설정:

```bash
# ArgoCD 접근
ARGOCD_ADMIN_USER=admin
ARGOCD_ADMIN_PASS=bingogo1
ARGOCD_API_TOKEN=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Docker Registry 접근
DOCKER_USERNAME=qws9411
DOCKER_PASSWORD=bingogo1

# GitHub 접근 (if needed for private repos)
GITHUB_TOKEN=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
```

### 3. 자동 배포 테스트
```bash
# 코드 변경 후 푸시
git add .
git commit -m "feat: test argocd deployment"
git push origin main
```

## 📁 파일 구조

```
k8s/argocd/
├── application.yaml       # ArgoCD Application 정의
├── project.yaml           # ArgoCD Project 설정
├── repository-secret.yaml # GitHub/Registry 접근 secrets
├── deploy-argocd.sh       # 자동 설치 스크립트
└── README.md              # 이 파일
```

## 🔧 ArgoCD 설정 세부사항

### Application 설정
- **이름**: safework
- **프로젝트**: default
- **소스**: GitHub repository (k8s/ 디렉토리)
- **대상**: safework namespace
- **동기화**: 자동 (auto-sync, self-heal, prune)

### 동기화 정책
```yaml
syncPolicy:
  automated:
    prune: true      # 삭제된 리소스 자동 제거
    selfHeal: true   # 드리프트 자동 복구
    allowEmpty: false
  syncOptions:
    - CreateNamespace=true
    - PrunePropagationPolicy=foreground
    - PruneLast=true
    - ApplyOutOfSyncOnly=true
```

## 🔄 CI/CD 파이프라인

### 워크플로우 단계
1. **테스트**: Python/Node.js 테스트 실행
2. **빌드**: Docker 이미지 빌드 및 Registry 푸시
3. **보안 스캔**: Trivy 취약점 스캔
4. **배포**: ArgoCD 애플리케이션 동기화
5. **검증**: 배포 상태 및 헬스 체크
6. **알림**: 배포 결과 알림

### 트리거 조건
- **main 브랜치**: 자동 프로덕션 배포
- **develop 브랜치**: 기존 Watchtower 파이프라인 사용
- **PR**: 테스트만 실행

## 🛠️ 관리 명령어

### ArgoCD CLI 명령어
```bash
# 애플리케이션 상태 확인
argocd app get safework

# 수동 동기화
argocd app sync safework --prune --force

# 로그 확인
argocd app logs safework

# 롤백
argocd app rollback safework <revision-id>
```

### Kubernetes 명령어
```bash
# 배포 상태 확인
kubectl get all -n safework

# 로그 확인
kubectl logs -n safework -l app=safework,component=backend --tail=50
kubectl logs -n safework -l app=safework,component=frontend --tail=50

# 스케일링
kubectl scale deployment safework-backend -n safework --replicas=3
```

### 스크립트 명령어
```bash
# 전체 설치
./deploy-argocd.sh install

# 설정만 적용
./deploy-argocd.sh configure

# 동기화
./deploy-argocd.sh sync

# 상태 확인
./deploy-argocd.sh status

# 로그 확인
./deploy-argocd.sh logs

# 삭제
./deploy-argocd.sh delete
```

## 🔒 보안 설정

### 1. Secrets 관리
- GitHub 토큰: Repository 읽기 권한
- Registry 자격증명: 이미지 Pull 권한
- ArgoCD API 토큰: 애플리케이션 관리 권한

### 2. RBAC 설정
- safework-project: 프로젝트별 권한 분리
- admin 역할: 모든 권한
- developer 역할: 읽기 및 동기화 권한

### 3. 네트워크 보안
- Ingress TLS 설정
- Service 간 통신 제한
- 시크릿 암호화

## 📊 모니터링

### ArgoCD 대시보드
- URL: https://argo.jclee.me
- Username: admin
- Password: bingogo1

### 애플리케이션 메트릭
- 동기화 상태
- 리소스 헬스
- 배포 히스토리
- 이벤트 로그

### 알림 설정
- GitHub 배포 상태
- Slack 통합 (선택사항)
- 이메일 알림 (선택사항)

## 🚨 트러블슈팅

### 일반적인 문제

1. **동기화 실패**
   ```bash
   # 애플리케이션 상태 확인
   argocd app get safework
   
   # 강제 새로고침
   argocd app sync safework --force --prune
   ```

2. **이미지 Pull 실패**
   ```bash
   # Registry secret 확인
   kubectl get secret registry-secret -n safework -o yaml
   
   # 새로운 secret 생성
   kubectl create secret docker-registry registry-secret \
     --docker-server=registry.jclee.me \
     --docker-username=qws9411 \
     --docker-password=bingogo1 \
     --namespace=safework
   ```

3. **ArgoCD 서버 접근 불가**
   ```bash
   # ArgoCD 서버 상태 확인
   kubectl get pods -n argocd
   
   # 포트 포워딩으로 접근
   kubectl port-forward -n argocd svc/argocd-server 8080:443
   ```

4. **애플리케이션 Out of Sync**
   ```bash
   # 차이점 확인
   argocd app diff safework
   
   # 하드 새로고침
   argocd app sync safework --force --replace
   ```

### 로그 수집
```bash
# ArgoCD 애플리케이션 로그
argocd app logs safework --tail=100

# Kubernetes 이벤트
kubectl get events -n safework --sort-by='.lastTimestamp'

# Pod 로그
kubectl logs -n safework deployment/safework-backend --tail=50
```

## 🔄 업데이트 프로세스

### 1. 코드 변경
```bash
git add .
git commit -m "feat: new feature implementation"
git push origin main
```

### 2. 자동 배포 흐름
1. GitHub Actions 트리거
2. 테스트 실행
3. Docker 이미지 빌드
4. Registry 푸시
5. ArgoCD 동기화 트리거
6. Kubernetes 배포
7. 헬스 체크
8. 배포 완료 알림

### 3. 수동 개입이 필요한 경우
```bash
# 배포 일시 중지
argocd app patch safework --patch '{"spec":{"syncPolicy":null}}'

# 수동 롤백
argocd app rollback safework <previous-revision>

# 자동 동기화 재활성화
argocd app patch safework --patch-file sync-policy.yaml
```

## 📈 성능 최적화

### 1. 리소스 조정
```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

### 2. HPA 설정
```bash
kubectl autoscale deployment safework-backend \
  -n safework --cpu-percent=70 --min=2 --max=10
```

### 3. 캐시 최적화
- Docker 빌드 캐시
- ArgoCD 동기화 캐시
- Kubernetes 리소스 캐시

---

**ArgoCD 배포 완료!** 이제 SafeWork Pro는 GitOps 방식으로 자동 배포됩니다.

문의사항이나 문제가 있으면 ArgoCD 대시보드를 확인하거나 위의 트러블슈팅 가이드를 참조하세요.