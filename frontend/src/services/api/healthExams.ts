import { api, PaginatedResponse } from './baseApi';
import { API_ENDPOINTS, EXAM_TYPES, STATUS_CODES } from '@/config/constants';

// 건강검진 타입 정의
export interface HealthExam {
  id: number;
  worker_id: number;
  worker_name?: string;
  exam_date: string;
  exam_type: keyof typeof EXAM_TYPES;
  exam_location: string;
  exam_agency: string;
  result_status: 'normal' | 'observation' | 'disease_suspect' | 'disease';
  overall_opinion?: string;
  next_exam_date?: string;
  created_at: string;
  updated_at: string;
}

export interface HealthExamCreate {
  worker_id: number;
  exam_date: string;
  exam_type: keyof typeof EXAM_TYPES;
  exam_location: string;
  exam_agency: string;
  result_status: 'normal' | 'observation' | 'disease_suspect' | 'disease';
  overall_opinion?: string;
  next_exam_date?: string;
}

export interface HealthExamPlan {
  id: number;
  year: number;
  category: keyof typeof EXAM_TYPES;
  plan_status: keyof typeof STATUS_CODES.EXAM_PLAN;
  created_at: string;
  updated_at: string;
  approved_by?: string;
  approved_at?: string;
  total_workers?: number;
  completed_workers?: number;
}

export interface HealthExamSchedule {
  id: number;
  plan_id: number;
  exam_date: string;
  location: string;
  provider: string;
  capacity: number;
  reserved_count: number;
  created_at: string;
  updated_at: string;
}

export interface HealthExamStats {
  total_workers: number;
  completed_exams: number;
  scheduled_exams: number;
  overdue_exams: number;
  completion_rate: number;
  by_department: {
    department: string;
    total: number;
    completed: number;
    rate: number;
  }[];
  by_exam_type: {
    exam_type: string;
    count: number;
  }[];
}

export interface HealthExamFilter {
  worker_id?: number;
  exam_type?: keyof typeof EXAM_TYPES;
  result_status?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  pageSize?: number;
}

// 건강검진 API 서비스
export const healthExamsApi = {
  // 건강검진 목록 조회
  getList: async (filter?: HealthExamFilter) => {
    return api.get<PaginatedResponse<HealthExam>>(API_ENDPOINTS.HEALTH_EXAMS, {
      params: filter,
    });
  },

  // 건강검진 상세 조회
  getById: async (id: number) => {
    return api.get<HealthExam>(API_ENDPOINTS.HEALTH_EXAM_DETAIL(id));
  },

  // 건강검진 기록 생성
  create: async (data: HealthExamCreate) => {
    return api.post<HealthExam>(API_ENDPOINTS.HEALTH_EXAMS, data);
  },

  // 건강검진 기록 수정
  update: async (id: number, data: Partial<HealthExamCreate>) => {
    return api.put<HealthExam>(API_ENDPOINTS.HEALTH_EXAM_DETAIL(id), data);
  },

  // 건강검진 기록 삭제
  delete: async (id: number) => {
    return api.delete(API_ENDPOINTS.HEALTH_EXAM_DETAIL(id));
  },

  // 검진 계획 관련
  plans: {
    getList: async (year?: number) => {
      return api.get<HealthExamPlan[]>(API_ENDPOINTS.HEALTH_EXAM_PLANS, {
        params: { year },
      });
    },

    getById: async (id: number) => {
      return api.get<HealthExamPlan>(`${API_ENDPOINTS.HEALTH_EXAM_PLANS}/${id}`);
    },

    create: async (data: Omit<HealthExamPlan, 'id' | 'created_at' | 'updated_at'>) => {
      return api.post<HealthExamPlan>(API_ENDPOINTS.HEALTH_EXAM_PLANS, data);
    },

    update: async (id: number, data: Partial<HealthExamPlan>) => {
      return api.put<HealthExamPlan>(`${API_ENDPOINTS.HEALTH_EXAM_PLANS}/${id}`, data);
    },

    approve: async (id: number) => {
      return api.post<HealthExamPlan>(`${API_ENDPOINTS.HEALTH_EXAM_PLANS}/${id}/approve`);
    },

    cancel: async (id: number, reason: string) => {
      return api.post<HealthExamPlan>(`${API_ENDPOINTS.HEALTH_EXAM_PLANS}/${id}/cancel`, { reason });
    },
  },

  // 검진 일정 관련
  schedules: {
    getList: async (planId?: number) => {
      return api.get<HealthExamSchedule[]>(API_ENDPOINTS.HEALTH_EXAM_SCHEDULES, {
        params: { plan_id: planId },
      });
    },

    create: async (data: Omit<HealthExamSchedule, 'id' | 'created_at' | 'updated_at' | 'reserved_count'>) => {
      return api.post<HealthExamSchedule>(API_ENDPOINTS.HEALTH_EXAM_SCHEDULES, data);
    },

    update: async (id: number, data: Partial<HealthExamSchedule>) => {
      return api.put<HealthExamSchedule>(`${API_ENDPOINTS.HEALTH_EXAM_SCHEDULES}/${id}`, data);
    },

    delete: async (id: number) => {
      return api.delete(`${API_ENDPOINTS.HEALTH_EXAM_SCHEDULES}/${id}`);
    },

    // 예약 관리
    makeReservation: async (scheduleId: number, workerIds: number[]) => {
      return api.post(`${API_ENDPOINTS.HEALTH_EXAM_SCHEDULES}/${scheduleId}/reservations`, {
        worker_ids: workerIds,
      });
    },

    cancelReservation: async (scheduleId: number, workerId: number) => {
      return api.delete(`${API_ENDPOINTS.HEALTH_EXAM_SCHEDULES}/${scheduleId}/reservations/${workerId}`);
    },
  },

  // 통계 조회
  getStats: async (year?: number) => {
    return api.get<any>(API_ENDPOINTS.HEALTH_EXAM_STATS, {
      params: { year },
    });
  },

  // 검진 결과 일괄 업로드
  uploadResults: async (file: File, planId: number) => {
    return api.upload<{ imported: number; failed: number; errors: string[] }>(
      `${API_ENDPOINTS.HEALTH_EXAMS}/upload-results`,
      file,
      { plan_id: planId }
    );
  },

  // 검진 대상자 목록 다운로드
  downloadTargets: async (planId: number) => {
    return api.download(
      `${API_ENDPOINTS.HEALTH_EXAM_PLANS}/${planId}/download-targets`,
      `exam-targets-${planId}.xlsx`
    );
  },

  // 검진 결과 보고서 생성
  generateReport: async (planId: number) => {
    return api.download(
      `${API_ENDPOINTS.HEALTH_EXAM_PLANS}/${planId}/generate-report`,
      `exam-report-${planId}.pdf`
    );
  },
};