# SafeWork Pro - 건설업 보건관리 시스템

<div align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge&logo=python">
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-green?style=for-the-badge&logo=fastapi">
  <img src="https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react">
  <img src="https://img.shields.io/badge/PostgreSQL-15-blue?style=for-the-badge&logo=postgresql">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker">
</div>

<div align="center">
  <br>
  <a href="https://github.com/qws941/health/actions/workflows/build-deploy.yml">
    <img src="https://github.com/qws941/health/actions/workflows/build-deploy.yml/badge.svg" alt="Build & Deploy">
  </a>
  <a href="https://github.com/qws941/health/actions/workflows/test.yml">
    <img src="https://github.com/qws941/health/actions/workflows/test.yml/badge.svg" alt="Tests">
  </a>
  <a href="https://github.com/qws941/health/actions/workflows/security.yml">
    <img src="https://github.com/qws941/health/actions/workflows/security.yml/badge.svg" alt="Security">
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

### Docker를 사용한 실행 (권장)

```bash
# 개발 환경
docker-compose -f docker-compose.dev.yml up --build

# 프로덕션 환경
docker-compose up -d
```

애플리케이션 접속: http://localhost:3001

### 수동 설치

#### 백엔드
```bash
# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 마이그레이션
alembic upgrade head

# 서버 실행
python main.py
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

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │────▶│  FastAPI    │────▶│ PostgreSQL  │
│  (Port 3001)│     │   Backend   │     │  Database   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │    Cache    │
                    └─────────────┘
```

### 기술 스택
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, Alembic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: PostgreSQL 15
- **Cache**: Redis 7
- **Container**: Docker, Docker Compose
- **Monitoring**: 실시간 메트릭 수집 및 WebSocket 스트리밍

## 📁 프로젝트 구조

```
health-management-system/
├── src/
│   ├── app.py              # FastAPI 애플리케이션
│   ├── config/             # 설정 및 데이터베이스
│   ├── models/             # SQLAlchemy 모델
│   ├── schemas/            # Pydantic 스키마
│   ├── handlers/           # API 엔드포인트
│   ├── services/           # 비즈니스 로직
│   ├── middleware/         # 미들웨어 (보안, 캐싱, 성능)
│   └── utils/              # 유틸리티 함수
├── tests/                  # 테스트 코드
├── document/               # PDF 템플릿 및 문서
├── docker-compose.yml      # 프로덕션 설정
├── docker-compose.dev.yml  # 개발 환경 설정
└── requirements.txt        # Python 의존성
```

## 🔧 환경 설정

### 환경 변수 (.env)
```bash
# Database
DATABASE_URL=postgresql://admin:password@postgres:5432/health_management

# Redis
REDIS_URL=redis://redis:6379/0

# Security
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# Application
DEBUG=false
LOG_LEVEL=INFO
TZ=Asia/Seoul
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
# 백엔드 테스트
pytest tests/ -v --cov=src --cov-report=html

# 프론트엔드 테스트
npm run test

# 통합 테스트
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 🚀 배포

### GitHub Actions CI/CD

`.github/workflows/deploy.yml`이 자동으로:
1. 코드 품질 검사 (lint, type check)
2. 테스트 실행
3. Docker 이미지 빌드
4. Registry 푸시 (registry.jclee.me)
5. 프로덕션 서버 배포

### 수동 배포
```bash
./deploy.sh health
```

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

이 프로젝트는 GitHub Actions를 사용하여 자동화된 CI/CD 파이프라인을 구현합니다.

### GitHub Actions Workflows

#### 1. Build & Deploy (`build-deploy.yml`)
- **트리거**: main/develop 브랜치 푸시, PR
- **기능**: 
  - Docker 이미지 빌드 (multi-arch: amd64, arm64)
  - Docker Hub 푸시
  - 프로덕션 자동 배포 (main 브랜치만)
  - Watchtower를 통한 자동 업데이트

#### 2. Test (`test.yml`)
- **트리거**: 모든 푸시 및 PR
- **기능**:
  - Python 백엔드 테스트 (pytest)
  - React 프론트엔드 테스트
  - 테스트 커버리지 리포트
  - PostgreSQL/Redis 통합 테스트

#### 3. Security Scan (`security.yml`)
- **트리거**: 푸시, PR, 주간 스케줄
- **기능**:
  - Trivy 취약점 스캔
  - Docker 이미지 보안 검사
  - Python/npm 의존성 감사

#### 4. Release (`release.yml`)
- **트리거**: 버전 태그 (v*)
- **기능**:
  - 자동 changelog 생성
  - GitHub Release 생성
  - 버전별 Docker 이미지 배포

### GitHub Secrets 설정

필요한 secrets를 설정하려면:

```bash
# 자동 설정 스크립트 실행
./setup-github-secrets.sh

# 또는 수동 설정
gh secret set DOCKER_USERNAME -b "your-username"
gh secret set DOCKER_PASSWORD -b "your-password"
gh secret set DEPLOY_HOST -b "192.168.50.215"
gh secret set DEPLOY_USER -b "docker"
gh secret set DEPLOY_KEY < ~/.ssh/id_rsa
```

### 배포 프로세스

1. **개발**: develop 브랜치에 푸시 → 테스트 실행
2. **스테이징**: develop → main PR → 모든 테스트 통과 필요
3. **프로덕션**: main 브랜치 머지 → 자동 배포
4. **모니터링**: Watchtower가 새 이미지 감지 시 자동 업데이트

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 📞 문의

프로젝트 관련 문의사항은 [Issues](https://github.com/qws941/health/issues)에 등록해주세요.

---

<div align="center">
  Made with ❤️ for Construction Site Safety
</div>