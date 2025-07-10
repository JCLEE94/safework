# SafeWork 프로젝트 중복 파일 분석 보고서

## 1. 폴더 구조 중복 문제

### Backend 소스코드 중복
- `/backend/` - 단일 main.py 파일만 존재
- `/src/` - 실제 백엔드 코드가 있는 위치
- **권장사항**: backend 폴더 삭제하고 src 폴더만 사용

### 테스트 파일 위치 혼재
- 프로젝트 루트: `test_api.py`, `test_pdf_generation.py`, `test_simple_api.py`, `test_system.py`
- `/tests/` 폴더: 정리된 테스트 파일들
- `/frontend/test_api.py`: 프론트엔드 폴더에 있는 테스트 파일
- **권장사항**: 모든 테스트를 /tests/ 폴더로 이동

## 2. 배포 스크립트 중복 (심각)

### 현재 사용 중인 스크립트
- `/deployment/deploy-single.sh` - 현재 주요 배포 스크립트
- `/docker-compose.yml` - 현재 사용 중

### 루트에 있는 중복 배포 스크립트들
- `deploy-cloudflare-direct.sh`
- `deploy-to-server.sh`
- `deploy-without-argocd.sh`
- `direct-deploy.sh`
- `emergency-deploy.sh`
- `local-deploy.sh`
- `server-update.sh`
- `trigger-argocd-deploy.sh`

### /deployment/ 폴더의 중복 스크립트들
- `start-external-db.sh`
- `start-external.sh`
- `start-fixed.sh`
- `start-gosu.sh`
- `start-minimal.sh`
- `start-official.sh`
- `start-postgres-fix.sh`
- `start.sh`
- `start-simple.sh`

### /archive/ 폴더 (이미 정리된 파일들)
- `/archive/deploy-scripts/` - 17개의 이전 배포 스크립트
- `/archive/docker-compose/` - 14개의 이전 docker-compose 파일
- `/archive/dockerfiles/` - 5개의 이전 Dockerfile

### /scripts/deploy/ 폴더의 스크립트들
- `deploy-complete.sh`
- `deploy-production.sh`
- `deploy.sh`
- `deploy-with-watchtower.sh`

## 3. Docker 관련 파일 중복

### Dockerfile 중복
- `/deployment/Dockerfile` - 현재 사용 중
- `/deployment/Dockerfile.prod`
- `/archive/dockerfiles/` - 5개의 이전 버전

### docker-compose 파일 중복
- `/docker-compose.yml` - 현재 사용 중
- `/archive/docker-compose/` - 14개의 이전 버전

## 4. 문서 파일 중복

### README 파일들
- `/README.md` - 메인 README
- `/README-USAGE.md`
- `/README-Claude-OAuth.md`
- `/.github/README-TESTING.md`
- `/archive/documentation/` - 4개의 이전 README
- `/docs/setup/README-DEPLOYMENT.md`
- `/k8s/README.md`
- `/k8s/argocd/README.md`
- `/k8s/cloudflare/README.md`
- `/k8s/safework/README.md`

### 배포 문서 중복
- `/DEPLOYMENT.md`
- `/docs/DEPLOYMENT.md`
- `/CI-CD-SETUP.md`
- `/docs/CICD.md`

## 5. Kubernetes 설정 중복

### ArgoCD 설정 중복
- `/k8s/argocd-app.json`
- `/k8s/argocd-app.yaml`
- `/k8s/argocd/` 폴더 내 여러 application yaml 파일들

### Cloudflare 설정 중복
- `/k8s/cloudflare/` 폴더
- `/k8s/cloudflare-only/` 폴더
- 두 폴더에 비슷한 설정 파일들 존재

### 중복된 deployment 파일들
- `/k8s/deployment.yaml`
- `/k8s/backend/backend-deployment.yaml`
- `/k8s/frontend/frontend-deployment.yaml`
- `/k8s/safework/deployment.yaml`

## 6. 설정 스크립트 중복

### GitHub Secrets 설정 스크립트
- `/setup-github-secrets.sh`
- `/setup-github-secrets.template.sh`
- `/scripts/setup-github-secrets.sh`
- `/scripts/ci/setup-github-secrets.sh`
- `/.github/scripts/check-oauth.sh`

### Claude 관련 설정
- `/setup-claude-code-runner.sh`
- `/setup-claude-oauth.sh`
- `/.github/scripts/install-claude.sh`

## 7. 기타 중복 파일들

### 데이터베이스 초기화 스크립트
- `/database/init_db.py`
- `/database/init-db.sh`
- `/database/add_sample_data.py`
- `/database/run_user_migration.py`

### 모니터링 스크립트
- `/scripts/monitor.sh`
- `/scripts/monitor-watchtower-api.sh`
- `/tools/monitor-pipeline.sh`

## 권장 조치사항

### 1. 즉시 삭제 가능한 파일들
```bash
# 루트의 중복 배포 스크립트들
rm deploy-cloudflare-direct.sh
rm deploy-to-server.sh
rm deploy-without-argocd.sh
rm direct-deploy.sh
rm emergency-deploy.sh
rm local-deploy.sh
rm server-update.sh
rm trigger-argocd-deploy.sh

# 루트의 테스트 파일들 (tests 폴더로 이동 후)
rm test_api.py
rm test_pdf_generation.py
rm test_simple_api.py
rm test_system.py

# backend 폴더 (src만 사용)
rm -rf backend/

# 중복 설정 스크립트
rm setup-github-secrets.template.sh
```

### 2. 통합이 필요한 파일들
- 모든 배포 스크립트를 `/scripts/deploy/` 폴더로 통합
- 모든 README를 하나의 구조화된 문서 체계로 정리
- K8s 설정을 환경별로 명확히 구분

### 3. 폴더 구조 개선
```
safework/
├── src/              # 백엔드 소스코드
├── frontend/         # 프론트엔드 소스코드
├── tests/            # 모든 테스트 파일
├── scripts/          # 모든 스크립트
│   ├── deploy/       # 배포 스크립트
│   ├── setup/        # 설정 스크립트
│   └── utils/        # 유틸리티 스크립트
├── k8s/              # Kubernetes 설정
│   ├── base/         # 기본 설정
│   ├── production/   # 프로덕션 설정
│   └── development/  # 개발 설정
├── docs/             # 모든 문서
└── archive/          # 이전 버전 파일들
```

### 4. .gitignore 업데이트 필요
- 임시 파일 패턴 추가
- 로컬 테스트 파일 제외
- 개인 설정 파일 제외

## 결론

현재 프로젝트에는 약 50개 이상의 중복되거나 불필요한 파일들이 존재합니다. 특히 배포 스크립트와 설정 파일들의 중복이 심각하며, 이는 유지보수와 협업에 혼란을 야기할 수 있습니다. 위의 권장사항에 따라 정리하면 프로젝트 구조가 훨씬 명확해질 것입니다.