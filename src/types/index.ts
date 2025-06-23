/**
 * 공통 타입 정의
 * Common type definitions
 */

export interface Worker {
  id: number;
  name: string;
  employee_id: string;
  gender?: string;
  birth_date?: string;
  phone?: string;
  email?: string;
  department?: string;
  position?: string;
  employment_type: string;
  work_type: string;
  hire_date?: string;
  health_status: string;
  is_special_exam_target: boolean;
  is_active: boolean;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface HealthExam {
  id: number;
  worker_id: number;
  worker_name?: string;
  employee_id?: string;
  exam_date: string;
  exam_type: string;
  result: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Environment {
  id: number;
  location: string;
  measurement_date: string;
  measurement_type: string;
  result: number;
  unit: string;
  status: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Education {
  id: number;
  title: string;
  date: string;
  participants: number;
  status: string;
  duration: number;
  instructor?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Chemical {
  id: number;
  name: string;
  cas_number: string;
  danger_grade: string;
  msds_status: string;
  stock: number;
  unit?: string;
  location?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Accident {
  id: number;
  date: string;
  type: string;
  severity: string;
  status: string;
  description: string;
  worker_id?: number;
  worker_name?: string;
  employee_id?: string;
  location?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface DashboardData {
  total_workers: number;
  special_exam_targets: number;
  health_exam_needed: number;
  accidents_this_month: number;
  employment_type_distribution: Record<string, { count: number; label: string }>;
  work_type_distribution: Record<string, { count: number; label: string }>;
  health_status_distribution: Record<string, { count: number; label: string }>;
  by_department?: Record<string, number>;
  updated_at: string;
}

export interface ApiResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'textarea' | 'email' | 'tel';
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    minLength?: number;
    maxLength?: number;
  };
}