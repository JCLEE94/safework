import React, { Suspense, lazy } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Spin } from 'antd';

// Lazy load pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const ExamDashboard = lazy(() => import('@/features/health-monitoring/pages/ExamDashboard'));

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
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/health-exam" element={<ExamDashboard />} />
      </Routes>
    </Suspense>
  );
};