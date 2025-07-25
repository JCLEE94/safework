/**
 * 상수 정의
 * Constants definitions
 */

// API_BASE_URL은 deprecated - config/api.ts의 API_CONFIG 사용 권장
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || window.location.origin;

export const BUILD_TIME = new Date().toLocaleString('ko-KR', {
  timeZone: 'Asia/Seoul',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit'
}).replace(/\. /g, '-').replace(/\.$/, '') + ' KST';

// 페이지네이션 및 표시 제한 설정
export const DASHBOARD_RECENT_ITEMS = 5;
export const MAX_RECENT_ITEMS = 10;

// 메뉴 정의 (통합 및 최적화)
export const MENU_ITEMS = [
  { id: 'dashboard', name: '대시보드', icon: 'LayoutGrid', color: 'text-blue-600' },
  { id: 'workers', name: '근로자관리', icon: 'Users', color: 'text-purple-600' },
  { id: 'health', name: '건강진단', icon: 'Heart', color: 'text-red-600' },
  { id: 'appointments', name: '건강진단예약', icon: 'CalendarCheck', color: 'text-purple-500' },
  { id: 'environment', name: '작업환경측정', icon: 'Activity', color: 'text-green-600' },
  { id: 'education', name: '보건교육', icon: 'BookOpen', color: 'text-indigo-600' },
  { id: 'chemicals', name: '화학물질관리', icon: 'FlaskConical', color: 'text-yellow-600' },
  { id: 'accidents', name: '산업재해', icon: 'AlertTriangle', color: 'text-orange-600' },
  { id: 'unified-documents', name: '법정서식', icon: 'FileText', color: 'text-cyan-600' },
  { id: 'integrated-documents', name: '통합문서관리', icon: 'FolderOpen', color: 'text-teal-600' },
  { id: 'reports', name: '종합보고서', icon: 'BarChart3', color: 'text-indigo-600' },
  { id: 'monitoring', name: '실시간모니터링', icon: 'MonitorDot', color: 'text-pink-600' },
  { id: 'qr-registration', name: 'QR코드', icon: 'QrCode', color: 'text-blue-500' },
  { id: 'common-qr', name: '공통 QR 등록', icon: 'Scan', color: 'text-green-500' },
  { id: 'confined-space', name: '밀폐공간 관리', icon: 'Shield', color: 'text-orange-600' },
  { id: 'cardiovascular', name: '뇌심혈관계 관리', icon: 'Heart', color: 'text-red-500' },
  { id: 'settings', name: '시스템설정', icon: 'Settings', color: 'text-gray-600' },
] as const;

// Enum 값 정의
export const EMPLOYMENT_TYPES = [
  { value: 'regular', label: '정규직' },
  { value: 'contract', label: '계약직' },
  { value: 'temporary', label: '임시직' },
  { value: 'daily', label: '일용직' },
] as const;

export const WORK_TYPES = [
  { value: 'construction', label: '건설' },
  { value: 'electrical', label: '전기' },
  { value: 'plumbing', label: '배관' },
  { value: 'painting', label: '도장' },
  { value: 'welding', label: '용접' },
  { value: 'rebar', label: '철근' },
  { value: 'concrete', label: '콘크리트' },
  { value: 'masonry', label: '조적' },
  { value: 'tiling', label: '타일' },
  { value: 'waterproofing', label: '방수' },
] as const;

export const GENDER_OPTIONS = [
  { value: 'male', label: '남성' },
  { value: 'female', label: '여성' },
] as const;

export const HEALTH_STATUS_OPTIONS = [
  { value: 'normal', label: '정상' },
  { value: 'caution', label: '주의' },
  { value: 'observation', label: '관찰' },
  { value: 'treatment', label: '치료' },
] as const;

export const EXAM_TYPES = [
  { value: 'general', label: '일반건강진단' },
  { value: 'special', label: '특수건강진단' },
  { value: 'pre_placement', label: '배치전건강진단' },
  { value: 'periodic', label: '수시건강진단' },
] as const;

export const MEASUREMENT_TYPES = [
  { value: 'noise', label: '소음' },
  { value: 'dust', label: '분진' },
  { value: 'chemical', label: '화학물질' },
  { value: 'temperature', label: '온도' },
  { value: 'humidity', label: '습도' },
  { value: 'illumination', label: '조도' },
  { value: 'vibration', label: '진동' },
] as const;

export const ACCIDENT_TYPES = [
  { value: 'fall', label: '추락' },
  { value: 'cut', label: '절단/베임' },
  { value: 'burn', label: '화상' },
  { value: 'collision', label: '충돌' },
  { value: 'caught', label: '끼임' },
  { value: 'electric_shock', label: '감전' },
  { value: 'poisoning', label: '중독' },
] as const;

export const ACCIDENT_SEVERITY = [
  { value: 'minor', label: '경미' },
  { value: 'moderate', label: '중등도' },
  { value: 'serious', label: '중대' },
  { value: 'fatal', label: '사망' },
] as const;

export const DANGER_GRADES = [
  { value: 'low', label: '낮음' },
  { value: 'medium', label: '보통' },
  { value: 'high', label: '높음' },
  { value: 'very_high', label: '매우 높음' },
] as const;

export const MSDS_STATUS = [
  { value: 'current', label: '최신' },
  { value: 'expired', label: '만료' },
  { value: 'pending', label: '대기중' },
] as const;

export const EDUCATION_STATUS = [
  { value: 'scheduled', label: '예정' },
  { value: 'in_progress', label: '진행중' },
  { value: 'completed', label: '완료' },
  { value: 'cancelled', label: '취소' },
] as const;

export const MEASUREMENT_STATUS = [
  { value: 'adequate', label: '적정' },
  { value: 'inadequate', label: '부적정' },
  { value: 'warning', label: '경고' },
] as const;

// PDF 양식 타입
export const PDF_FORM_TYPES = [
  { value: 'health_consultation_log', label: '건강관리 상담방문 일지' },
  { value: 'health_findings_ledger', label: '유소견자 관리대장' },
  { value: 'msds_management_ledger', label: 'MSDS 관리대장' },
  { value: 'special_substance_log', label: '특별관리물질 취급일지' },
] as const;

// 상태 색상 매핑
export const STATUS_COLORS = {
  normal: 'bg-green-100 text-green-800',
  caution: 'bg-yellow-100 text-yellow-800',
  observation: 'bg-orange-100 text-orange-800',
  treatment: 'bg-red-100 text-red-800',
  adequate: 'bg-green-100 text-green-800',
  inadequate: 'bg-red-100 text-red-800',
  warning: 'bg-yellow-100 text-yellow-800',
  scheduled: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-yellow-100 text-yellow-800',
  completed: 'bg-green-100 text-green-800',
  cancelled: 'bg-gray-100 text-gray-800',
  current: 'bg-green-100 text-green-800',
  expired: 'bg-red-100 text-red-800',
  pending: 'bg-yellow-100 text-yellow-800',
  minor: 'bg-yellow-100 text-yellow-800',
  moderate: 'bg-orange-100 text-orange-800',
  serious: 'bg-red-100 text-red-800',
  fatal: 'bg-gray-900 text-white',
} as const;