import { api, PaginatedResponse } from './baseApi';
import { API_ENDPOINTS, STATUS_CODES } from '@/config/constants';

// 교육 타입 정의
export interface Education {
  id: number;
  title: string;
  category: 'safety' | 'health' | 'emergency' | 'special' | 'regular';
  description?: string;
  instructor: string;
  location: string;
  education_date: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  max_participants: number;
  current_participants: number;
  status: keyof typeof STATUS_CODES.EDUCATION;
  is_mandatory: boolean;
  target_departments?: string[];
  target_positions?: string[];
  prerequisites?: string;
  materials_url?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
}

export interface EducationParticipant {
  id: number;
  education_id: number;
  worker_id: number;
  worker_name: string;
  department: string;
  attendance_status: 'registered' | 'attended' | 'absent' | 'late';
  completion_status: 'completed' | 'incomplete' | 'failed';
  test_score?: number;
  certificate_issued: boolean;
  certificate_issue_date?: string;
  registered_at: string;
  attended_at?: string;
}

export interface EducationCreate {
  title: string;
  category: 'safety' | 'health' | 'emergency' | 'special' | 'regular';
  description?: string;
  instructor: string;
  location: string;
  education_date: string;
  start_time: string;
  end_time: string;
  duration_hours: number;
  max_participants: number;
  is_mandatory: boolean;
  target_departments?: string[];
  target_positions?: string[];
  prerequisites?: string;
  materials_url?: string;
}

export interface EducationFilter {
  category?: string;
  status?: keyof typeof STATUS_CODES.EDUCATION;
  is_mandatory?: boolean;
  instructor?: string;
  start_date?: string;
  end_date?: string;
  page?: number;
  pageSize?: number;
}

export interface EducationStats {
  total_educations: number;
  completed_educations: number;
  total_participants: number;
  average_attendance_rate: number;
  average_completion_rate: number;
  by_category: {
    category: string;
    count: number;
    participants: number;
  }[];
  by_department: {
    department: string;
    total_required: number;
    completed: number;
    completion_rate: number;
  }[];
  upcoming_educations: {
    id: number;
    title: string;
    date: string;
    remaining_seats: number;
  }[];
}

export interface WorkerEducationRecord {
  worker_id: number;
  worker_name: string;
  department: string;
  total_required: number;
  total_completed: number;
  completion_rate: number;
  educations: {
    id: number;
    title: string;
    date: string;
    status: string;
    score?: number;
  }[];
  next_required: {
    title: string;
    due_date: string;
  }[];
}

// 교육 API 서비스
export const educationsApi = {
  // 교육 목록 조회
  getList: async (filter?: EducationFilter) => {
    return api.get<PaginatedResponse<Education>>(API_ENDPOINTS.EDUCATIONS, {
      params: filter,
    });
  },

  // 교육 상세 조회
  getById: async (id: number) => {
    return api.get<Education>(API_ENDPOINTS.EDUCATION_DETAIL(id));
  },

  // 교육 생성
  create: async (data: EducationCreate) => {
    return api.post<Education>(API_ENDPOINTS.EDUCATIONS, data);
  },

  // 교육 수정
  update: async (id: number, data: Partial<EducationCreate>) => {
    return api.put<Education>(API_ENDPOINTS.EDUCATION_DETAIL(id), data);
  },

  // 교육 삭제
  delete: async (id: number) => {
    return api.delete(API_ENDPOINTS.EDUCATION_DETAIL(id));
  },

  // 교육 상태 변경
  updateStatus: async (id: number, status: keyof typeof STATUS_CODES.EDUCATION) => {
    return api.patch<Education>(`${API_ENDPOINTS.EDUCATION_DETAIL(id)}/status`, { status });
  },

  // 참가자 관리
  participants: {
    // 참가자 목록 조회
    getList: async (educationId: number) => {
      return api.get<EducationParticipant[]>(
        `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/participants`
      );
    },

    // 참가자 등록
    register: async (educationId: number, workerIds: number[]) => {
      return api.post<{ registered: number; failed: number; errors: string[] }>(
        `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/participants`,
        { worker_ids: workerIds }
      );
    },

    // 참가자 취소
    cancel: async (educationId: number, participantId: number) => {
      return api.delete(
        `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/participants/${participantId}`
      );
    },

    // 출석 체크
    updateAttendance: async (
      educationId: number,
      updates: { participant_id: number; status: string }[]
    ) => {
      return api.post(
        `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/attendance`,
        { updates }
      );
    },

    // 시험 점수 입력
    updateScores: async (
      educationId: number,
      scores: { participant_id: number; score: number }[]
    ) => {
      return api.post(
        `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/scores`,
        { scores }
      );
    },

    // 수료증 발급
    issueCertificate: async (educationId: number, participantId: number) => {
      return api.post(
        `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/participants/${participantId}/certificate`
      );
    },
  },

  // 통계 조회
  getStats: async (filter?: {
    start_date?: string;
    end_date?: string;
    department?: string;
  }) => {
    return api.get<EducationStats>(`${API_ENDPOINTS.EDUCATIONS}/stats`, {
      params: filter,
    });
  },

  // 작업자별 교육 이력
  getWorkerRecord: async (workerId: number) => {
    return api.get<WorkerEducationRecord>(`${API_ENDPOINTS.EDUCATIONS}/worker/${workerId}`);
  },

  // 교육 자료 업로드
  uploadMaterials: async (educationId: number, file: File) => {
    return api.upload<{ url: string }>(
      `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/materials`,
      file
    );
  },

  // 출석부 다운로드
  downloadAttendanceSheet: async (educationId: number) => {
    return api.download(
      `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/attendance-sheet`,
      `attendance-${educationId}.xlsx`
    );
  },

  // 수료증 다운로드
  downloadCertificate: async (educationId: number, participantId: number) => {
    return api.download(
      `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/participants/${participantId}/certificate/download`,
      `certificate-${educationId}-${participantId}.pdf`
    );
  },

  // 교육 보고서 생성
  generateReport: async (educationId: number) => {
    return api.download(
      `${API_ENDPOINTS.EDUCATION_DETAIL(educationId)}/report`,
      `education-report-${educationId}.pdf`
    );
  },

  // 월간 교육 보고서
  generateMonthlyReport: async (year: number, month: number) => {
    return api.download(
      `${API_ENDPOINTS.EDUCATIONS}/monthly-report`,
      `education-report-${year}-${month}.pdf`
    );
  },

  // 교육 대상자 자동 선정
  getTargetWorkers: async (criteria: {
    category: string;
    departments?: string[];
    positions?: string[];
    last_education_before?: string;
  }) => {
    return api.post<{ workers: { id: number; name: string; department: string }[] }>(
      `${API_ENDPOINTS.EDUCATIONS}/target-workers`,
      criteria
    );
  },
};