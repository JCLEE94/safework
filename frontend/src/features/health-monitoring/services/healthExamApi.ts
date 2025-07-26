import { api } from '@/services/api';
import { ExamPlan, ExamSchedule, WorkerExamStatus, ExamStats } from '../types';

const API_BASE = '/api/v1/health-exam-management';

export const healthExamApi = {
  // Exam Plans
  getPlans: async (params?: { year?: number }) => {
    return api.get<ExamPlan[]>(`${API_BASE}/plans`, { params });
  },

  createPlan: async (plan: Omit<ExamPlan, 'id' | 'created_at' | 'updated_at'>) => {
    return api.post<ExamPlan>(`${API_BASE}/plans`, plan);
  },

  updatePlan: async (id: number, plan: Partial<ExamPlan>) => {
    return api.put<ExamPlan>(`${API_BASE}/plans/${id}`, plan);
  },

  approvePlan: async (id: number) => {
    return api.post<ExamPlan>(`${API_BASE}/plans/${id}/approve`);
  },

  // Exam Schedules
  getSchedules: async (planId: number) => {
    return api.get<ExamSchedule[]>(`${API_BASE}/schedules`, {
      params: { plan_id: planId }
    });
  },

  createSchedule: async (schedule: Omit<ExamSchedule, 'id' | 'reserved_count'>) => {
    return api.post<ExamSchedule>(`${API_BASE}/schedules`, schedule);
  },

  // Worker Status
  getWorkerStatuses: async (params?: { department?: string; status?: string }) => {
    return api.get<WorkerExamStatus[]>(`${API_BASE}/worker-status`, { params });
  },

  // Statistics
  getExamStats: async (year?: number) => {
    return api.get<ExamStats>(`${API_BASE}/stats`, {
      params: { year }
    });
  }
};