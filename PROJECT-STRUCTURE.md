# SafeWork Pro 프로젝트 구조

## 📁 주요 디렉토리 구조

```
safework/
├── src/                    # 소스 코드 (백엔드 + 프론트엔드 통합)
│   ├── app.py             # FastAPI 메인 애플리케이션
│   ├── models/            # SQLAlchemy 데이터베이스 모델
│   ├── schemas/           # Pydantic 검증 스키마
│   ├── handlers/          # API 엔드포인트 핸들러
│   ├── services/          # 비즈니스 로직 서비스
│   ├── middleware/        # 미들웨어 (보안, 캐싱, 로깅)
│   ├── utils/             # 유틸리티 함수
│   ├── components/        # React 컴포넌트
│   └── types/             # TypeScript 타입 정의
│
├── frontend/              # 프론트엔드 개발 환경
│   ├── src/              # React 소스 (src/로 심볼릭 링크)
│   ├── package.json      # NPM 패키지 설정
│   └── vite.config.ts    # Vite 빌드 설정
│
├── backend/               # 백엔드 설정 파일
│   ├── requirements.txt   # Python 패키지 목록
│   └── pytest.ini        # pytest 설정
│
├── database/              # 데이터베이스 관련
│   ├── migrations/       # SQL 마이그레이션 파일
│   │   └── direct-migration.sql  # 최신 마이그레이션
│   └── init-db.sh        # DB 초기화 스크립트
│
├── deployment/            # 배포 관련 파일
│   ├── Dockerfile.prod   # 운영 환경 Docker 이미지
│   ├── start-official.sh # 공식 시작 스크립트
│   └── deploy-single.sh  # 배포 스크립트
│
├── tests/                 # 테스트 코드
│   ├── conftest.py       # pytest 공통 설정
│   └── test_*.py         # 각종 테스트 파일
│
├── document/              # 법정 서식 및 문서
│   ├── 01-업무매뉴얼/
│   ├── 02-법정서식/
│   └── ...
│
├── scripts/               # 유틸리티 스크립트
│   ├── deploy/           # 배포 자동화
│   └── ci/               # CI/CD 관련
│
├── config/                # 설정 파일
│   ├── project.yml       # 프로젝트 설정
│   └── secrets/          # 보안 설정
│
├── .github/               # GitHub Actions CI/CD
│   └── workflows/
│       ├── build-push.yml
│       └── test.yml
│
└── archive/               # 이전 버전 백업
```

## 🚀 새로운 기능 구조

### 1. 체크리스트 자동화 시스템
- **모델**: `src/models/checklist.py`
- **스키마**: `src/schemas/checklist.py`
- **핸들러**: `src/handlers/checklist.py`
- **프론트엔드**: 미구현 (TODO)

### 2. 특별관리물질 처리 시스템
- **모델**: `src/models/special_materials.py`
- **스키마**: `src/schemas/special_materials.py`
- **핸들러**: `src/handlers/special_materials.py`
- **프론트엔드**: 미구현 (TODO)

### 3. 설정 관리 시스템
- **모델**: `src/models/settings.py`
- **스키마**: `src/schemas/settings.py`
- **핸들러**: `src/handlers/settings.py`
- **프론트엔드**: `src/components/Settings/`

### 4. 법정서식 개별 처리
- **모델**: `src/models/legal_forms.py`
- **스키마**: `src/schemas/legal_forms.py`
- **핸들러**: `src/handlers/legal_forms.py`
- **프론트엔드**: `src/components/LegalForms/`

## 📋 파일 정리 권장사항

### 정리 대상
1. **archive/** - 오래된 설정 파일들
2. **deployment/** - 사용하지 않는 시작 스크립트
3. **alembic/** - 직접 SQL 마이그레이션으로 대체

### 유지 필수
1. **src/** - 모든 소스 코드
2. **database/migrations/** - SQL 마이그레이션
3. **deployment/Dockerfile.prod** - 운영 이미지
4. **deployment/start-official.sh** - 공식 시작 스크립트
5. **tests/** - 테스트 코드
6. **document/** - 법정 서식

## 🔧 개발 가이드

### 새 기능 추가 시
1. `src/models/`에 모델 정의
2. `src/schemas/`에 Pydantic 스키마 작성
3. `src/handlers/`에 API 핸들러 구현
4. `src/app.py`에 라우터 등록
5. `database/migrations/`에 SQL 마이그레이션 추가
6. `src/components/`에 React 컴포넌트 작성
7. `tests/`에 테스트 코드 작성

### 배포 시
1. 코드 커밋 및 푸시
2. GitHub Actions 자동 실행
3. Docker 이미지 빌드 및 레지스트리 푸시
4. Watchtower 자동 배포

## 📝 마이그레이션 관리

모든 데이터베이스 변경사항은 `database/migrations/direct-migration.sql`에 추가하여 관리합니다.

```sql
-- 새 테이블 추가 예시
CREATE TABLE IF NOT EXISTS new_table (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ...
);

-- 컬럼 추가 예시
ALTER TABLE existing_table ADD COLUMN IF NOT EXISTS new_column VARCHAR(255);
```

## 🐳 Docker 구조

All-in-One 컨테이너:
- PostgreSQL (포트 5432)
- Redis (포트 6379)
- FastAPI + React (포트 3001)

환경변수:
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `REDIS_URL`: Redis 연결 문자열
- `JWT_SECRET`: JWT 비밀키
- `PORT`: 서비스 포트 (기본값: 3001)

---
최종 업데이트: 2025-07-04