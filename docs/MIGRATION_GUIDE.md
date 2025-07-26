# SafeWork Pro 데이터 마이그레이션 가이드

## 개요
이 문서는 SafeWork Pro의 기존 데이터베이스 구조를 새로운 표준화된 구조로 마이그레이션하는 과정을 설명합니다.

## 마이그레이션 목표

### 1. 데이터 표준화
- 상태 코드 통합 관리
- 부서/직위/작업유형 마스터 데이터 구축
- 일관된 명명 규칙 적용

### 2. 참조 무결성 강화
- 외래 키 관계 정립
- 코드 기반 참조 체계 구축
- 데이터 일관성 보장

### 3. 성능 최적화
- 적절한 인덱스 생성
- 쿼리 최적화를 위한 구조 개선

## 마이그레이션 단계

### Phase 1: 준비 단계
1. 데이터베이스 백업
   ```bash
   pg_dump -U admin -d health_management > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. 마이그레이션 스크립트 확인
   - `/scripts/migrate-data.py`: 메인 마이그레이션 스크립트
   - `/scripts/validate-migration.py`: 검증 스크립트

### Phase 2: 마이그레이션 실행
```bash
# 마이그레이션 실행
cd /home/jclee/app/safework
python scripts/migrate-data.py

# 출력 예시:
# 🚀 SafeWork Pro 데이터 마이그레이션 시작...
# ==================================================
# ✅ [standardized_tables] created: 5 records
# ✅ [standard_codes] inserted: 26 records
# ✅ [departments] migrated: 10 records
# ✅ [positions] migrated: 8 records
# ✅ [work_types] migrated: 15 records
# ✅ [foreign_keys] updated: 4 records
# ✅ [indexes] created: 8 records
# ==================================================
# ✅ 마이그레이션 완료!
# 📄 마이그레이션 로그 저장: migration_log_20250126_153045.json
```

### Phase 3: 검증
```bash
# 마이그레이션 검증
python scripts/validate-migration.py

# 출력 예시:
# 🔍 SafeWork Pro 마이그레이션 검증 시작...
# ==================================================
# ✅ Standard Tables: PASS
# ✅ Code Data: PASS
# ✅ Master Data: PASS
# ✅ Data Mapping: PASS
# ✅ Foreign Key Integrity: PASS
# ✅ Database Indexes: PASS
# ⚠️  Data Consistency: WARN
# ==================================================
# 📄 검증 보고서 저장: validation_report_20250126_153245.json
```

## 새로운 데이터 구조

### 1. 표준 코드 관리
```sql
-- status_codes 테이블
CREATE TABLE status_codes (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,    -- EXAM_PLAN_STATUS, EXAM_STATUS 등
    code VARCHAR(50) NOT NULL,        -- draft, approved, completed 등
    name_ko VARCHAR(100) NOT NULL,    -- 한글명
    name_en VARCHAR(100) NOT NULL,    -- 영문명
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    UNIQUE(category, code)
);
```

### 2. 마스터 데이터 테이블
- **departments**: 부서 마스터
- **positions**: 직위/직급 마스터
- **work_types**: 작업 유형 마스터 (특수건강진단 대상 여부 포함)

### 3. 업데이트된 workers 테이블
```sql
-- 새로운 컬럼 추가
ALTER TABLE workers ADD COLUMN department_code VARCHAR(50);
ALTER TABLE workers ADD COLUMN position_code VARCHAR(50);
ALTER TABLE workers ADD COLUMN work_type_code VARCHAR(50);

-- 외래 키 관계 (선택적)
ALTER TABLE workers 
ADD CONSTRAINT fk_department 
FOREIGN KEY (department_code) REFERENCES departments(code);
```

## 애플리케이션 영향도

### 1. API 변경사항
- 기존 텍스트 필드는 유지 (하위 호환성)
- 새로운 코드 필드 추가 반환
- 점진적 마이그레이션 지원

### 2. 프론트엔드 변경사항
- 드롭다운 목록을 마스터 데이터에서 조회
- 코드-텍스트 매핑 처리
- 다국어 지원 준비

### 3. 비즈니스 로직 변경
- 특수건강진단 대상자 자동 식별
- 부서별 계층 구조 지원
- 직급별 권한 관리 가능

## 롤백 계획

마이그레이션 문제 발생 시:
```bash
# 1. 백업에서 복원
psql -U admin -d health_management < backup_YYYYMMDD_HHMMSS.sql

# 2. 추가된 컬럼만 제거 (부분 롤백)
ALTER TABLE workers 
DROP COLUMN department_code,
DROP COLUMN position_code,
DROP COLUMN work_type_code;

# 3. 표준화 테이블 제거 (완전 롤백)
DROP TABLE IF EXISTS status_codes CASCADE;
DROP TABLE IF EXISTS code_categories CASCADE;
DROP TABLE IF EXISTS departments CASCADE;
DROP TABLE IF EXISTS positions CASCADE;
DROP TABLE IF EXISTS work_types CASCADE;
```

## 주의사항

1. **데이터 백업 필수**
   - 마이그레이션 전 반드시 전체 백업 수행
   - 프로덕션 환경에서는 유지보수 시간에 실행

2. **단계적 적용**
   - 개발 환경에서 충분한 테스트 후 적용
   - 애플리케이션 코드 변경과 동기화

3. **모니터링**
   - 마이그레이션 후 성능 모니터링
   - 데이터 일관성 주기적 검증

## 트러블슈팅

### 문제 1: 외래 키 제약 조건 위반
```sql
-- 매핑되지 않은 데이터 확인
SELECT DISTINCT department 
FROM workers 
WHERE department_code IS NULL 
AND department IS NOT NULL;
```

### 문제 2: 중복 코드 발생
```sql
-- 중복 제거
DELETE FROM departments 
WHERE id NOT IN (
    SELECT MIN(id) 
    FROM departments 
    GROUP BY code
);
```

### 문제 3: 성능 저하
```sql
-- 통계 업데이트
ANALYZE workers;
ANALYZE departments;
ANALYZE positions;
ANALYZE work_types;
```

## 마이그레이션 후 체크리스트

- [ ] 모든 표준 테이블 생성 확인
- [ ] 코드 데이터 정상 입력 확인
- [ ] 기존 데이터 매핑 완료 확인
- [ ] 외래 키 무결성 검증
- [ ] 인덱스 생성 확인
- [ ] 애플리케이션 정상 동작 테스트
- [ ] 성능 벤치마크 비교
- [ ] 백업 파일 안전한 위치에 보관

---
**문서 버전**: 1.0.0  
**작성일**: 2025-07-26  
**작성자**: SafeWork Pro 개발팀