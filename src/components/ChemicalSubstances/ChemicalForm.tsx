import React, { useState, useEffect } from 'react';
import { Save, ArrowLeft, Plus, Trash2 } from 'lucide-react';
import { Button, Modal } from '../common';
import { DANGER_GRADES } from '../../constants';

interface ChemicalSubstance {
  id?: number;
  name: string;
  cas_number: string;
  manufacturer: string;
  supplier: string;
  hazard_class: string;
  hazard_level: 'low' | 'medium' | 'high' | 'very_high';
  msds_available: boolean;
  msds_updated_date: string;
  storage_location: string;
  quantity: number;
  unit: string;
  last_inspection_date: string;
  expiry_date?: string;
  safety_measures: string[];
  responsible_person: string;
  notes?: string;
}

interface ChemicalFormProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: Partial<ChemicalSubstance>) => void;
  initialData?: ChemicalSubstance | null;
  mode: 'create' | 'edit';
}

const HAZARD_CLASSES = [
  { value: '인화성 액체', label: '인화성 액체' },
  { value: '독성 물질', label: '독성 물질' },
  { value: '부식성 물질', label: '부식성 물질' },
  { value: '발암성 물질', label: '발암성 물질' },
  { value: '산화성 물질', label: '산화성 물질' },
  { value: '압축가스', label: '압축가스' },
  { value: '폭발성 물질', label: '폭발성 물질' },
  { value: '방사성 물질', label: '방사성 물질' },
  { value: '기타', label: '기타' }
];

const UNITS = [
  { value: 'L', label: 'L (리터)' },
  { value: 'kg', label: 'kg (킬로그램)' },
  { value: 'g', label: 'g (그램)' },
  { value: 'mL', label: 'mL (밀리리터)' },
  { value: 'm³', label: 'm³ (세제곱미터)' },
  { value: '개', label: '개' }
];

