# SafeWork Pro v2.0 Frontend

## 개요
SafeWork Pro의 현대적인 프론트엔드 리팩토링 프로젝트입니다. React 19, TypeScript, Ant Design을 기반으로 구축되었습니다.

## 기술 스택
- **Framework**: React 19 with TypeScript
- **UI Library**: Ant Design 5.26.6
- **State Management**: 
  - Server State: TanStack Query v5.83+
  - Client State: Redux Toolkit 2.8+
- **Routing**: React Router v7.7+
- **Styling**: styled-components v6.1+
- **HTTP Client**: Axios v1.11+
- **Build Tool**: Vite v7.0+
- **Package Manager**: npm
- **Testing**: Jest 30 + React Testing Library 16.3+

## 시작하기

### 개발 서버 실행
```bash
npm install
npm run dev
```

개발 서버는 http://localhost:3000 에서 실행됩니다.

### 빌드
```bash
npm run build
```

### 미리보기
```bash
npm run preview
```

## 프로젝트 구조
```
src/
├── components/           # 아토믹 디자인 컴포넌트
│   ├── atoms/           # 기본 요소
│   ├── molecules/       # 복합 컴포넌트
│   ├── organisms/       # 복잡한 UI 컴포넌트
│   └── templates/       # 페이지 템플릿
├── features/            # 기능별 모듈
│   ├── dashboard/
│   ├── health-monitoring/
│   ├── incident-management/
│   └── compliance/
├── pages/               # 페이지 컴포넌트
├── services/            # API 서비스
├── hooks/               # 커스텀 React 훅
├── store/               # Redux 스토어
├── styles/              # 글로벌 스타일
├── utils/               # 유틸리티 함수
└── types/               # TypeScript 타입 정의
```

## 주요 기능
- 과업 중심 정보 구조
- 반응형 디자인 (모바일 우선)
- 역할 기반 대시보드
- 건강검진 관리 시스템
- 실시간 데이터 동기화

## 개발 가이드라인
- 아토믹 디자인 패턴 준수
- TypeScript 타입 안정성 보장
- React Query로 서버 상태 관리
- 모바일 우선 반응형 디자인

## 관련 문서
- [서비스 재설계 계획](../docs/SERVICE_REDESIGN_PLAN.md)
- [Phase 1 구현 가이드](../docs/PHASE1_IMPLEMENTATION_GUIDE.md)

## 🤖 AI Agent 활용 가이드

### SafeWork Pro 프로젝트에서 Agent 활용하기

Claude Code의 Task tool을 사용하여 실제 서브 에이전트를 생성하고 SafeWork Pro 프로젝트에서 효율적으로 작업할 수 있습니다.

### 실용적인 활용 예시

#### 1. 전체 시스템 분석 (5개 Agent 병렬 실행)
```
"SafeWork Pro 시스템을 5개 전문 Agent로 분석해줘:
1. 프론트엔드 아키텍트: React 19 컴포넌트 구조와 성능 분석
2. 백엔드 아키텍트: FastAPI 서버 구조와 API 설계 분석
3. 데이터베이스 전문가: PostgreSQL 스키마와 쿼리 최적화 분석
4. 보안 전문가: JWT 인증, CORS, 보안 취약점 분석
5. DevOps 전문가: Docker, K8s, ArgoCD 배포 구조 분석"
```

#### 2. 건강관리실 기능 개발 (4개 Agent 협업)
```
"건강관리실 대시보드 기능을 구현해줘. 4개 Agent로 나누어서:
1. UI/UX 개발자: Ant Design으로 대시보드 UI 구현
2. API 개발자: 건강검진 통계 API 엔드포인트 구현
3. 상태 관리 전문가: TanStack Query로 서버 상태 관리
4. 테스트 엔지니어: Jest로 컴포넌트 및 API 테스트 작성"
```

#### 3. 성능 최적화 (3개 Agent 동시 분석)
```
"SafeWork Pro의 성능을 최적화해줘:
1. 프론트엔드 성능 전문가: React 19 최적화, 번들 크기 줄이기
2. 백엔드 성능 전문가: FastAPI 응답 속도, Redis 캐싱 최적화
3. 데이터베이스 성능 전문가: PostgreSQL 인덱스, 쿼리 최적화"
```

