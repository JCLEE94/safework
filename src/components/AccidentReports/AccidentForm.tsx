import React, { useState, useEffect } from 'react';
import { Save, ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { Button, Modal } from '../common';
import { ACCIDENT_TYPES, ACCIDENT_SEVERITY } from '../../constants';

interface AccidentReport {
  id?: number;
  report_number?: string;
  incident_date: string;
  report_date: string;
  location: string;
  injured_person: string;
  department: string;
  accident_type: string;
  severity: 'minor' | 'moderate' | 'severe' | 'fatal';
  injury_type: string;
  description: string;
  immediate_cause: string;
  root_cause: string;
  corrective_actions: string[];
  preventive_measures: string[];
  reported_by: string;
  investigated_by: string;
  investigation_date: string;
  status: 'reported' | 'investigating' | 'action_required' | 'completed' | 'closed';
  follow_up_required: boolean;
  follow_up_date?: string;
  cost_estimate?: number;
  lost_work_days?: number;
  witnesses: string[];
  photos_attached: boolean;
  medical_treatment_required: boolean;
  government_notification_required: boolean;
  government_reported: boolean;
  notes?: string;
}

interface AccidentFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<AccidentReport>) => void;
  initialData?: AccidentReport | null;
  mode: 'create' | 'edit';
}

