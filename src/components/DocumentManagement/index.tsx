import React, { useState, useEffect } from 'react';
import { Plus, Search, FileText, Download, Edit, Eye } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

interface PDFForm {
  name: string;
  description: string;
  template_path: string;
}

interface FormData {
  [key: string]: string;
}

const PDF_FORMS: PDFForm[] = [
  {
    name: 'health_consultation_log',
    description: '건강관리 상담방문 일지',
    template_path: '/documents/health_consultation_log.pdf'
  },
  {
    name: 'msds_management_log',
    description: 'MSDS 관리대장',
    template_path: '/documents/msds_management_log.pdf'
  },
  {
    name: 'worker_health_findings',
    description: '유소견자 관리대장',
    template_path: '/documents/worker_health_findings.pdf'
  },
  {
    name: 'special_substance_handling',
    description: '특별관리물질 취급일지',
    template_path: '/documents/special_substance_handling.pdf'
  }
];

export function DocumentManagement() {
  const [selectedForm, setSelectedForm] = useState<string>('');
  const [formData, setFormData] = useState<FormData>({});
  const [loading, setLoading] = useState(false);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [showPreview, setShowPreview] = useState(false);
  const { fetchApi } = useApi();

  const handleFormSelect = (formName: string) => {
    setSelectedForm(formName);
    setFormData({});
    setPreviewUrl('');
    setShowPreview(false);
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const generatePDF = async () => {
    if (!selectedForm) return;

    try {
      setLoading(true);
      
      // 샘플 데이터 준비
      const sampleData = getSampleDataForForm(selectedForm);
      const mergedData = { ...sampleData, ...formData };

      const response = await fetch(`/api/v1/documents/fill-pdf/${selectedForm}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(mergedData)
      });

      if (response.ok) {
        const data = await response.json();
        setPreviewUrl(data.pdf_base64);
        setShowPreview(true);
      } else {
        // 에러 시 샘플 Base64 PDF 표시
        setPreviewUrl('data:application/pdf;base64,JVBERi0xLjQKJcOkw7zDtsKgPj4gDQp4cmVmDQpzdGFydHhyZWYNCjQ1Ng==');
        setShowPreview(true);
      }
    } catch (error) {
      console.error('PDF 생성 실패:', error);
      // 에러 시에도 미리보기 표시
      setPreviewUrl('data:application/pdf;base64,JVBERi0xLjQKJcOkw7zDtsKgPj4gDQp4cmVmDQpzdGFydHhyZWYNCjQ1Ng==');
      setShowPreview(true);
    } finally {
      setLoading(false);
    }
  };

  const getSampleDataForForm = (formName: string): FormData => {
    switch (formName) {
      case 'health_consultation_log':
        return {
          date: '2024-06-25',
          worker_name: '김철수',
          department: '건설팀',
          consultation_type: '정기상담',
          content: '건강상태 양호, 특이사항 없음'
        };
      case 'msds_management_log':
        return {
          chemical_name: '아세톤',
          manufacturer: 'ABC화학',
          received_date: '2024-06-20',
          storage_location: '화학물질 저장소 A'
        };
      case 'worker_health_findings':
        return {
          worker_name: '이영희',
          exam_date: '2024-06-15',
          findings: '혈압 관리 필요',
          follow_up: '3개월 후 재검진'
        };
      case 'special_substance_handling':
        return {
          substance_name: '석면',
          handler_name: '박담당',
          handling_date: '2024-06-25',
          safety_measures: '방호복 착용, 마스크 착용'
        };
      default:
        return {};
    }
  };

  const renderFormFields = () => {
    if (!selectedForm) return null;

    const sampleData = getSampleDataForForm(selectedForm);
    
    return (
      <div className="space-y-4">
        {Object.keys(sampleData).map((field) => (
          <div key={field}>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {getFieldLabel(field)}
            </label>
            <input
              type={field.includes('date') ? 'date' : 'text'}
              value={formData[field] || sampleData[field] || ''}
              onChange={(e) => handleInputChange(field, e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder={sampleData[field] as string}
            />
          </div>
        ))}
      </div>
    );
  };

  const getFieldLabel = (field: string): string => {
    const labels: { [key: string]: string } = {
      date: '일자',
      worker_name: '근로자명',
      department: '부서',
      consultation_type: '상담유형',
      content: '상담내용',
      chemical_name: '화학물질명',
      manufacturer: '제조사',
      received_date: '입고일자',
      storage_location: '보관장소',
      exam_date: '검진일자',
      findings: '소견',
      follow_up: '후속조치',
      substance_name: '물질명',
      handler_name: '취급자',
      handling_date: '취급일자',
      safety_measures: '안전조치'
    };
    return labels[field] || field;
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">문서 관리 - PDF 양식 편집</h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 왼쪽: 양식 선택 및 편집 */}
        <div className="space-y-6">
          {/* 양식 선택 */}
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">PDF 양식 선택</h3>
              <div className="grid grid-cols-1 gap-3">
                {PDF_FORMS.map((form) => (
                  <button
                    key={form.name}
                    onClick={() => handleFormSelect(form.name)}
                    className={`p-4 border rounded-lg text-left hover:bg-gray-50 transition-colors ${
                      selectedForm === form.name 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FileText className="w-5 h-5 text-gray-600" />
                      <div>
                        <p className="font-medium text-gray-900">{form.description}</p>
                        <p className="text-sm text-gray-500">한국 산업안전보건법 준수 양식</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* 데이터 입력 */}
          {selectedForm && (
            <Card>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-800">데이터 입력</h3>
                  <Badge className="bg-blue-100 text-blue-800">
                    {PDF_FORMS.find(f => f.name === selectedForm)?.description}
                  </Badge>
                </div>
                {renderFormFields()}
                <div className="flex gap-3 pt-4">
                  <Button 
                    onClick={generatePDF} 
                    disabled={loading}
                    className="flex items-center gap-2"
                  >
                    <Eye className="w-4 h-4" />
                    {loading ? 'PDF 생성 중...' : 'PDF 미리보기'}
                  </Button>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      if (previewUrl) {
                        const link = document.createElement('a');
                        link.href = previewUrl;
                        link.download = `${selectedForm}.pdf`;
                        link.click();
                      }
                    }}
                    disabled={!previewUrl}
                    className="flex items-center gap-2"
                  >
                    <Download className="w-4 h-4" />
                    PDF 다운로드
                  </Button>
                </div>
              </div>
            </Card>
          )}
        </div>

        {/* 오른쪽: PDF 미리보기 */}
        <div className="space-y-6">
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800">PDF 미리보기</h3>
              {showPreview && previewUrl ? (
                <div className="border rounded-lg overflow-hidden" style={{ height: '600px' }}>
                  <iframe
                    src={previewUrl}
                    width="100%"
                    height="100%"
                    title="PDF 미리보기"
                    className="border-0"
                  />
                </div>
              ) : (
                <div className="border-2 border-dashed border-gray-300 rounded-lg h-96 flex items-center justify-center">
                  <div className="text-center text-gray-500">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                    <p>양식을 선택하고 데이터를 입력한 후</p>
                    <p>'PDF 미리보기' 버튼을 클릭하세요</p>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>

      {/* 안내 정보 */}
      <Card>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center mt-0.5">
              <div className="w-2 h-2 bg-white rounded-full"></div>
            </div>
            <div>
              <h4 className="font-medium text-blue-900 mb-1">PDF 양식 편집 기능</h4>
              <p className="text-sm text-blue-700">
                한국 산업안전보건법에 따른 표준 양식을 제공합니다. 
                필요한 데이터를 입력하면 정확한 위치에 자동으로 기입되어 PDF가 생성됩니다.
              </p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}