#### 4. 보안 감사 (4개 Agent 체크리스트)
```
"전체 시스템 보안을 점검해줘:
1. 프론트엔드 보안: XSS, CSRF 방어 체크
2. API 보안: JWT 검증, 권한 체크, Rate Limiting
3. 데이터베이스 보안: SQL Injection 방어, 암호화
4. 인프라 보안: K8s 보안 설정, 네트워크 정책"
```

#### 5. 모바일 대응 개발 (3개 Agent)
```
"모바일 우선 반응형 디자인을 구현해줘:
1. UI 전문가: Ant Design Mobile 컴포넌트 적용
2. 성능 전문가: 모바일 최적화 (이미지, 번들 크기)
3. 테스트 전문가: 다양한 디바이스 테스트"
```

### 프로젝트별 Agent 활용 패턴

#### Feature 개발 패턴
```
"health-monitoring 기능을 개선해줘. 3개 Agent로:
1. 컴포넌트 개발자: ExamPlanCard, WorkerExamStatusTable 개선
2. Hook 개발자: useExamPlans, useExamStats 최적화
3. API 개발자: healthExamApi 엔드포인트 확장"
```

#### 코드 리뷰 패턴
```
"최근 커밋된 코드를 3명의 리뷰어가 검토해줘:
1. React 전문가: 컴포넌트 설계와 Hooks 사용법
2. TypeScript 전문가: 타입 안정성과 인터페이스 설계
3. 품질 전문가: 코드 스타일, 테스트 커버리지"
```

#### 문서화 패턴
```
"프로젝트 문서를 업데이트해줘. 3개 Agent로:
1. API 문서 작성자: Swagger/OpenAPI 문서 업데이트
2. 컴포넌트 문서 작성자: Storybook 스토리 작성
3. 배포 문서 작성자: K8s 매니페스트 문서화"
```

### SafeWork Pro 특화 명령어

#### 건설업 도메인 분석
```
"건설업 보건관리 요구사항을 4개 관점에서 분석해줘:
1. 법규 준수 전문가: 산업안전보건법 준수 사항
2. UX 전문가: 건설 현장 작업자 사용성
3. 데이터 전문가: 건강검진 데이터 관리
4. 통합 전문가: 외부 시스템 연동 (MSDS, 검진기관)"
```

#### 다국어 지원
```
"한국어 UI를 개선해줘. 2개 Agent로:
1. i18n 전문가: 다국어 시스템 구축
2. 한국어 전문가: 산업 용어 번역 검증"
```

### 효율적인 Agent 조합

#### 풀스택 개발 (5 Agent)
```
Frontend (2) + Backend (2) + Database (1)
- React 개발자 + UI 디자이너
- FastAPI 개발자 + API 설계자
- PostgreSQL 전문가
```

#### 테스트 자동화 (4 Agent)
```
Unit Test (1) + Integration (1) + E2E (1) + Performance (1)
- Jest 단위 테스트
- API 통합 테스트
- Cypress E2E 테스트
- Lighthouse 성능 테스트
```

#### 배포 파이프라인 (3 Agent)
```
CI (1) + CD (1) + Monitoring (1)
- GitHub Actions 설정
- ArgoCD 배포 설정
- Prometheus/Grafana 모니터링
```

### 실행 우선순위

1. **긴급 버그 수정**: 단일 Agent로 빠른 처리
2. **기능 개발**: 2-3개 Agent로 효율적 개발
3. **시스템 분석**: 4-5개 Agent로 심층 분석
4. **대규모 리팩토링**: 5-10개 Agent로 체계적 진행

### 주의사항

- **컨텍스트 공유**: 각 Agent는 독립적이므로 공통 정보는 메인 Agent가 전달
- **병렬 처리 한계**: 최대 10개 Agent 동시 실행
- **시간 고려**: 복잡한 작업일수록 Agent 수를 늘려 병렬 처리
- **결과 통합**: 메인 Agent가 서브 Agent들의 결과를 종합하여 일관성 유지

### Phase별 Agent 활용 전략

#### Phase 1: 기반 구축 (디자인 시스템)
```
"Ant Design 기반 아토믹 컴포넌트를 구축해줘. 4개 Agent로:
1. Atoms 개발자: Button, Icon, Typography 컴포넌트
2. Molecules 개발자: Input.Search, DatePicker, Select 
3. Organisms 개발자: Table, Form, Card, PageHeader
4. Storybook 개발자: 컴포넌트 문서화 및 테스트"
```

