import React, { useState, useEffect } from 'react';
import { X, Calendar, User, FileText, AlertTriangle, Save, Plus } from 'lucide-react';
import { Button, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface Worker {
  id: number;
  employee_id: string;
  name: string;
  department: string;
  position: string;
}

interface ConsultationFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  initialData?: any;
  mode: 'create' | 'edit';
}

const CONSULTATION_TYPES = [
  { value: '정기상담', label: '정기상담' },
  { value: '응급상담', label: '응급상담' },
  { value: '사후관리', label: '사후관리' },
  { value: '건강문제', label: '건강문제' },
  { value: '직업병관련', label: '직업병관련' }
];

const CONSULTATION_STATUS = [
  { value: '예정', label: '예정' },
  { value: '진행중', label: '진행중' },
  { value: '완료', label: '완료' },
  { value: '취소', label: '취소' },
  { value: '재예약', label: '재예약' }
];

const HEALTH_ISSUE_CATEGORIES = [
  { value: '호흡기', label: '호흡기' },
  { value: '근골격계', label: '근골격계' },
  { value: '피부', label: '피부' },
  { value: '눈', label: '눈' },
  { value: '심혈관', label: '심혈관' },
  { value: '정신건강', label: '정신건강' },
  { value: '소화기', label: '소화기' },
  { value: '기타', label: '기타' }
];

const CONSULTATION_LOCATIONS = [
  { value: '현장 사무실', label: '현장 사무실' },
  { value: '작업장', label: '작업장' },
  { value: '의무실', label: '의무실' },
  { value: '병원', label: '병원' },
  { value: '화상상담', label: '화상상담' },
  { value: '기타', label: '기타' }
];

