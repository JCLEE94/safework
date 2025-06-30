/**
 * PDF 양식 편집기 컴포넌트
 * Web-based PDF Form Editor
 */

import React, { useState, useEffect } from 'react';
import { 
  FileEdit, Save, Download, Eye, RotateCcw, 
  Calendar, User, Building, MapPin, Phone, Mail,
  Hash, Clock, CheckSquare, AlertCircle
} from 'lucide-react';
import { Card, Button, Badge, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface PDFForm {
  id: string;
  name: string;
  name_korean: string;
  description: string;
  category: string;
  fields: string[];
}

interface FormFieldValue {
  [key: string]: string | number | boolean;
}

interface PDFFormEditorProps {
  form: PDFForm;
  onClose: () => void;
  onSave?: (data: FormFieldValue) => void;
}

// 필드 타입 매핑
const FIELD_TYPES: { [key: string]: string } = {
  'company_name': 'text',
  'department': 'text',
  'manager': 'text',
  'worker_name': 'text',
  'employee_id': 'text',
  'position': 'text',
  'visit_date': 'date',
  'exam_date': 'date',
  'creation_date': 'date',
  'date': 'date',
  'signature_date': 'date',
  'worker_count': 'number',
  'quantity': 'number',
  'quantity_2': 'number',
  'exposure_time': 'number',
  'cas_number': 'text',
  'cas_number_2': 'text',
  'phone': 'tel',
  'email': 'email',
  'description': 'textarea',
  'work_description': 'textarea',
  'counseling_topic': 'textarea',
  'health_issues': 'textarea',
  'work_environment': 'textarea',
  'improvement_suggestions': 'textarea',
  'immediate_actions': 'textarea',
  'follow_up_actions': 'textarea',
  'next_visit_plan': 'textarea',
  'safety_measures': 'textarea',
  'emergency_procedures': 'textarea'
};

// 필드 라벨 매핑
const FIELD_LABELS: { [key: string]: string } = {
  'company_name': '회사명',
  'department': '부서',
  'manager': '관리자',
  'worker_name': '근로자명',
  'employee_id': '사번',
  'position': '직위',
  'visit_date': '방문일자',
  'exam_date': '검진일자',
  'creation_date': '작성일자',
  'date': '일자',
  'signature_date': '서명일자',
  'worker_count': '근로자 수',
  'quantity': '수량',
  'quantity_2': '수량2',
  'exposure_time': '노출시간',
  'cas_number': 'CAS 번호',
  'cas_number_2': 'CAS 번호2',
  'site_name': '현장명',
  'counselor': '상담자',
  'work_type': '작업종류',
  'participant_1': '참석자1',
  'participant_2': '참석자2',
  'participant_3': '참석자3',
  'participant_4': '참석자4',
  'counseling_topic': '상담주제',
  'health_issues': '건강문제',
  'work_environment': '작업환경',
  'improvement_suggestions': '개선제안',
  'immediate_actions': '즉시조치',
  'follow_up_actions': '후속조치',
  'next_visit_plan': '다음방문계획',
  'counselor_signature': '상담자서명',
  'manager_signature': '관리자서명',
  'chemical_name': '화학물질명',
  'chemical_name_2': '화학물질명2',
  'manufacturer': '제조회사',
  'manufacturer_2': '제조회사2',
  'usage': '용도',
  'usage_2': '용도2',
  'storage_location': '보관장소',
  'storage_location_2': '보관장소2',
  'hazard_class': '위험등급',
  'hazard_class_2': '위험등급2',
  'msds_date': 'MSDS 일자',
  'msds_version': 'MSDS 버전',
  'update_date': '갱신일자',
  'safety_measures': '안전조치',
  'emergency_procedures': '응급처치',
  'prepared_by': '작성자',
  'approved_by': '승인자',
  'year': '연도',
  'exam_agency': '검진기관',
  'exam_result': '검진결과',
  'opinion': '의견',
  'substance_name': '물질명',
  'work_date': '작업일자',
  'protection_equipment': '보호장비'
};

// 필드 아이콘 매핑
const getFieldIcon = (fieldName: string) => {
  if (fieldName.includes('date')) return Calendar;
  if (fieldName.includes('name') || fieldName.includes('worker')) return User;
  if (fieldName.includes('company') || fieldName.includes('department')) return Building;
  if (fieldName.includes('location') || fieldName.includes('site')) return MapPin;
  if (fieldName.includes('phone')) return Phone;
  if (fieldName.includes('email') || fieldName.includes('mail')) return Mail;
  if (fieldName.includes('number') || fieldName.includes('count') || fieldName.includes('quantity')) return Hash;
  if (fieldName.includes('time') || fieldName.includes('hour')) return Clock;
  if (fieldName.includes('signature') || fieldName.includes('approved')) return CheckSquare;
  return FileEdit;
};

export function PDFFormEditor({ form, onClose, onSave }: PDFFormEditorProps) {
  const [formData, setFormData] = useState<FormFieldValue>({});
  const [loading, setLoading] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});
  
  const { fetchApi } = useApi();

  // 초기 데이터 로드
  useEffect(() => {
    const initialData: FormFieldValue = {};
    form.fields.forEach(field => {
      if (field.includes('date')) {
        initialData[field] = new Date().toISOString().split('T')[0];
      } else {
        initialData[field] = '';
      }
    });
    setFormData(initialData);
  }, [form]);

  const handleFieldChange = (fieldName: string, value: string | number | boolean) => {
    setFormData(prev => ({
      ...prev,
      [fieldName]: value
    }));
    
    // 에러 제거
    if (errors[fieldName]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[fieldName];
        return newErrors;
      });
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};
    
    // 필수 필드 검증
    const requiredFields = ['company_name', 'date', 'worker_name'];
    requiredFields.forEach(field => {
      if (form.fields.includes(field) && !formData[field]) {
        newErrors[field] = '필수 입력 항목입니다.';
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = async () => {
    if (!validateForm()) {
      alert('필수 항목을 모두 입력해주세요.');
      return;
    }

    setLoading(true);
    try {
      const response = await fetchApi(`/api/v1/documents/fill-pdf/${form.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          entries: [formData]  // 백엔드에서 기대하는 형식
        }),
      });

      if (response.status === 'success') {
        // JSON 응답을 텍스트 파일로 다운로드 (임시)
        const jsonString = JSON.stringify(response, null, 2);
        const blob = new Blob([jsonString], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${form.name_korean}_${new Date().toISOString().split('T')[0]}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert(`양식이 성공적으로 처리되었습니다.
처리된 필드: ${response.processed_fields.length}개`);
      }

      onSave?.(formData);
      alert('PDF가 성공적으로 생성되었습니다.');
    } catch (error) {
      console.error('PDF 생성 실패:', error);
      alert('PDF 생성 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = () => {
    if (!validateForm()) {
      alert('필수 항목을 모두 입력해주세요.');
      return;
    }
    setPreviewMode(true);
  };

  const handleReset = () => {
    if (confirm('입력한 내용을 모두 초기화하시겠습니까?')) {
      const resetData: FormFieldValue = {};
      form.fields.forEach(field => {
        if (field.includes('date')) {
          resetData[field] = new Date().toISOString().split('T')[0];
        } else {
          resetData[field] = '';
        }
      });
      setFormData(resetData);
      setErrors({});
    }
  };

  const renderField = (fieldName: string) => {
    const fieldType = FIELD_TYPES[fieldName] || 'text';
    const label = FIELD_LABELS[fieldName] || fieldName;
    const Icon = getFieldIcon(fieldName);
    const hasError = !!errors[fieldName];
    
    const commonProps = {
      id: fieldName,
      value: formData[fieldName] || '',
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => 
        handleFieldChange(fieldName, e.target.value),
      className: `w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
        hasError ? 'border-red-300 bg-red-50' : 'border-gray-300'
      }`,
      placeholder: `${label} 입력`
    };

    return (
      <div key={fieldName} className="space-y-2">
        <label htmlFor={fieldName} className="flex items-center text-sm font-medium text-gray-700">
          <Icon size={16} className="mr-2 text-gray-500" />
          {label}
          {['company_name', 'date', 'worker_name'].includes(fieldName) && (
            <span className="text-red-500 ml-1">*</span>
          )}
        </label>
        
        {fieldType === 'textarea' ? (
          <textarea
            {...commonProps}
            rows={3}
          />
        ) : fieldType === 'number' ? (
          <input
            {...commonProps}
            type="number"
            min="0"
            onChange={(e) => handleFieldChange(fieldName, parseInt(e.target.value) || 0)}
          />
        ) : (
          <input
            {...commonProps}
            type={fieldType}
          />
        )}
        
        {hasError && (
          <p className="text-sm text-red-600 flex items-center">
            <AlertCircle size={14} className="mr-1" />
            {errors[fieldName]}
          </p>
        )}
      </div>
    );
  };

  if (previewMode) {
    return (
      <Modal onClose={() => setPreviewMode(false)}>
        <div className="max-w-4xl mx-auto p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold">{form.name_korean} - 미리보기</h2>
            <div className="flex gap-2">
              <Button onClick={handleSave} disabled={loading}>
                <Download size={16} className="mr-2" />
                PDF 생성
              </Button>
              <Button variant="outline" onClick={() => setPreviewMode(false)}>
                수정하기
              </Button>
            </div>
          </div>
          
          <Card className="p-6">
            <div className="space-y-4">
              {form.fields.map(field => {
                const label = FIELD_LABELS[field] || field;
                const value = formData[field];
                
                return (
                  <div key={field} className="flex justify-between py-2 border-b border-gray-100">
                    <span className="font-medium text-gray-700">{label}:</span>
                    <span className="text-gray-900">{value || '-'}</span>
                  </div>
                );
              })}
            </div>
          </Card>
        </div>
      </Modal>
    );
  }

  return (
    <Modal onClose={onClose}>
      <div className="max-w-4xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div className="flex items-center">
            <FileEdit className="text-green-600 mr-3" size={24} />
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{form.name_korean}</h2>
              <p className="text-sm text-gray-600">{form.description}</p>
            </div>
          </div>
          <Badge color="blue">{form.fields.length}개 필드</Badge>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="flex gap-2">
            <Button onClick={handlePreview} variant="outline" disabled={loading}>
              <Eye size={16} className="mr-2" />
              미리보기
            </Button>
            <Button onClick={handleReset} variant="outline">
              <RotateCcw size={16} className="mr-2" />
              초기화
            </Button>
          </div>
          <Button onClick={handleSave} disabled={loading}>
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                생성 중...
              </>
            ) : (
              <>
                <Save size={16} className="mr-2" />
                PDF 생성
              </>
            )}
          </Button>
        </div>

        {/* Form Fields */}
        <Card className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {form.fields.map(renderField)}
          </div>
        </Card>

        {/* Required Fields Notice */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700">
            <AlertCircle size={14} className="inline mr-1" />
            <span className="text-red-500">*</span> 표시된 항목은 필수 입력 항목입니다.
          </p>
        </div>
      </div>
    </Modal>
  );
}