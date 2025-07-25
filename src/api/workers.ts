import { API_BASE } from './config';

export interface Worker {
  id: number;
  employee_id: string;
  name: string;
  birth_date?: string;
  gender?: string;
  phone?: string;
  email?: string;
  address: string;
  company_name: string;
  work_category: string;
  employment_type: string;
  work_type: string;
  hire_date?: string;
  department: string;
  position?: string;
  health_status?: string;
  blood_type?: string;
  emergency_contact?: string;
  emergency_relationship?: string;
  is_active: boolean;
}

export const workersApi = {
  getAll: async () => {
    const response = await fetch(`${API_BASE}/workers/`);
    if (!response.ok) throw new Error('Failed to fetch workers');
    return response.json();
  },

  getById: async (id: number) => {
    const response = await fetch(`${API_BASE}/workers/${id}`);
    if (!response.ok) throw new Error('Failed to fetch worker');
    return response.json();
  },

  create: async (data: Partial<Worker>) => {
    const response = await fetch(`${API_BASE}/workers/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to create worker');
    return response.json();
  },

  update: async (id: number, data: Partial<Worker>) => {
    const response = await fetch(`${API_BASE}/workers/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to update worker');
    return response.json();
  },

  delete: async (id: number) => {
    const response = await fetch(`${API_BASE}/workers/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Failed to delete worker');
    return response.json();
  }
};