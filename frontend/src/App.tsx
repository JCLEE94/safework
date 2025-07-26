import { ConfigProvider } from 'antd';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { safeworkTheme } from './styles/theme';
import { store } from './store';
import { AppRoutes } from './routes/AppRoutes';
import { DashboardLayout } from './components/templates/DashboardLayout';
import GlobalTableStyles from './styles/GlobalTableStyles';
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
          <GlobalTableStyles />
          <BrowserRouter>
            <DashboardLayout>
              <AppRoutes />
            </DashboardLayout>
          </BrowserRouter>
        </ConfigProvider>
      </QueryClientProvider>
    </Provider>
  );
}

export default App;
