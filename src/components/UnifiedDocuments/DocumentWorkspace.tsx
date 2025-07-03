import React, { useState, useEffect } from 'react';
import {
  FileText, FolderOpen, Search, Filter, Grid, List, Upload,
  Download, Edit, Eye, Trash2, Plus, Settings, History,
  FileEdit, FilePlus, Archive, Bookmark, Share2, Tag,
  Calendar, User, Clock, AlertCircle, CheckCircle
} from 'lucide-react';
import { Card, Button, Table, Badge, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface Document {
  id: number;
  title: string;
  type: string;
  category: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  description?: string;
  tags: string[];
  created_by: string;
  created_at: string;
  updated_at: string;
  status: string;
  version: number;
  is_template: boolean;
  access_level: string;
  metadata?: any;
}

interface DocumentCategory {
  id: string;
  name: string;
  icon: React.ReactNode;
  color: string;
  description: string;
  count: number;
  templates: number;
}

interface DocumentWorkspaceProps {
  onDocumentSelect?: (document: Document) => void;
  selectedDocuments?: Document[];
  mode?: 'selection' | 'management';
}

const DOCUMENT_CATEGORIES: DocumentCategory[] = [
  {
    id: 'legal_forms',
    name: '법정서식',
    icon: <FileText className="w-5 h-5" />,
    color: 'blue',
    description: '법령에서 요구하는 필수 서식 및 양식',
    count: 0,
    templates: 0
  },
  {
    id: 'health_checkups',
    name: '건강진단',
    icon: <FileEdit className="w-5 h-5" />,
    color: 'green',
    description: '건강진단 관련 서류 및 결과서',
    count: 0,
    templates: 0
  },
  {
    id: 'safety_education',
    name: '안전교육',
    icon: <FilePlus className="w-5 h-5" />,
    color: 'orange',
    description: '안전보건 교육자료 및 이수증',
    count: 0,
    templates: 0
  },
  {
    id: 'accident_reports',
    name: '사고보고서',
    icon: <AlertCircle className="w-5 h-5" />,
    color: 'red',
    description: '산업재해 및 사고 관련 보고서',
    count: 0,
    templates: 0
  },
  {
    id: 'msds',
    name: 'MSDS',
    icon: <Archive className="w-5 h-5" />,
    color: 'purple',
    description: '화학물질 안전보건자료',
    count: 0,
    templates: 0
  },
  {
    id: 'certificates',
    name: '인증서류',
    icon: <CheckCircle className="w-5 h-5" />,
    color: 'indigo',
    description: '각종 자격증 및 인증서',
    count: 0,
    templates: 0
  },
  {
    id: 'policies',
    name: '정책문서',
    icon: <FolderOpen className="w-5 h-5" />,
    color: 'gray',
    description: '회사 정책 및 규정 문서',
    count: 0,
    templates: 0
  },
  {
    id: 'templates',
    name: '서식템플릿',
    icon: <Bookmark className="w-5 h-5" />,
    color: 'yellow',
    description: '재사용 가능한 문서 템플릿',
    count: 0,
    templates: 0
  }
];

const DOCUMENT_STATUS = [
  { value: 'draft', label: '초안', color: 'gray' },
  { value: 'review', label: '검토중', color: 'yellow' },
  { value: 'approved', label: '승인됨', color: 'green' },
  { value: 'archived', label: '보관됨', color: 'blue' },
  { value: 'expired', label: '만료됨', color: 'red' }
];

const VIEW_MODES = [
  { value: 'grid', label: '카드뷰', icon: <Grid size={16} /> },
  { value: 'list', label: '목록뷰', icon: <List size={16} /> }
];

export function DocumentWorkspace({ onDocumentSelect, selectedDocuments = [], mode = 'management' }: DocumentWorkspaceProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [categories, setCategories] = useState<DocumentCategory[]>(DOCUMENT_CATEGORIES);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [filters, setFilters] = useState({
    status: '',
    type: '',
    created_by: '',
    date_from: '',
    date_to: '',
    tags: '',
    is_template: false
  });
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedDocs, setSelectedDocs] = useState<Set<number>>(new Set());

  const { fetchApi } = useApi();

  useEffect(() => {
    loadDocuments();
    loadCategoryCounts();
  }, [selectedCategory, filters]);

  const loadDocuments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (selectedCategory) params.append('category', selectedCategory);
      if (searchTerm) params.append('search', searchTerm);
      if (filters.status) params.append('status', filters.status);
      if (filters.type) params.append('type', filters.type);
      if (filters.created_by) params.append('created_by', filters.created_by);
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.tags) params.append('tags', filters.tags);
      if (filters.is_template) params.append('is_template', 'true');

      const data = await fetchApi(`/documents?${params}`);
      setDocuments(data.items || []);
    } catch (error) {
      console.error('문서 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCategoryCounts = async () => {
    try {
      const data = await fetchApi('/documents/categories/stats');
      setCategories(prev => prev.map(cat => ({
        ...cat,
        count: data[cat.id]?.count || 0,
        templates: data[cat.id]?.templates || 0
      })));
    } catch (error) {
      console.error('카테고리 통계 조회 실패:', error);
    }
  };

  const handleDocumentClick = (document: Document) => {
    if (mode === 'selection') {
      onDocumentSelect?.(document);
    } else {
      // 문서 상세보기 또는 편집
      handleViewDocument(document);
    }
  };

  const handleViewDocument = (document: Document) => {
    // PDF, 이미지 등은 미리보기, 다른 형식은 다운로드
    if (document.mime_type.includes('pdf') || document.mime_type.includes('image')) {
      window.open(`/api/v1/documents/${document.id}/preview`, '_blank');
    } else {
      handleDownloadDocument(document.id);
    }
  };

  const handleDownloadDocument = async (documentId: number) => {
    try {
      const response = await fetch(`/api/v1/documents/${documentId}/download`);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'document';
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('문서 다운로드 실패:', error);
    }
  };

  const handleDeleteDocument = async (documentId: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;

    try {
      await fetchApi(`/documents/${documentId}`, { method: 'DELETE' });
      await loadDocuments();
      await loadCategoryCounts();
    } catch (error) {
      console.error('문서 삭제 실패:', error);
    }
  };

  const handleBulkAction = async (action: string) => {
    if (selectedDocs.size === 0) return;

    const documentIds = Array.from(selectedDocs);
    
    try {
      switch (action) {
        case 'delete':
          if (!confirm(`선택된 ${documentIds.length}개 문서를 삭제하시겠습니까?`)) return;
          await fetchApi('/documents/bulk-delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document_ids: documentIds })
          });
          break;
        case 'archive':
          await fetchApi('/documents/bulk-archive', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document_ids: documentIds })
          });
          break;
        case 'download':
          await fetchApi('/documents/bulk-download', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ document_ids: documentIds })
          });
          break;
      }
      
      setSelectedDocs(new Set());
      await loadDocuments();
      await loadCategoryCounts();
    } catch (error) {
      console.error('일괄 작업 실패:', error);
    }
  };

  const handleDocumentSelect = (documentId: number) => {
    const newSelected = new Set(selectedDocs);
    if (newSelected.has(documentId)) {
      newSelected.delete(documentId);
    } else {
      newSelected.add(documentId);
    }
    setSelectedDocs(newSelected);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    const statusInfo = DOCUMENT_STATUS.find(s => s.value === status);
    return statusInfo?.color || 'gray';
  };

  const filteredDocuments = documents.filter(doc => {
    if (searchTerm) {
      return doc.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
             doc.description?.toLowerCase().includes(searchTerm.toLowerCase()) ||
             doc.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()));
    }
    return true;
  });

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">통합 문서 관리</h1>
          <p className="text-gray-600 mt-1">모든 문서를 한 곳에서 관리하고 처리하세요</p>
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
            onClick={() => setShowUploadModal(true)}
            icon={<Upload size={16} />}
          >
            문서 업로드
          </Button>
        </div>
      </div>

      {/* 카테고리 그리드 */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-4">
        <Card
          className={`p-4 cursor-pointer transition-colors ${
            selectedCategory === '' ? 'ring-2 ring-blue-500 bg-blue-50' : 'hover:bg-gray-50'
          }`}
          onClick={() => setSelectedCategory('')}
        >
          <div className="text-center">
            <div className="text-gray-600 mb-2">
              <FolderOpen className="w-6 h-6 mx-auto" />
            </div>
            <div className="text-sm font-medium text-gray-700">전체</div>
            <div className="text-xs text-gray-500">{documents.length}개</div>
          </div>
        </Card>

        {categories.map(category => (
          <Card
            key={category.id}
            className={`p-4 cursor-pointer transition-colors ${
              selectedCategory === category.id ? `ring-2 ring-${category.color}-500 bg-${category.color}-50` : 'hover:bg-gray-50'
            }`}
            onClick={() => setSelectedCategory(category.id)}
          >
            <div className="text-center">
              <div className={`text-${category.color}-600 mb-2`}>
                {category.icon}
              </div>
              <div className="text-sm font-medium text-gray-700">{category.name}</div>
              <div className="text-xs text-gray-500">
                {category.count}개
                {category.templates > 0 && (
                  <span className="text-blue-500"> (+{category.templates})</span>
                )}
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* 검색 및 도구 모음 */}
      <Card className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* 검색창 */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
              <input
                type="text"
                placeholder="문서명, 내용, 태그로 검색..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && loadDocuments()}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* 뷰 모드 */}
          <div className="flex border border-gray-300 rounded-lg overflow-hidden">
            {VIEW_MODES.map(viewMode => (
              <button
                key={viewMode.value}
                onClick={() => setViewMode(viewMode.value as 'grid' | 'list')}
                className={`px-3 py-2 flex items-center gap-2 text-sm ${
                  viewMode.value === viewMode ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {viewMode.icon}
                {viewMode.label}
              </button>
            ))}
          </div>

          {/* 일괄 작업 */}
          {selectedDocs.size > 0 && (
            <div className="flex gap-2">
              <span className="flex items-center text-sm text-gray-600">
                {selectedDocs.size}개 선택됨
              </span>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleBulkAction('download')}
                icon={<Download size={14} />}
              >
                다운로드
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleBulkAction('archive')}
                icon={<Archive size={14} />}
              >
                보관
              </Button>
              <Button
                variant="secondary"
                size="sm"
                onClick={() => handleBulkAction('delete')}
                icon={<Trash2 size={14} />}
              >
                삭제
              </Button>
            </div>
          )}
        </div>

        {/* 고급 필터 */}
        {showFilters && (
          <div className="mt-4 pt-4 border-t border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">상태</label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">모든 상태</option>
                  {DOCUMENT_STATUS.map(status => (
                    <option key={status.value} value={status.value}>{status.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">생성자</label>
                <input
                  type="text"
                  value={filters.created_by}
                  onChange={(e) => setFilters(prev => ({ ...prev, created_by: e.target.value }))}
                  placeholder="생성자명"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">시작일</label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters(prev => ({ ...prev, date_from: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">종료일</label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters(prev => ({ ...prev, date_to: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">태그</label>
                <input
                  type="text"
                  value={filters.tags}
                  onChange={(e) => setFilters(prev => ({ ...prev, tags: e.target.value }))}
                  placeholder="태그명 (쉼표로 구분)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div className="flex items-end">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.is_template}
                    onChange={(e) => setFilters(prev => ({ ...prev, is_template: e.target.checked }))}
                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-700">템플릿만</span>
                </label>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 문서 목록 */}
      <Card>
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-600">문서를 불러오는 중...</p>
          </div>
        ) : filteredDocuments.length === 0 ? (
          <div className="p-8 text-center">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">문서가 없습니다</h3>
            <p className="mt-1 text-sm text-gray-500">새 문서를 업로드하거나 템플릿을 생성해보세요.</p>
            <div className="mt-6">
              <Button onClick={() => setShowUploadModal(true)} icon={<Plus size={16} />}>
                문서 업로드
              </Button>
            </div>
          </div>
        ) : (
          <div className={viewMode === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4' : 'p-4'}>
            {viewMode === 'grid' ? (
              filteredDocuments.map(document => (
                <Card
                  key={document.id}
                  className={`p-4 cursor-pointer transition-all hover:shadow-md ${
                    selectedDocs.has(document.id) ? 'ring-2 ring-blue-500 bg-blue-50' : ''
                  }`}
                  onClick={() => mode === 'management' ? handleDocumentSelect(document.id) : handleDocumentClick(document)}
                >
                  <div className="space-y-3">
                    {/* 헤더 */}
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-600" />
                          <span className="text-sm font-medium text-gray-900 truncate">
                            {document.title}
                          </span>
                        </div>
                        {document.is_template && (
                          <Badge color="yellow" size="sm" className="mt-1">템플릿</Badge>
                        )}
                      </div>
                      {mode === 'management' && (
                        <input
                          type="checkbox"
                          checked={selectedDocs.has(document.id)}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleDocumentSelect(document.id);
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                      )}
                    </div>

                    {/* 내용 */}
                    {document.description && (
                      <p className="text-sm text-gray-600 line-clamp-2">
                        {document.description}
                      </p>
                    )}

                    {/* 태그 */}
                    {document.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {document.tags.slice(0, 3).map(tag => (
                          <Badge key={tag} color="gray" size="sm">
                            {tag}
                          </Badge>
                        ))}
                        {document.tags.length > 3 && (
                          <Badge color="gray" size="sm">
                            +{document.tags.length - 3}
                          </Badge>
                        )}
                      </div>
                    )}

                    {/* 메타데이터 */}
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center gap-2">
                        <Badge color={getStatusColor(document.status)} size="sm">
                          {DOCUMENT_STATUS.find(s => s.value === document.status)?.label || document.status}
                        </Badge>
                        <span>{formatFileSize(document.file_size)}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(document.updated_at).toLocaleDateString()}</span>
                      </div>
                    </div>

                    {/* 액션 버튼 */}
                    <div className="flex gap-1 pt-2 border-t">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewDocument(document);
                        }}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1 text-xs text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <Eye className="w-3 h-3" />
                        미리보기
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          handleDownloadDocument(document.id);
                        }}
                        className="flex-1 flex items-center justify-center gap-1 px-2 py-1 text-xs text-green-600 hover:bg-green-50 rounded"
                      >
                        <Download className="w-3 h-3" />
                        다운로드
                      </button>
                      {mode === 'management' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteDocument(document.id);
                          }}
                          className="flex items-center justify-center gap-1 px-2 py-1 text-xs text-red-600 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      )}
                    </div>
                  </div>
                </Card>
              ))
            ) : (
              <Table
                columns={[
                  {
                    key: 'select',
                    header: mode === 'management' ? (
                      <input
                        type="checkbox"
                        checked={selectedDocs.size === filteredDocuments.length}
                        onChange={(e) => {
                          if (e.target.checked) {
                            setSelectedDocs(new Set(filteredDocuments.map(d => d.id)));
                          } else {
                            setSelectedDocs(new Set());
                          }
                        }}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    ) : '',
                    render: (document: Document) => mode === 'management' ? (
                      <input
                        type="checkbox"
                        checked={selectedDocs.has(document.id)}
                        onChange={() => handleDocumentSelect(document.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                    ) : null
                  },
                  {
                    key: 'title',
                    header: '문서명',
                    render: (document: Document) => (
                      <div className="flex items-center gap-2">
                        <FileText className="w-4 h-4 text-gray-600" />
                        <div>
                          <div className="font-medium text-gray-900">{document.title}</div>
                          {document.description && (
                            <div className="text-sm text-gray-500 truncate max-w-xs">
                              {document.description}
                            </div>
                          )}
                        </div>
                        {document.is_template && (
                          <Badge color="yellow" size="sm">템플릿</Badge>
                        )}
                      </div>
                    )
                  },
                  {
                    key: 'category',
                    header: '카테고리',
                    render: (document: Document) => {
                      const category = categories.find(c => c.id === document.category);
                      return category ? (
                        <Badge color={category.color}>{category.name}</Badge>
                      ) : (
                        <span className="text-gray-500">{document.category}</span>
                      );
                    }
                  },
                  {
                    key: 'status',
                    header: '상태',
                    render: (document: Document) => (
                      <Badge color={getStatusColor(document.status)}>
                        {DOCUMENT_STATUS.find(s => s.value === document.status)?.label || document.status}
                      </Badge>
                    )
                  },
                  {
                    key: 'size',
                    header: '크기',
                    render: (document: Document) => formatFileSize(document.file_size)
                  },
                  {
                    key: 'created_by',
                    header: '생성자',
                    render: (document: Document) => (
                      <div className="flex items-center gap-1">
                        <User className="w-3 h-3 text-gray-400" />
                        <span className="text-sm">{document.created_by}</span>
                      </div>
                    )
                  },
                  {
                    key: 'updated_at',
                    header: '수정일',
                    render: (document: Document) => (
                      <div className="flex items-center gap-1">
                        <Calendar className="w-3 h-3 text-gray-400" />
                        <span className="text-sm">{new Date(document.updated_at).toLocaleDateString()}</span>
                      </div>
                    )
                  },
                  {
                    key: 'actions',
                    header: '작업',
                    render: (document: Document) => (
                      <div className="flex gap-1">
                        <button
                          onClick={() => handleViewDocument(document)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                          title="미리보기"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDownloadDocument(document.id)}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                          title="다운로드"
                        >
                          <Download className="w-4 h-4" />
                        </button>
                        {mode === 'management' && (
                          <>
                            <button
                              onClick={() => {/* 편집 모달 열기 */}}
                              className="p-1 text-orange-600 hover:bg-orange-50 rounded"
                              title="편집"
                            >
                              <Edit className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleDeleteDocument(document.id)}
                              className="p-1 text-red-600 hover:bg-red-50 rounded"
                              title="삭제"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    )
                  }
                ]}
                data={filteredDocuments}
                loading={loading}
                emptyMessage="조건에 맞는 문서가 없습니다."
              />
            )}
          </div>
        )}
      </Card>

      {/* 업로드 모달 */}
      {showUploadModal && (
        <Modal isOpen={showUploadModal} onClose={() => setShowUploadModal(false)} maxWidth="2xl">
          <div className="p-6">
            <h3 className="text-lg font-semibold mb-4">문서 업로드</h3>
            {/* 업로드 폼 컴포넌트 - 별도로 구현 필요 */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400" />
              <p className="mt-2 text-sm text-gray-600">
                파일을 드래그 앤 드롭하거나 클릭하여 업로드하세요
              </p>
              <p className="text-xs text-gray-500 mt-1">
                지원 형식: PDF, DOC, DOCX, XLS, XLSX, PPT, PPTX, 이미지 파일
              </p>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}