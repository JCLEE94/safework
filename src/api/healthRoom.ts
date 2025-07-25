import { API_BASE } from './config';

// 투약 기록 관련 타입
export interface MedicationRecord {
  id?: number;
  worker_id: number;
  medication_name: string;
  dosage: string;
  quantity: number;
  purpose?: string;
  symptoms?: string;
  administered_by?: string;
  notes?: string;
  follow_up_required: boolean;
  administered_at?: string;
  created_at?: string;
  updated_at?: string;
}

// 생체 신호 측정 관련 타입
export interface VitalSignRecord {
  id?: number;
  worker_id: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  blood_sugar?: number;
  blood_sugar_type?: '공복' | '식후';
  heart_rate?: number;
  body_temperature?: number;
  oxygen_saturation?: number;
  measured_by?: string;
  notes?: string;
  status?: string;
  measured_at?: string;
  created_at?: string;
  updated_at?: string;
}

// 인바디 측정 관련 타입
export interface InBodyRecord {
  id?: number;
  worker_id: number;
  height: number;
  weight: number;
  bmi: number;
  body_fat_mass?: number;
  body_fat_percentage?: number;
  muscle_mass?: number;
  lean_body_mass?: number;
  total_body_water?: number;
  right_arm_muscle?: number;
  left_arm_muscle?: number;
  trunk_muscle?: number;
  right_leg_muscle?: number;
  left_leg_muscle?: number;
  right_arm_fat?: number;
  left_arm_fat?: number;
  trunk_fat?: number;
  right_leg_fat?: number;
  left_leg_fat?: number;
  visceral_fat_level?: number;
  basal_metabolic_rate?: number;
  body_age?: number;
  device_model?: string;
  evaluation?: string;
  recommendations?: string;
  measured_at?: string;
  created_at?: string;
  updated_at?: string;
}

// 건강관리실 방문 기록 타입
export interface HealthRoomVisit {
  id?: number;
  worker_id: number;
  visit_reason: string;
  chief_complaint?: string;
  treatment_provided?: string;
  medication_given: boolean;
  measurement_taken: boolean;
  follow_up_required: boolean;
  referral_required: boolean;
  referral_location?: string;
  notes?: string;
  status?: string;
  visit_date?: string;
  created_at?: string;
  updated_at?: string;
}

// API 함수들
export const healthRoomApi = {
  // 투약 기록 관리
  medications: {
    create: async (data: MedicationRecord) => {
      const response = await fetch(`${API_BASE}/health-room/medications`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('투약 기록 생성 실패');
      return response.json();
    },
    
    getList: async (params?: {
      worker_id?: number;
      start_date?: string;
      end_date?: string;
      follow_up_only?: boolean;
      skip?: number;
      limit?: number;
    }) => {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) queryParams.append(key, String(value));
        });
      }
      const response = await fetch(`${API_BASE}/health-room/medications?${queryParams}`);
      if (!response.ok) throw new Error('투약 기록 조회 실패');
      return response.json();
    }
  },

  // 생체 신호 측정 관리
  vitalSigns: {
    create: async (data: VitalSignRecord) => {
      const response = await fetch(`${API_BASE}/health-room/vital-signs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('생체 신호 측정 기록 생성 실패');
      return response.json();
    },
    
    getList: async (params?: {
      worker_id?: number;
      status?: string;
      start_date?: string;
      end_date?: string;
      skip?: number;
      limit?: number;
    }) => {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) queryParams.append(key, String(value));
        });
      }
      const response = await fetch(`${API_BASE}/health-room/vital-signs?${queryParams}`);
      if (!response.ok) throw new Error('생체 신호 측정 기록 조회 실패');
      return response.json();
    }
  },

  // 인바디 측정 관리
  inbody: {
    create: async (data: InBodyRecord) => {
      const response = await fetch(`${API_BASE}/health-room/inbody`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('인바디 측정 기록 생성 실패');
      return response.json();
    },
    
    getList: async (params?: {
      worker_id?: number;
      start_date?: string;
      end_date?: string;
      skip?: number;
      limit?: number;
    }) => {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) queryParams.append(key, String(value));
        });
      }
      const response = await fetch(`${API_BASE}/health-room/inbody?${queryParams}`);
      if (!response.ok) throw new Error('인바디 측정 기록 조회 실패');
      return response.json();
    },
    
    getLatest: async (workerId: number) => {
      const response = await fetch(`${API_BASE}/health-room/inbody/${workerId}/latest`);
      if (!response.ok) throw new Error('최신 인바디 측정 기록 조회 실패');
      return response.json();
    }
  },

  // 건강관리실 방문 기록 관리
  visits: {
    create: async (data: HealthRoomVisit) => {
      const response = await fetch(`${API_BASE}/health-room/visits`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
      if (!response.ok) throw new Error('방문 기록 생성 실패');
      return response.json();
    },
    
    getList: async (params?: {
      worker_id?: number;
      start_date?: string;
      end_date?: string;
      follow_up_only?: boolean;
      referral_only?: boolean;
      skip?: number;
      limit?: number;
    }) => {
      const queryParams = new URLSearchParams();
      if (params) {
        Object.entries(params).forEach(([key, value]) => {
          if (value !== undefined) queryParams.append(key, String(value));
        });
      }
      const response = await fetch(`${API_BASE}/health-room/visits?${queryParams}`);
      if (!response.ok) throw new Error('방문 기록 조회 실패');
      return response.json();
    }
  },

  // 통계 및 대시보드
  getStats: async (start_date?: string, end_date?: string) => {
    const queryParams = new URLSearchParams();
    if (start_date) queryParams.append('start_date', start_date);
    if (end_date) queryParams.append('end_date', end_date);
    
    const response = await fetch(`${API_BASE}/health-room/stats?${queryParams}`);
    if (!response.ok) throw new Error('건강관리실 통계 조회 실패');
    return response.json();
  },

  getWorkerSummary: async (workerId: number, days: number = 30) => {
    const response = await fetch(`${API_BASE}/health-room/workers/${workerId}/summary?days=${days}`);
    if (!response.ok) throw new Error('근로자 건강 요약 조회 실패');
    return response.json();
  }
};