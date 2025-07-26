# SafeWork Pro - 건설업 보건관리 시스템

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-green?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/React-19-blue?style=for-the-badge&logo=react">
  <img src="https://img.shields.io/badge/PostgreSQL-15-blue?style=for-the-badge&logo=postgresql">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker">
</div>

<div align="center">
  <br>
  <a href="https://github.com/JCLEE94/safework/actions/workflows/build-push.yml">
    <img src="https://github.com/JCLEE94/safework/actions/workflows/build-push.yml/badge.svg" alt="Build & Push">
  </a>
  <a href="https://github.com/JCLEE94/safework/actions/workflows/test.yml">
    <img src="https://github.com/JCLEE94/safework/actions/workflows/test.yml/badge.svg" alt="Tests">
  </a>
  <a href="https://github.com/JCLEE94/safework/actions/workflows/security.yml">
    <img src="https://github.com/JCLEE94/safework/actions/workflows/security.yml/badge.svg" alt="Security">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License">
  </a>
</div>

## 🏗️ 프로젝트 소개

SafeWork Pro는 한국 산업안전보건법에 따른 건설업 보건관리를 위한 통합 웹 애플리케이션입니다. 근로자 건강관리, 작업환경 측정, 보건교육, 화학물질 관리, 산업재해 보고 등을 효율적으로 관리할 수 있습니다.

### 주요 기능
- 👷 **근로자 관리**: 건강상태 추적, 의료 검진 일정 관리
- 🏥 **건강진단**: 일반/특수 건강진단 기록 및 유소견자 관리
- 🌡️ **작업환경측정**: 소음, 분진, 화학물질 등 환경 모니터링
- 📚 **보건교육**: 교육 일정 및 이수 현황 관리
- ⚗️ **화학물질관리**: MSDS 관리 및 특별관리물질 추적
- 🚨 **산업재해**: 사고 보고 및 조사 관리
- 📄 **문서관리**: PDF 양식 자동 생성 및 관리
- 📊 **실시간 모니터링**: 시스템 성능 및 상태 대시보드

## 🚀 빠른 시작

### 운영 환경 (단일 컨테이너)
```bash
# 1. 환경 설정
cp config/env.production.example .env

# 2. 배포 실행
docker-compose up -d

# 3. 상태 확인
curl http://localhost:3001/health
```

### 개발 환경 (분리된 서비스)
```bash
# 1. 환경 설정
cp config/env.development.example .env

# 2. 개발 환경 실행 (override 파일 자동 적용)
ENVIRONMENT=development docker-compose up -d

# 또는 기존 개발용 설정 사용
docker-compose -f docker-compose.dev.yml up --build
```

> 📖 **자세한 배포 가이드**: [DEPLOYMENT.md](DEPLOYMENT.md) 참조

애플리케이션 접속: 
- 로컬 개발: http://localhost:3001
- 프로덕션: https://safework.jclee.me
- NodePort 접속: Port 32301 (Kubernetes 환경)

### 수동 설치

#### 백엔드
```bash
# UV 패키지 관리자 사용 (권장)
# 의존성 설치 및 가상환경 자동 생성
uv sync

# 데이터베이스 마이그레이션
uv run alembic upgrade head

# 서버 실행
uv run python main.py

# 또는 기존 방식
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### 프론트엔드
```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 프로덕션 빌드
npm run build
```

## 🏛️ 아키텍처

### 애플리케이션 아키텍처
```
┌─────────────────────────────────────────────────┐
│                SafeWork Pro                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  React UI   │──│  FastAPI    │──│ PG 15   │ │
│  │  (Nginx)    │  │  Backend    │  │ Database│ │
│  │  :3001      │  └──────┬──────┘  └─────────┘ │
│  └─────────────┘         │                     │
│                  ┌───────┴───────┐             │
│                  │   Redis 7     │             │
│                  │   Cache       │             │
│                  └───────────────┘             │
└─────────────────────────────────────────────────┘
        External Port: 3001 / NodePort: 32301
```

### CI/CD 아키텍처
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

### 기술 스택
- **Backend**: Python 3.11, FastAPI 0.104.1, SQLAlchemy, Alembic
- **Frontend**: React 19, TypeScript, Vite, Ant Design 5.26.6, TanStack Query 5.83+
- **State Management**: Redux Toolkit 2.8+ (UI 상태), TanStack Query (서버 상태)
- **Testing**: Jest 30 + React Testing Library 16.3+ + Testing Library User Event
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Container**: Docker, Docker Compose
- **CI/CD**: GitHub Actions, ArgoCD, ArgoCD Image Updater
- **Registry**: registry.jclee.me (공개 Docker Registry)
- **Monitoring**: 실시간 메트릭 수집 및 WebSocket 스트리밍

## 📁 프로젝트 구조

### 🎯 정리된 프로젝트 구조
```
safework/
├── 🐳 docker-compose.yml        # 통합 Docker Compose 설정
├── 📄 .env                      # 환경별 설정 파일
├── 
├── 📂 src/                      # 소스 코드 (FastAPI + React)
├── 📂 frontend/                 # 프론트엔드 빌드 설정
├── 📂 backend/                  # 백엔드 설정 파일
├── 📂 database/                 # 데이터베이스 스크립트
├── 📂 deployment/               # 배포 관련 파일
├── 📂 tools/                    # 유틸리티 도구
├── 📂 scripts/                  # 자동화 스크립트
├── 📂 tests/                    # 테스트 코드
├── 
├── 📂 config/                   # 환경 설정
├── 📂 docs/                     # 문서
├── 📂 document/                 # 법정 서식 및 매뉴얼
├── 📂 archive/                  # 이전 파일 보관
└── 📂 logs/                     # 로그 파일
```

### 🗃️ 정리된 파일들 (archive/)
```
archive/
├── docker-compose/            # 20개 이상의 중복 docker-compose 파일들
├── deploy-scripts/            # 10개 이상의 사용하지 않는 배포 스크립트들
├── documentation/             # 이전 README 파일들
├── dockerfiles/              # 사용하지 않는 Dockerfile들
├── configs/                  # 사용하지 않는 설정 파일들
└── docker/                   # 전체 docker 디렉터리 (이전 구조)
```

> 📖 **자세한 사용법**: [DEPLOYMENT.md](DEPLOYMENT.md)에서 환경별 설정 방법을 확인하세요.

## 🔧 환경 설정

### 환경별 설정 파일
```bash
# 운영 환경
cp config/env.production.example .env

