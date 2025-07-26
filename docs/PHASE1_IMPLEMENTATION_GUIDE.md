# Phase 1: 기반 구축 실행 가이드

## 1. 프로젝트 구조 설정

### 1.1 새로운 프론트엔드 구조
```
safework-frontend-v2/
├── src/
│   ├── components/           # 아토믹 디자인 컴포넌트
│   │   ├── atoms/           # 기본 요소
│   │   ├── molecules/       # 복합 컴포넌트
│   │   ├── organisms/       # 복잡한 UI 컴포넌트
│   │   └── templates/       # 페이지 템플릿
│   ├── pages/               # 실제 페이지 컴포넌트
│   ├── features/            # 기능별 모듈
│   │   ├── dashboard/
│   │   ├── health-monitoring/
│   │   ├── incident-management/
│   │   └── compliance/
│   ├── services/            # API 서비스
│   ├── hooks/               # 커스텀 React 훅
│   ├── store/               # Redux 스토어
│   ├── styles/              # 글로벌 스타일
│   ├── utils/               # 유틸리티 함수
│   └── types/               # TypeScript 타입 정의
├── tests/                   # 테스트 파일
├── public/                  # 정적 파일
└── docs/                    # 문서
```

### 1.2 기술 스택 초기 설정

```bash
# Vite 프로젝트 생성
npm create vite@latest safework-frontend-v2 -- --template react-ts

# 핵심 패키지 설치
cd safework-frontend-v2

# UI 라이브러리
npm install antd @ant-design/icons

# 상태 관리
npm install @reduxjs/toolkit react-redux
npm install @tanstack/react-query

# 라우팅
npm install react-router-dom

# 스타일링
npm install styled-components
npm install @types/styled-components -D

# 유틸리티
npm install axios dayjs lodash
npm install @types/lodash -D

# 개발 도구
npm install -D eslint prettier eslint-config-prettier
npm install -D @typescript-eslint/parser @typescript-eslint/eslint-plugin
```

## 2. Ant Design 기반 디자인 시스템

### 2.1 테마 설정
```typescript
// src/styles/theme.ts
import { ThemeConfig } from 'antd';

export const safeworkTheme: ThemeConfig = {
  token: {
    // 색상
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#f5222d',
    
    // 타이포그래피
    fontFamily: "'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: 14,
    
    // 간격
    borderRadius: 6,
    
    // 컴포넌트별 토큰
    controlHeight: 40,
  },
  components: {
    Button: {
      controlHeight: 40,
      fontSize: 16,
    },
    Table: {
      headerBg: '#fafafa',
      rowHoverBg: '#f5f5f5',
    },
    Card: {
      borderRadiusLG: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.09)',
    },
  },
};
```

### 2.2 기본 컴포넌트 래퍼
```typescript
// src/components/atoms/Button/index.tsx
import React from 'react';
import { Button as AntButton, ButtonProps as AntButtonProps } from 'antd';
import styled from 'styled-components';

export interface ButtonProps extends AntButtonProps {
  variant?: 'primary' | 'secondary' | 'danger' | 'text';
  fullWidth?: boolean;
}

const StyledButton = styled(AntButton)<{ $fullWidth?: boolean }>`
  ${props => props.$fullWidth && 'width: 100%;'}
  
  &.secondary {
    background-color: #f0f0f0;
    border-color: #d9d9d9;
    color: rgba(0, 0, 0, 0.85);
    
    &:hover {
      background-color: #e6e6e6;
      border-color: #d9d9d9;
    }
  }
`;

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'primary', 
  fullWidth,
  className = '',
  ...props 
}) => {
  const variantMap = {
    primary: 'primary',
    secondary: 'default',
    danger: 'primary',
    text: 'text',
  };

  return (
    <StyledButton
      {...props}
      type={variantMap[variant]}
      danger={variant === 'danger'}
      className={`${className} ${variant === 'secondary' ? 'secondary' : ''}`}
      $fullWidth={fullWidth}
    />
  );
};
```

## 3. 파일럿 모듈: 건강검진 관리

