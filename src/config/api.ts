/**
 * API 설정 파일
 * API configuration file
 */

// API 기본 URL - 환경변수에서 가져오거나 현재 호스트 사용
export const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;

// API 엔드포인트 정의
export const API_ENDPOINTS = {
  // 근로자 관리
  workers: '/workers',
  
  // 건강진단
  healthExams: '/health-exams',
  
  // 작업환경측정
  workEnvironments: '/work-environments',
  
  // 보건교육
  education: '/educations',
  
  // 화학물질관리
  chemicals: '/chemical-substances',
  
  // 산업재해
  accidents: '/accidents',
  
  // 문서관리
  documents: {
    forms: '/documents/pdf-forms',
    fillPdf: '/documents/fill-pdf',
    templates: '/documents/templates',
  },
  
  // PDF 자동 매핑
  pdfAuto: {
    detectFields: '/pdf-auto/detect-fields',
    autoFill: '/pdf-auto/auto-fill',
    suggestMapping: '/pdf-auto/suggest-mapping',
  },
  
  // PDF 편집기
  pdfEditor: {
    forms: '/pdf-editor/forms',
    upload: '/pdf-editor/upload-and-edit',
    edit: '/pdf-editor/forms/:formId/edit',
  },
  
  // 모니터링
  monitoring: {
    dashboard: '/monitoring/dashboard',
    realtime: '/monitoring/ws',
    metrics: '/monitoring/metrics',
  },
  
  // 보고서
  reports: {
    generate: '/reports/generate',
    templates: '/reports/templates',
    history: '/reports/history',
  },
  
  // 인증
  auth: {
    login: '/auth/login',
    logout: '/auth/logout',
    refresh: '/auth/refresh',
    profile: '/auth/profile',
  },
  
  // 파이프라인
  pipeline: {
    status: '/pipeline/status',
    logs: '/pipeline/logs',
  },
} as const;

// API 버전
export const API_VERSION = 'v1';

// API 전체 경로 생성 헬퍼
export function getApiUrl(endpoint: string): string {
  return `${API_BASE_URL}/api/${API_VERSION}${endpoint}`;
}

// WebSocket URL 생성 헬퍼
export function getWebSocketUrl(endpoint: string): string {
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = API_BASE_URL.replace(/^https?:\/\//, '');
  return `${wsProtocol}//${host}/api/${API_VERSION}${endpoint}`;
}

// 파일 다운로드 URL 생성 헬퍼
export function getDownloadUrl(endpoint: string, params?: Record<string, string>): string {
  const url = getApiUrl(endpoint);
  if (params) {
    const searchParams = new URLSearchParams(params);
    return `${url}?${searchParams.toString()}`;
  }
  return url;
}

// API 요청 기본 헤더
export const DEFAULT_HEADERS = {
  'Content-Type': 'application/json',
} as const;

// 파일 업로드 헤더 (Content-Type 제거)
export const FILE_UPLOAD_HEADERS = {} as const;

// API 타임아웃 설정 (밀리초)
export const API_TIMEOUT = 30000; // 30초

// 재시도 설정
export const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // 1초
  retryableStatuses: [408, 429, 500, 502, 503, 504],
} as const;