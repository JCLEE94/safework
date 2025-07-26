# SafeWork Pro v2.0 Frontend

## 개요
SafeWork Pro의 현대적인 프론트엔드 리팩토링 프로젝트입니다. React, TypeScript, Ant Design을 기반으로 구축되었습니다.

## 기술 스택
- **Framework**: React 18+ with TypeScript
- **UI Library**: Ant Design 5.x
- **State Management**: 
  - Server State: React Query (TanStack Query)
  - Client State: Redux Toolkit
- **Styling**: styled-components
- **Build Tool**: Vite
- **Package Manager**: npm

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