### 3.1 모듈 구조
```
src/features/health-monitoring/
├── components/
│   ├── ExamPlanCard.tsx
│   ├── ExamScheduleTable.tsx
│   └── WorkerExamStatus.tsx
├── pages/
│   ├── ExamDashboard.tsx
│   ├── ExamPlanManagement.tsx
│   └── ExamSchedule.tsx
├── services/
│   └── healthExamApi.ts
├── hooks/
│   ├── useExamPlans.ts
│   └── useExamStats.ts
└── types/
    └── index.ts
```

### 3.2 React Query 서비스 설정
```typescript
// src/services/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5분
      gcTime: 1000 * 60 * 10, // 10분
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// src/features/health-monitoring/hooks/useExamPlans.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { healthExamApi } from '../services/healthExamApi';
import { ExamPlan } from '../types';

export const useExamPlans = (year?: number) => {
  return useQuery({
    queryKey: ['examPlans', year],
    queryFn: () => healthExamApi.getPlans({ year }),
    select: (data) => data.filter(plan => plan.plan_status !== 'cancelled'),
  });
};

export const useCreateExamPlan = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: Omit<ExamPlan, 'id'>) => healthExamApi.createPlan(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['examPlans'] });
    },
  });
};
```

### 3.3 반응형 데이터 테이블
```typescript
// src/components/organisms/DataTable/index.tsx
import React from 'react';
import { Table, TableProps } from 'antd';
import { useMediaQuery } from '@/hooks/useMediaQuery';
import styled from 'styled-components';

const ResponsiveTableWrapper = styled.div`
  .ant-table-wrapper {
    .ant-table {
      font-size: 14px;
    }
    
    @media (max-width: 768px) {
      .ant-table-thead > tr > th {
        padding: 8px 8px;
        font-size: 12px;
      }
      
      .ant-table-tbody > tr > td {
        padding: 8px 8px;
        font-size: 12px;
      }
    }
  }
`;

export interface DataTableProps<T> extends TableProps<T> {
  mobileColumns?: TableProps<T>['columns'];
}

export function DataTable<T extends object>({ 
  columns, 
  mobileColumns, 
  ...props 
}: DataTableProps<T>) {
  const isMobile = useMediaQuery('(max-width: 768px)');
  
  return (
    <ResponsiveTableWrapper>
      <Table<T>
        {...props}
        columns={isMobile && mobileColumns ? mobileColumns : columns}
        scroll={{ x: isMobile ? 'max-content' : undefined }}
        pagination={{
          ...props.pagination,
          size: isMobile ? 'small' : 'default',
          showSizeChanger: !isMobile,
        }}
      />
    </ResponsiveTableWrapper>
  );
}
```

## 4. 모바일 우선 레이아웃

### 4.1 반응형 레이아웃 컴포넌트
```typescript
// src/components/templates/DashboardLayout.tsx
import React, { useState } from 'react';
import { Layout, Menu, Drawer, Grid } from 'antd';
import { MenuOutlined } from '@ant-design/icons';
import styled from 'styled-components';
import { useLocation, useNavigate } from 'react-router-dom';

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

const StyledLayout = styled(Layout)`
  min-height: 100vh;
`;

const MobileHeader = styled(Header)`
  display: none;
  padding: 0 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.09);
  
  @media (max-width: 768px) {
    display: flex;
    align-items: center;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
  }
`;

const StyledContent = styled(Content)`
  padding: 24px;
  background: #f0f2f5;
  
  @media (max-width: 768px) {
    padding: 16px;
    margin-top: 64px;
  }
`;

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const screens = useBreakpoint();
  const location = useLocation();
  const navigate = useNavigate();

  const isMobile = !screens.md;

  const menuItems = [
    { key: 'dashboard', label: '대시보드' },
    { key: 'workers', label: '작업자 관리' },
    { key: 'health-exam', label: '건강검진 관리' },
    { key: 'incidents', label: '사고 관리' },
    { key: 'compliance', label: '규정 준수' },
  ];

  return (
    <StyledLayout>
      {isMobile && (
        <MobileHeader>
          <MenuOutlined onClick={() => setMobileDrawerVisible(true)} />
          <h2 style={{ margin: '0 0 0 16px' }}>SafeWork Pro</h2>
        </MobileHeader>
      )}
      
      {!isMobile ? (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="light"
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname.split('/')[1] || 'dashboard']}
            items={menuItems}
            onClick={({ key }) => navigate(`/${key}`)}
          />
        </Sider>
      ) : (
        <Drawer
          placement="left"
          open={mobileDrawerVisible}
          onClose={() => setMobileDrawerVisible(false)}
          width={280}
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname.split('/')[1] || 'dashboard']}
            items={menuItems}
            onClick={({ key }) => {
              navigate(`/${key}`);
              setMobileDrawerVisible(false);
            }}
          />
        </Drawer>
      )}
      
      <Layout>
        <StyledContent>{children}</StyledContent>
      </Layout>
    </StyledLayout>
  );
};
```

