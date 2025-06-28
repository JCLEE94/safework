import React, { useState, useEffect } from 'react';

// Components
import { Layout } from './components/Layout';
import { SimpleDashboard } from './components/SimpleDashboard';
import { AdvancedMonitoring } from './components/AdvancedMonitoring';
import { Workers } from './components/Workers';
import { HealthExams } from './components/HealthExams';
import { WorkEnvironments } from './components/WorkEnvironments';
import { HealthEducation } from './components/HealthEducation';
import { ChemicalSubstances } from './components/ChemicalSubstances';
import { AccidentReports } from './components/AccidentReports';
import { UnifiedDocuments } from './components/UnifiedDocuments';
import { EnhancedReports } from './components/EnhancedReports';
import { Settings } from './components/Settings';

function App() {
  const [activeMenu, setActiveMenu] = useState('dashboard');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  const renderContent = () => {
    switch (activeMenu) {
      case 'dashboard':
        return <SimpleDashboard />;
      case 'workers':
        return <Workers />;
      case 'health':
        return <HealthExams />;
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
      case 'reports':
        return <EnhancedReports />;
      case 'monitoring':
        return <AdvancedMonitoring />;
      case 'settings':
        return <Settings />;
      default:
        return <SimpleDashboard />;
    }
  };
  
  return (
    <Layout
      sidebarOpen={sidebarOpen}
      setSidebarOpen={setSidebarOpen}
      activeMenu={activeMenu}
      setActiveMenu={setActiveMenu}
    >
      {renderContent()}
    </Layout>
  );
}

export default App;