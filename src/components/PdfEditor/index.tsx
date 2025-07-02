import React, { useState, useEffect } from 'react';
import { Upload, Download, Edit3, Save, FileText, X, Plus } from 'lucide-react';

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

interface TextEdit {
  x: number;
  y: number;
  text: string;
  font_size: number;
}

const PdfEditor: React.FC = () => {
  const [availableForms, setAvailableForms] = useState<PdfForm[]>([]);
  const [selectedForm, setSelectedForm] = useState<string>('');
  const [formFields, setFormFields] = useState<FieldInfo[]>([]);
  const [fieldValues, setFieldValues] = useState<Record<string, string>>({});
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [textEdits, setTextEdits] = useState<TextEdit[]>([]);
  const [loading, setLoading] = useState(false);

  // 사용 가능한 양식 목록 로드
  useEffect(() => {
    fetchAvailableForms();
  }, []);

  // 선택된 양식의 필드 정보 로드
  useEffect(() => {
    if (selectedForm) {
      fetchFormFields(selectedForm);
    }
  }, [selectedForm]);

  const fetchAvailableForms = async () => {
    try {
      const response = await fetch('/api/v1/pdf-editor/forms/');
      const data = await response.json();
      if (data.status === 'success') {
        setAvailableForms(data.forms);
      }
    } catch (error) {
      console.error('양식 목록 로드 실패:', error);
    }
  };

  const fetchFormFields = async (formId: string) => {
    try {
      const response = await fetch(`/api/v1/pdf-editor/forms/${formId}/fields`);
      const data = await response.json();
      if (data.status === 'success') {
        setFormFields(data.fields);
        // 필드값 초기화
        const initialValues: Record<string, string> = {};
        data.fields.forEach((field: FieldInfo) => {
          initialValues[field.name] = '';
        });
        setFieldValues(initialValues);
      }
    } catch (error) {
      console.error('필드 정보 로드 실패:', error);
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
      setSelectedForm(''); // 업로드 시 기본 양식 선택 해제
    } else {
      alert('PDF 파일만 업로드 가능합니다.');
    }
  };

  const handleFieldChange = (fieldName: string, value: string) => {
    setFieldValues(prev => ({
      ...prev,
      [fieldName]: value
    }));
  };

  const handleFormEdit = async () => {
    if (!selectedForm && !uploadedFile) {
      alert('양식을 선택하거나 PDF 파일을 업로드해주세요.');
      return;
    }

    setLoading(true);
    try {
      let response: Response;

      if (uploadedFile) {
        // 업로드된 파일 편집
        const formData = new FormData();
        formData.append('file', uploadedFile);
        formData.append('field_data', JSON.stringify(fieldValues));

        response = await fetch('/api/v1/pdf-editor/upload-and-edit', {
          method: 'POST',
          body: formData
        });
      } else {
        // 기본 양식 편집
        const formData = new FormData();
        Object.entries(fieldValues).forEach(([key, value]) => {
          formData.append(key, value);
        });

        response = await fetch(`/api/v1/pdf-editor/forms/${selectedForm}/edit`, {
          method: 'POST',
          body: formData
        });
      }

      if (response.ok) {
        // PDF 다운로드
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `편집된_문서_${new Date().toISOString().slice(0, 10)}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const errorData = await response.json();
        alert(`편집 실패: ${errorData.detail}`);
      }
    } catch (error) {
      console.error('PDF 편집 실패:', error);
      alert('PDF 편집 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const downloadTemplate = async () => {
    if (!selectedForm) {
      alert('양식을 선택해주세요.');
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
        a.download = `${form?.name || 'template'}.xlsx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('템플릿 다운로드 실패:', error);
    }
  };

  const addTextEdit = () => {
    setTextEdits(prev => [...prev, {
      x: 100,
      y: 700,
      text: '',
      font_size: 12
    }]);
  };

  const updateTextEdit = (index: number, field: keyof TextEdit, value: string | number) => {
    setTextEdits(prev => prev.map((edit, i) => 
      i === index ? { ...edit, [field]: value } : edit
    ));
  };

  const removeTextEdit = (index: number) => {
    setTextEdits(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">PDF 편집기</h1>
        <p className="text-gray-600">건설업 보건관리 양식을 편집하고 생성하세요.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* 좌측: 양식 선택 및 파일 업로드 */}
        <div className="space-y-6">
          {/* 양식 선택 */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <FileText className="mr-2" size={20} />
              기본 양식 선택
            </h2>
            <select
              value={selectedForm}
              onChange={(e) => setSelectedForm(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
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
                className="mt-3 flex items-center px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition-colors"
              >
                <Download className="mr-2" size={16} />
                템플릿 다운로드
              </button>
            )}
          </div>

          {/* 파일 업로드 */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Upload className="mr-2" size={20} />
              PDF 파일 업로드
            </h2>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="pdf-upload"
              />
              <label
                htmlFor="pdf-upload"
                className="cursor-pointer flex flex-col items-center"
              >
                <Upload size={48} className="text-gray-400 mb-2" />
                <span className="text-gray-600">
                  {uploadedFile ? uploadedFile.name : 'PDF 파일을 선택하세요'}
                </span>
              </label>
            </div>
            {uploadedFile && (
              <button
                onClick={() => setUploadedFile(null)}
                className="mt-3 flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
              >
                <X className="mr-2" size={16} />
                파일 제거
              </button>
            )}
          </div>

          {/* 고급 편집 옵션 */}
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <Edit3 className="mr-2" size={20} />
              고급 편집 옵션
            </h2>
            <button
              onClick={addTextEdit}
              className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors"
            >
              <Plus className="mr-2" size={16} />
              텍스트 추가
            </button>
            
            {textEdits.map((edit, index) => (
              <div key={index} className="mt-4 p-4 bg-white rounded border">
                <div className="flex justify-between items-center mb-2">
                  <span className="font-medium">텍스트 {index + 1}</span>
                  <button
                    onClick={() => removeTextEdit(index)}
                    className="text-red-600 hover:text-red-800"
                  >
                    <X size={16} />
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="number"
                    placeholder="X 좌표"
                    value={edit.x}
                    onChange={(e) => updateTextEdit(index, 'x', parseInt(e.target.value) || 0)}
                    className="p-2 border rounded"
                  />
                  <input
                    type="number"
                    placeholder="Y 좌표"
                    value={edit.y}
                    onChange={(e) => updateTextEdit(index, 'y', parseInt(e.target.value) || 0)}
                    className="p-2 border rounded"
                  />
                </div>
                <input
                  type="text"
                  placeholder="텍스트 내용"
                  value={edit.text}
                  onChange={(e) => updateTextEdit(index, 'text', e.target.value)}
                  className="w-full mt-2 p-2 border rounded"
                />
                <input
                  type="number"
                  placeholder="폰트 크기"
                  value={edit.font_size}
                  onChange={(e) => updateTextEdit(index, 'font_size', parseInt(e.target.value) || 12)}
                  className="w-full mt-2 p-2 border rounded"
                />
              </div>
            ))}
          </div>
        </div>

        {/* 우측: 필드 입력 */}
        <div className="space-y-6">
          <div className="bg-gray-50 p-6 rounded-lg">
            <h2 className="text-xl font-semibold mb-4">필드 입력</h2>
            
            {formFields.length > 0 ? (
              <div className="space-y-4">
                {formFields.map((field) => (
                  <div key={field.name}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {field.label}
                      {field.required && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {field.type === 'date' ? (
                      <input
                        type="date"
                        value={fieldValues[field.name] || ''}
                        onChange={(e) => handleFieldChange(field.name, e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required={field.required}
                      />
                    ) : field.type === 'number' ? (
                      <input
                        type="number"
                        value={fieldValues[field.name] || ''}
                        onChange={(e) => handleFieldChange(field.name, e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required={field.required}
                      />
                    ) : field.type === 'signature' ? (
                      <div className="relative">
                        <input
                          type="text"
                          value={fieldValues[field.name] || ''}
                          onChange={(e) => handleFieldChange(field.name, e.target.value)}
                          placeholder="서명란 (이름 입력)"
                          className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                          required={field.required}
                        />
                        <span className="absolute right-3 top-3 text-gray-400 text-sm">✍️</span>
                      </div>
                    ) : (
                      <input
                        type="text"
                        value={fieldValues[field.name] || ''}
                        onChange={(e) => handleFieldChange(field.name, e.target.value)}
                        className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                        required={field.required}
                      />
                    )}
                  </div>
                ))}
              </div>
            ) : uploadedFile ? (
              <div className="space-y-4">
                <p className="text-gray-600 mb-4">업로드된 PDF에 추가할 정보를 입력하세요:</p>
                {['company_name', 'date', 'manager', 'notes'].map((fieldName) => (
                  <div key={fieldName}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {fieldName === 'company_name' ? '회사명' :
                       fieldName === 'date' ? '날짜' :
                       fieldName === 'manager' ? '담당자' : '비고'}
                    </label>
                    <input
                      type={fieldName === 'date' ? 'date' : 'text'}
                      value={fieldValues[fieldName] || ''}
                      onChange={(e) => handleFieldChange(fieldName, e.target.value)}
                      className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-8">
                양식을 선택하거나 PDF 파일을 업로드하면<br />
                편집 가능한 필드가 표시됩니다.
              </p>
            )}

            {(formFields.length > 0 || uploadedFile) && (
              <button
                onClick={handleFormEdit}
                disabled={loading}
                className="w-full mt-6 flex items-center justify-center px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                ) : (
                  <Save className="mr-2" size={20} />
                )}
                {loading ? '편집 중...' : 'PDF 편집 및 다운로드'}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default PdfEditor;