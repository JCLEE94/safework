import { API_ENDPOINTS } from '@/config/constants';
import api from './baseApi';

// 대시보드 통계
export interface DashboardStats {
  // 근로자 통계
  total_workers: number;
  worker_change: number;
  
  // 건강검진 통계
  pending_health_exams: number;
  health_exam_completion_rate: number;
  special_exam_targets: number;
  
  // 사고 통계
  monthly_accidents: number;
  ltifr: number;
  
  // 컴플라이언스 통계
  compliance_rate: number;
  
  // 교육 통계
  education_completion_rate: number;
  completed_educations: number;
  total_educations: number;
  
  // 작업환경측정 통계
  work_environment_status: number;
  next_measurement_date: string;
  
  // MSDS 통계
  msds_registered: number;
  msds_pending: number;
}

// 최근 활동
export interface RecentActivity {
  id: number;
  type: 'exam' | 'accident' | 'education' | 'other';
  title: string;
  description: string;
  created_at: string;
  created_by: string;
}

// 다가오는 일정
export interface UpcomingSchedule {
  id: number;
  category: 'health_exam' | 'education' | 'work_environment' | 'other';
  title: string;
  target_info: string;
  scheduled_date: string;
  days_remaining: number;
  responsible_person: string;
}

export const dashboardApi = {
  // 대시보드 통계 조회
  getStats: async () => {
    const response = await api.get<DashboardStats>(`${API_ENDPOINTS.DASHBOARD}/stats`);
    return response;
  },

  // 최근 활동 조회
  getRecentActivities: async (limit: number = 10) => {
    const response = await api.get<RecentActivity[]>(
      `${API_ENDPOINTS.DASHBOARD}/recent-activities`,
      { params: { limit } }
    );
    return response;
  },

  // 다가오는 일정 조회
  getUpcomingSchedules: async (days: number = 30) => {
    const response = await api.get<UpcomingSchedule[]>(
      `${API_ENDPOINTS.DASHBOARD}/upcoming-schedules`,
      { params: { days } }
    );
    return response;
  },

  // 주간 트렌드 조회
  getWeeklyTrends: async () => {
    const response = await api.get(`${API_ENDPOINTS.DASHBOARD}/weekly-trends`);
    return response;
  },

  // 부서별 통계 조회
  getDepartmentStats: async () => {
    const response = await api.get(`${API_ENDPOINTS.DASHBOARD}/department-stats`);
    return response;
  },
};