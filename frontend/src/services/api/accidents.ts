import { api, PaginatedResponse } from './baseApi';
import { API_ENDPOINTS, ACCIDENT_TYPES, STATUS_CODES } from '@/config/constants';

// 사고 타입 정의
export interface Accident {
  id: number;
  accident_date: string;
  accident_time: string;
  accident_type: keyof typeof ACCIDENT_TYPES;
  location: string;
  description: string;
  severity: 'minor' | 'moderate' | 'major' | 'fatal';
  injured_worker_id?: number;
  injured_worker_name?: string;
  department?: string;
  witness_names?: string;
  immediate_action?: string;
  status: keyof typeof STATUS_CODES.ACCIDENT;
  investigation_date?: string;
  investigator?: string;
  root_cause?: string;
  corrective_actions?: string;
  preventive_measures?: string;
  return_to_work_date?: string;
  lost_work_days?: number;
  medical_costs?: number;
  attachments?: AccidentAttachment[];
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface AccidentAttachment {
  id: number;
  filename: string;
  file_url: string;
  file_size: number;
  uploaded_at: string;
}

export interface AccidentCreate {
  accident_date: string;
  accident_time: string;
  accident_type: keyof typeof ACCIDENT_TYPES;
  location: string;
  description: string;
  severity: 'minor' | 'moderate' | 'major' | 'fatal';
  injured_worker_id?: number;
  department?: string;
  witness_names?: string;
  immediate_action?: string;
}

export interface AccidentInvestigation {
  investigation_date: string;
  investigator: string;
  root_cause: string;
  corrective_actions: string;
  preventive_measures: string;
  return_to_work_date?: string;
  lost_work_days?: number;
  medical_costs?: number;
}

export interface AccidentFilter {
  accident_type?: keyof typeof ACCIDENT_TYPES;
  severity?: string;
  status?: keyof typeof STATUS_CODES.ACCIDENT;
  department?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  pageSize?: number;
}

export interface AccidentStats {
  total_accidents: number;
  by_type: {
    type: string;
    count: number;
  }[];
  by_severity: {
    severity: string;
    count: number;
  }[];
  by_department: {
    department: string;
    count: number;
  }[];
  by_month: {
    month: string;
    count: number;
  }[];
  ltifr: number; // Lost Time Injury Frequency Rate
  trir: number; // Total Recordable Injury Rate
  total_lost_days: number;
  total_medical_costs: number;
}

// 사고 API 서비스
export const accidentsApi = {
  // 사고 목록 조회
  getList: async (filter?: AccidentFilter) => {
    return api.get<PaginatedResponse<Accident>>(API_ENDPOINTS.ACCIDENTS, {
      params: filter,
    });
  },

  // 사고 상세 조회
  getById: async (id: number) => {
    return api.get<Accident>(API_ENDPOINTS.ACCIDENT_DETAIL(id));
  },

  // 사고 보고
  create: async (data: AccidentCreate) => {
    return api.post<Accident>(API_ENDPOINTS.ACCIDENTS, data);
  },

  // 사고 정보 수정
  update: async (id: number, data: Partial<AccidentCreate>) => {
    return api.put<Accident>(API_ENDPOINTS.ACCIDENT_DETAIL(id), data);
  },

  // 사고 삭제
  delete: async (id: number) => {
    return api.delete(API_ENDPOINTS.ACCIDENT_DETAIL(id));
  },

  // 사고 조사 결과 입력
  addInvestigation: async (id: number, data: AccidentInvestigation) => {
    return api.post<Accident>(`${API_ENDPOINTS.ACCIDENT_DETAIL(id)}/investigation`, data);
  },

  // 사고 조사 결과 수정
  updateInvestigation: async (id: number, data: Partial<AccidentInvestigation>) => {
    return api.put<Accident>(`${API_ENDPOINTS.ACCIDENT_DETAIL(id)}/investigation`, data);
  },

  // 상태 변경
  updateStatus: async (id: number, status: keyof typeof STATUS_CODES.ACCIDENT) => {
    return api.patch<Accident>(`${API_ENDPOINTS.ACCIDENT_DETAIL(id)}/status`, { status });
  },

  // 파일 첨부
  uploadAttachment: async (accidentId: number, file: File) => {
    return api.upload<AccidentAttachment>(
      `${API_ENDPOINTS.ACCIDENT_DETAIL(accidentId)}/attachments`,
      file
    );
  },

  // 파일 삭제
  deleteAttachment: async (accidentId: number, attachmentId: number) => {
    return api.delete(`${API_ENDPOINTS.ACCIDENT_DETAIL(accidentId)}/attachments/${attachmentId}`);
  },

  // 통계 조회
  getStats: async (filter?: {
    start_date?: string;
    end_date?: string;
    department?: string;
  }) => {
    return api.get<AccidentStats>(`${API_ENDPOINTS.ACCIDENTS}/stats`, {
      params: filter,
    });
  },

  // 사고 보고서 생성
  generateReport: async (id: number) => {
    return api.download(
      `${API_ENDPOINTS.ACCIDENT_DETAIL(id)}/generate-report`,
      `accident-report-${id}.pdf`
    );
  },

  // 월간 사고 보고서
  generateMonthlyReport: async (year: number, month: number) => {
    return api.download(
      `${API_ENDPOINTS.ACCIDENTS}/monthly-report`,
      `accident-report-${year}-${month}.pdf`
    );
  },

  // 근본 원인 분석 템플릿
  getRootCauseTemplate: async () => {
    return api.get<{
      categories: string[];
      common_causes: { category: string; causes: string[] }[];
    }>(`${API_ENDPOINTS.ACCIDENTS}/root-cause-template`);
  },

  // 시정 조치 템플릿
  getCorrectiveActionTemplate: async () => {
    return api.get<{
      immediate_actions: string[];
      long_term_actions: string[];
      preventive_measures: string[];
    }>(`${API_ENDPOINTS.ACCIDENTS}/corrective-action-template`);
  },
};