export function ChemicalForm({ isOpen, onClose, onSubmit, initialData, mode }: ChemicalFormProps) {
  const [formData, setFormData] = useState<Partial<ChemicalSubstance>>({
    name: '',
    cas_number: '',
    manufacturer: '',
    supplier: '',
    hazard_class: '인화성 액체',
    hazard_level: 'medium',
    msds_available: false,
    msds_updated_date: new Date().toISOString().split('T')[0],
    storage_location: '',
    quantity: 0,
    unit: 'L',
    last_inspection_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    safety_measures: [''],
    responsible_person: '',
    notes: ''
  });

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
    } else {
      // Reset form for create mode
      setFormData({
        name: '',
        cas_number: '',
        manufacturer: '',
        supplier: '',
        hazard_class: '인화성 액체',
        hazard_level: 'medium',
        msds_available: false,
        msds_updated_date: new Date().toISOString().split('T')[0],
        storage_location: '',
        quantity: 0,
        unit: 'L',
        last_inspection_date: new Date().toISOString().split('T')[0],
        expiry_date: '',
        safety_measures: [''],
        responsible_person: '',
        notes: ''
      });
    }
  }, [initialData, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Clean up empty strings from safety_measures array
    const cleanedData = {
      ...formData,
      safety_measures: formData.safety_measures?.filter(measure => measure.trim() !== '') || []
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

  const handleSafetyMeasureChange = (index: number, value: string) => {
    setFormData(prev => ({
      ...prev,
      safety_measures: prev.safety_measures?.map((measure, i) => i === index ? value : measure) || []
    }));
  };

  const addSafetyMeasure = () => {
    setFormData(prev => ({
      ...prev,
      safety_measures: [...(prev.safety_measures || []), '']
    }));
  };

  const removeSafetyMeasure = (index: number) => {
    setFormData(prev => ({
      ...prev,
      safety_measures: prev.safety_measures?.filter((_, i) => i !== index) || []
    }));
  };

  const handleHazardClassChange = (hazardClass: string) => {
    // Set default hazard level based on hazard class
    let defaultLevel: 'low' | 'medium' | 'high' | 'very_high' = 'medium';
    
    switch (hazardClass) {
      case '발암성 물질':
      case '방사성 물질':
      case '폭발성 물질':
        defaultLevel = 'very_high';
        break;
      case '독성 물질':
      case '부식성 물질':
        defaultLevel = 'high';
        break;
      case '인화성 액체':
      case '산화성 물질':
        defaultLevel = 'medium';
        break;
      default:
        defaultLevel = 'low';
    }

    setFormData(prev => ({
      ...prev,
      hazard_class: hazardClass,
      hazard_level: defaultLevel
    }));
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={mode === 'create' ? '화학물질 등록' : '화학물질 정보 수정'}
      size="xl"
    >
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 기본 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              화학물질명 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="예: 아세톤"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              CAS 번호 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="cas_number"
              value={formData.cas_number}
              onChange={handleChange}
              placeholder="예: 67-64-1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              제조사 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="manufacturer"
              value={formData.manufacturer}
              onChange={handleChange}
              placeholder="예: 한국화학 주식회사"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              공급업체 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="supplier"
              value={formData.supplier}
              onChange={handleChange}
              placeholder="예: 산업화학 유통"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              위험 분류 <span className="text-red-500">*</span>
            </label>
            <select
              name="hazard_class"
              value={formData.hazard_class}
              onChange={(e) => handleHazardClassChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {HAZARD_CLASSES.map(hazard => (
                <option key={hazard.value} value={hazard.value}>{hazard.label}</option>
              ))}
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              위험 등급 <span className="text-red-500">*</span>
            </label>
            <select
              name="hazard_level"
              value={formData.hazard_level}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {DANGER_GRADES.map(grade => (
                <option key={grade.value} value={grade.value}>{grade.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* 보관 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              보관 장소 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="storage_location"
              value={formData.storage_location}
              onChange={handleChange}
              placeholder="예: 화학물질 저장소 A동"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              보관량 <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              name="quantity"
              value={formData.quantity}
              onChange={handleChange}
              min="0"
              step="0.1"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              단위 <span className="text-red-500">*</span>
            </label>
            <select
              name="unit"
              value={formData.unit}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            >
              {UNITS.map(unit => (
                <option key={unit.value} value={unit.value}>{unit.label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* 관리 정보 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              관리책임자 <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="responsible_person"
              value={formData.responsible_person}
              onChange={handleChange}
              placeholder="예: 김화학"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              최근 점검일 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="last_inspection_date"
              value={formData.last_inspection_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">유효기간</label>
            <input
              type="date"
              name="expiry_date"
              value={formData.expiry_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              MSDS 업데이트일 <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              name="msds_updated_date"
              value={formData.msds_updated_date}
              onChange={handleChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
            />
          </div>
        </div>

        {/* MSDS 여부 */}
        <div>
          <label className="flex items-center">
            <input
              type="checkbox"
              name="msds_available"
              checked={formData.msds_available}
              onChange={handleChange}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">MSDS (물질안전보건자료) 보유</span>
          </label>
        </div>

        {/* 안전 조치사항 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            안전 조치사항 <span className="text-red-500">*</span>
          </label>
          {formData.safety_measures?.map((measure, index) => (
            <div key={index} className="flex gap-2 mb-2">
              <input
                type="text"
                value={measure}
                onChange={(e) => handleSafetyMeasureChange(index, e.target.value)}
                placeholder="안전 조치사항을 입력하세요 (예: 방화, 환기, 개인보호구 착용)"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                required={index === 0}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => removeSafetyMeasure(index)}
                disabled={formData.safety_measures?.length === 1}
              >
                <Trash2 size={16} />
              </Button>
            </div>
          ))}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={addSafetyMeasure}
            className="flex items-center gap-2"
          >
            <Plus size={16} />
            안전조치 추가
          </Button>
        </div>

        {/* 비고 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">비고</label>
          <textarea
            name="notes"
            value={formData.notes}
            onChange={handleChange}
            rows={3}
            placeholder="특별 주의사항, 보관 조건, 기타 중요 정보를 기록하세요"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {/* 위험 등급별 안내 */}
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
          <h4 className="text-sm font-medium text-orange-900 mb-2">화학물질 위험 등급 기준</h4>
          <div className="text-xs text-orange-700 space-y-1">
            <p>• <strong>매우 높음</strong>: 발암성, 방사성, 폭발성 물질</p>
            <p>• <strong>높음</strong>: 독성, 부식성 물질</p>
            <p>• <strong>보통</strong>: 인화성, 산화성 물질</p>
            <p>• <strong>낮음</strong>: 일반적인 화학물질</p>
          </div>
        </div>

        <div className="flex justify-end gap-3 pt-4">
          <Button variant="secondary" onClick={onClose}>
            <ArrowLeft size={16} />
            취소
          </Button>
          <Button type="submit" icon={<Save size={16} />}>
            {mode === 'create' ? '화학물질 등록' : '수정 완료'}
          </Button>
        </div>
      </form>
    </Modal>
  );
}