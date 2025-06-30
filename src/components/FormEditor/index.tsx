/**
 * 웹 기반 양식 편집기
 * Web-based Form Editor for SafeWork Pro
 */

import React, { useState, useEffect } from 'react';
import { 
  Save, X, Plus, Trash2, Edit3, Eye, FileText, 
  ArrowLeft, Check, AlertCircle, Copy
} from 'lucide-react';
import { Card, Button, Badge, Modal } from '../common';

interface FormField {
  id: string;
  name: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'textarea' | 'select' | 'checkbox';
  value: string;
  required: boolean;
  placeholder?: string;
  options?: string[];
  position?: { x: number; y: number };
}

interface FormData {
  id: string;
  name: string;
  title: string;
  description: string;
  category: string;
  fields: FormField[];
  metadata: {
    created: string;
    modified: string;
    version: string;
  };
}

interface FormEditorProps {
  formId?: string;
  onClose: () => void;
  onSave: (formData: FormData) => void;
}

const FormEditor: React.FC<FormEditorProps> = ({ formId, onClose, onSave }) => {
  const [formData, setFormData] = useState<FormData>({
    id: formId || `form_${Date.now()}`,
    name: '',
    title: '',
    description: '',
    category: '',
    fields: [],
    metadata: {
      created: new Date().toISOString(),
      modified: new Date().toISOString(),
      version: '1.0'
    }
  });

  const [activeField, setActiveField] = useState<string | null>(null);
  const [previewMode, setPreviewMode] = useState(false);
  const [showFieldModal, setShowFieldModal] = useState(false);
  const [editingField, setEditingField] = useState<FormField | null>(null);

  // 폼 데이터 로드 (기존 폼 편집 시)
  useEffect(() => {
    if (formId) {
      loadFormData(formId);
    }
  }, [formId]);

  const loadFormData = async (id: string) => {
    try {
      // 기존 폼 데이터 로드 로직
      // API 호출 등
    } catch (error) {
      console.error('Failed to load form data:', error);
    }
  };

  // 필드 타입별 기본 설정
  const getDefaultField = (type: FormField['type']): Partial<FormField> => {
    const base = {
      id: `field_${Date.now()}`,
      name: '',
      label: '',
      value: '',
      required: false,
      type
    };

    switch (type) {
      case 'text':
        return { ...base, placeholder: '텍스트를 입력하세요' };
      case 'number':
        return { ...base, placeholder: '숫자를 입력하세요' };
      case 'date':
        return { ...base, placeholder: 'YYYY-MM-DD' };
      case 'textarea':
        return { ...base, placeholder: '내용을 입력하세요' };
      case 'select':
        return { ...base, options: ['옵션1', '옵션2', '옵션3'] };
      case 'checkbox':
        return { ...base, value: 'false' };
      default:
        return base;
    }
  };

  // 필드 추가
  const addField = (type: FormField['type']) => {
    const newField = {
      ...getDefaultField(type),
      name: `field_${formData.fields.length + 1}`,
      label: `필드 ${formData.fields.length + 1}`
    } as FormField;

    setFormData(prev => ({
      ...prev,
      fields: [...prev.fields, newField],
      metadata: { ...prev.metadata, modified: new Date().toISOString() }
    }));
    setEditingField(newField);
    setShowFieldModal(true);
  };

  // 필드 수정
  const updateField = (fieldId: string, updates: Partial<FormField>) => {
    setFormData(prev => ({
      ...prev,
      fields: prev.fields.map(field => 
        field.id === fieldId ? { ...field, ...updates } : field
      ),
      metadata: { ...prev.metadata, modified: new Date().toISOString() }
    }));
  };

  // 필드 삭제
  const deleteField = (fieldId: string) => {
    setFormData(prev => ({
      ...prev,
      fields: prev.fields.filter(field => field.id !== fieldId),
      metadata: { ...prev.metadata, modified: new Date().toISOString() }
    }));
  };

  // 필드 순서 변경
  const moveField = (fieldId: string, direction: 'up' | 'down') => {
    const currentIndex = formData.fields.findIndex(f => f.id === fieldId);
    if (currentIndex === -1) return;

    const newIndex = direction === 'up' ? currentIndex - 1 : currentIndex + 1;
    if (newIndex < 0 || newIndex >= formData.fields.length) return;

    const newFields = [...formData.fields];
    [newFields[currentIndex], newFields[newIndex]] = [newFields[newIndex], newFields[currentIndex]];

    setFormData(prev => ({
      ...prev,
      fields: newFields,
      metadata: { ...prev.metadata, modified: new Date().toISOString() }
    }));
  };

  // 폼 저장
  const handleSave = () => {
    if (!formData.name.trim() || !formData.title.trim()) {
      alert('폼 이름과 제목을 입력해주세요.');
      return;
    }

    if (formData.fields.length === 0) {
      alert('최소 하나의 필드를 추가해주세요.');
      return;
    }

    onSave(formData);
  };

  // 필드 렌더링 (편집 모드)
  const renderFieldEditor = (field: FormField, index: number) => (
    <Card key={field.id} className={`p-4 ${activeField === field.id ? 'ring-2 ring-blue-500' : ''}`}>
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-sm font-medium text-gray-700">{field.label}</span>
            {field.required && <span className="text-red-500">*</span>}
            <Badge color="gray">{field.type}</Badge>
          </div>
          <p className="text-xs text-gray-500">이름: {field.name}</p>
        </div>
        <div className="flex gap-1">
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              setEditingField(field);
              setShowFieldModal(true);
            }}
          >
            <Edit3 size={12} />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => deleteField(field.id)}
          >
            <Trash2 size={12} />
          </Button>
        </div>
      </div>
      
      {/* 필드 미리보기 */}
      <div className="border border-gray-200 rounded p-2 bg-gray-50">
        {renderFieldPreview(field)}
      </div>
      
      {/* 순서 변경 버튼 */}
      <div className="flex justify-center gap-2 mt-2">
        <Button
          size="sm"
          variant="outline"
          onClick={() => moveField(field.id, 'up')}
          disabled={index === 0}
        >
          ↑
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => moveField(field.id, 'down')}
          disabled={index === formData.fields.length - 1}
        >
          ↓
        </Button>
      </div>
    </Card>
  );

  // 필드 미리보기 렌더링
  const renderFieldPreview = (field: FormField) => {
    const commonProps = {
      name: field.name,
      placeholder: field.placeholder,
      required: field.required,
      className: "w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
    };

    switch (field.type) {
      case 'text':
        return <input type="text" {...commonProps} value={field.value} readOnly />;
      case 'number':
        return <input type="number" {...commonProps} value={field.value} readOnly />;
      case 'date':
        return <input type="date" {...commonProps} value={field.value} readOnly />;
      case 'textarea':
        return <textarea {...commonProps} rows={3} value={field.value} readOnly />;
      case 'select':
        return (
          <select {...commonProps} value={field.value} disabled>
            <option value="">선택하세요</option>
            {field.options?.map((option, idx) => (
              <option key={idx} value={option}>{option}</option>
            ))}
          </select>
        );
      case 'checkbox':
        return (
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={field.value === 'true'}
              readOnly
              className="mr-2"
            />
            {field.label}
          </label>
        );
      default:
        return <div className="text-gray-500">미지원 필드 타입</div>;
    }
  };

  // 필드 타입 선택 버튼들
  const fieldTypes = [
    { type: 'text' as const, label: '텍스트', icon: '📝' },
    { type: 'number' as const, label: '숫자', icon: '🔢' },
    { type: 'date' as const, label: '날짜', icon: '📅' },
    { type: 'textarea' as const, label: '긴 텍스트', icon: '📄' },
    { type: 'select' as const, label: '선택목록', icon: '📋' },
    { type: 'checkbox' as const, label: '체크박스', icon: '☑️' }
  ];

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl h-full max-h-[90vh] flex flex-col">
        {/* 헤더 */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center gap-4">
            <Button variant="outline" onClick={onClose}>
              <ArrowLeft size={16} />
            </Button>
            <div>
              <h2 className="text-xl font-semibold">
                {formId ? '양식 편집' : '새 양식 만들기'}
              </h2>
              <p className="text-sm text-gray-500">
                웹 기반 양식 편집기
              </p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => setPreviewMode(!previewMode)}
            >
              <Eye size={16} className="mr-2" />
              {previewMode ? '편집' : '미리보기'}
            </Button>
            <Button onClick={handleSave}>
              <Save size={16} className="mr-2" />
              저장
            </Button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden">
          {/* 왼쪽 패널: 폼 정보 및 필드 타입 */}
          {!previewMode && (
            <div className="w-1/4 border-r p-6 overflow-y-auto">
              <div className="space-y-6">
                {/* 폼 기본 정보 */}
                <div>
                  <h3 className="font-medium mb-3">폼 정보</h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        폼 이름 *
                      </label>
                      <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="예: employee_health_form"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        폼 제목 *
                      </label>
                      <input
                        type="text"
                        value={formData.title}
                        onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="예: 근로자 건강검진 양식"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        설명
                      </label>
                      <textarea
                        value={formData.description}
                        onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                        rows={3}
                        placeholder="양식에 대한 설명을 입력하세요"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        카테고리
                      </label>
                      <select
                        value={formData.category}
                        onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                      >
                        <option value="">선택하세요</option>
                        <option value="관리대장">관리대장</option>
                        <option value="건강관리">건강관리</option>
                        <option value="특별관리물질">특별관리물질</option>
                        <option value="법정서식">법정서식</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* 필드 타입 추가 */}
                <div>
                  <h3 className="font-medium mb-3">필드 추가</h3>
                  <div className="grid grid-cols-2 gap-2">
                    {fieldTypes.map(({ type, label, icon }) => (
                      <Button
                        key={type}
                        variant="outline"
                        size="sm"
                        onClick={() => addField(type)}
                        className="text-left"
                      >
                        <span className="mr-2">{icon}</span>
                        {label}
                      </Button>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* 오른쪽 패널: 폼 편집/미리보기 영역 */}
          <div className={`${previewMode ? 'w-full' : 'w-3/4'} p-6 overflow-y-auto`}>
            {previewMode ? (
              /* 미리보기 모드 */
              <div className="max-w-2xl mx-auto">
                <div className="mb-6">
                  <h1 className="text-2xl font-bold text-gray-900">{formData.title || '제목 없음'}</h1>
                  {formData.description && (
                    <p className="text-gray-600 mt-2">{formData.description}</p>
                  )}
                </div>
                
                <Card className="p-6">
                  <form className="space-y-6">
                    {formData.fields.map((field) => (
                      <div key={field.id}>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          {field.label}
                          {field.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        {renderFieldPreview(field)}
                      </div>
                    ))}
                  </form>
                </Card>
              </div>
            ) : (
              /* 편집 모드 */
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-medium">
                    폼 필드 ({formData.fields.length}개)
                  </h3>
                  <Badge color="blue">
                    마지막 수정: {new Date(formData.metadata.modified).toLocaleString()}
                  </Badge>
                </div>

                {formData.fields.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <p>필드를 추가하여 양식을 만들어보세요.</p>
                    <p className="text-sm">왼쪽 패널에서 필드 타입을 선택하세요.</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {formData.fields.map((field, index) => 
                      renderFieldEditor(field, index)
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* 필드 편집 모달 */}
        {showFieldModal && editingField && (
          <FieldEditModal
            field={editingField}
            onSave={(updatedField) => {
              updateField(editingField.id, updatedField);
              setShowFieldModal(false);
              setEditingField(null);
            }}
            onClose={() => {
              setShowFieldModal(false);
              setEditingField(null);
            }}
          />
        )}
      </div>
    </div>
  );
};

// 필드 편집 모달 컴포넌트
interface FieldEditModalProps {
  field: FormField;
  onSave: (field: Partial<FormField>) => void;
  onClose: () => void;
}

const FieldEditModal: React.FC<FieldEditModalProps> = ({ field, onSave, onClose }) => {
  const [editedField, setEditedField] = useState<FormField>({ ...field });

  const handleSave = () => {
    if (!editedField.name.trim() || !editedField.label.trim()) {
      alert('필드 이름과 라벨을 입력해주세요.');
      return;
    }
    onSave(editedField);
  };

  return (
    <Modal title="필드 편집" onClose={onClose}>
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            필드 이름 *
          </label>
          <input
            type="text"
            value={editedField.name}
            onChange={(e) => setEditedField(prev => ({ ...prev, name: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="예: worker_name"
          />
          <p className="text-xs text-gray-500 mt-1">영문, 숫자, 언더스코어만 사용 가능</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            라벨 *
          </label>
          <input
            type="text"
            value={editedField.label}
            onChange={(e) => setEditedField(prev => ({ ...prev, label: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="예: 근로자명"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            플레이스홀더
          </label>
          <input
            type="text"
            value={editedField.placeholder || ''}
            onChange={(e) => setEditedField(prev => ({ ...prev, placeholder: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="입력 안내 텍스트"
          />
        </div>

        {editedField.type === 'select' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              선택 옵션 (줄바꿈으로 구분)
            </label>
            <textarea
              value={editedField.options?.join('\n') || ''}
              onChange={(e) => setEditedField(prev => ({ 
                ...prev, 
                options: e.target.value.split('\n').filter(option => option.trim()) 
              }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              placeholder="옵션1&#10;옵션2&#10;옵션3"
            />
          </div>
        )}

        <div className="flex items-center">
          <input
            type="checkbox"
            id="required"
            checked={editedField.required}
            onChange={(e) => setEditedField(prev => ({ ...prev, required: e.target.checked }))}
            className="mr-2"
          />
          <label htmlFor="required" className="text-sm font-medium text-gray-700">
            필수 입력 필드
          </label>
        </div>

        <div className="flex justify-end gap-2 mt-6">
          <Button variant="outline" onClick={onClose}>
            취소
          </Button>
          <Button onClick={handleSave}>
            저장
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default FormEditor;