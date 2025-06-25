import React, { useState, useEffect } from 'react';
import { Save, ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { Button, Modal } from '../common';
import { EDUCATION_STATUS } from '../../constants';

interface HealthEducation {
  id?: number;
  title: string;
  education_type: string;
  instructor: string;
  duration: number;
  target_workers: string[];
  scheduled_date: string;
  completion_rate: number;
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled';
  required_hours: number;
  description: string;
}

interface EducationFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<HealthEducation>) => void;
  initialData?: HealthEducation | null;
  mode: 'create' | 'edit';
}

const EDUCATION_TYPES = [
  { value: '법정교육', label: '법정교육' },
  { value: '정기교육', label: '정기교육' },
  { value: '특별교육', label: '특별교육' },
  { value: '관리감독자교육', label: '관리감독자교육' },
  { value: '자율교육', label: '자율교육' }
];

export function EducationForm({ isOpen, onClose, onSubmit, initialData, mode }: EducationFormProps) {
  const [formData, setFormData] = useState<Partial<HealthEducation>>({
    title: '',
    education_type: '정기교육',
    instructor: '',
    duration: 3,
    target_workers: [''],
    scheduled_date: new Date().toISOString().split('T')[0],
    completion_rate: 0,
    status: 'scheduled',
    required_hours: 3,
    description: ''
  });

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      // Reset form for create mode
      setFormData({
        title: '',
        education_type: '정기교육',
        instructor: '',
        duration: 3,
        target_workers: [''],
        scheduled_date: new Date().toISOString().split('T')[0],
        completion_rate: 0,
        status: 'scheduled',
        required_hours: 3,
        description: ''
      });
    }
  }, [initialData, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clean up empty strings from target_workers array
    const cleanedData = {
      ...formData,
      target_workers: formData.target_workers?.filter(worker => worker.trim() !== '') || []
    };

    onSubmit(cleanedData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'number') {
      setFormData(prev => ({
        ...prev,
        [name]: value === '' ? 0 : Number(value)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const handleWorkerChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      target_workers: prev.target_workers?.map((worker, i) => i === index ? value : worker) || []
    }));
  };

  const addWorker = () => {
    setFormData(prev => ({
      ...prev,
      target_workers: [...(prev.target_workers || []), '']
    }));
  };

  const removeWorker = (index: number) => {
    setFormData(prev => ({
      ...prev,
      target_workers: prev.target_workers?.filter((_, i) => i !== index) || []
    }));
  };

  const handleEducationTypeChange = (type: string) => {
    // Set default required hours based on education type
    let defaultHours = 3;
    switch (type) {
      case '법정교육':
        defaultHours = 8;
        break;
      case '정기교육':
        defaultHours = 3;
        break;
      case '특별교육':
        defaultHours = 4;
        break;
      case '관리감독자교육':
        defaultHours = 16;
        break;
      default:
        defaultHours = 3;
    }

    setFormData(prev => ({
      ...prev,
      education_type: type,
      required_hours: defaultHours,
      duration: defaultHours
    }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? '보건교육 계획 등록' : '보건교육 계획 수정'}
      size="lg"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              교육명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleChange}
              placeholder="예: 신입 근로자 안전보건교육"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              교육 유형 <span className="text-red-500">*</span>
            </label>
            <select
              name="education_type"
              value={formData.education_type}
              onChange={(e) => handleEducationTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {EDUCATION_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              강사 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="instructor"
              value={formData.instructor}
              onChange={handleChange}
              placeholder="예: 안전관리자 김교육"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              예정일 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="scheduled_date"
              value={formData.scheduled_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              법정 필수 시간 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="required_hours"
              value={formData.required_hours}
              onChange={handleChange}
              min="1"
              max="40"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              실제 교육 시간 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="duration"
              value={formData.duration}
              onChange={handleChange}
              min="1"
              max="40"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">진행 상태</label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {EDUCATION_STATUS.map(status => (
                <option key={status.value} value={status.value}>{status.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">완료율 (%)</label>
            <input
              type="number"
              name="completion_rate"
              value={formData.completion_rate}
              onChange={handleChange}
              min="0"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* 교육 대상자 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            교육 대상자 <span className="text-red-500">*</span>
          </label>
          {formData.target_workers?.map((worker, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={worker}
                onChange={(e) => handleWorkerChange(index, e.target.value)}
                placeholder="근로자명을 입력하세요"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={index === 0}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => removeWorker(index)}
                disabled={formData.target_workers?.length === 1}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addWorker}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            대상자 추가
          </Button>
        </div>

        {/* 교육 내용 설명 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            교육 내용 <span className="text-red-500">*</span>
          </label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows={4}
            placeholder="교육 목적, 내용, 법적 근거 등을 상세히 기록하세요"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            required
          />
        </div>

        {/* 교육 유형별 안내 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <h4 className="text-sm font-medium text-blue-900 mb-2">교육 유형별 법정 기준</h4>
          <div className="text-xs text-blue-700 space-y-1">
            <p>• <strong>신입 근로자 (법정교육)</strong>: 8시간 이상</p>
            <p>• <strong>정기 교육</strong>: 분기별 3시간 이상</p>
            <p>• <strong>특별 교육</strong>: 위험 작업별 2~16시간</p>
            <p>• <strong>관리감독자 교육</strong>: 연 16시간 이상</p>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="secondary" onClick={onClose}>
            <ArrowLeft size={16} />
            취소
          </Button>
          <Button type="submit" icon={<Save size={16} />}>
            {mode === 'create' ? '교육 등록' : '수정 완료'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}