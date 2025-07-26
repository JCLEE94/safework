import { api, PaginatedResponse } from './baseApi';
import { API_ENDPOINTS } from '@/config/constants';

// 작업자 타입 정의
export interface Worker {
  id: number;
  name: string;
  employee_id: string;
  department: string;
  position: string;
  email?: string;
  phone: string;
  gender?: 'male' | 'female';
  birth_date?: string;
  employment_date: string;
  employment_type: 'permanent' | 'contract' | 'temporary';
  work_type: string;
  health_status?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface WorkerCreate {
  name: string;
  employee_id: string;
  department: string;
  position: string;
  email?: string;
  phone: string;
  gender?: 'male' | 'female';
  birth_date?: string;
  employment_date: string;
  employment_type: 'permanent' | 'contract' | 'temporary';
  work_type: string;
  health_status?: string;
}

export interface WorkerUpdate extends Partial<WorkerCreate> {
  is_active?: boolean;
}

export interface WorkerFilter {
  name?: string;
  department?: string;
  employment_type?: string;
  is_active?: boolean;
  page?: number;
  pageSize?: number;
}

// 작업자 API 서비스
export const workersApi = {
  // 작업자 목록 조회
  getList: async (filter?: WorkerFilter) => {
    return api.get<PaginatedResponse<Worker>>(API_ENDPOINTS.WORKERS, {
      params: filter,
    });
  },

  // 작업자 상세 조회
  getById: async (id: number) => {
    return api.get<Worker>(API_ENDPOINTS.WORKER_DETAIL(id));
  },

  // 작업자 생성
  create: async (data: WorkerCreate) => {
    return api.post<Worker>(API_ENDPOINTS.WORKERS, data);
  },

  // 작업자 수정
  update: async (id: number, data: WorkerUpdate) => {
    return api.put<Worker>(API_ENDPOINTS.WORKER_DETAIL(id), data);
  },

  // 작업자 삭제
  delete: async (id: number) => {
    return api.delete(API_ENDPOINTS.WORKER_DETAIL(id));
  },

  // 작업자 일괄 가져오기 (엑셀 업로드)
  importFromExcel: async (file: File) => {
    return api.upload<{ imported: number; failed: number; errors: string[] }>(
      `${API_ENDPOINTS.WORKERS}/import`,
      file
    );
  },

  // 작업자 목록 내보내기 (엑셀 다운로드)
  exportToExcel: async () => {
    return api.download(`${API_ENDPOINTS.WORKERS}/export`, 'workers.xlsx');
  },

  // 중복 확인
  checkDuplicate: async (field: 'employee_id' | 'email', value: string) => {
    return api.get<{ exists: boolean }>(`${API_ENDPOINTS.WORKERS}/check-duplicate`, {
      params: { field, value },
    });
  },

  // 부서 목록 조회
  getDepartments: async () => {
    return api.get<string[]>(`${API_ENDPOINTS.WORKERS}/departments`);
  },

  // 직위 목록 조회
  getPositions: async () => {
    return api.get<string[]>(`${API_ENDPOINTS.WORKERS}/positions`);
  },

  // 작업 유형 목록 조회
  getWorkTypes: async () => {
    return api.get<string[]>(`${API_ENDPOINTS.WORKERS}/work-types`);
  },
};