import { API_BASE } from './config';

// Enums
export enum ExamPlanStatus {
  DRAFT = 'draft',
  APPROVED = 'approved',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export enum ExamCategory {
  GENERAL_REGULAR = '일반건강진단_정기',
  GENERAL_TEMPORARY = '일반건강진단_임시',
  SPECIAL_REGULAR = '특수건강진단_정기',
  SPECIAL_TEMPORARY = '특수건강진단_임시',
  PRE_PLACEMENT = '배치전건강진단',
  JOB_CHANGE = '직무전환건강진단',
  NIGHT_WORK = '야간작업건강진단'
}

export enum ResultDeliveryMethod {
  DIRECT = '직접수령',
  POSTAL = '우편발송',
  EMAIL = '이메일',
  MOBILE = '모바일',
  COMPANY_BATCH = '회사일괄'
}

// Types
export interface HealthExamPlan {
  id?: number;
  plan_year: number;
  plan_name: string;
  plan_status?: ExamPlanStatus;
  total_workers: number;
  general_exam_targets: number;
  special_exam_targets: number;
  night_work_targets: number;
  plan_start_date?: string;
  plan_end_date?: string;
  primary_institution?: string;
  secondary_institutions?: string[];
  estimated_budget?: number;
  budget_per_person?: number;
  harmful_factors?: string[];
  notes?: string;
  approved_by?: string;
  approved_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface HealthExamTarget {
  id?: number;
  plan_id: number;
  worker_id: number;
  exam_categories: ExamCategory[];
  general_exam_required: boolean;
  general_exam_date?: string;
  special_exam_required: boolean;
  special_exam_harmful_factors?: string[];
  special_exam_date?: string;
  night_work_exam_required: boolean;
  night_work_months?: number;
  night_work_exam_date?: string;
  exam_cycle_months: number;
  last_exam_date?: string;
  next_exam_due_date?: string;
  reservation_status?: string;
  reserved_date?: string;
  is_completed: boolean;
  completed_date?: string;
  special_notes?: string;
}

export interface HealthExamSchedule {
  id?: number;
  plan_id: number;
  schedule_date: string;
  start_time?: string;
  end_time?: string;
  institution_name: string;
  institution_address?: string;
  institution_contact?: string;
  exam_types?: ExamCategory[];
  total_capacity: number;
  reserved_count: number;
  available_slots: number;
  group_code?: string;
  is_active: boolean;
  is_full: boolean;
  special_requirements?: string;
}

export interface HealthExamReservation {
  id?: number;
  schedule_id: number;
  worker_id: number;
  reservation_number?: string;
  reserved_exam_types?: ExamCategory[];
  reserved_time?: string;
  estimated_duration?: number;
  status: string;
  check_in_time?: string;
  check_out_time?: string;
  fasting_required: boolean;
  special_preparations?: string;
  contact_phone?: string;
  contact_email?: string;
  result_delivery_method?: ResultDeliveryMethod;
  result_delivery_address?: string;
  reminder_sent: boolean;
  reminder_sent_at?: string;
  is_cancelled: boolean;
  cancelled_at?: string;
  cancellation_reason?: string;
}

export interface HealthExamChart {
  id?: number;
  reservation_id?: number;
  worker_id: number;
  exam_date: string;
  chart_number?: string;
  exam_type?: string;
  medical_history?: {
    past_diseases?: string[];
    current_medications?: string[];
    family_history?: string[];
    allergies?: string[];
    surgeries?: string[];
  };
  lifestyle_habits?: {
    smoking?: { status: string; amount?: string; years?: number };
    drinking?: { frequency: string; amount?: string };
    exercise?: { frequency: string; type?: string };
    sleep?: { hours: number; quality: string };
  };
  symptoms?: {
    general?: string[];
    respiratory?: string[];
    cardiovascular?: string[];
    musculoskeletal?: string[];
    neurological?: string[];
  };
  work_environment?: {
    harmful_factors?: string[];
    ppe_usage?: Record<string, string>;
    work_hours?: { day: number; overtime?: number };
    shift_work?: boolean;
  };
  special_exam_questionnaire?: any;
  female_health_info?: any;
  exam_day_condition?: any;
}

// API Functions
export const healthExamManagementApi = {
  // 검진 계획 관리
  plans: {
    create: async (data: Omit<HealthExamPlan, 'id'>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/plans/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('검진 계획 생성 실패');
      return response.json();
    },

    getList: async (params?: { year?: number; status?: ExamPlanStatus }) => {
      const queryParams = new URLSearchParams();
      if (params?.year) queryParams.append('year', params.year.toString());
      if (params?.status) queryParams.append('status', params.status);
      
      const response = await fetch(`${API_BASE}/health-exam-management/plans/?${queryParams}`);
      if (!response.ok) throw new Error('검진 계획 목록 조회 실패');
      return response.json();
    },

    getById: async (planId: number) => {
      const response = await fetch(`${API_BASE}/health-exam-management/plans/${planId}`);
      if (!response.ok) throw new Error('검진 계획 조회 실패');
      return response.json();
    },

    update: async (planId: number, data: Partial<HealthExamPlan>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/plans/${planId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('검진 계획 수정 실패');
      return response.json();
    },

    approve: async (planId: number) => {
      const response = await fetch(`${API_BASE}/health-exam-management/plans/${planId}/approve`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('검진 계획 승인 실패');
      return response.json();
    }
  },

  // 검진 대상자 관리
  targets: {
    generateTargets: async (planId: number) => {
      const response = await fetch(`${API_BASE}/health-exam-management/plans/${planId}/generate-targets`, {
        method: 'POST'
      });
      if (!response.ok) throw new Error('검진 대상자 생성 실패');
      return response.json();
    },

    getTargets: async (planId: number, params?: { 
      exam_type?: string; 
      is_completed?: boolean;
      skip?: number;
      limit?: number;
    }) => {
      const queryParams = new URLSearchParams();
      if (params?.exam_type) queryParams.append('exam_type', params.exam_type);
      if (params?.is_completed !== undefined) {
        queryParams.append('is_completed', params.is_completed.toString());
      }
      if (params?.skip) queryParams.append('skip', params.skip.toString());
      if (params?.limit) queryParams.append('limit', params.limit.toString());
      
      const response = await fetch(
        `${API_BASE}/health-exam-management/plans/${planId}/targets?${queryParams}`
      );
      if (!response.ok) throw new Error('검진 대상자 조회 실패');
      return response.json();
    },

    updateTarget: async (targetId: number, data: Partial<HealthExamTarget>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/targets/${targetId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('검진 대상자 수정 실패');
      return response.json();
    }
  },

  // 검진 일정 관리
  schedules: {
    create: async (data: Omit<HealthExamSchedule, 'id'>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/schedules/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('검진 일정 생성 실패');
      return response.json();
    },

    getList: async (params?: {
      plan_id?: number;
      start_date?: string;
      end_date?: string;
      institution?: string;
    }) => {
      const queryParams = new URLSearchParams();
      if (params?.plan_id) queryParams.append('plan_id', params.plan_id.toString());
      if (params?.start_date) queryParams.append('start_date', params.start_date);
      if (params?.end_date) queryParams.append('end_date', params.end_date);
      if (params?.institution) queryParams.append('institution', params.institution);
      
      const response = await fetch(`${API_BASE}/health-exam-management/schedules/?${queryParams}`);
      if (!response.ok) throw new Error('검진 일정 조회 실패');
      return response.json();
    },

    update: async (scheduleId: number, data: Partial<HealthExamSchedule>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/schedules/${scheduleId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('검진 일정 수정 실패');
      return response.json();
    }
  },

  // 예약 관리
  reservations: {
    create: async (data: {
      schedule_id: number;
      worker_id: number;
      reserved_exam_types: ExamCategory[];
      result_delivery_method?: ResultDeliveryMethod;
    }) => {
      const response = await fetch(`${API_BASE}/health-exam-management/reservations/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('예약 생성 실패');
      return response.json();
    },

    getList: async (params?: {
      schedule_id?: number;
      worker_id?: number;
      status?: string;
      date?: string;
    }) => {
      const queryParams = new URLSearchParams();
      if (params?.schedule_id) queryParams.append('schedule_id', params.schedule_id.toString());
      if (params?.worker_id) queryParams.append('worker_id', params.worker_id.toString());
      if (params?.status) queryParams.append('status', params.status);
      if (params?.date) queryParams.append('date', params.date);
      
      const response = await fetch(`${API_BASE}/health-exam-management/reservations/?${queryParams}`);
      if (!response.ok) throw new Error('예약 목록 조회 실패');
      return response.json();
    },

    checkIn: async (reservationId: number) => {
      const response = await fetch(
        `${API_BASE}/health-exam-management/reservations/${reservationId}/check-in`,
        { method: 'POST' }
      );
      if (!response.ok) throw new Error('체크인 실패');
      return response.json();
    },

    cancel: async (reservationId: number, reason: string) => {
      const response = await fetch(
        `${API_BASE}/health-exam-management/reservations/${reservationId}/cancel`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ reason })
        }
      );
      if (!response.ok) throw new Error('예약 취소 실패');
      return response.json();
    }
  },

  // 문진표 관리
  charts: {
    create: async (data: Omit<HealthExamChart, 'id'>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/charts/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('문진표 생성 실패');
      return response.json();
    },

    getByWorkerId: async (workerId: number) => {
      const response = await fetch(`${API_BASE}/health-exam-management/charts/worker/${workerId}`);
      if (!response.ok) throw new Error('문진표 조회 실패');
      return response.json();
    },

    update: async (chartId: number, data: Partial<HealthExamChart>) => {
      const response = await fetch(`${API_BASE}/health-exam-management/charts/${chartId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('문진표 수정 실패');
      return response.json();
    }
  },

  // 통계 및 대시보드
  stats: {
    getPlanStats: async (planId: number) => {
      const response = await fetch(`${API_BASE}/health-exam-management/plans/${planId}/stats`);
      if (!response.ok) throw new Error('계획 통계 조회 실패');
      return response.json();
    },

    getOverallStats: async (year?: number) => {
      const queryParams = year ? `?year=${year}` : '';
      const response = await fetch(`${API_BASE}/health-exam-management/stats${queryParams}`);
      if (!response.ok) throw new Error('전체 통계 조회 실패');
      return response.json();
    }
  }
};