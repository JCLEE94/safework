import React, { useState, useEffect } from 'react';
import {
  FileText, Edit, Download, Upload, Save, Eye, CheckCircle,
  AlertCircle, Clock, Calendar, User, Building, Hash,
  Printer, Send, Archive, Bookmark, Tag, Search, Filter,
  RefreshCw, Settings, MoreHorizontal, Plus, Trash2
} from 'lucide-react';
import { Card, Button, Table, Badge, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface LegalForm {
  id: string;
  form_code: string;
  form_name: string;
  form_name_korean: string;
  category: string;
  department: string;
  description: string;
  required_fields: LegalFormField[];
  submission_deadline?: string;
  regulatory_basis: string;
  template_path?: string;
  status: 'draft' | 'in_progress' | 'completed' | 'submitted' | 'approved' | 'rejected';
  priority: 'high' | 'medium' | 'low';
  assignee?: string;
  created_at: string;
  updated_at: string;
  submitted_at?: string;
  approved_at?: string;
  version: number;
  attachments: FormAttachment[];
  approval_history: ApprovalRecord[];
}

interface LegalFormField {
  field_name: string;
  field_label: string;
  field_type: 'text' | 'number' | 'date' | 'select' | 'textarea' | 'file' | 'checkbox';
  required: boolean;
  validation_rules?: string;
  options?: string[];
  default_value?: string;
  help_text?: string;
}

interface FormAttachment {
  id: string;
  file_name: string;
  file_size: number;
  file_type: string;
  uploaded_at: string;
  uploaded_by: string;
}

interface ApprovalRecord {
  id: string;
  approver: string;
  status: 'pending' | 'approved' | 'rejected';
  comment?: string;
  approved_at?: string;
}

interface LegalFormProcessorProps {
  onFormSelect?: (form: LegalForm) => void;
  selectedDepartment?: string;
  viewMode?: 'list' | 'grid' | 'kanban';
}

const FORM_CATEGORIES = [
  { value: 'safety', label: '안전관리', color: 'red' },
  { value: 'health', label: '보건관리', color: 'green' },
  { value: 'environment', label: '환경관리', color: 'blue' },
  { value: 'labor', label: '노무관리', color: 'purple' },
  { value: 'construction', label: '건설업무', color: 'orange' },
  { value: 'reporting', label: '신고업무', color: 'indigo' },
  { value: 'permit', label: '허가업무', color: 'yellow' },
  { value: 'inspection', label: '점검업무', color: 'pink' }
];

const FORM_STATUS = [
  { value: 'draft', label: '초안', color: 'gray' },
  { value: 'in_progress', label: '진행중', color: 'blue' },
  { value: 'completed', label: '작성완료', color: 'green' },
  { value: 'submitted', label: '제출완료', color: 'indigo' },
  { value: 'approved', label: '승인완료', color: 'emerald' },
  { value: 'rejected', label: '반려', color: 'red' }
];

const FORM_PRIORITIES = [
  { value: 'high', label: '긴급', color: 'red' },
  { value: 'medium', label: '보통', color: 'yellow' },
  { value: 'low', label: '낮음', color: 'green' }
];

export function LegalFormProcessor({ onFormSelect, selectedDepartment, viewMode = 'list' }: LegalFormProcessorProps) {
  const [forms, setForms] = useState<LegalForm[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    priority: '',
    assignee: '',
    department: selectedDepartment || '',
    deadline_upcoming: false
  });
  const [selectedForm, setSelectedForm] = useState<LegalForm | null>(null);
  const [showFormModal, setShowFormModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const { fetchApi } = useApi();

  useEffect(() => {
    loadLegalForms();
  }, [filters, selectedDepartment]);

  const loadLegalForms = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (searchTerm) params.append('search', searchTerm);
      if (filters.category) params.append('category', filters.category);
      if (filters.status) params.append('status', filters.status);
      if (filters.priority) params.append('priority', filters.priority);
      if (filters.assignee) params.append('assignee', filters.assignee);
      if (filters.department || selectedDepartment) {
        params.append('department', filters.department || selectedDepartment);
      }
      if (filters.deadline_upcoming) params.append('deadline_upcoming', 'true');

      const data = await fetchApi(`/legal-forms?${params}`);
      setForms(data.items || []);
    } catch (error) {
      console.error('법정서식 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFormAction = async (action: string, form: LegalForm) => {
    switch (action) {
      case 'edit':
        setSelectedForm(form);
        setShowFormModal(true);
        break;
      case 'submit':
        await handleSubmitForm(form.id);
        break;
      case 'approve':
        await handleApproveForm(form.id);
        break;
      case 'reject':
        await handleRejectForm(form.id);
        break;
      case 'download':
        await handleDownloadForm(form.id);
        break;
      case 'duplicate':
        await handleDuplicateForm(form.id);
        break;
      case 'archive':
        await handleArchiveForm(form.id);
        break;
      case 'delete':
        if (confirm('정말 삭제하시겠습니까?')) {
          await handleDeleteForm(form.id);
        }
        break;
    }
  };

  const handleSubmitForm = async (formId: string) => {
    try {
      await fetchApi(`/legal-forms/${formId}/submit`, { method: 'POST' });
      await loadLegalForms();
    } catch (error) {
      console.error('서식 제출 실패:', error);
    }
  };

  const handleApproveForm = async (formId: string) => {
    try {
      await fetchApi(`/legal-forms/${formId}/approve`, { method: 'POST' });
      await loadLegalForms();
    } catch (error) {
      console.error('서식 승인 실패:', error);
    }
  };

  const handleRejectForm = async (formId: string) => {
    const comment = prompt('반려 사유를 입력하세요:');
    if (!comment) return;

    try {
      await fetchApi(`/legal-forms/${formId}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ comment })
      });
      await loadLegalForms();
    } catch (error) {
      console.error('서식 반려 실패:', error);
    }
  };

  const handleDownloadForm = async (formId: string) => {
    try {
      const response = await fetch(`/api/v1/legal-forms/${formId}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'form.pdf';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('서식 다운로드 실패:', error);
    }
  };

  const handleDuplicateForm = async (formId: string) => {
    try {
      await fetchApi(`/legal-forms/${formId}/duplicate`, { method: 'POST' });
      await loadLegalForms();
    } catch (error) {
      console.error('서식 복제 실패:', error);
    }
  };

  const handleArchiveForm = async (formId: string) => {
    try {
      await fetchApi(`/legal-forms/${formId}/archive`, { method: 'POST' });
      await loadLegalForms();
    } catch (error) {
      console.error('서식 보관 실패:', error);
    }
  };

  const handleDeleteForm = async (formId: string) => {
    try {
      await fetchApi(`/legal-forms/${formId}`, { method: 'DELETE' });
      await loadLegalForms();
    } catch (error) {
      console.error('서식 삭제 실패:', error);
    }
  };

  const getStatusColor = (status: string) => {
    const statusInfo = FORM_STATUS.find(s => s.value === status);
    return statusInfo?.color || 'gray';
  };

  const getPriorityColor = (priority: string) => {
    const priorityInfo = FORM_PRIORITIES.find(p => p.value === priority);
    return priorityInfo?.color || 'gray';
  };

  const getCategoryColor = (category: string) => {
    const categoryInfo = FORM_CATEGORIES.find(c => c.value === category);
    return categoryInfo?.color || 'gray';
  };

  const isDeadlineApproaching = (deadline?: string) => {
    if (!deadline) return false;
    const deadlineDate = new Date(deadline);
    const today = new Date();
    const diffDays = Math.ceil((deadlineDate.getTime() - today.getTime()) / (1000 * 3600 * 24));
    return diffDays <= 7 && diffDays > 0;
  };

  const isOverdue = (deadline?: string) => {
    if (!deadline) return false;
    const deadlineDate = new Date(deadline);
    const today = new Date();
    return deadlineDate < today;
  };

  const filteredForms = forms.filter(form => {
    if (searchTerm) {
      return form.form_name_korean.toLowerCase().includes(searchTerm.toLowerCase()) ||
             form.form_code.toLowerCase().includes(searchTerm.toLowerCase()) ||
             form.description.toLowerCase().includes(searchTerm.toLowerCase());
    }
    return true;
  });

  const renderListView = () => (
    <Table
      columns={[
        {
          key: 'form_info',
          header: '서식 정보',
          render: (form: LegalForm) => (
            <div className="flex items-center gap-3">
              <FileText className="text-blue-600 flex-shrink-0" size={20} />
              <div>
                <div className="font-medium text-gray-900">{form.form_name_korean}</div>
                <div className="text-sm text-gray-500">{form.form_code}</div>
              </div>
            </div>
          )
        },
        {
          key: 'category',
          header: '분류',
          render: (form: LegalForm) => {
            const category = FORM_CATEGORIES.find(c => c.value === form.category);
            return (
              <Badge color={getCategoryColor(form.category)}>
                {category?.label || form.category}
              </Badge>
            );
          }
        },
        {
          key: 'status',
          header: '상태',
          render: (form: LegalForm) => {
            const status = FORM_STATUS.find(s => s.value === form.status);
            return (
              <Badge color={getStatusColor(form.status)}>
                {status?.label || form.status}
              </Badge>
            );
          }
        },
        {
          key: 'priority',
          header: '우선순위',
          render: (form: LegalForm) => {
            const priority = FORM_PRIORITIES.find(p => p.value === form.priority);
            return (
              <Badge color={getPriorityColor(form.priority)} size="sm">
                {priority?.label || form.priority}
              </Badge>
            );
          }
        },
        {
          key: 'deadline',
          header: '마감일',
          render: (form: LegalForm) => (
            <div className="flex items-center gap-1">
              {form.submission_deadline ? (
                <>
                  <Calendar className="text-gray-400" size={14} />
                  <span className={`text-sm ${
                    isOverdue(form.submission_deadline) ? 'text-red-600 font-medium' :
                    isDeadlineApproaching(form.submission_deadline) ? 'text-orange-600 font-medium' :
                    'text-gray-600'
                  }`}>
                    {new Date(form.submission_deadline).toLocaleDateString()}
                  </span>
                  {isOverdue(form.submission_deadline) && (
                    <AlertCircle className="text-red-500" size={14} />
                  )}
                  {isDeadlineApproaching(form.submission_deadline) && !isOverdue(form.submission_deadline) && (
                    <Clock className="text-orange-500" size={14} />
                  )}
                </>
              ) : (
                <span className="text-sm text-gray-400">-</span>
              )}
            </div>
          )
        },
        {
          key: 'assignee',
          header: '담당자',
          render: (form: LegalForm) => (
            <div className="flex items-center gap-1">
              <User className="text-gray-400" size={14} />
              <span className="text-sm">{form.assignee || '미지정'}</span>
            </div>
          )
        },
        {
          key: 'updated_at',
          header: '수정일',
          render: (form: LegalForm) => (
            <span className="text-sm text-gray-600">
              {new Date(form.updated_at).toLocaleDateString()}
            </span>
          )
        },
        {
          key: 'actions',
          header: '작업',
          render: (form: LegalForm) => (
            <div className="flex gap-1">
              <button
                onClick={() => handleFormAction('edit', form)}
                className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                title="편집"
              >
                <Edit size={16} />
              </button>
              <button
                onClick={() => handleFormAction('download', form)}
                className="p-1 text-green-600 hover:bg-green-50 rounded"
                title="다운로드"
              >
                <Download size={16} />
              </button>
              {form.status === 'completed' && (
                <button
                  onClick={() => handleFormAction('submit', form)}
                  className="p-1 text-purple-600 hover:bg-purple-50 rounded"
                  title="제출"
                >
                  <Send size={16} />
                </button>
              )}
              {form.status === 'submitted' && (
                <>
                  <button
                    onClick={() => handleFormAction('approve', form)}
                    className="p-1 text-emerald-600 hover:bg-emerald-50 rounded"
                    title="승인"
                  >
                    <CheckCircle size={16} />
                  </button>
                  <button
                    onClick={() => handleFormAction('reject', form)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded"
                    title="반려"
                  >
                    <AlertCircle size={16} />
                  </button>
                </>
              )}
              <div className="relative group">
                <button className="p-1 text-gray-600 hover:bg-gray-50 rounded">
                  <MoreHorizontal size={16} />
                </button>
                <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg py-1 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <button
                    onClick={() => handleFormAction('duplicate', form)}
                    className="block w-full text-left px-3 py-1 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    복제
                  </button>
                  <button
                    onClick={() => handleFormAction('archive', form)}
                    className="block w-full text-left px-3 py-1 text-sm text-gray-700 hover:bg-gray-100"
                  >
                    보관
                  </button>
                  <button
                    onClick={() => handleFormAction('delete', form)}
                    className="block w-full text-left px-3 py-1 text-sm text-red-600 hover:bg-red-50"
                  >
                    삭제
                  </button>
                </div>
              </div>
            </div>
          )
        }
      ]}
      data={filteredForms}
      loading={loading}
      emptyMessage="조건에 맞는 법정서식이 없습니다."
    />
  );

  const renderGridView = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {filteredForms.map(form => (
        <Card key={form.id} className="p-6 hover:shadow-md transition-shadow">
          <div className="space-y-4">
            {/* 헤더 */}
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3 flex-1">
                <FileText className="text-blue-600 flex-shrink-0" size={24} />
                <div className="min-w-0">
                  <h3 className="font-medium text-gray-900 truncate">{form.form_name_korean}</h3>
                  <p className="text-sm text-gray-500">{form.form_code}</p>
                </div>
              </div>
              <div className="flex gap-1">
                <Badge color={getPriorityColor(form.priority)} size="sm">
                  {FORM_PRIORITIES.find(p => p.value === form.priority)?.label}
                </Badge>
              </div>
            </div>

            {/* 내용 */}
            <p className="text-sm text-gray-600 line-clamp-2">{form.description}</p>

            {/* 메타데이터 */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Badge color={getCategoryColor(form.category)}>
                  {FORM_CATEGORIES.find(c => c.value === form.category)?.label}
                </Badge>
                <Badge color={getStatusColor(form.status)}>
                  {FORM_STATUS.find(s => s.value === form.status)?.label}
                </Badge>
              </div>

              {form.submission_deadline && (
                <div className="flex items-center gap-1">
                  <Calendar className="text-gray-400" size={14} />
                  <span className={`text-sm ${
                    isOverdue(form.submission_deadline) ? 'text-red-600 font-medium' :
                    isDeadlineApproaching(form.submission_deadline) ? 'text-orange-600 font-medium' :
                    'text-gray-600'
                  }`}>
                    마감: {new Date(form.submission_deadline).toLocaleDateString()}
                  </span>
                </div>
              )}

              {form.assignee && (
                <div className="flex items-center gap-1">
                  <User className="text-gray-400" size={14} />
                  <span className="text-sm text-gray-600">{form.assignee}</span>
                </div>
              )}
            </div>

            {/* 액션 버튼 */}
            <div className="flex gap-2 pt-2 border-t">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => handleFormAction('edit', form)}
                className="flex-1"
              >
                <Edit size={14} className="mr-1" />
                편집
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => handleFormAction('download', form)}
              >
                <Download size={14} />
              </Button>
              {form.status === 'completed' && (
                <Button
                  size="sm"
                  onClick={() => handleFormAction('submit', form)}
                >
                  <Send size={14} />
                </Button>
              )}
            </div>
          </div>
        </Card>
      ))}
    </div>
  );

  const renderKanbanView = () => {
    const statusColumns = FORM_STATUS.map(status => ({
      ...status,
      forms: filteredForms.filter(form => form.status === status.value)
    }));

    return (
      <div className="flex gap-6 overflow-x-auto pb-4">
        {statusColumns.map(column => (
          <div key={column.value} className="flex-shrink-0 w-80">
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-medium text-gray-900">{column.label}</h3>
                <Badge color={column.color}>{column.forms.length}</Badge>
              </div>
              
              <div className="space-y-3">
                {column.forms.map(form => (
                  <Card key={form.id} className="p-4 cursor-pointer hover:shadow-md transition-shadow">
                    <div className="space-y-3">
                      <div className="flex items-start justify-between">
                        <h4 className="font-medium text-gray-900 text-sm leading-tight">
                          {form.form_name_korean}
                        </h4>
                        <Badge color={getPriorityColor(form.priority)} size="sm">
                          {FORM_PRIORITIES.find(p => p.value === form.priority)?.label}
                        </Badge>
                      </div>
                      
                      <p className="text-xs text-gray-600 line-clamp-2">{form.description}</p>
                      
                      <div className="flex items-center justify-between">
                        <Badge color={getCategoryColor(form.category)} size="sm">
                          {FORM_CATEGORIES.find(c => c.value === form.category)?.label}
                        </Badge>
                        {form.submission_deadline && (
                          <span className={`text-xs ${
                            isOverdue(form.submission_deadline) ? 'text-red-600' :
                            isDeadlineApproaching(form.submission_deadline) ? 'text-orange-600' :
                            'text-gray-500'
                          }`}>
                            {new Date(form.submission_deadline).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                      
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleFormAction('edit', form)}
                          className="flex-1 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
                        >
                          편집
                        </button>
                        <button
                          onClick={() => handleFormAction('download', form)}
                          className="px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded"
                        >
                          <Download size={12} />
                        </button>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderContent = () => {
    switch (viewMode) {
      case 'grid':
        return renderGridView();
      case 'kanban':
        return renderKanbanView();
      default:
        return renderListView();
    }
  };

  return (
    <div className="space-y-6">
      {/* 검색 및 필터 */}
      <Card className="p-4">
        <div className="space-y-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="서식명, 서식코드, 설명으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && loadLegalForms()}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="secondary"
                onClick={() => setShowFilters(!showFilters)}
                icon={<Filter size={16} />}
              >
                필터
              </Button>
              <Button
                variant="secondary"
                onClick={loadLegalForms}
                icon={<RefreshCw size={16} />}
              >
                새로고침
              </Button>
              <Button
                onClick={() => setShowFormModal(true)}
                icon={<Plus size={16} />}
              >
                새 서식
              </Button>
            </div>
          </div>

          {showFilters && (
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4 pt-4 border-t">
              <select
                value={filters.category}
                onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">모든 분류</option>
                {FORM_CATEGORIES.map(category => (
                  <option key={category.value} value={category.value}>{category.label}</option>
                ))}
              </select>

              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">모든 상태</option>
                {FORM_STATUS.map(status => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </select>

              <select
                value={filters.priority}
                onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">모든 우선순위</option>
                {FORM_PRIORITIES.map(priority => (
                  <option key={priority.value} value={priority.value}>{priority.label}</option>
                ))}
              </select>

              <input
                type="text"
                placeholder="담당자"
                value={filters.assignee}
                onChange={(e) => setFilters(prev => ({ ...prev, assignee: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />

              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={filters.deadline_upcoming}
                  onChange={(e) => setFilters(prev => ({ ...prev, deadline_upcoming: e.target.checked }))}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm text-gray-700">마감임박</span>
              </label>
            </div>
          )}
        </div>
      </Card>

      {/* 메인 콘텐츠 */}
      <Card>
        {loading ? (
          <div className="p-8 text-center">
            <RefreshCw className="animate-spin mx-auto" size={32} />
            <p className="mt-2 text-gray-600">법정서식을 불러오는 중...</p>
          </div>
        ) : filteredForms.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">법정서식이 없습니다</h3>
            <p className="mt-1 text-sm text-gray-500">새 서식을 추가하거나 필터를 조정해보세요.</p>
            <div className="mt-6">
              <Button onClick={() => setShowFormModal(true)} icon={<Plus size={16} />}>
                새 서식 추가
              </Button>
            </div>
          </div>
        ) : (
          renderContent()
        )}
      </Card>

      {/* 서식 편집/생성 모달 */}
      {showFormModal && (
        <Modal
          isOpen={showFormModal}
          onClose={() => {
            setShowFormModal(false);
            setSelectedForm(null);
          }}
          maxWidth="4xl"
        >
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">
              {selectedForm ? '법정서식 편집' : '새 법정서식 추가'}
            </h3>
            {/* 서식 편집/생성 폼 - 별도 컴포넌트로 구현 필요 */}
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <Settings className="mx-auto text-gray-400" size={48} />
              <p className="text-gray-600 mt-2">서식 편집기</p>
              <p className="text-sm text-gray-500">상세 편집 기능 구현 예정</p>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}