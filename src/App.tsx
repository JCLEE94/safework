import React, { useState, useEffect } from 'react';

// Components
import { Layout } from './components/Layout';
import { SimpleDashboard } from './components/SimpleDashboard';
import { RealTimeMonitoring } from './components/Monitoring/RealTimeMonitoring';
import { Workers } from './components/Workers';
import { HealthExams } from './components/HealthExams';
import { WorkEnvironments } from './components/WorkEnvironments';
import { HealthEducation } from './components/HealthEducation';
import { ChemicalSubstances } from './components/ChemicalSubstances';
import { AccidentReports } from './components/AccidentReports';
import { DocumentManagement } from './components/DocumentManagement';
import { PDFForms } from './components/PDFForms';
import { FileManagement } from './components/FileManagement';
import { Reports } from './components/Reports';
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
      case 'documents':
        return <DocumentManagement />;
      case 'file-management':
        return <FileManagement />;
      case 'pdf-forms':
        return <PDFForms />;
      case 'reports':
        return <Reports />;
      case 'monitoring':
        return <RealTimeMonitoring />;
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