## 5. 개발 환경 설정

### 5.1 ESLint 설정
```javascript
// .eslintrc.js
module.exports = {
  parser: '@typescript-eslint/parser',
  extends: [
    'react-app',
    'plugin:@typescript-eslint/recommended',
    'prettier',
  ],
  plugins: ['@typescript-eslint', 'react-hooks'],
  rules: {
    'react-hooks/rules-of-hooks': 'error',
    'react-hooks/exhaustive-deps': 'warn',
    '@typescript-eslint/explicit-module-boundary-types': 'off',
    '@typescript-eslint/no-explicit-any': 'warn',
  },
};
```

### 5.2 절대 경로 설정
```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@features': path.resolve(__dirname, './src/features'),
      '@services': path.resolve(__dirname, './src/services'),
      '@hooks': path.resolve(__dirname, './src/hooks'),
      '@utils': path.resolve(__dirname, './src/utils'),
      '@types': path.resolve(__dirname, './src/types'),
    },
  },
});
```

## 6. 테스트 전략

### 6.1 컴포넌트 테스트
```typescript
// src/components/atoms/Button/Button.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './index';

describe('Button Component', () => {
  it('renders correctly', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText('Click me')).toBeInTheDocument();
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    fireEvent.click(screen.getByText('Click me'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('applies fullWidth prop', () => {
    const { container } = render(<Button fullWidth>Full Width</Button>);
    const button = container.firstChild;
    expect(button).toHaveStyle('width: 100%');
  });
});
```

## 7. 성능 최적화

### 7.1 코드 분할
```typescript
// src/App.tsx
import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Spin } from 'antd';

// Lazy load pages
const Dashboard = lazy(() => import('./pages/Dashboard'));
const HealthExamManagement = lazy(() => import('./features/health-monitoring/pages/ExamDashboard'));
const IncidentManagement = lazy(() => import('./features/incident-management/pages/IncidentDashboard'));

const PageLoader = () => (
  <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
    <Spin size="large" />
  </div>
);

export const App: React.FC = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/health-exam/*" element={<HealthExamManagement />} />
        <Route path="/incidents/*" element={<IncidentManagement />} />
      </Routes>
    </Suspense>
  );
};
```

### 7.2 React Query 최적화
```typescript
// src/hooks/useOptimisticUpdate.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';

export function useOptimisticUpdate<TData, TVariables>(
  mutationFn: (variables: TVariables) => Promise<TData>,
  queryKey: string[],
  updateFn: (old: TData | undefined, variables: TVariables) => TData
) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onMutate: async (variables) => {
      await queryClient.cancelQueries({ queryKey });
      const previousData = queryClient.getQueryData<TData>(queryKey);
      queryClient.setQueryData(queryKey, (old) => updateFn(old, variables));
      return { previousData };
    },
    onError: (err, variables, context) => {
      queryClient.setQueryData(queryKey, context?.previousData);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });
}
```

## 8. 배포 준비

### 8.1 빌드 최적화
```typescript
// vite.config.ts (production)
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
          'state-vendor': ['@reduxjs/toolkit', 'react-redux', '@tanstack/react-query'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
```

### 8.2 환경 변수 설정
```typescript
// src/config/env.ts
export const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:3001/api/v1',
  environment: import.meta.env.VITE_ENVIRONMENT || 'development',
  version: import.meta.env.VITE_APP_VERSION || '2.0.0',
};
```

## 다음 단계

Phase 1 완료 후:
1. 파일럿 모듈 사용자 테스트
2. 피드백 반영 및 개선
3. Phase 2 계획 구체화
4. 추가 모듈 개발 착수

---
**문서 버전**: 1.0.0  
**작성일**: 2025-07-26