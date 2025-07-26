import React from 'react';
import {
  DashboardOutlined,
  TeamOutlined,
  MedicineBoxOutlined,
  SafetyOutlined,
  FileSearchOutlined,
  BookOutlined,
  ExperimentOutlined,
  AreaChartOutlined,
  SettingOutlined,
  AlertOutlined,
} from '@ant-design/icons';

export interface MenuItem {
  key: string;
  label: string;
  icon?: React.ReactNode;
  path?: string;
  children?: MenuItem[];
  roles?: string[];
}

// 메뉴 구조 정의
export const navigationMenus: MenuItem[] = [
  {
    key: 'dashboard',
    label: '대시보드',
    icon: <DashboardOutlined />,
    path: '/',
  },
  {
    key: 'worker-management',
    label: '근로자 관리',
    icon: <TeamOutlined />,
    children: [
      {
        key: 'worker-list',
        label: '근로자 목록',
        path: '/workers',
      },
      {
        key: 'worker-registration',
        label: '근로자 등록',
        path: '/workers/new',
      },
      {
        key: 'worker-health-status',
        label: '건강상태 현황',
        path: '/workers/health-status',
      },
    ],
  },
  {
    key: 'health-management',
    label: '보건관리',
    icon: <MedicineBoxOutlined />,
    children: [
      {
        key: 'health-exam',
        label: '건강진단 관리',
        path: '/health/exams',
      },
      {
        key: 'health-room',
        label: '건강관리실 운영',
        path: '/health/room',
      },
      {
        key: 'health-consultation',
        label: '건강상담 관리',
        path: '/health/consultation',
      },
      {
        key: 'emergency-care',
        label: '응급처치 관리',
        path: '/health/emergency',
      },
    ],
  },
  {
    key: 'safety-health-education',
    label: '안전보건교육',
    icon: <BookOutlined />,
    children: [
      {
        key: 'education-plan',
        label: '교육계획 수립',
        path: '/education/plan',
      },
      {
        key: 'education-execution',
        label: '교육실시 관리',
        path: '/education/execution',
      },
      {
        key: 'education-records',
        label: '교육이수 현황',
        path: '/education/records',
      },
      {
        key: 'education-materials',
        label: '교육자료 관리',
        path: '/education/materials',
      },
    ],
  },
  {
    key: 'work-environment',
    label: '작업환경관리',
    icon: <SafetyOutlined />,
    children: [
      {
        key: 'environment-measurement',
        label: '작업환경측정',
        path: '/environment/measurement',
      },
      {
        key: 'hazard-factors',
        label: '유해인자 관리',
        path: '/environment/hazards',
      },
      {
        key: 'ppe-management',
        label: '보호구 관리',
        path: '/environment/ppe',
      },
      {
        key: 'workplace-inspection',
        label: '작업장 순회점검',
        path: '/environment/inspection',
      },
    ],
  },
  {
    key: 'chemical-management',
    label: '화학물질관리',
    icon: <ExperimentOutlined />,
    children: [
      {
        key: 'msds-management',
        label: 'MSDS 관리',
        path: '/chemical/msds',
      },
      {
        key: 'chemical-inventory',
        label: '화학물질 목록',
        path: '/chemical/inventory',
      },
      {
        key: 'chemical-risk-assessment',
        label: '위험성평가',
        path: '/chemical/risk-assessment',
      },
      {
        key: 'chemical-handling',
        label: '취급자 교육관리',
        path: '/chemical/training',
      },
    ],
  },
  {
    key: 'accident-management',
    label: '사고관리',
    icon: <AlertOutlined />,
    children: [
      {
        key: 'accident-report',
        label: '사고보고',
        path: '/accident/report',
      },
      {
        key: 'accident-investigation',
        label: '사고조사',
        path: '/accident/investigation',
      },
      {
        key: 'accident-statistics',
        label: '사고통계',
        path: '/accident/statistics',
      },
      {
        key: 'near-miss',
        label: '아차사고 관리',
        path: '/accident/near-miss',
      },
    ],
  },
  {
    key: 'compliance',
    label: '법규준수',
    icon: <FileSearchOutlined />,
    children: [
      {
        key: 'legal-requirements',
        label: '법적 요구사항',
        path: '/compliance/requirements',
      },
      {
        key: 'compliance-checklist',
        label: '준수사항 점검',
        path: '/compliance/checklist',
      },
      {
        key: 'audit-management',
        label: '감사관리',
        path: '/compliance/audit',
      },
      {
        key: 'improvement-actions',
        label: '개선조치 관리',
        path: '/compliance/improvements',
      },
    ],
  },
  {
    key: 'reports',
    label: '보고서/통계',
    icon: <AreaChartOutlined />,
    children: [
      {
        key: 'monthly-report',
        label: '월간 보고서',
        path: '/reports/monthly',
      },
      {
        key: 'annual-report',
        label: '연간 보고서',
        path: '/reports/annual',
      },
      {
        key: 'custom-report',
        label: '맞춤 보고서',
        path: '/reports/custom',
      },
      {
        key: 'statistics-dashboard',
        label: '통계 대시보드',
        path: '/reports/statistics',
      },
    ],
  },
  {
    key: 'system',
    label: '시스템 관리',
    icon: <SettingOutlined />,
    roles: ['admin'], // 관리자만 접근 가능
    children: [
      {
        key: 'user-management',
        label: '사용자 관리',
        path: '/system/users',
      },
      {
        key: 'role-management',
        label: '권한 관리',
        path: '/system/roles',
      },
      {
        key: 'company-info',
        label: '회사정보 관리',
        path: '/system/company',
      },
      {
        key: 'system-log',
        label: '시스템 로그',
        path: '/system/logs',
      },
    ],
  },
];

