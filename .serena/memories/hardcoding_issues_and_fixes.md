# SafeWork Pro - 하드코딩 이슈 및 수정 계획

## 🔧 발견된 하드코딩 이슈들

### 1. 인증 관련 하드코딩
- **문제**: 모든 곳에서 `created_by = "system"` 사용
- **파일들**: handlers/*.py (accident_reports, chemical_substances, health_education, work_environments, special_materials, checklist, legal_forms, settings)
- **수정방안**: JWT 토큰에서 실제 사용자 정보 추출하는 서비스 구현

### 2. 포트 및 호스트 하드코딩
- **문제**: 3001, 8000, localhost 등 하드코딩
- **파일들**: 
  - `test_api.py`, `tests/test_*.py`: localhost:3001
  - `src/app.py`: port=8000
  - `src/config/settings.py`: 기본값들
- **수정방안**: 환경변수로 완전히 대체

### 3. 데이터베이스 자격증명 하드코딩
- **문제**: `admin`, `safework123` 등 기본 패스워드
- **파일**: `src/config/settings.py`
- **수정방안**: 환경변수 필수화, 기본값 제거

### 4. 임시 인증 우회 코드
- **문제**: `# TODO: Remove this in production` 주석과 함께 인증 스킵
- **파일**: `src/middleware/auth.py`
- **수정방안**: 개발/프로덕션 모드 분리, 프로덕션에서는 인증 필수

## 🎯 수정 우선순위

### Priority 1 (보안 위험)
1. 인증 미들웨어 프로덕션 모드 활성화
2. 데이터베이스 자격증명 환경변수화
3. JWT 기반 사용자 인증 구현

### Priority 2 (운영 안정성)
1. 포트 및 호스트 설정 환경변수화
2. 테스트 코드의 URL 하드코딩 제거
3. IP 화이트리스트 설정 개선

### Priority 3 (코드 품질)
1. Magic number 상수화
2. TODO/FIXME 주석 해결
3. 중복 코드 제거