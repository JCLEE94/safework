import { API_ENDPOINTS } from '@/config/constants';
import api from './baseApi';

// 컴플라이언스 대시보드 데이터
export interface ComplianceDashboard {
  overall_compliance_rate: number;
  health_exam_compliance: number;
  education_compliance: number;
  work_environment_compliance: number;
  report_compliance: number;
  compliance_message: string;
  health_exam_stats: {
    completed: number;
    required: number;
  };
  education_stats: {
    completed: number;
    required: number;
  };
  work_environment_stats: {
    measured: number;
    required: number;
  };
  report_stats: {
    submitted: number;
    required: number;
  };
}

// 미준수 항목
export interface ComplianceViolation {
  id: number;
  title: string;
  requirement: string;
  category: string;
  due_date: string;
  severity: 'high' | 'medium' | 'low';
  status: string;
}

// 만료 예정 항목
export interface UpcomingExpiry {
  id: number;
  title: string;
  description: string;
  category: string;
  expiry_date: string;
  days_remaining: number;
  responsible_department: string;
}

export const complianceApi = {
  // 대시보드 데이터 조회
  getDashboard: async (period: 'month' | 'quarter' | 'year' = 'month') => {
    const response = await api.get<ComplianceDashboard>(
      `${API_ENDPOINTS.COMPLIANCE}/dashboard`,
      { params: { period } }
    );
    return response;
  },

  // 미준수 항목 조회
  getViolations: async () => {
    const response = await api.get<ComplianceViolation[]>(
      `${API_ENDPOINTS.COMPLIANCE}/violations`
    );
    return response;
  },

  // 다가오는 만료 항목 조회
  getUpcomingExpiries: async (days: number = 30) => {
    const response = await api.get<UpcomingExpiry[]>(
      `${API_ENDPOINTS.COMPLIANCE}/expiries`,
      { params: { days } }
    );
    return response;
  },

  // 컴플라이언스 보고서 생성
  generateReport: async (year: number, month: number) => {
    const response = await api.post(
      `${API_ENDPOINTS.COMPLIANCE}/generate-report`,
      { year, month },
      { responseType: 'blob' }
    );
    return response;
  },

  // 컴플라이언스 체크리스트 조회
  getChecklist: async (category?: string) => {
    const response = await api.get(
      `${API_ENDPOINTS.COMPLIANCE}/checklist`,
      { params: { category } }
    );
    return response;
  },

  // 컴플라이언스 항목 업데이트
  updateComplianceItem: async (id: number, data: any) => {
    const response = await api.put(
      `${API_ENDPOINTS.COMPLIANCE}/${id}`,
      data
    );
    return response;
  },
};