// API 엔드포인트
export const API_ENDPOINTS = {
  // 작업자 관리
  WORKERS: '/api/v1/workers',
  WORKER_DETAIL: (id: number) => `/api/v1/workers/${id}`,
  
  // 건강검진 관리
  HEALTH_EXAMS: '/api/v1/health-exams',
  HEALTH_EXAM_DETAIL: (id: number) => `/api/v1/health-exams/${id}`,
  HEALTH_EXAM_PLANS: '/api/v1/health-exam-management/plans',
  HEALTH_EXAM_SCHEDULES: '/api/v1/health-exam-management/schedules',
  HEALTH_EXAM_STATS: '/api/v1/health-exam-management/stats',
  
  // 작업 환경 측정
  WORK_ENVIRONMENTS: '/api/v1/work-environments',
  WORK_ENVIRONMENT_DETAIL: (id: number) => `/api/v1/work-environments/${id}`,
  
  // 교육 관리
  EDUCATIONS: '/api/v1/educations',
  EDUCATION_DETAIL: (id: number) => `/api/v1/educations/${id}`,
  
  // 화학물질 관리
  CHEMICAL_SUBSTANCES: '/api/v1/chemical-substances',
  CHEMICAL_SUBSTANCE_DETAIL: (id: number) => `/api/v1/chemical-substances/${id}`,
  
  // 사고 관리
  ACCIDENTS: '/api/v1/accidents',
  ACCIDENT_DETAIL: (id: number) => `/api/v1/accidents/${id}`,
  
  // 문서 관리
  DOCUMENTS: '/api/v1/documents',
  INTEGRATED_DOCUMENTS: '/api/v1/integrated-documents',
  
  // 컴플라이언스
  COMPLIANCE: '/api/v1/compliance',
  
  // 대시보드
  DASHBOARD: '/api/v1/dashboard',
} as const;

// 상태 코드
export const STATUS_CODES = {
  // 건강검진 계획 상태
  EXAM_PLAN: {
    DRAFT: 'draft',
    PENDING_APPROVAL: 'pending_approval',
    APPROVED: 'approved',
    IN_PROGRESS: 'in_progress',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
  },
  
  // 건강검진 상태
  EXAM_STATUS: {
    SCHEDULED: 'scheduled',
    COMPLETED: 'completed',
    OVERDUE: 'overdue',
    CANCELLED: 'cancelled',
  },
  
  // 사고 상태
  ACCIDENT: {
    REPORTED: 'reported',
    INVESTIGATING: 'investigating',
    RESOLVED: 'resolved',
    CLOSED: 'closed',
  },
  
  // 교육 상태
  EDUCATION: {
    PLANNED: 'planned',
    IN_PROGRESS: 'in_progress',
    COMPLETED: 'completed',
    CANCELLED: 'cancelled',
  },
} as const;

// 검진 종류
export const EXAM_TYPES = {
  GENERAL: 'general',
  SPECIAL: 'special',
  PLACEMENT: 'placement',
  RETURN_TO_WORK: 'return_to_work',
} as const;

// 사고 유형
export const ACCIDENT_TYPES = {
  INJURY: 'injury',
  NEAR_MISS: 'near_miss',
  PROPERTY_DAMAGE: 'property_damage',
  ENVIRONMENTAL: 'environmental',
} as const;

// 교육 카테고리
export const EDUCATION_CATEGORIES = {
  SAFETY_BASIC: 'safety_basic',
  JOB_SPECIFIC: 'job_specific',
  HEALTH_MANAGEMENT: 'health_management',
  EMERGENCY_RESPONSE: 'emergency_response',
  SPECIAL_WORK: 'special_work',
} as const;

// 문서 카테고리
export const DOCUMENT_CATEGORIES = {
  MANUAL: 'manual',
  LEGAL_FORM: 'legal_form',
  REGULATION: 'regulation',
  REPORT: 'report',
  TRAINING: 'training',
  TEMPLATE: 'template',
  ETC: 'etc',
} as const;

// 역할
export const USER_ROLES = {
  ADMIN: 'admin',
  MANAGER: 'manager',
  EMPLOYEE: 'employee',
  HEALTH_PROFESSIONAL: 'health_professional',
} as const;

// 페이지 경로
export const ROUTES = {
  // 메인
  HOME: '/',
  DASHBOARD: '/dashboard',
  
  // 작업자 관리
  WORKERS: '/workers',
  WORKER_DETAIL: (id: number) => `/workers/${id}`,
  WORKER_CREATE: '/workers/new',
  WORKER_EDIT: (id: number) => `/workers/${id}/edit`,
  
  // 건강검진 관리
  HEALTH_EXAMS: '/health-exams',
  HEALTH_EXAM_DETAIL: (id: number) => `/health-exams/${id}`,
  HEALTH_EXAM_CREATE: '/health-exams/new',
  HEALTH_EXAM_PLANS: '/health-exams/plans',
  HEALTH_EXAM_SCHEDULES: '/health-exams/schedules',
  
  // 사고 관리
  ACCIDENTS: '/accidents',
  ACCIDENT_DETAIL: (id: number) => `/accidents/${id}`,
  ACCIDENT_CREATE: '/accidents/new',
  ACCIDENT_INVESTIGATION: (id: number) => `/accidents/${id}/investigation`,
  
  // 규정 준수
  COMPLIANCE: '/compliance',
  COMPLIANCE_AUDITS: '/compliance/audits',
  COMPLIANCE_REPORTS: '/compliance/reports',
  
  // 설정
  SETTINGS: '/settings',
  SETTINGS_PROFILE: '/settings/profile',
  SETTINGS_SYSTEM: '/settings/system',
} as const;

// 날짜 형식
export const DATE_FORMATS = {
  DATE: 'YYYY-MM-DD',
  DATETIME: 'YYYY-MM-DD HH:mm:ss',
  TIME: 'HH:mm',
  MONTH: 'YYYY-MM',
  YEAR: 'YYYY',
} as const;

// 페이지네이션
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: [10, 20, 50, 100],
} as const;

// 파일 업로드
export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ACCEPT_TYPES: {
    IMAGE: '.jpg,.jpeg,.png,.gif',
    DOCUMENT: '.pdf,.doc,.docx,.xls,.xlsx',
    ALL: '*',
  },
} as const;