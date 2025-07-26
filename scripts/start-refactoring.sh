#!/bin/bash

# SafeWork Pro 리팩토링 시작 스크립트
# Phase 1: 기반 구축

echo "🚀 SafeWork Pro 리팩토링 프로젝트 시작..."
echo "================================================"

# 색상 정의
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 프로젝트 루트 확인
if [ ! -f "README.md" ]; then
    echo "❌ 프로젝트 루트에서 실행해주세요."
    exit 1
fi

echo -e "${BLUE}1. 새로운 프론트엔드 프로젝트 생성${NC}"
echo "----------------------------------------"

# 기존 v2 디렉토리 확인
if [ -d "safework-frontend-v2" ]; then
    echo -e "${YELLOW}⚠️  safework-frontend-v2 디렉토리가 이미 존재합니다.${NC}"
    read -p "삭제하고 새로 생성하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf safework-frontend-v2
    else
        echo "기존 디렉토리를 유지합니다."
        cd safework-frontend-v2
    fi
else
    # Vite 프로젝트 생성
    echo "Vite + React + TypeScript 프로젝트 생성 중..."
    npm create vite@latest safework-frontend-v2 -- --template react-ts
    cd safework-frontend-v2
fi

echo -e "\n${BLUE}2. 필수 패키지 설치${NC}"
echo "----------------------------------------"

# 패키지 설치
echo "핵심 의존성 설치 중..."
npm install \
    antd@^5.0.0 \
    @ant-design/icons \
    @reduxjs/toolkit \
    react-redux \
    @tanstack/react-query \
    react-router-dom \
    styled-components \
    axios \
    dayjs \
    lodash

echo -e "\n개발 의존성 설치 중..."
npm install -D \
    @types/styled-components \
    @types/lodash \
    eslint \
    prettier \
    eslint-config-prettier \
    @typescript-eslint/parser \
    @typescript-eslint/eslint-plugin \
    @testing-library/react \
    @testing-library/jest-dom \
    @testing-library/user-event \
    jest \
    @types/jest

echo -e "\n${BLUE}3. 프로젝트 구조 생성${NC}"
echo "----------------------------------------"

# 디렉토리 구조 생성
mkdir -p src/{components/{atoms,molecules,organisms,templates},pages,features,services,hooks,store,styles,utils,types}
mkdir -p src/features/{dashboard,health-monitoring,incident-management,compliance}/{components,pages,services,hooks,types}

echo -e "${GREEN}✅ 디렉토리 구조 생성 완료${NC}"

echo -e "\n${BLUE}4. 기본 설정 파일 생성${NC}"
echo "----------------------------------------"

# TypeScript 설정
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"],
      "@components/*": ["src/components/*"],
      "@features/*": ["src/features/*"],
      "@services/*": ["src/services/*"],
      "@hooks/*": ["src/hooks/*"],
      "@utils/*": ["src/utils/*"],
      "@types/*": ["src/types/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

# Vite 설정 업데이트
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
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
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:3001',
        changeOrigin: true,
      },
    },
  },
});
EOF

# ESLint 설정
cat > .eslintrc.js << 'EOF'
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
EOF

# Prettier 설정
cat > .prettierrc << 'EOF'
{
  "semi": true,
  "trailingComma": "es5",
  "singleQuote": true,
  "printWidth": 100,
  "tabWidth": 2,
  "useTabs": false
}
EOF

echo -e "${GREEN}✅ 설정 파일 생성 완료${NC}"

echo -e "\n${BLUE}5. 초기 컴포넌트 생성${NC}"
echo "----------------------------------------"

# App.tsx 생성
cat > src/App.tsx << 'EOF'
import React from 'react';
import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { safeworkTheme } from './styles/theme';
import { store } from './store';
import { AppRoutes } from './routes';
import './styles/global.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5분
      gcTime: 1000 * 60 * 10, // 10분
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={safeworkTheme}>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </ConfigProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
EOF

# 테마 파일 생성
mkdir -p src/styles
cat > src/styles/theme.ts << 'EOF'
import { ThemeConfig } from 'antd';

export const safeworkTheme: ThemeConfig = {
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#f5222d',
    fontFamily: "'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontSize: 14,
    borderRadius: 6,
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
EOF

# 글로벌 스타일
cat > src/styles/global.css << 'EOF'
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #root {
  height: 100%;
}

body {
  font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
EOF

# Redux 스토어 생성
cat > src/store/index.ts << 'EOF'
import { configureStore } from '@reduxjs/toolkit';

export const store = configureStore({
  reducer: {
    // 리듀서들이 여기에 추가됩니다
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
EOF

# 라우트 설정
cat > src/routes/index.tsx << 'EOF'
import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Spin } from 'antd';

// Lazy load pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));

const PageLoader = () => (
  <div style={{ display: 'flex', justifyContent: 'center', padding: '100px' }}>
    <Spin size="large" />
  </div>
);

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
      </Routes>
    </Suspense>
  );
};
EOF

# 대시보드 페이지 생성
cat > src/pages/Dashboard.tsx << 'EOF'
import React from 'react';
import { Typography, Card, Row, Col } from 'antd';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>SafeWork Pro v2.0 대시보드</Title>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Title level={4}>전체 근로자</Title>
            <p>준비 중...</p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Title level={4}>건강검진 현황</Title>
            <p>준비 중...</p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Title level={4}>사고 현황</Title>
            <p>준비 중...</p>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Title level={4}>규정 준수율</Title>
            <p>준비 중...</p>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;
EOF

echo -e "${GREEN}✅ 초기 컴포넌트 생성 완료${NC}"

echo -e "\n${BLUE}6. Git 설정${NC}"
echo "----------------------------------------"

# .gitignore 업데이트
cat >> .gitignore << 'EOF'

# 환경 변수
.env.local
.env.development
.env.production

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db
EOF

echo -e "${GREEN}✅ Git 설정 완료${NC}"

echo -e "\n${GREEN}🎉 SafeWork Pro v2.0 리팩토링 프로젝트 설정 완료!${NC}"
echo -e "================================================"
echo -e "\n다음 명령어로 개발 서버를 시작하세요:"
echo -e "${BLUE}cd safework-frontend-v2${NC}"
echo -e "${BLUE}npm run dev${NC}"
echo -e "\n자세한 구현 가이드는 다음 문서를 참조하세요:"
echo -e "- ${YELLOW}docs/SERVICE_REDESIGN_PLAN.md${NC}"
echo -e "- ${YELLOW}docs/PHASE1_IMPLEMENTATION_GUIDE.md${NC}"