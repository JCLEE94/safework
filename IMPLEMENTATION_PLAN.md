# SafeWork 미구현 기능 구현 계획

## 🎯 Phase 1: 개인 건강관리카드 시스템 구현

### 1. 개인 건강관리카드 (Personal Health Card)

#### 📋 기능 요구사항
- 작업자별 건강 이력 추적
- 유소견자 관리 시스템
- 건강 상태 변화 추적
- 개인별 건강 대시보드
- 건강검진 결과 통합 관리

#### 🗄️ 데이터베이스 설계

**새로운 테이블들:**
1. `personal_health_cards` - 개인 건강관리카드 기본 정보
2. `health_history` - 건강 이력 추적
3. `abnormal_findings` - 유소견자 관리
4. `health_indicators` - 건강 지표 관리
5. `health_recommendations` - 건강 권고사항

#### 🔗 API 엔드포인트
- `GET /api/v1/personal-health-cards/` - 건강관리카드 목록
- `POST /api/v1/personal-health-cards/` - 새 건강관리카드 생성
- `GET /api/v1/personal-health-cards/{worker_id}` - 특정 작업자 건강관리카드
- `PUT /api/v1/personal-health-cards/{worker_id}` - 건강관리카드 업데이트
- `GET /api/v1/personal-health-cards/{worker_id}/history` - 건강 이력
- `POST /api/v1/personal-health-cards/{worker_id}/findings` - 유소견 사항 등록

#### 🎨 프론트엔드 컴포넌트
- `PersonalHealthCard` - 메인 건강관리카드 컴포넌트
- `HealthHistoryTimeline` - 건강 이력 타임라인
- `AbnormalFindingsManager` - 유소견자 관리
- `HealthDashboard` - 개인별 건강 대시보드

### 2. 구현 순서

#### Step 1: 데이터베이스 모델 및 스키마 생성
1. SQLAlchemy 모델 정의
2. Alembic 마이그레이션 생성
3. 데이터베이스 스키마 업데이트

#### Step 2: 백엔드 API 구현
1. Pydantic 스키마 정의
2. FastAPI 핸들러 구현
3. 비즈니스 로직 서비스 구현

#### Step 3: 프론트엔드 구현
1. TypeScript 타입 정의
2. React 컴포넌트 구현
3. API 연동 및 상태 관리

#### Step 4: 통합 테스트
1. 단위 테스트 작성
2. API 통합 테스트
3. 프론트엔드 테스트

### 3. 세부 구현 계획

#### 🗄️ 데이터베이스 스키마

```sql
-- 개인 건강관리카드 기본 정보
CREATE TABLE personal_health_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    worker_id UUID NOT NULL REFERENCES workers(id),
    card_number VARCHAR(20) UNIQUE NOT NULL,
    issued_date DATE NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 건강 이력 추적
CREATE TABLE health_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES personal_health_cards(id),
    exam_date DATE NOT NULL,
    exam_type VARCHAR(50) NOT NULL,
    result_summary TEXT,
    recommendations TEXT,
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 유소견자 관리
CREATE TABLE abnormal_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES personal_health_cards(id),
    finding_date DATE NOT NULL,
    category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    action_taken TEXT,
    follow_up_required BOOLEAN DEFAULT TRUE,
    resolved_date DATE,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 건강 지표 관리
CREATE TABLE health_indicators (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES personal_health_cards(id),
    measurement_date DATE NOT NULL,
    indicator_type VARCHAR(50) NOT NULL,
    value DECIMAL(10,2) NOT NULL,
    unit VARCHAR(20) NOT NULL,
    normal_range_min DECIMAL(10,2),
    normal_range_max DECIMAL(10,2),
    is_abnormal BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 🔧 핵심 기능 구현 포인트

1. **건강 이력 추적**
   - 모든 건강검진 결과 자동 연동
   - 시간순 정렬된 건강 이력 표시
   - 변화 추이 그래프 생성

2. **유소견자 관리**
   - 자동 유소견 판정 로직
   - 심각도별 분류 시스템
   - 후속 조치 관리

3. **개인별 대시보드**
   - 주요 건강 지표 시각화
   - 개선 추천 사항 표시
   - 예정된 검진 일정 안내

### 4. 예상 개발 일정

| 단계 | 작업 내용 | 소요 시간 |
|------|-----------|----------|
| 1 | 데이터베이스 설계 및 마이그레이션 | 2일 |
| 2 | 백엔드 API 구현 | 4일 |
| 3 | 프론트엔드 컴포넌트 구현 | 5일 |
| 4 | 통합 테스트 및 버그 수정 | 2일 |
| 5 | 문서화 및 배포 | 1일 |

**총 예상 소요 시간: 14일 (약 2주)**

### 5. 다음 단계

Phase 1 완료 후 다음 우선순위 기능들을 순차적으로 구현:

1. **인바디 측정 현황 관리**
2. **자가진단 프로그램**
3. **밀폐공간 관리 시스템**
4. **뇌심혈관계 관리**

---

**작성일**: 2025-01-17  
**버전**: 1.0  
**담당자**: SafeWork Pro Development Team