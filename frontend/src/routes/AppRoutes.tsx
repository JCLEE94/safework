import React, { Suspense } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { Dashboard } from '../components/pages/Dashboard/Dashboard';
import { WorkerList } from '../components/pages/Workers/WorkerList';

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
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        
        {/* 근로자 관리 */}
        <Route path="/workers" element={<WorkerList />} />
        <Route path="/workers/new" element={<div>근로자 등록 페이지</div>} />
        <Route path="/workers/health-status" element={<div>건강상태 현황 페이지</div>} />
        
        {/* 보건관리 */}
        <Route path="/health/exams" element={<div>건강진단 관리 페이지</div>} />
        <Route path="/health/room" element={<div>건강관리실 운영 페이지</div>} />
        <Route path="/health/consultation" element={<div>건강상담 관리 페이지</div>} />
        <Route path="/health/emergency" element={<div>응급처치 관리 페이지</div>} />
        
        {/* 안전보건교육 */}
        <Route path="/education/plan" element={<div>교육계획 수립 페이지</div>} />
        <Route path="/education/execution" element={<div>교육실시 관리 페이지</div>} />
        <Route path="/education/records" element={<div>교육이수 현황 페이지</div>} />
        <Route path="/education/materials" element={<div>교육자료 관리 페이지</div>} />
        
        {/* 작업환경관리 */}
        <Route path="/environment/measurement" element={<div>작업환경측정 페이지</div>} />
        <Route path="/environment/hazards" element={<div>유해인자 관리 페이지</div>} />
        <Route path="/environment/ppe" element={<div>보호구 관리 페이지</div>} />
        <Route path="/environment/inspection" element={<div>작업장 순회점검 페이지</div>} />
        
        {/* 화학물질관리 */}
        <Route path="/chemical/msds" element={<div>MSDS 관리 페이지</div>} />
        <Route path="/chemical/inventory" element={<div>화학물질 목록 페이지</div>} />
        <Route path="/chemical/risk-assessment" element={<div>위험성평가 페이지</div>} />
        <Route path="/chemical/training" element={<div>취급자 교육관리 페이지</div>} />
        
        {/* 사고관리 */}
        <Route path="/accident/report" element={<div>사고보고 페이지</div>} />
        <Route path="/accident/investigation" element={<div>사고조사 페이지</div>} />
        <Route path="/accident/statistics" element={<div>사고통계 페이지</div>} />
        <Route path="/accident/near-miss" element={<div>아차사고 관리 페이지</div>} />
        
        {/* 법규준수 */}
        <Route path="/compliance/requirements" element={<div>법적 요구사항 페이지</div>} />
        <Route path="/compliance/checklist" element={<div>준수사항 점검 페이지</div>} />
        <Route path="/compliance/audit" element={<div>감사관리 페이지</div>} />
        <Route path="/compliance/improvements" element={<div>개선조치 관리 페이지</div>} />
        
        {/* 보고서/통계 */}
        <Route path="/reports/monthly" element={<div>월간 보고서 페이지</div>} />
        <Route path="/reports/annual" element={<div>연간 보고서 페이지</div>} />
        <Route path="/reports/custom" element={<div>맞춤 보고서 페이지</div>} />
        <Route path="/reports/statistics" element={<div>통계 대시보드 페이지</div>} />
        
        {/* 시스템 관리 */}
        <Route path="/system/users" element={<div>사용자 관리 페이지</div>} />
        <Route path="/system/roles" element={<div>권한 관리 페이지</div>} />
        <Route path="/system/company" element={<div>회사정보 관리 페이지</div>} />
        <Route path="/system/logs" element={<div>시스템 로그 페이지</div>} />
        
        {/* 404 페이지 */}
        <Route path="*" element={<div>페이지를 찾을 수 없습니다</div>} />
      </Routes>
    </Suspense>
  );
};