// 역할별 대시보드 정의
export const dashboardsByRole = {
  admin: {
    title: '관리자 대시보드',
    widgets: [
      'systemOverview',
      'userActivity',
      'complianceStatus',
      'alertsAndNotifications',
    ],
  },
  healthManager: {
    title: '보건관리자 대시보드',
    widgets: [
      'healthExamStatus',
      'consultationSchedule',
      'emergencyStats',
      'educationProgress',
    ],
  },
  safetyManager: {
    title: '안전관리자 대시보드',
    widgets: [
      'accidentTrends',
      'workEnvironmentStatus',
      'chemicalInventory',
      'inspectionSchedule',
    ],
  },
  worker: {
    title: '근로자 대시보드',
    widgets: [
      'myHealthStatus',
      'myEducationRecords',
      'upcomingExams',
      'safetyNotices',
    ],
  },
};

// 빠른 작업 메뉴
export const quickActions = [
  {
    key: 'new-worker',
    label: '근로자 등록',
    icon: <TeamOutlined />,
    path: '/workers/new',
    color: '#1677FF',
  },
  {
    key: 'new-exam',
    label: '건강진단 등록',
    icon: <MedicineBoxOutlined />,
    path: '/health/exams/new',
    color: '#52C41A',
  },
  {
    key: 'new-accident',
    label: '사고 보고',
    icon: <AlertOutlined />,
    path: '/accident/report/new',
    color: '#F5222D',
  },
  {
    key: 'new-education',
    label: '교육 등록',
    icon: <BookOutlined />,
    path: '/education/execution/new',
    color: '#FAAD14',
  },
];

// 브레드크럼 경로 생성 함수
export const getBreadcrumbPath = (pathname: string): MenuItem[] => {
  const paths = pathname.split('/').filter(Boolean);
  const breadcrumbs: MenuItem[] = [];
  
  let currentMenus = navigationMenus;
  let currentPath = '';
  
  for (const path of paths) {
    currentPath += `/${path}`;
    const menu = currentMenus.find(m => 
      m.path === currentPath || 
      m.children?.some((c: MenuItem) => c.path === currentPath)
    );
    
    if (menu) {
      breadcrumbs.push(menu);
      if (menu.children) {
        currentMenus = menu.children;
      }
    }
  }
  
  return breadcrumbs;
};