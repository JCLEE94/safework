import React, { useState, useEffect } from 'react';
import { Save, ArrowLeft, User } from 'lucide-react';
import { Button, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface HealthExam {
  id?: number;
  worker_id: number;
  exam_type: string;
  exam_date: string;
  exam_result: string;
  exam_institution?: string;
  doctor_name?: string;
  followup_required?: string;
  next_exam_date?: string;
  notes?: string;
  vital_signs?: {
    height?: number;
    weight?: number;
    blood_pressure_systolic?: number;
    blood_pressure_diastolic?: number;
    pulse?: number;
    temperature?: number;
  };
  lab_results?: Array<{
    test_name: string;
    result_value: string;
    reference_range: string;
    unit?: string;
  }>;
}

interface Worker {
  id: number;
  name: string;
  employee_id: string;
}

interface HealthExamFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<HealthExam>) => void;
  initialData?: HealthExam | null;
  mode: 'create' | 'edit';
}

const EXAM_TYPES = [
  { value: 'GENERAL', label: '일반건강진단' },
  { value: 'SPECIAL', label: '특수건강진단' },
  { value: 'EMPLOYMENT', label: '채용시건강진단' },
  { value: 'PERIODIC', label: '정기건강진단' }
];

const EXAM_RESULTS = [
  { value: 'NORMAL', label: '정상' },
  { value: 'OBSERVATION', label: '요관찰' },
  { value: 'ABNORMAL', label: '유소견' },
  { value: 'TREATMENT', label: '치료요구' }
];

export function HealthExamForm({ isOpen, onClose, onSubmit, initialData, mode }: HealthExamFormProps) {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [formData, setFormData] = useState<Partial<HealthExam>>({
    worker_id: 0,
    exam_type: 'GENERAL',
    exam_date: new Date().toISOString().split('T')[0],
    exam_result: 'NORMAL',
    exam_institution: '',
    doctor_name: '',
    followup_required: 'N',
    notes: '',
    vital_signs: {
      height: undefined,
      weight: undefined,
      blood_pressure_systolic: undefined,
      blood_pressure_diastolic: undefined,
      pulse: undefined,
      temperature: undefined
    },
    lab_results: []
  });

  const { fetchApi } = useApi();

  useEffect(() => {
    if (isOpen) {
      loadWorkers();
    }
  }, [isOpen]);

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      // Reset form for create mode
      setFormData({
        worker_id: 0,
        exam_type: 'GENERAL',
        exam_date: new Date().toISOString().split('T')[0],
        exam_result: 'NORMAL',
        exam_institution: '',
        doctor_name: '',
        followup_required: 'N',
        notes: '',
        vital_signs: {
          height: undefined,
          weight: undefined,
          blood_pressure_systolic: undefined,
          blood_pressure_diastolic: undefined,
          pulse: undefined,
          temperature: undefined
        },
        lab_results: []
      });
    }
  }, [initialData]);

  const loadWorkers = async () => {
    try {
      const data = await fetchApi<{items: Worker[]}>('/workers');
      setWorkers(data.items || []);
    } catch (error) {
      console.error('근로자 목록 조회 실패:', error);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.worker_id || formData.worker_id === 0) {
      alert('근로자를 선택해주세요.');
      return;
    }

    // Calculate next exam date (1 year for general, 6 months for special)
    const examDate = new Date(formData.exam_date!);
    const nextExamDate = new Date(examDate);
    
    if (formData.exam_type === 'SPECIAL') {
      nextExamDate.setMonth(nextExamDate.getMonth() + 6);
    } else {
      nextExamDate.setFullYear(nextExamDate.getFullYear() + 1);
    }

    const submitData = {
      ...formData,
      next_exam_date: nextExamDate.toISOString().split('T')[0]
    };

    onSubmit(submitData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    
    if (name.startsWith('vital_')) {
      const vitalKey = name.replace('vital_', '');
      setFormData(prev => ({
        ...prev,
        vital_signs: {
          ...prev.vital_signs,
          [vitalKey]: value ? Number(value) : undefined
        }
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: name === 'worker_id' ? Number(value) : value
      }));
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? '건강진단 등록' : '건강진단 수정'}
      size="xl"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 기본 정보 */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <User className="mr-2" size={20} />
            기본 정보
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                근로자 <span className="text-red-500">*</span>
              </label>
              <select
                name="worker_id"
                value={formData.worker_id}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
                disabled={mode === 'edit'}
              >
                <option value={0}>근로자 선택</option>
                {workers.map(worker => (
                  <option key={worker.id} value={worker.id}>
                    {worker.name} ({worker.employee_id})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                검진유형 <span className="text-red-500">*</span>
              </label>
              <select
                name="exam_type"
                value={formData.exam_type}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {EXAM_TYPES.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                검진일자 <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                name="exam_date"
                value={formData.exam_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                검진결과 <span className="text-red-500">*</span>
              </label>
              <select
                name="exam_result"
                value={formData.exam_result}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {EXAM_RESULTS.map(result => (
                  <option key={result.value} value={result.value}>{result.label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">검진기관</label>
              <input
                type="text"
                name="exam_institution"
                value={formData.exam_institution}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="검진기관명"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">담당의사</label>
              <input
                type="text"
                name="doctor_name"
                value={formData.doctor_name}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="담당의사명"
              />
            </div>
          </div>

          <div className="mt-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                name="followup_required"
                checked={formData.followup_required === 'Y'}
                onChange={(e) => setFormData(prev => ({
                  ...prev,
                  followup_required: e.target.checked ? 'Y' : 'N'
                }))}
                className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-sm text-gray-700">사후관리 필요</span>
            </label>
          </div>
        </div>

        {/* 생체징후 */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">생체징후</h3>
          
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">신장 (cm)</label>
              <input
                type="number"
                name="vital_height"
                value={formData.vital_signs?.height || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
                step="0.1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">체중 (kg)</label>
              <input
                type="number"
                name="vital_weight"
                value={formData.vital_signs?.weight || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
                step="0.1"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">맥박 (bpm)</label>
              <input
                type="number"
                name="vital_pulse"
                value={formData.vital_signs?.pulse || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">수축기 혈압 (mmHg)</label>
              <input
                type="number"
                name="vital_blood_pressure_systolic"
                value={formData.vital_signs?.blood_pressure_systolic || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">이완기 혈압 (mmHg)</label>
              <input
                type="number"
                name="vital_blood_pressure_diastolic"
                value={formData.vital_signs?.blood_pressure_diastolic || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">체온 (°C)</label>
              <input
                type="number"
                name="vital_temperature"
                value={formData.vital_signs?.temperature || ''}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                min="0"
                step="0.1"
              />
            </div>
          </div>
        </div>

        {/* 비고 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">비고</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="검진 결과 상세 내용, 주의사항 등"
          />
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="secondary" onClick={onClose}>
            <ArrowLeft size={16} />
            취소
          </Button>
          <Button type="submit" icon={<Save size={16} />}>
            {mode === 'create' ? '등록' : '수정'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}