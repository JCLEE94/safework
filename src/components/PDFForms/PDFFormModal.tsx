import React, { useState, useEffect } from 'react';
import { Save, ArrowLeft, FileText, Download, Eye } from 'lucide-react';
import { Button, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface PDFForm {
  id: string;
  name: string;
  name_korean: string;
  description: string;
  category: string;
}

interface FormField {
  name: string;
  label: string;
  type: string;
  required: boolean;
}

interface PDFFormModalProps {
  isOpen: boolean;
  onClose: () => void;
  form: PDFForm;
}

// 양식별 기본 필드 정의
const FORM_FIELD_CONFIGS = {
  "유소견자_관리대장": [
    { name: "company_name", label: "회사명", type: "text", required: true },
    { name: "department", label: "부서", type: "text", required: false },
    { name: "year", label: "년도", type: "text", required: true },
    { name: "worker_name", label: "근로자명", type: "text", required: true },
    { name: "employee_id", label: "사번", type: "text", required: true },
    { name: "position", label: "직책", type: "text", required: false },
    { name: "exam_date", label: "검진일", type: "date", required: true },
    { name: "exam_agency", label: "검진기관", type: "text", required: false },
    { name: "exam_result", label: "검진결과", type: "select", required: true, options: ["정상", "요관찰", "유소견", "치료요구"] },
    { name: "opinion", label: "의견", type: "textarea", required: false },
    { name: "manager_signature", label: "관리자 서명", type: "text", required: false }
  ],
  "MSDS_관리대장": [
    { name: "company_name", label: "회사명", type: "text", required: true },
    { name: "department", label: "부서", type: "text", required: false },
    { name: "manager", label: "관리자", type: "text", required: true },
    { name: "chemical_name", label: "화학물질명", type: "text", required: true },
    { name: "manufacturer", label: "제조업체", type: "text", required: true },
    { name: "cas_number", label: "CAS 번호", type: "text", required: false },
    { name: "usage", label: "용도", type: "text", required: false },
    { name: "quantity", label: "사용량", type: "text", required: false },
    { name: "storage_location", label: "보관장소", type: "text", required: false },
    { name: "hazard_class", label: "유해성 분류", type: "text", required: false },
    { name: "msds_date", label: "MSDS 작성일", type: "date", required: false },
    { name: "update_date", label: "갱신일", type: "date", required: false },
    { name: "safety_measures", label: "안전조치사항", type: "textarea", required: false }
  ],
  "건강관리_상담방문_일지": [
    { name: "visit_date", label: "방문일자", type: "date", required: true },
    { name: "site_name", label: "현장명", type: "text", required: true },
    { name: "counselor", label: "상담자", type: "text", required: true },
    { name: "work_type", label: "작업종류", type: "text", required: false },
    { name: "worker_count", label: "작업인원", type: "number", required: false },
    { name: "counseling_topic", label: "상담주제", type: "text", required: false },
    { name: "health_issues", label: "건강문제", type: "textarea", required: false },
    { name: "work_environment", label: "작업환경", type: "textarea", required: false },
    { name: "improvement_suggestions", label: "개선사항", type: "textarea", required: false },
    { name: "immediate_actions", label: "즉시조치사항", type: "textarea", required: false },
    { name: "follow_up_actions", label: "사후조치사항", type: "textarea", required: false },
    { name: "next_visit_plan", label: "다음방문계획", type: "textarea", required: false }
  ],
  "특별관리물질_취급일지": [
    { name: "work_date", label: "작업일자", type: "date", required: true },
    { name: "department", label: "부서", type: "text", required: false },
    { name: "weather", label: "날씨", type: "text", required: false },
    { name: "chemical_name", label: "특별관리물질명", type: "text", required: true },
    { name: "manufacturer", label: "제조업체", type: "text", required: false },
    { name: "cas_number", label: "CAS 번호", type: "text", required: false },
    { name: "work_location", label: "작업장소", type: "text", required: true },
    { name: "work_content", label: "작업내용", type: "textarea", required: true },
    { name: "worker_name", label: "작업자명", type: "text", required: true },
    { name: "worker_id", label: "사번", type: "text", required: false },
    { name: "start_time", label: "시작시간", type: "time", required: false },
    { name: "end_time", label: "종료시간", type: "time", required: false },
    { name: "quantity_used", label: "사용량", type: "text", required: false },
    { name: "safety_procedures", label: "안전절차", type: "textarea", required: false },
    { name: "health_symptoms", label: "건강증상", type: "textarea", required: false }
  ]
};

export function PDFFormModal({ isOpen, onClose, form }: PDFFormModalProps) {
  const [formData, setFormData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  
  const { fetchApi } = useApi();

  const formFields = FORM_FIELD_CONFIGS[form.id as keyof typeof FORM_FIELD_CONFIGS] || [];

  useEffect(() => {
    if (isOpen) {
      // 초기 데이터 설정
      const initialData: Record<string, any> = {};
      formFields.forEach(field => {
        if (field.type === 'date') {
          initialData[field.name] = new Date().toISOString().split('T')[0];
        } else {
          initialData[field.name] = '';
        }
      });
      setFormData(initialData);
      setShowPreview(false);
      setPreviewUrl(null);
    }
  }, [isOpen, form.id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handlePreview = async () => {
    try {
      setLoading(true);
      
      const requestData = {
        entries: [formData]
      };

      const response = await fetch(`/api/v1/documents/preview-base64/${form.id}`, {
        method: 'GET'
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewUrl(data.data_uri);
        setShowPreview(true);
      } else {
        console.error('미리보기 생성 실패');
      }
    } catch (error) {
      console.error('미리보기 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (action: 'download' | 'preview') => {
    try {
      setLoading(true);

      const requestData = {
        entries: [formData]
      };

      if (action === 'download') {
        const response = await fetch(`/api/v1/documents/fill-pdf/${form.id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        });

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `${form.name_korean}_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(a);
          a.click();
          window.URL.revokeObjectURL(url);
          document.body.removeChild(a);
          onClose();
        }
      } else if (action === 'preview') {
        await handlePreview();
      }
    } catch (error) {
      console.error('PDF 생성 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderField = (field: any) => {
    const commonProps = {
      name: field.name,
      value: formData[field.name] || '',
      onChange: handleChange,
      className: "w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent",
      required: field.required
    };

    switch (field.type) {
      case 'textarea':
        return (
          <textarea
            {...commonProps}
            rows={3}
            placeholder={`${field.label} 입력`}
          />
        );
      case 'select':
        return (
          <select {...commonProps}>
            <option value="">{field.label} 선택</option>
            {field.options?.map((option: string) => (
              <option key={option} value={option}>{option}</option>
            ))}
          </select>
        );
      case 'date':
        return <input {...commonProps} type="date" />;
      case 'time':
        return <input {...commonProps} type="time" />;
      case 'number':
        return <input {...commonProps} type="number" placeholder={`${field.label} 입력`} />;
      default:
        return <input {...commonProps} type="text" placeholder={`${field.label} 입력`} />;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`${form.name_korean} 작성`}
      size="xl"
    >
      <div className="space-y-6">
        {/* 양식 정보 */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <div className="flex items-center mb-2">
            <FileText className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-blue-800">{form.name_korean}</h3>
          </div>
          <p className="text-blue-700 text-sm">{form.description}</p>
        </div>

        {/* 양식 작성 영역 */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {formFields.map((field) => (
            <div key={field.name} className={field.type === 'textarea' ? 'md:col-span-2' : ''}>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {field.label}
                {field.required && <span className="text-red-500 ml-1">*</span>}
              </label>
              {renderField(field)}
            </div>
          ))}
        </div>

        {/* 미리보기 영역 */}
        {showPreview && previewUrl && (
          <div className="border rounded-lg p-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-3">PDF 미리보기</h3>
            <div className="border border-gray-300 rounded-lg overflow-hidden" style={{ height: '500px' }}>
              <iframe
                src={previewUrl}
                width="100%"
                height="100%"
                title="PDF 미리보기"
                className="border-0"
              />
            </div>
          </div>
        )}

        {/* 액션 버튼 */}
        <div className="flex justify-between pt-4 border-t">
          <Button variant="secondary" onClick={onClose}>
            <ArrowLeft size={16} className="mr-1" />
            취소
          </Button>
          
          <div className="flex gap-3">
            <Button
              variant="outline"
              onClick={() => handleSubmit('preview')}
              disabled={loading}
            >
              <Eye size={16} className="mr-1" />
              {loading ? '생성 중...' : '미리보기'}
            </Button>
            
            <Button
              onClick={() => handleSubmit('download')}
              disabled={loading}
              icon={<Download size={16} />}
            >
              {loading ? '생성 중...' : 'PDF 다운로드'}
            </Button>
          </div>
        </div>

        {/* 로딩 상태 */}
        {loading && (
          <div className="flex items-center justify-center py-4">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            <span className="ml-2 text-gray-600">PDF를 생성하고 있습니다...</span>
          </div>
        )}
      </div>
    </Modal>
  );
}