#### Phase 2: 핵심 기능 재구축
```
"역할 기반 대시보드를 구현해줘. 5개 Agent로:
1. HSManager 대시보드: 보건안전 관리자용 위젯
2. Executive 대시보드: 임원용 KPI 차트
3. Worker 대시보드: 일반 직원용 인터페이스
4. API 연동 전문가: TanStack Query 설정
5. 상태 관리자: Redux Toolkit 설정"
```

#### Phase 3: 전체 마이그레이션
```
"레거시 시스템 마이그레이션을 준비해줘. 4개 Agent로:
1. 데이터 마이그레이션 전문가: PostgreSQL 스키마 분석
2. API 호환성 전문가: 레거시 API 래퍼 구현
3. 테스트 자동화 전문가: E2E 테스트 시나리오
4. 배포 전문가: Blue-Green 배포 전략"
```

### 실전 활용 시나리오

#### 1. 새 기능 모듈 개발
```
"화학물질 관리(MSDS) 모듈을 구현해줘. 6개 Agent로:
1. DB 스키마 설계자: chemical_substances 테이블 설계
2. API 개발자: FastAPI 엔드포인트 구현
3. UI 컴포넌트 개발자: MSDS 조회/등록 폼
4. 파일 업로드 전문가: MSDS PDF 파일 처리
5. 검색 기능 개발자: 화학물질 검색 기능
6. 테스트 개발자: 통합 테스트 작성"
```

#### 2. 성능 최적화 Sprint
```
"전체 앱 성능을 최적화해줘. 5개 Agent로:
1. Bundle 분석가: Vite 번들 크기 최적화
2. React 최적화 전문가: React.lazy, Suspense 적용
3. API 최적화 전문가: GraphQL 도입 검토
4. 캐싱 전문가: Redis 캐싱 전략 구현
5. 모니터링 전문가: 성능 메트릭 대시보드"
```

#### 3. 규정 준수 감사
```
"산업안전보건법 준수사항을 점검해줘. 4개 Agent로:
1. 법규 분석가: 최신 법규 요구사항 매핑
2. 기능 검토자: 현재 구현된 기능 vs 법규 비교
3. 보고서 전문가: 규정 준수 보고서 양식 구현
4. 알림 시스템 개발자: 규정 위반 알림 기능"
```

### Agent 협업 Best Practices

#### 1. 정보 아키텍처 개선
```
"정보 구조를 과업 중심으로 재설계해줘:
Agent 1: 사용자 인터뷰 분석 → 페르소나별 니즈 파악
Agent 2: 카드 소팅 → 최적 메뉴 구조 도출
Agent 3: 프로토타입 → Figma 목업 제작
Agent 4: 구현 → React Router 구조 구현"
```

#### 2. 모바일 우선 개발
```
"모바일 경험을 최적화해줘:
Agent 1: 터치 인터페이스 → 제스처 기반 UI
Agent 2: 오프라인 지원 → PWA 구현
Agent 3: 성능 최적화 → 3G 환경 최적화
Agent 4: 디바이스 테스트 → 실기기 테스트"
```

### 도메인 특화 Agent 활용

#### 건설 현장 특화 기능
```
"건설 현장용 모바일 앱을 개발해줘:
1. QR 코드 전문가: 작업자 출입 관리
2. 오프라인 전문가: 네트워크 없는 환경 대응
3. 음성 입력 전문가: 헬멧 착용 상태 입력
4. 위치 기반 전문가: 현장 내 위치 추적"
```

#### 건강검진 자동화
```
"건강검진 프로세스를 자동화해줘:
1. 일정 관리자: 검진 주기 자동 계산
2. 알림 개발자: 카카오톡/SMS 알림
3. 문서 자동화: PDF 검진 결과서 파싱
4. 통계 분석가: 검진 결과 트렌드 분석"
```

### 트러블슈팅 Agent 패턴

#### 버그 해결
```
"프로덕션 버그를 해결해줘:
1. 로그 분석가: Sentry 에러 로그 분석
2. 재현 전문가: 버그 재현 시나리오 작성
3. 수정 개발자: 핫픽스 구현
4. 검증 전문가: 회귀 테스트 수행"
```

#### 성능 이슈
```
"느린 페이지 로딩을 해결해줘:
1. 프로파일러: React DevTools 분석
2. 네트워크 분석가: API 호출 최적화
3. 이미지 전문가: 이미지 최적화
4. 코드 스플리터: 동적 import 적용"
```

이 가이드를 참고하여 SafeWork Pro 프로젝트에서 효율적으로 Agent 기능을 활용하세요!