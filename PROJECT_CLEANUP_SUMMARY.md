# SafeWork 프로젝트 정리 결과

## 완료된 작업

### 1. 테스트 파일 정리
- 루트에 있던 4개의 테스트 파일을 `/tests/` 폴더로 이동
  - test_api.py
  - test_pdf_generation.py
  - test_simple_api.py
  - test_system.py

### 2. backend 폴더 제거
- `/backend/` 폴더 삭제 (백업은 archive/cleanup-backup-YYYYMMDD에 보관)
- 실제 백엔드 코드는 `/src/` 폴더에 있으므로 중복 제거

### 3. 배포 스크립트 정리
- 루트에 있던 8개의 중복 배포 스크립트 제거 (백업 완료)
- 주요 배포 스크립트를 `/scripts/deploy/` 폴더로 이동
  - deployment/deploy-single.sh → scripts/deploy/deploy-main.sh
- deployment 폴더의 중복 start*.sh 스크립트들 제거

### 4. 설정 스크립트 정리
- 설정 관련 스크립트들을 `/scripts/setup/` 폴더로 이동
  - setup-argocd-token.sh
  - setup-claude-oauth.sh
  - setup-claude-code-runner.sh
  - setup-github-secrets.template.sh

### 5. 문서 파일 정리
- README 파일들을 체계적으로 재구성
  - README-USAGE.md → docs/USAGE.md
  - README-Claude-OAuth.md → docs/setup/Claude-OAuth.md
  - CI-CD-SETUP.md → docs/deployment/CI-CD-SETUP.md
  - 중복된 DEPLOYMENT.md 제거

### 6. K8s 폴더 정리
- 환경별 폴더 구조 생성 (base, production, development)
- 기본 리소스를 base 폴더로 이동 (namespace, configmap, secrets)
- 중복 파일 제거
  - argocd-app.json (yaml 버전 유지)
  - cloudflare-only 폴더 (cloudflare 폴더와 중복)
  - deployment.yaml (각 서비스별 deployment 파일 사용)
- K8s 관련 스크립트를 scripts 폴더로 이동

## 새로운 폴더 구조

```
safework/
├── src/                    # 백엔드 소스코드
├── frontend/               # 프론트엔드 소스코드
├── tests/                  # 모든 테스트 파일 (통합됨)
├── scripts/                # 모든 스크립트 (체계적으로 정리)
│   ├── deploy/             # 배포 스크립트
│   ├── setup/              # 설정 스크립트
│   └── utils/              # 유틸리티 스크립트
├── k8s/                    # Kubernetes 설정 (재구성됨)
│   ├── base/               # 기본 설정
│   ├── production/         # 프로덕션 설정
│   └── development/        # 개발 설정
├── docs/                   # 모든 문서 (체계적으로 정리)
│   ├── setup/              # 설정 관련 문서
│   ├── deployment/         # 배포 관련 문서
│   └── api/                # API 문서
├── deployment/             # Docker 및 배포 설정
└── archive/                # 이전 버전 및 백업
    └── cleanup-backup-YYYYMMDD/  # 오늘 정리 전 백업

```

## 삭제된 파일 수
- 배포 스크립트: 16개 
- 테스트 파일: 4개 (이동됨)
- 설정 스크립트: 7개 (이동/통합됨)
- K8s 관련: 6개
- 문서 파일: 3개 (이동/통합됨)
- 폴더: 2개 (backend, k8s/cloudflare-only)

총 38개 이상의 중복/불필요한 파일 정리 완료

## 백업 위치
모든 삭제된 파일은 `/archive/cleanup-backup-YYYYMMDD/` 폴더에 안전하게 백업되어 있습니다.

## 다음 단계 권장사항
1. 정리된 구조로 CI/CD 파이프라인 업데이트
2. CLAUDE.md 및 README.md 파일 업데이트하여 새 구조 반영
3. .gitignore 파일 업데이트
4. 테스트 실행하여 모든 기능이 정상 작동하는지 확인