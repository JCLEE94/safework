import React, { useState, useRef, useCallback } from 'react';
import { EmbedPDF, useEmbed } from '@simplepdf/react-embed-pdf';
import { API_BASE_URL } from '../../config/api';
import { 
  Upload, 
  Download, 
  FileText, 
  Edit3, 
  Save, 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  X,
  Eye,
  Signature,
  Type,
  Square,
  RotateCw,
  Plus
} from 'lucide-react';

interface PdfForm {
  form_id: string;
  name: string;
  category: string;
  fields: string[];
}

interface FieldInfo {
  name: string;
  label: string;
  type: string;
  required: boolean;
}

interface FormData {
  [key: string]: string;
}

const EnhancedPdfEditor: React.FC = () => {
  const [availableForms, setAvailableForms] = useState<PdfForm[]>([]);
  const [selectedForm, setSelectedForm] = useState<string>('');
  const [formFields, setFormFields] = useState<FieldInfo[]>([]);
  const [fieldValues, setFieldValues] = useState<FormData>({});
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [documentUrl, setDocumentUrl] = useState<string>('');
  const [editMode, setEditMode] = useState<'simple' | 'advanced'>('simple');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [pdfViewerMode, setPdfViewerMode] = useState<'viewer' | 'editor'>('editor');
  const [autoMapping, setAutoMapping] = useState(false);
  const [mappingSuggestions, setMappingSuggestions] = useState<any[]>([]);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { embedRef, actions } = useEmbed();

  // 기존 SafeWork API 호출 함수들 유지
  const fetchAvailableForms = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/pdf-editor/forms/`);
      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        setAvailableForms(data.forms);
      } else {
        throw new Error(data.detail || '양식 목록을 불러올 수 없습니다');
      }
    } catch (error) {
      console.error('양식 목록 로드 실패:', error);
      setError('양식 목록을 불러오는 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const fetchFormFields = async (formId: string) => {
    try {
      setLoading(true);
      const response = await fetch(`/api/v1/pdf-editor/forms/${formId}/fields`);
      const data = await response.json();
      
      if (response.ok && data.status === 'success') {
        setFormFields(data.fields);
        const initialValues: FormData = {};
        data.fields.forEach((field: FieldInfo) => {
          initialValues[field.name] = '';
        });
        setFieldValues(initialValues);
      } else {
        throw new Error(data.detail || '필드 정보를 불러올 수 없습니다');
      }
    } catch (error) {
      console.error('필드 정보 로드 실패:', error);
      setError('필드 정보를 불러오는 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    fetchAvailableForms();
  }, []);

  React.useEffect(() => {
    if (selectedForm) {
      fetchFormFields(selectedForm);
      // 선택된 양식의 템플릿 URL 설정
      setDocumentUrl(`/api/v1/pdf-editor/forms/${selectedForm}/template`);
    } else {
      setFormFields([]);
      setFieldValues({});
      setDocumentUrl('');
    }
  }, [selectedForm]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
      // 업로드된 파일을 위한 Blob URL 생성
      const blobUrl = URL.createObjectURL(file);
      setDocumentUrl(blobUrl);
      setSelectedForm(''); // 업로드 시 기본 양식 선택 해제
      setError(null);
      
      // 자동 필드 감지 옵션이 켜져있으면 필드 감지
      if (autoMapping) {
        setLoading(true);
        const detectionResult = await detectPdfFields(file);
        if (detectionResult) {
          // 감지된 필드 정보 표시
          console.log('감지된 필드:', detectionResult);
          if (detectionResult.auto_detection?.mapped_fields) {
            // 자동 매핑된 필드가 있으면 표시
            setMappingSuggestions(Object.entries(detectionResult.auto_detection.mapped_fields));
            setSuccess(`${Object.keys(detectionResult.auto_detection.mapped_fields).length}개의 필드가 자동으로 감지되었습니다`);
          }
        }
        setLoading(false);
      }
      
      setEditMode('advanced'); // 업로드된 파일은 고급 편집기로
    } else {
      setError('PDF 파일만 업로드 가능합니다');
    }
  };

  const handleFieldChange = (fieldName: string, value: string) => {
    setFieldValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  // SimplePDF Embed 이벤트 핸들러
  const handleEmbedEvent = useCallback((event: any) => {
    console.log('PDF 편집기 이벤트:', event);
    
    switch (event.type) {
      case 'documentLoaded':
        setSuccess('PDF 문서가 성공적으로 로드되었습니다');
        break;
      case 'documentSaved':
        setSuccess('PDF 문서가 저장되었습니다');
        break;
      case 'error':
        setError(`PDF 편집 오류: ${event.message}`);
        break;
    }
  }, []);

  // 고급 편집기 도구 선택
  const selectTool = async (tool: 'TEXT' | 'CHECKBOX' | 'SIGNATURE' | 'IMAGE') => {
    try {
      if (actions && actions.selectTool) {
        await actions.selectTool(tool);
      }
    } catch (error) {
      console.error('도구 선택 실패:', error);
      setError('도구 선택에 실패했습니다');
    }
  };

  // PDF 필드 자동 감지
  const detectPdfFields = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await fetch(`${API_BASE_URL}/api/v1/pdf-auto/detect-fields`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const data = await response.json();
        return data;
      }
    } catch (error) {
      console.error('필드 감지 실패:', error);
    }
    return null;
  };

  // 자동 필드 매핑
  const autoFillPdf = async (file: File, data: Record<string, string>) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('data', JSON.stringify(data));
      
      const response = await fetch(`${API_BASE_URL}/api/v1/pdf-auto/auto-fill`, {
        method: 'POST',
        body: formData
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        setDocumentUrl(url);
        setSuccess('PDF 필드가 자동으로 채워졌습니다');
      }
    } catch (error) {
      console.error('자동 채우기 실패:', error);
      setError('PDF 자동 채우기 중 오류가 발생했습니다');
    }
  };

  // 문서 제출 및 다운로드
  const submitDocument = async (downloadCopy: boolean = true) => {
    try {
      if (actions && actions.submit) {
        await actions.submit({ downloadCopyOnDevice: downloadCopy });
        setSuccess('PDF가 성공적으로 처리되었습니다');
      }
    } catch (error) {
      console.error('문서 제출 실패:', error);
      setError('문서 제출에 실패했습니다');
    }
  };

  // 기존 SafeWork API로 폼 편집
  const handleLegacyFormEdit = async () => {
    if (!selectedForm && !uploadedFile) {
      setError('양식을 선택하거나 PDF 파일을 업로드해주세요');
      return;
    }

    // 필수 필드 검증
    const missingFields = formFields
      .filter(field => field.required && !fieldValues[field.name])
      .map(field => field.label);

    if (missingFields.length > 0) {
      setError(`다음 필수 항목을 입력해주세요: ${missingFields.join(', ')}`);
      return;
    }

    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      let response: Response;

      if (uploadedFile) {
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('field_data', JSON.stringify(fieldValues));

        response = await fetch(`${API_BASE_URL}/api/v1/pdf-editor/upload-and-edit`, {
          method: 'POST',
          body: formData
        });
      } else {
        const formData = new FormData();
        Object.entries(fieldValues).forEach(([key, value]) => {
          formData.append(key, value);
        });

        response = await fetch(`${API_BASE_URL}/api/v1/pdf-editor/forms/${selectedForm}/edit`, {
          method: 'POST',
          body: formData
        });
      }

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `편집된_${selectedForm || 'PDF'}_${new Date().toISOString().slice(0, 10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        setSuccess('PDF가 성공적으로 편집되어 다운로드되었습니다');
        
        // 폼 초기화
        setFieldValues({});
        setUploadedFile(null);
        setSelectedForm('');
        if (fileInputRef.current) {
          fileInputRef.current.value = '';
        }
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'PDF 편집에 실패했습니다');
      }
    } catch (error) {
      console.error('PDF 편집 실패:', error);
      setError(error instanceof Error ? error.message : 'PDF 편집 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = async () => {
    if (!selectedForm) {
      setError('양식을 선택해주세요');
      return;
    }

    try {
      const response = await fetch(`/api/v1/pdf-editor/forms/${selectedForm}/template`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        const form = availableForms.find(f => f.form_id === selectedForm);
        a.download = `${form?.name || 'template'}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        setSuccess('템플릿이 다운로드되었습니다');
      } else {
        throw new Error('템플릿 다운로드에 실패했습니다');
      }
    } catch (error) {
      console.error('템플릿 다운로드 실패:', error);
      setError('템플릿 다운로드 중 오류가 발생했습니다');
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">향상된 PDF 편집기</h1>
              <p className="mt-2 text-gray-600">
                브라우저에서 직접 PDF를 편집하고 양식을 작성하세요
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setEditMode('simple')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  editMode === 'simple'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <FileText className="inline mr-2" size={16} />
                간단 편집
              </button>
              <button
                onClick={() => setEditMode('advanced')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  editMode === 'advanced'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <Edit3 className="inline mr-2" size={16} />
                고급 편집
              </button>
            </div>
          </div>
        </div>

        {/* 알림 메시지 */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-start">
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 mr-2 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-red-800">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        {success && (
          <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-md flex items-start">
            <CheckCircle className="h-5 w-5 text-green-400 mt-0.5 mr-2 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-green-800">{success}</p>
            </div>
            <button onClick={() => setSuccess(null)} className="text-green-400 hover:text-green-600">
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        <div className="p-6">
          {editMode === 'simple' ? (
            // 기존 Simple 편집기 UI
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* 좌측: 양식 선택 및 파일 업로드 */}
              <div className="space-y-6">
                {/* 양식 선택 */}
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <FileText className="mr-2" size={20} />
                    기본 양식 선택
                  </h2>
                  <select
                    value={selectedForm}
                    onChange={(e) => setSelectedForm(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={loading}
                  >
                    <option value="">양식을 선택하세요</option>
                    {availableForms.map((form) => (
                      <option key={form.form_id} value={form.form_id}>
                        {form.name} ({form.category})
                      </option>
                    ))}
                  </select>
                  {selectedForm && (
                    <button
                      onClick={downloadTemplate}
                      className="mt-3 inline-flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
                      disabled={loading}
                    >
                      <Download className="mr-2" size={16} />
                      템플릿 다운로드
                    </button>
                  )}
                </div>

                {/* 파일 업로드 */}
                <div>
                  <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <Upload className="mr-2" size={20} />
                    PDF 파일 업로드
                  </h2>
                  
                  {/* 자동 필드 매핑 토글 */}
                  <div className="mb-4 flex items-center">
                    <input
                      type="checkbox"
                      id="autoMapping"
                      checked={autoMapping}
                      onChange={(e) => setAutoMapping(e.target.checked)}
                      className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <label htmlFor="autoMapping" className="ml-2 text-sm text-gray-700">
                      PDF 필드 자동 감지 및 매핑
                    </label>
                  </div>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf"
                      onChange={handleFileUpload}
                      className="hidden"
                      id="pdf-upload"
                      disabled={loading}
                    />
                    <label
                      htmlFor="pdf-upload"
                      className="cursor-pointer flex flex-col items-center"
                    >
                      <Upload size={48} className="text-gray-400 mb-2" />
                      <span className="text-gray-600">
                        {uploadedFile ? uploadedFile.name : '클릭하여 PDF 파일을 선택하세요'}
                      </span>
                      <span className="text-sm text-gray-500 mt-1">
                        또는 파일을 여기로 드래그하세요
                      </span>
                    </label>
                  </div>
                </div>
                
                {/* 자동 감지된 필드 표시 */}
                {mappingSuggestions.length > 0 && (
                  <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                    <h3 className="text-sm font-semibold text-blue-900 mb-2">
                      자동 감지된 필드 ({mappingSuggestions.length}개)
                    </h3>
                    <div className="space-y-1">
                      {mappingSuggestions.slice(0, 5).map(([key, value]: any, idx) => (
                        <div key={idx} className="text-xs text-blue-700">
                          {value.original_name || key} → {key}
                        </div>
                      ))}
                      {mappingSuggestions.length > 5 && (
                        <div className="text-xs text-blue-600">
                          ... 외 {mappingSuggestions.length - 5}개
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* 우측: 필드 입력 */}
              <div>
                <h2 className="text-lg font-semibold text-gray-900 mb-4">필드 입력</h2>
                
                {formFields.length > 0 ? (
                  <div className="space-y-4 max-h-96 overflow-y-auto pr-2">
                    {formFields.map((field) => (
                      <div key={field.name}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        <input
                          type={field.type === 'date' ? 'date' : field.type === 'number' ? 'number' : 'text'}
                          value={fieldValues[field.name] || ''}
                          onChange={(e) => handleFieldChange(field.name, e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          required={field.required}
                          disabled={loading}
                          placeholder={field.type === 'signature' ? '서명란 (이름 입력)' : ''}
                        />
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <FileText className="mx-auto h-12 w-12 text-gray-400" />
                    <p className="mt-2 text-sm text-gray-600">
                      양식을 선택하거나 PDF 파일을 업로드하면
                    </p>
                    <p className="text-sm text-gray-600">
                      편집 가능한 필드가 표시됩니다
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            // 고급 편집기 UI (SimplePDF Embed)
            <div className="space-y-6">
              {/* 파일 선택 영역 */}
              {!documentUrl && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">기본 양식 선택</h2>
                    <select
                      value={selectedForm}
                      onChange={(e) => setSelectedForm(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">양식을 선택하세요</option>
                      {availableForms.map((form) => (
                        <option key={form.form_id} value={form.form_id}>
                          {form.name} ({form.category})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900 mb-4">PDF 파일 업로드</h2>
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf"
                      onChange={handleFileUpload}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              )}

              {/* 고급 편집기 도구 모음 */}
              {documentUrl && (
                <div className="border-b pb-4">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">편집 도구</h3>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setPdfViewerMode(pdfViewerMode === 'viewer' ? 'editor' : 'viewer')}
                        className={`px-3 py-2 rounded-md text-sm transition-colors ${
                          pdfViewerMode === 'viewer'
                            ? 'bg-green-600 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        <Eye className="inline mr-1" size={14} />
                        {pdfViewerMode === 'viewer' ? '보기 모드' : '편집 모드'}
                      </button>
                    </div>
                  </div>
                  
                  {pdfViewerMode === 'editor' && (
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => selectTool('TEXT')}
                        className="px-3 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors text-sm"
                      >
                        <Type className="inline mr-1" size={14} />
                        텍스트
                      </button>
                      <button
                        onClick={() => selectTool('CHECKBOX')}
                        className="px-3 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors text-sm"
                      >
                        <Square className="inline mr-1" size={14} />
                        체크박스
                      </button>
                      <button
                        onClick={() => selectTool('SIGNATURE')}
                        className="px-3 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors text-sm"
                      >
                        <Signature className="inline mr-1" size={14} />
                        서명
                      </button>
                      <button
                        onClick={() => selectTool('IMAGE')}
                        className="px-3 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700 transition-colors text-sm"
                      >
                        <Plus className="inline mr-1" size={14} />
                        이미지
                      </button>
                      <button
                        onClick={() => submitDocument(true)}
                        className="px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-gray-900 transition-colors text-sm ml-auto"
                      >
                        <Save className="inline mr-1" size={14} />
                        저장 및 다운로드
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* SimplePDF Embed 영역 */}
              {documentUrl && (
                <div className="bg-gray-50 rounded-lg p-4">
                  <EmbedPDF
                    ref={embedRef}
                    mode="inline"
                    style={{ width: '100%', height: '700px', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    documentURL={documentUrl}
                    onEmbedEvent={handleEmbedEvent}
                    companyIdentifier={pdfViewerMode === 'viewer' ? 'react-viewer' : undefined}
                    locale="en"
                  />
                </div>
              )}

              {/* 문서가 없을 때의 안내 메시지 */}
              {!documentUrl && (
                <div className="text-center py-12 bg-gray-50 rounded-lg">
                  <FileText className="mx-auto h-16 w-16 text-gray-400 mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">PDF 편집기가 준비되었습니다</h3>
                  <p className="text-gray-600 mb-4">
                    양식을 선택하거나 PDF 파일을 업로드하여 시작하세요
                  </p>
                  <p className="text-sm text-gray-500">
                    • 텍스트, 체크박스, 서명 추가<br/>
                    • 자동 필드 감지<br/>
                    • 페이지 회전 및 병합<br/>
                    • 브라우저에서 완전한 편집
                  </p>
                </div>
              )}
            </div>
          )}

          {/* 하단 버튼 - Simple 모드일 때만 표시 */}
          {editMode === 'simple' && (formFields.length > 0 || uploadedFile) && (
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleLegacyFormEdit}
                disabled={loading}
                className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="animate-spin mr-2" size={20} />
                    처리 중...
                  </>
                ) : (
                  <>
                    <Save className="mr-2" size={20} />
                    PDF 편집 및 다운로드
                  </>
                )}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EnhancedPdfEditor;