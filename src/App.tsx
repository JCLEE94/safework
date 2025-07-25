import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';

// Components
import { Layout } from './components/Layout';
import { SimpleDashboard } from './components/SimpleDashboard';
import { AdvancedMonitoring } from './components/AdvancedMonitoring';
import { Workers } from './components/Workers';
import { HealthExams } from './components/HealthExams';
import { HealthExamAppointments } from './components/HealthExamAppointments';
import { WorkEnvironments } from './components/WorkEnvironments';
import { HealthEducation } from './components/HealthEducation';
import { ChemicalSubstances } from './components/ChemicalSubstances';
import { AccidentReports } from './components/AccidentReports';
import { UnifiedDocuments } from './components/UnifiedDocuments';
import IntegratedDocuments from './components/IntegratedDocuments';
import { EnhancedReports } from './components/EnhancedReports';
import { Settings } from './components/Settings';
import ErrorBoundary from './components/ErrorBoundary';
import { LoginForm } from './components/Auth/LoginForm';
import QRRegistration from './components/QRRegistration';
import WorkerRegistration from './components/WorkerRegistration';
import ConfinedSpace from './components/ConfinedSpace';
// import CardiovascularPage from './pages/CardiovascularPage';
import { QRRegistrationPage } from './pages/QRRegistrationPage';
import { PublicQRRegistration } from './pages/PublicQRRegistration';
import SimpleRegistration from './pages/SimpleRegistration';
import { CommonQRRegistration } from './components/CommonQRRegistration';
import { CommonQRGenerator } from './components/CommonQRGenerator';
import HealthRoom from './pages/HealthRoom';
import { authService } from './services/authService';

function MainApp() {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const location = useLocation();
  
  useEffect(() => {
    // 초기 인증 상태 확인
    const checkAuth = () => {
      const authenticated = authService.isAuthenticated();
      setIsAuthenticated(authenticated);
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  // Worker Registration 페이지인지 확인
  const isWorkerRegistrationPage = () => {
    return location.pathname === '/worker-registration';
  };

  // Simple Registration 페이지인지 확인
  const isSimpleRegistrationPage = () => {
    return location.pathname === '/register';
  };
  
  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };
  
  const handleLogout = async () => {
    try {
      await authService.logout();
    } catch (error) {
      console.error('로그아웃 오류:', error);
    } finally {
      setIsAuthenticated(false);
      setActiveMenu('dashboard');
    }
  };
  
  const renderContent = () => {
    switch (activeMenu) {
      case 'dashboard':
        return <SimpleDashboard />;
      case 'workers':
        return <Workers />;
      case 'health':
        return <HealthExams />;
      case 'appointments':
        return <HealthExamAppointments />;
      case 'environment':
        return <WorkEnvironments />;
      case 'education':
        return <HealthEducation />;
      case 'chemicals':
        return <ChemicalSubstances />;
      case 'accidents':
        return <AccidentReports />;
      case 'unified-documents':
        return <UnifiedDocuments />;
      case 'integrated-documents':
        return <IntegratedDocuments />;
      case 'reports':
        return <EnhancedReports />;
      case 'monitoring':
        return <AdvancedMonitoring />;
      case 'qr-registration':
        return <QRRegistration />;
      case 'common-qr':
        return <CommonQRGenerator />;
      case 'confined-space':
        return <ConfinedSpace />;
      case 'cardiovascular':
        return <div>심혈관 시스템 (임시 비활성화)</div>;
      case 'health-room':
        return <HealthRoom />;
      case 'settings':
        return <Settings />;
      default:
        return <SimpleDashboard />;
    }
  };
  
  // 근로자 등록 페이지는 인증 없이 접근 가능
  if (isWorkerRegistrationPage()) {
    return <WorkerRegistration />;
  }

  // 간단한 등록 페이지는 인증 없이 접근 가능
  if (isSimpleRegistrationPage()) {
    return <SimpleRegistration />;
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
          <p className="mt-4 text-gray-600">로딩 중...</p>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <LoginForm onLoginSuccess={handleLoginSuccess} />;
  }
  
  return (
    <ErrorBoundary>
      <Layout
        sidebarOpen={sidebarOpen}
        setSidebarOpen={setSidebarOpen}
        activeMenu={activeMenu}
        setActiveMenu={setActiveMenu}
        onLogout={handleLogout}
      >
        {renderContent()}
      </Layout>
    </ErrorBoundary>
  );
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/qr-register" element={<PublicQRRegistration />} />
        <Route path="/qr-register/:token" element={<QRRegistrationPage />} />
        <Route path="/register" element={<SimpleRegistration />} />
        <Route path="/register-qr" element={<CommonQRRegistration />} />
        <Route path="/*" element={<MainApp />} />
      </Routes>
    </Router>
  );
}

export default App;