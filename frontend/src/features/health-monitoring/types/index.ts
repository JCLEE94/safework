export enum ExamPlanStatus {
  DRAFT = 'draft',
  PENDING_APPROVAL = 'pending_approval',
  APPROVED = 'approved',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled'
}

export enum ExamCategory {
  GENERAL = 'general',
  SPECIAL = 'special',
  PLACEMENT = 'placement',
  RETURN_TO_WORK = 'return_to_work'
}

export interface ExamPlan {
  id: number;
  year: number;
  category: ExamCategory;
  plan_status: ExamPlanStatus;
  created_at: string;
  updated_at: string;
  approved_by?: string;
  approved_at?: string;
}

export interface ExamSchedule {
  id: number;
  plan_id: number;
  exam_date: string;
  location: string;
  provider: string;
  capacity: number;
  reserved_count: number;
}

export interface WorkerExamStatus {
  worker_id: number;
  worker_name: string;
  department: string;
  last_exam_date?: string;
  next_exam_due: string;
  exam_status: 'completed' | 'scheduled' | 'overdue';
}

export interface ExamStats {
  total_workers: number;
  completed_exams: number;
  scheduled_exams: number;
  overdue_exams: number;
  completion_rate: number;
}