export function ConsultationForm({ isOpen, onClose, onSubmit, initialData, mode }: ConsultationFormProps) {
  const [formData, setFormData] = useState({
    worker_id: '',
    consultation_date: '',
    consultation_time: '',
    consultation_type: '',
    chief_complaint: '',
    symptoms: '',
    health_issue_category: '',
    consultation_location: '',
    consultant_name: '',
    consultation_content: '',
    recommendations: '',
    status: '예정',
    referral_needed: false,
    referral_details: '',
    follow_up_needed: false,
    follow_up_date: '',
    follow_up_notes: '',
    work_related: false,
    confidential_notes: ''
  });

  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showWorkerDropdown, setShowWorkerDropdown] = useState(false);

  const { fetchApi } = useApi();

  useEffect(() => {
    if (isOpen) {
      loadWorkers();
      if (mode === 'edit' && initialData) {
        const consultationDateTime = new Date(initialData.consultation_date);
        setFormData({
          worker_id: initialData.worker_id || '',
          consultation_date: consultationDateTime.toISOString().split('T')[0],
          consultation_time: consultationDateTime.toTimeString().slice(0, 5),
          consultation_type: initialData.consultation_type || '',
          chief_complaint: initialData.chief_complaint || '',
          symptoms: initialData.symptoms || '',
          health_issue_category: initialData.health_issue_category || '',
          consultation_location: initialData.consultation_location || '',
          consultant_name: initialData.consultant_name || '',
          consultation_content: initialData.consultation_details || '',
          recommendations: initialData.action_taken || '',
          status: initialData.status || '예정',
          referral_needed: initialData.referral_needed || false,
          referral_details: initialData.referral_details || '',
          follow_up_needed: initialData.follow_up_needed || false,
          follow_up_date: initialData.follow_up_date || '',
          follow_up_notes: initialData.follow_up_notes || '',
          work_related: initialData.work_related || false,
          confidential_notes: initialData.confidential_notes || ''
        });
      } else {
        resetForm();
      }
    }
  }, [isOpen, mode, initialData]);

  const resetForm = () => {
    const now = new Date();
    setFormData({
      worker_id: '',
      consultation_date: now.toISOString().split('T')[0],
      consultation_time: now.toTimeString().slice(0, 5),
      consultation_type: '',
      chief_complaint: '',
      symptoms: '',
      health_issue_category: '',
      consultation_location: '현장 사무실',
      consultant_name: '',
      consultation_content: '',
      recommendations: '',
      status: '예정',
      referral_needed: false,
      referral_details: '',
      follow_up_needed: false,
      follow_up_date: '',
      follow_up_notes: '',
      work_related: false,
      confidential_notes: ''
    });
    setSearchTerm('');
  };

  const loadWorkers = async () => {
    try {
      const data = await fetchApi('/workers?limit=1000&is_active=true');
      setWorkers(data.items || []);
    } catch (error) {
      console.error('근로자 목록 조회 실패:', error);
    }
  };

  const filteredWorkers = workers.filter(worker =>
    worker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    worker.employee_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    worker.department.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const consultationDateTime = new Date(`${formData.consultation_date}T${formData.consultation_time}`);
      
      const submitData = {
        worker_id: parseInt(formData.worker_id),
        consultation_date: consultationDateTime.toISOString(),
        consultation_type: formData.consultation_type,
        chief_complaint: formData.chief_complaint,
        symptoms: formData.symptoms,
        health_issue_category: formData.health_issue_category,
        consultation_location: formData.consultation_location,
        consultant_name: formData.consultant_name,
        consultation_content: formData.consultation_content,
        recommendations: formData.recommendations,
        status: formData.status,
        referral_needed: formData.referral_needed,
        referral_details: formData.referral_details,
        follow_up_needed: formData.follow_up_needed,
        follow_up_date: formData.follow_up_date || null,
        follow_up_notes: formData.follow_up_notes,
        work_related: formData.work_related,
        confidential_notes: formData.confidential_notes
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error('상담 정보 저장 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectedWorker = workers.find(w => w.id === parseInt(formData.worker_id));

  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} maxWidth="4xl">
      <div className="bg-white rounded-lg shadow-xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-800">
            {mode === 'create' ? '보건상담 등록' : '보건상담 수정'}
          </h2>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* 기본 정보 */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* 근로자 선택 */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                근로자 <span className="text-red-500">*</span>
              </label>
              <div className="relative">
                <input
                  type="text"
                  placeholder="근로자명, 사번, 부서로 검색..."
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value);
                    setShowWorkerDropdown(true);
                  }}
                  onFocus={() => setShowWorkerDropdown(true)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                {selectedWorker && (
                  <div className="mt-2 p-3 bg-blue-50 rounded-lg">
                    <div className="flex items-center justify-between">
                      <div>
                        <span className="font-medium">{selectedWorker.name}</span>
                        <span className="text-gray-500 ml-2">({selectedWorker.employee_id})</span>
                      </div>
                      <span className="text-sm text-gray-600">
                        {selectedWorker.department} / {selectedWorker.position}
                      </span>
                    </div>
                  </div>
                )}
                
                {showWorkerDropdown && filteredWorkers.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                    {filteredWorkers.map(worker => (
                      <div
                        key={worker.id}
                        onClick={() => {
                          handleInputChange('worker_id', worker.id.toString());
                          setSearchTerm(worker.name);
                          setShowWorkerDropdown(false);
                        }}
                        className="p-3 hover:bg-gray-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                      >
                        <div className="flex justify-between items-center">
                          <div>
                            <span className="font-medium">{worker.name}</span>
                            <span className="text-gray-500 ml-2">({worker.employee_id})</span>
                          </div>
                          <span className="text-sm text-gray-600">
                            {worker.department} / {worker.position}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* 상담일시 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담일자 <span className="text-red-500">*</span>
              </label>
              <input
                type="date"
                value={formData.consultation_date}
                onChange={(e) => handleInputChange('consultation_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담시간 <span className="text-red-500">*</span>
              </label>
              <input
                type="time"
                value={formData.consultation_time}
                onChange={(e) => handleInputChange('consultation_time', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* 상담유형 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담유형 <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.consultation_type}
                onChange={(e) => handleInputChange('consultation_type', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                <option value="">상담유형 선택</option>
                {CONSULTATION_TYPES.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
            </div>

            {/* 상담장소 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담장소 <span className="text-red-500">*</span>
              </label>
              <select
                value={formData.consultation_location}
                onChange={(e) => handleInputChange('consultation_location', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              >
                {CONSULTATION_LOCATIONS.map(location => (
                  <option key={location.value} value={location.value}>{location.label}</option>
                ))}
              </select>
            </div>

            {/* 상담자 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담자 <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.consultant_name}
                onChange={(e) => handleInputChange('consultant_name', e.target.value)}
                placeholder="상담자명 입력"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* 상태 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담상태
              </label>
              <select
                value={formData.status}
                onChange={(e) => handleInputChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {CONSULTATION_STATUS.map(status => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* 상담 내용 */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-800 border-b pb-2">상담 내용</h3>
            
            {/* 주 호소사항 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                주 호소사항 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.chief_complaint}
                onChange={(e) => handleInputChange('chief_complaint', e.target.value)}
                placeholder="근로자가 호소하는 주요 증상이나 문제를 입력하세요"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* 증상 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                세부 증상
              </label>
              <textarea
                value={formData.symptoms}
                onChange={(e) => handleInputChange('symptoms', e.target.value)}
                placeholder="관찰된 증상이나 근로자가 설명한 세부 증상을 입력하세요"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>

            {/* 건강문제 카테고리 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                건강문제 카테고리
              </label>
              <select
                value={formData.health_issue_category}
                onChange={(e) => handleInputChange('health_issue_category', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">카테고리 선택</option>
                {HEALTH_ISSUE_CATEGORIES.map(category => (
                  <option key={category.value} value={category.value}>{category.label}</option>
                ))}
              </select>
            </div>

            {/* 상담 내용 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                상담 내용 <span className="text-red-500">*</span>
              </label>
              <textarea
                value={formData.consultation_content}
                onChange={(e) => handleInputChange('consultation_content', e.target.value)}
                placeholder="상담 진행 과정과 주요 내용을 상세히 기록하세요"
                rows={4}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required
              />
            </div>

            {/* 권고사항 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                권고사항 및 조치내용
              </label>
              <textarea
                value={formData.recommendations}
                onChange={(e) => handleInputChange('recommendations', e.target.value)}
                placeholder="상담 결과에 따른 권고사항이나 조치내용을 입력하세요"
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* 추가 옵션 */}
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-gray-800 border-b pb-2">추가 정보</h3>
            
            {/* 체크박스 옵션들 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.work_related}
                  onChange={(e) => handleInputChange('work_related', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">작업 관련</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.referral_needed}
                  onChange={(e) => handleInputChange('referral_needed', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">의료기관 의뢰 필요</span>
              </label>

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.follow_up_needed}
                  onChange={(e) => handleInputChange('follow_up_needed', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">추적관찰 필요</span>
              </label>
            </div>

            {/* 의료기관 의뢰 상세 */}
            {formData.referral_needed && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  의뢰 상세사항
                </label>
                <textarea
                  value={formData.referral_details}
                  onChange={(e) => handleInputChange('referral_details', e.target.value)}
                  placeholder="의뢰 사유, 의뢰 기관, 검사 항목 등을 입력하세요"
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            )}

            {/* 추적관찰 정보 */}
            {formData.follow_up_needed && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    추적관찰 예정일
                  </label>
                  <input
                    type="date"
                    value={formData.follow_up_date}
                    onChange={(e) => handleInputChange('follow_up_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    추적관찰 비고
                  </label>
                  <textarea
                    value={formData.follow_up_notes}
                    onChange={(e) => handleInputChange('follow_up_notes', e.target.value)}
                    placeholder="추적관찰 계획이나 주의사항을 입력하세요"
                    rows={2}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            )}

            {/* 기밀 메모 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                기밀 메모 (관리자만 열람)
              </label>
              <textarea
                value={formData.confidential_notes}
                onChange={(e) => handleInputChange('confidential_notes', e.target.value)}
                placeholder="기밀이 요구되는 민감한 정보나 개인적인 내용을 입력하세요"
                rows={2}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* 제출 버튼 */}
          <div className="flex justify-end space-x-3 pt-6 border-t border-gray-200">
            <Button
              type="button"
              variant="secondary"
              onClick={onClose}
              disabled={loading}
            >
              취소
            </Button>
            <Button
              type="submit"
              loading={loading}
              icon={<Save size={16} />}
            >
              {mode === 'create' ? '등록' : '수정'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
}