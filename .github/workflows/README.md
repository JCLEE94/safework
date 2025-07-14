# SafeWork Pro CI/CD Workflows

이 디렉토리는 SafeWork Pro 프로젝트의 GitHub Actions CI/CD 워크플로우를 포함합니다.

## 활성화된 워크플로우

### 1. main.yml - 메인 CI/CD 파이프라인
- **트리거**: `main` 브랜치 push, 수동 실행
- **기능**: 전체 테스트 → Docker 이미지 빌드 → ArgoCD Image Updater 자동 배포
- **특징**: 
  - GitHub-hosted runners 사용으로 안정성 확보
  - 병렬 테스트 실행 (backend-unit, backend-integration, frontend)
  - registry.jclee.me 퍼블릭 레지스트리 사용 (인증 불필요)
  - ArgoCD Image Updater가 자동으로 새 이미지 감지 및 배포

### 2. test-quick.yml - PR 빠른 검증
- **트리거**: Pull Request 생성/업데이트
- **기능**: 빠른 단위 테스트 및 코드 품질 검사
- **특징**: 
  - 10분 제한으로 빠른 피드백
  - slow/integration 테스트 제외
  - 코드 포맷팅 및 린팅 검사

### 3. monitor-pipeline.yml - 파이프라인 헬스 모니터링
- **트리거**: 6시간마다 스케줄 실행, 수동 실행
- **기능**: CI/CD 파이프라인 상태 모니터링 및 알림
- **특징**:
  - 실패율 20% 초과시 알림
  - 레지스트리 상태 체크
  - 자동 이슈 생성 (실패율 30% 초과)

## CI/CD 아키텍처

```
GitHub Push (main)
     ↓
GitHub Actions (main.yml)
     ↓
병렬 테스트 실행
     ↓
Docker 이미지 빌드 & 푸시
     ↓
registry.jclee.me/safework:prod-YYYYMMDD-SHA7
     ↓
ArgoCD Image Updater 자동 감지
     ↓
K8s 매니페스트 자동 업데이트
     ↓
ArgoCD 자동 싱크 & 배포
     ↓
Production: https://safework.jclee.me
```

## 이미지 태깅 전략

- **Latest**: `latest` - 최신 프로덕션 이미지
- **Production**: `prod-YYYYMMDD-SHA7` - 날짜 + 커밋 해시
- **Semantic**: `1.YYYYMMDD.BUILD_NUMBER` - 시맨틱 버저닝

ArgoCD Image Updater는 `^prod-[0-9]{8}-[a-f0-9]{7}$` 패턴으로 새 이미지를 자동 감지합니다.

## 환경 변수

### 테스트 환경
```yaml
DATABASE_URL: postgresql://admin:password@localhost:5432/health_management
REDIS_URL: redis://localhost:6379/0
JWT_SECRET: test-secret-key
ENVIRONMENT: development
PYTHONPATH: ${{ github.workspace }}
```

### 빌드 환경
```yaml
REGISTRY: registry.jclee.me
IMAGE_NAME: safework
DOCKER_BUILDKIT: 1
```

## 트러블슈팅

### 일반적인 문제들

1. **413 Request Entity Too Large**
   - 상태: registry.jclee.me 사용으로 해결
   - 액션: 필요시 이미지 크기 최적화

2. **테스트 타임아웃**
   - 상태: 병렬 실행으로 개선
   - 액션: pytest-timeout으로 제한

3. **ArgoCD 배포 지연**
   - 상태: Image Updater 자동화
   - 액션: ArgoCD 로그 확인

### 파이프라인 상태 확인

```bash
# 최근 실행 상태
gh run list --limit 5

# 특정 실행 로그
gh run view <run-id> --log-failed

# 파이프라인 헬스 리포트
gh workflow run monitor-pipeline.yml
```

## 배포 상태 확인

```bash
# 애플리케이션 헬스 체크
curl https://safework.jclee.me/health

# ArgoCD 앱 상태
kubectl get application safework -n argocd

# 컨테이너 로그
docker logs safework --tail=50
```

---
**최종 업데이트**: 2025-01-14  
**파이프라인 상태**: ✅ 최적화 완료  
**배포 방식**: ArgoCD Image Updater 자동화