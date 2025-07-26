import React, { lazy, Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';

// Lazy load pages
const Dashboard = lazy(() => import('@/pages/Dashboard'));
const Workers = lazy(() => import('@/pages/Workers'));
const HealthExams = lazy(() => import('@/pages/HealthExams'));
const Accidents = lazy(() => import('@/pages/Accidents'));
const Educations = lazy(() => import('@/pages/Educations'));
const Documents = lazy(() => import('@/pages/Documents'));
const Compliance = lazy(() => import('@/pages/Compliance'));

// Loading component
const PageLoading = () => (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'center', 
    alignItems: 'center', 
    height: '100vh' 
  }}>
    <Spin size="large" />
  </div>
);

export const AppRoutes: React.FC = () => {
  return (
    <Suspense fallback={<PageLoading />}>
      <Routes>
        {/* 대시보드 */}
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        
        {/* 작업자 관리 */}
        <Route path="/workers" element={<Workers />} />
        
        {/* 건강검진 관리 */}
        <Route path="/health-exams" element={<HealthExams />} />
        
        {/* 사고 관리 */}
        <Route path="/accidents" element={<Accidents />} />
        
        {/* 교육 관리 */}
        <Route path="/educations" element={<Educations />} />
        
        {/* 문서 관리 */}
        <Route path="/documents" element={<Documents />} />
        
        {/* 법규 준수 */}
        <Route path="/compliance" element={<Compliance />} />
        
        {/* 404 */}
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
};