# 개발 환경
cp config/env.development.example .env
```

### 주요 환경 변수
- `ENVIRONMENT`: production/development/test
- `DEBUG`: true/false (개발 환경에서만 true)
- `LOG_LEVEL`: DEBUG/INFO/WARNING/ERROR
- `DATABASE_URL`: 데이터베이스 연결 URL
- `REDIS_URL`: Redis 연결 URL
- `JWT_SECRET`: JWT 토큰 비밀키

### Docker Compose 사용법
```bash
# 운영 환경 (단일 컨테이너)
docker-compose up -d

# 개발 환경 (분리된 서비스)
ENVIRONMENT=development docker-compose up -d
# 또는
docker-compose -f docker-compose.dev.yml up --build
```

## 📊 API 문서

FastAPI 자동 생성 문서:
- Swagger UI: http://localhost:3001/api/docs
- ReDoc: http://localhost:3001/api/redoc

### 주요 API 엔드포인트
- `GET /api/v1/workers/` - 근로자 목록 조회
- `POST /api/v1/workers/` - 근로자 등록
- `GET /api/v1/health-exams/` - 건강진단 목록
- `GET /api/v1/monitoring/ws` - 실시간 모니터링 WebSocket
- `POST /api/v1/documents/fill-pdf/{form_name}` - PDF 양식 생성

## 🧪 테스트

```bash
# 백엔드 테스트 (UV 사용 권장)
uv run pytest tests/ -v --cov=src --cov-report=html --timeout=60 -x

# 또는 기존 방식
pytest tests/ -v --cov=src --cov-report=html

# 코드 품질 검사
uv run black src/ tests/ && uv run isort src/ tests/ && uv run flake8 src/ tests/

# 프론트엔드 테스트
cd frontend && npm run test

# 프론트엔드 린팅
cd frontend && npm run lint

# 통합 테스트
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🚀 배포

### 자동 배포 (Watchtower)

1. **개발자**: `git push origin main`
2. **GitHub Actions**: Docker 이미지 빌드 → registry.jclee.me 푸시
3. **Watchtower**: 30초마다 체크 → 자동 배포

상세 설정: [Watchtower 설정 가이드](docs/deployment/WATCHTOWER-SETUP.md)

## 🔒 보안 기능

- JWT 기반 인증
- CSRF 보호
- XSS 방지
- SQL Injection 보호
- Rate Limiting
- API Key 인증
- HTTPS 강제

## 📈 성능 최적화

- Redis 캐싱 (API 응답, 세션, PDF)
- 데이터베이스 인덱스 최적화
- 압축 미들웨어
- 비동기 처리
- Connection Pooling

## 🚀 CI/CD 파이프라인

이 프로젝트는 GitHub Actions와 ArgoCD Image Updater를 사용하여 완전 자동화된 CI/CD 파이프라인을 구현합니다.

### 최적화된 배포 프로세스

1. **코드 푸시**: `git push origin main`
2. **자동 테스트**: GitHub Actions에서 병렬 테스트 실행
3. **이미지 빌드**: 최적화된 Docker 이미지 빌드 및 registry.jclee.me 푸시
4. **자동 배포**: ArgoCD Image Updater가 새 이미지 감지 및 자동 배포
5. **무중단 배포**: Kubernetes rolling update로 서비스 중단 없이 배포

### 주요 특징

- **Registry**: registry.jclee.me (공개 레지스트리, 인증 불필요)
- **이미지 태그**: 
  - 프로덕션: `prod-YYYYMMDD-SHA7`
  - Semantic: `1.YYYYMMDD.BUILD_NUMBER`
- **자동화**: 수동 K8s 매니페스트 업데이트 불필요
- **모니터링**: ArgoCD 대시보드에서 실시간 배포 상태 확인

### GitHub Secrets 설정

필요한 secrets를 설정하려면:

```bash
# 자동 설정 스크립트 실행
./setup-github-secrets.sh

# 또는 수동 설정
gh secret set DOCKER_USERNAME -b "your-username"
gh secret set DOCKER_PASSWORD -b "your-password"
gh secret set DEPLOY_HOST -b "your-production-host"
gh secret set DEPLOY_USER -b "docker"
gh secret set DEPLOY_KEY < ~/.ssh/id_rsa
```

### 배포 프로세스

1. **개발**: feature 브랜치에서 개발 → PR 생성
2. **테스트**: GitHub Actions에서 자동 테스트 실행
3. **머지**: main 브랜치로 머지 → 이미지 자동 빌드
4. **배포**: ArgoCD Image Updater가 자동으로 새 이미지 배포
5. **모니터링**: ArgoCD 대시보드에서 배포 상태 확인

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의

프로젝트 관련 문의사항은 [Issues](https://github.com/JCLEE94/safework/issues)에 등록해주세요.

---

<div align="center">
  Made with ❤️ for Construction Site Safety
</div># Test runner - 2025. 06. 24. (화) 22:06:25 KST
 