export function AccidentForm({ isOpen, onClose, onSubmit, initialData, mode }: AccidentFormProps) {
  const [formData, setFormData] = useState<Partial<AccidentReport>>({
    incident_date: new Date().toISOString().split('T')[0],
    report_date: new Date().toISOString().split('T')[0],
    location: '',
    injured_person: '',
    department: '',
    accident_type: ACCIDENT_TYPES[0]?.value || 'fall',
    severity: 'minor',
    injury_type: '',
    description: '',
    immediate_cause: '',
    root_cause: '',
    corrective_actions: [''],
    preventive_measures: [''],
    reported_by: '',
    investigated_by: '',
    investigation_date: new Date().toISOString().split('T')[0],
    status: 'reported',
    follow_up_required: false,
    follow_up_date: '',
    cost_estimate: 0,
    lost_work_days: 0,
    witnesses: [''],
    photos_attached: false,
    medical_treatment_required: false,
    government_notification_required: false,
    government_reported: false,
    notes: ''
  });

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      // Reset form for create mode
      setFormData({
        incident_date: new Date().toISOString().split('T')[0],
        report_date: new Date().toISOString().split('T')[0],
        location: '',
        injured_person: '',
        department: '',
        accident_type: ACCIDENT_TYPES[0]?.value || 'fall',
        severity: 'minor',
        injury_type: '',
        description: '',
        immediate_cause: '',
        root_cause: '',
        corrective_actions: [''],
        preventive_measures: [''],
        reported_by: '',
        investigated_by: '',
        investigation_date: new Date().toISOString().split('T')[0],
        status: 'reported',
        follow_up_required: false,
        follow_up_date: '',
        cost_estimate: 0,
        lost_work_days: 0,
        witnesses: [''],
        photos_attached: false,
        medical_treatment_required: false,
        government_notification_required: false,
        government_reported: false,
        notes: ''
      });
    }
  }, [initialData, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Generate report number for new reports
    if (mode === 'create' && !formData.report_number) {
      const year = new Date().getFullYear();
      const randomNum = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
      formData.report_number = `ACC-${year}-${randomNum}`;
    }

    // Clean up empty strings from arrays
    const cleanedData = {
      ...formData,
      corrective_actions: formData.corrective_actions?.filter(action => action.trim() !== '') || [],
      preventive_measures: formData.preventive_measures?.filter(measure => measure.trim() !== '') || [],
      witnesses: formData.witnesses?.filter(witness => witness.trim() !== '') || []
    };

    onSubmit(cleanedData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    
    if (type === 'checkbox') {
      setFormData(prev => ({
        ...prev,
        [name]: (e.target as HTMLInputElement).checked
      }));
    } else if (type === 'number') {
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

  const handleArrayChange = (field: 'corrective_actions' | 'preventive_measures' | 'witnesses', index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field]?.map((item, i) => i === index ? value : item) || []
    }));
  };

  const addArrayItem = (field: 'corrective_actions' | 'preventive_measures' | 'witnesses') => {
    setFormData(prev => ({
      ...prev,
      [field]: [...(prev[field] || []), '']
    }));
  };

  const removeArrayItem = (field: 'corrective_actions' | 'preventive_measures' | 'witnesses', index: number) => {
    setFormData(prev => ({
      ...prev,
      [field]: prev[field]?.filter((_, i) => i !== index) || []
    }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? '사고 신고 등록' : '사고 보고서 수정'}
      size="xl"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 기본 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사고 발생일 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="incident_date"
              value={formData.incident_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              신고일 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="report_date"
              value={formData.report_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사고 장소 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="location"
              value={formData.location}
              onChange={handleChange}
              placeholder="예: 건설 현장 A구역"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              부상자명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="injured_person"
              value={formData.injured_person}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              소속 부서 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="department"
              value={formData.department}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사고 유형 <span className="text-red-500">*</span>
            </label>
            <select
              name="accident_type"
              value={formData.accident_type}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {ACCIDENT_TYPES.map(type => (
                <option key={type.value} value={type.value}>{type.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              심각도 <span className="text-red-500">*</span>
            </label>
            <select
              name="severity"
              value={formData.severity}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {ACCIDENT_SEVERITY.map(severity => (
                <option key={severity.value} value={severity.value}>{severity.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              부상 유형 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="injury_type"
              value={formData.injury_type}
              onChange={handleChange}
              placeholder="예: 타박상, 골절"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>

        {/* 사고 상세 정보 */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사고 경위 <span className="text-red-500">*</span>
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              rows={3}
              placeholder="사고 발생 경위를 상세히 기록하세요"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              직접 원인 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="immediate_cause"
              value={formData.immediate_cause}
              onChange={handleChange}
              placeholder="예: 안전대 미착용"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              근본 원인 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="root_cause"
              value={formData.root_cause}
              onChange={handleChange}
              placeholder="예: 안전교육 부족 및 안전점검 소홀"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>

        {/* 시정 조치사항 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">시정 조치사항</label>
          {formData.corrective_actions?.map((action, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={action}
                onChange={(e) => handleArrayChange('corrective_actions', index, e.target.value)}
                placeholder="시정 조치사항을 입력하세요"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => removeArrayItem('corrective_actions', index)}
                disabled={formData.corrective_actions?.length === 1}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addArrayItem('corrective_actions')}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            조치사항 추가
          </Button>
        </div>

        {/* 예방 대책 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">예방 대책</label>
          {formData.preventive_measures?.map((measure, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={measure}
                onChange={(e) => handleArrayChange('preventive_measures', index, e.target.value)}
                placeholder="예방 대책을 입력하세요"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => removeArrayItem('preventive_measures', index)}
                disabled={formData.preventive_measures?.length === 1}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addArrayItem('preventive_measures')}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            예방대책 추가
          </Button>
        </div>

        {/* 목격자 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">목격자</label>
          {formData.witnesses?.map((witness, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={witness}
                onChange={(e) => handleArrayChange('witnesses', index, e.target.value)}
                placeholder="목격자명을 입력하세요"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => removeArrayItem('witnesses', index)}
                disabled={formData.witnesses?.length === 1}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => addArrayItem('witnesses')}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            목격자 추가
          </Button>
        </div>

        {/* 조사 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">신고자</label>
            <input
              type="text"
              name="reported_by"
              value={formData.reported_by}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">조사자</label>
            <input
              type="text"
              name="investigated_by"
              value={formData.investigated_by}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">조사일</label>
            <input
              type="date"
              name="investigation_date"
              value={formData.investigation_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">처리상태</label>
            <select
              name="status"
              value={formData.status}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="reported">신고됨</option>
              <option value="investigating">조사중</option>
              <option value="action_required">조치필요</option>
              <option value="completed">완료</option>
              <option value="closed">종료</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">휴업일수</label>
            <input
              type="number"
              name="lost_work_days"
              value={formData.lost_work_days}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">예상 비용 (원)</label>
            <input
              type="number"
              name="cost_estimate"
              value={formData.cost_estimate}
              onChange={handleChange}
              min="0"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {/* 체크박스 옵션들 */}
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              name="follow_up_required"
              checked={formData.follow_up_required}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">후속 조치 필요</span>
          </label>
          
          {formData.follow_up_required && (
            <div className="ml-6">
              <label className="block text-sm font-medium text-gray-700 mb-1">후속 조치 예정일</label>
              <input
                type="date"
                name="follow_up_date"
                value={formData.follow_up_date}
                onChange={handleChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          )}
          
          <label className="flex items-center">
            <input
              type="checkbox"
              name="medical_treatment_required"
              checked={formData.medical_treatment_required}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">의료 치료 필요</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              name="government_notification_required"
              checked={formData.government_notification_required}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">정부 신고 대상</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              name="government_reported"
              checked={formData.government_reported}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">정부 신고 완료</span>
          </label>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              name="photos_attached"
              checked={formData.photos_attached}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">사진 첨부됨</span>
          </label>
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
          />
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="secondary" onClick={onClose}>
            <ArrowLeft size={16} />
            취소
          </Button>
          <Button type="submit" icon={<Save size={16} />}>
            {mode === 'create' ? '사고 신고' : '수정 완료'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}