/**
 * 통합 문서관리 시스템
 * Unified Document Management System
 * 
 * 기존의 DocumentManagement, FileManagement, PDFForms를 통합
 * DocumentWorkspace와 함께 완전한 문서 관리 솔루션 제공
 */

import React, { useState, useEffect } from 'react';
import { apiUrl } from '../../config/api';
import { 
  FileText, FolderOpen, Plus, Download, Upload, Search, 
  Filter, Edit, Eye, Trash2, Settings, FileEdit, File,
  RefreshCw, AlertCircle, CheckCircle, BarChart, Activity,
  Users, Archive, Share2, Clock
} from 'lucide-react';
import { Card, Button, Badge, Modal } from '../common';
import { useApi } from '../../hooks/useApi';
import { PDFFormEditor } from '../PDFFormEditor';
import { DocumentWorkspace } from './DocumentWorkspace';
import { EDITABLE_FORMS, EditableForm, getEditableFormsByCategory } from '../../services/editableForms';

// 탭 정의
type DocumentTab = 'workspace' | 'editable-forms' | 'categories' | 'analytics';

interface DocumentFile {
  id: string;
  name: string;
  size: number;
  modified: string;
  type: string;
  category: string;
  path: string;
  status?: 'available' | 'processing' | 'error';
}

interface PDFForm {
  id: string;
  name: string;
  name_korean: string;
  description: string;
  category: string;
  fields: string[];
  template_path?: string;
}

interface DocumentCategory {
  id: string;
  name: string;
  description: string;
  file_count: number;
  last_updated: string;
}

const DOCUMENT_CATEGORIES = [
  { id: 'manual', name: '01-업무매뉴얼', description: '업무 매뉴얼 및 지침서' },
  { id: 'legal', name: '02-법정서식', description: '법정 서식 및 양식' },
  { id: 'register', name: '03-관리대장', description: '각종 관리대장' },
  { id: 'checklist', name: '04-체크리스트', description: '점검 체크리스트' },
  { id: 'education', name: '05-교육자료', description: '안전보건교육 자료' },
  { id: 'msds', name: '06-MSDS관련', description: 'MSDS 관련 자료' },
  { id: 'special', name: '07-특별관리물질', description: '특별관리물질 관련' },
  { id: 'health', name: '08-건강관리', description: '건강관리 관련 문서' },
  { id: 'reference', name: '09-참고자료', description: '참고 자료 및 문서' },
  { id: 'latest', name: '10-최신자료_2024-2025', description: '최신 자료 및 업데이트' }
];

export function UnifiedDocuments() {
  const [activeTab, setActiveTab] = useState<DocumentTab>('workspace');
  const [editableForms, setEditableForms] = useState<EditableForm[]>(EDITABLE_FORMS);
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showFormModal, setShowFormModal] = useState(false);
  const [selectedForm, setSelectedForm] = useState<EditableForm | null>(null);
  const [editingData, setEditingData] = useState<Record<string, string>>({});
  
  const { fetchApi } = useApi();

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    try {
      switch (activeTab) {
        case 'editable-forms':
          // 편집 가능한 양식은 이미 로드됨
          break;
        case 'categories':
          await loadCategories();
          break;
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFiles = async () => {
    try {
      const data = await fetchApi(apiUrl('/documents/files'));
      setFiles(data || []);
    } catch (error) {
      console.error('Failed to load files:', error);
      setFiles([]);
    }
  };

  const loadPDFForms = async () => {
    try {
      const data = await fetchApi(apiUrl('/documents/pdf-forms'));
      // API returns { forms: [...] } structure
      setPdfForms(data?.forms || []);
    } catch (error) {
      console.error('Failed to load PDF forms:', error);
      setPdfForms([]);
    }
  };

  const loadCategories = async () => {
    try {
      const data = await fetchApi(apiUrl('/documents/categories'));
      setCategories(data || DOCUMENT_CATEGORIES.map(cat => ({
        ...cat,
        file_count: 0,
        last_updated: new Date().toISOString()
      })));
    } catch (error) {
      console.error('Failed to load categories:', error);
      setCategories(DOCUMENT_CATEGORIES.map(cat => ({
        ...cat,
        file_count: 0,
        last_updated: new Date().toISOString()
      })));
    }
  };

  const handleTabChange = (tab: DocumentTab) => {
    setActiveTab(tab);
    setSearchTerm('');
    setSelectedCategory('');
  };

  const handleFileAction = async (action: string, file: DocumentFile) => {
    switch (action) {
      case 'download':
        // Implement download
        window.open(`/api/v1/documents/download/${file.id}`, '_blank');
        break;
      case 'view':
        setSelectedFile(file);
        // Show preview modal
        break;
      case 'delete':
        if (confirm('파일을 삭제하시겠습니까?')) {
          try {
            await fetchApi(`/api/v1/documents/files/${file.id}`, { method: 'DELETE' });
            await loadFiles();
          } catch (error) {
            console.error('Failed to delete file:', error);
          }
        }
        break;
    }
  };

  const handleFormAction = async (action: string, form: EditableForm) => {
    switch (action) {
      case 'edit':
        setSelectedForm(form);
        setShowFormModal(true);
        break;
      case 'view':
        // 문서 파일 다운로드하여 보기
        try {
          const response = await fetch(`/api/v1/document-editor/view/${form.file_path}`);
          if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            window.open(url, '_blank');
          }
        } catch (error) {
          console.error('View failed:', error);
          alert('문서 보기에 실패했습니다.');
        }
        break;
      case 'download':
        // 원본 템플릿 다운로드
        try {
          const response = await fetch(`/api/v1/document-editor/download/${form.file_path}`);
          if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${form.korean_name}_template.${form.file_path.split('.').pop()}`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
          }
        } catch (error) {
          console.error('Download failed:', error);
          alert('다운로드에 실패했습니다.');
        }
        break;
    }
  };

  const filteredFiles = files.filter(file => {
    const matchesSearch = !searchTerm || 
      file.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || file.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const filteredForms = editableForms.filter(form => {
    const matchesSearch = !searchTerm || 
      form.korean_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      form.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      form.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || form.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const renderTabContent = () => {
    switch (activeTab) {
      case 'workspace':
        return <DocumentWorkspace />;
      case 'editable-forms':
        return renderEditableFormsTab();
      case 'categories':
        return renderCategoriesTab();
      case 'analytics':
        return renderAnalyticsTab();
      default:
        return <DocumentWorkspace />;
    }
  };

  const renderFilesTab = () => (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="파일 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">모든 카테고리</option>
            {DOCUMENT_CATEGORIES.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => loadFiles()} variant="outline">
            <RefreshCw size={16} className="mr-2" />
            새로고침
          </Button>
          <Button onClick={() => setShowUploadModal(true)}>
            <Upload size={16} className="mr-2" />
            파일 업로드
          </Button>
        </div>
      </div>

      {/* Files Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="animate-spin" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredFiles.map(file => (
            <Card key={file.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center min-w-0 flex-1">
                    <FileText className="text-blue-600 mr-3 flex-shrink-0" size={24} />
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 text-lg truncate">{file.name}</h3>
                      <p className="text-sm text-gray-600 mt-1">
                        {(file.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Badge color={file.status === 'available' ? 'green' : 'yellow'} className="ml-2 flex-shrink-0">
                    {file.status === 'available' ? '사용가능' : '처리중'}
                  </Badge>
                </div>
                
                {/* Category and Date */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {DOCUMENT_CATEGORIES.find(cat => cat.id === file.category)?.name || file.category || '기타'}
                    </span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {new Date(file.modified).toLocaleDateString()}
                  </span>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t border-gray-100">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFileAction('view', file)}
                    className="flex-1"
                  >
                    <Eye size={16} className="mr-1" />
                    보기
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFileAction('download', file)}
                    className="flex-1"
                  >
                    <Download size={16} className="mr-1" />
                    다운로드
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFileAction('delete', file)}
                    className="text-red-600 hover:text-red-700"
                  >
                    <Trash2 size={16} />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {filteredFiles.length === 0 && !loading && (
        <div className="text-center py-12">
          <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">파일이 없습니다</h3>
          <p className="mt-1 text-sm text-gray-500">파일을 업로드하여 시작하세요.</p>
          <div className="mt-6">
            <Button onClick={() => setShowUploadModal(true)}>
              <Upload size={16} className="mr-2" />
              파일 업로드
            </Button>
          </div>
        </div>
      )}
    </div>
  );

  const renderPDFFormsTab = () => (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="양식 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">모든 카테고리</option>
            {DOCUMENT_CATEGORIES.map(category => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => loadPDFForms()} variant="outline">
            <RefreshCw size={16} className="mr-2" />
            새로고침
          </Button>
        </div>
      </div>

      {/* PDF Forms Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="animate-spin" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredForms.map(form => (
            <Card key={form.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center min-w-0 flex-1">
                    <FileEdit className="text-green-600 mr-3 flex-shrink-0" size={24} />
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 text-lg truncate">{form.name_korean}</h3>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">{form.description}</p>
                    </div>
                  </div>
                  <Badge color="blue" className="ml-2 flex-shrink-0">
                    {form.fields?.length || 0}개 필드
                  </Badge>
                </div>
                
                {/* Category */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {DOCUMENT_CATEGORIES.find(cat => cat.id === form.category)?.name || form.category}
                    </span>
                  </div>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t border-gray-100">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFormAction('preview', form)}
                    className="flex-1"
                  >
                    <Eye size={16} className="mr-1" />
                    미리보기
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleFormAction('fill', form)}
                    className="flex-1"
                  >
                    <Edit size={16} className="mr-1" />
                    편집
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFormAction('download', form)}
                  >
                    <Download size={16} />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {filteredForms.length === 0 && !loading && (
        <div className="text-center py-12">
          <FileEdit className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">PDF 양식이 없습니다</h3>
          <p className="mt-1 text-sm text-gray-500">사용 가능한 PDF 양식을 확인하세요.</p>
        </div>
      )}
    </div>
  );

  const renderEditableFormsTab = () => (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between">
        <div className="flex gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="편집 양식 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="">모든 카테고리</option>
            {DOCUMENT_CATEGORIES.map(category => (
              <option key={category.id} value={category.name}>
                {category.name}
              </option>
            ))}
          </select>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => loadData()} variant="outline">
            <RefreshCw size={16} className="mr-2" />
            새로고침
          </Button>
        </div>
      </div>

      {/* Editable Forms Grid */}
      {loading ? (
        <div className="flex justify-center items-center h-64">
          <RefreshCw className="animate-spin" size={32} />
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {filteredForms.map(form => (
            <Card key={form.id} className="p-6 hover:shadow-lg transition-shadow">
              <div className="space-y-4">
                {/* Header */}
                <div className="flex items-start justify-between">
                  <div className="flex items-center min-w-0 flex-1">
                    <FileEdit className="text-green-600 mr-3 flex-shrink-0" size={24} />
                    <div className="min-w-0">
                      <h3 className="font-semibold text-gray-900 text-lg truncate">{form.korean_name}</h3>
                      <p className="text-sm text-gray-600 mt-1 line-clamp-2">{form.description}</p>
                    </div>
                  </div>
                  <Badge color="blue" className="ml-2 flex-shrink-0">
                    {form.template_type}
                  </Badge>
                </div>
                
                {/* Category and File Path */}
                <div className="space-y-2">
                  <div className="flex items-center">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      {form.category}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 truncate">{form.file_path}</p>
                </div>
                
                {/* Actions */}
                <div className="flex gap-2 pt-2 border-t border-gray-100">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFormAction('view', form)}
                    className="flex-1"
                  >
                    <Eye size={16} className="mr-1" />
                    보기
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => handleFormAction('edit', form)}
                    className="flex-1"
                  >
                    <Edit size={16} className="mr-1" />
                    편집
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleFormAction('download', form)}
                  >
                    <Download size={16} />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {filteredForms.length === 0 && !loading && (
        <div className="text-center py-12">
          <FileEdit className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">편집 가능한 양식이 없습니다</h3>
          <p className="mt-1 text-sm text-gray-500">검색 조건을 변경하여 다시 시도하세요.</p>
        </div>
      )}
    </div>
  );

  const renderCategoriesTab = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {categories.map(category => (
          <Card key={category.id} className="p-6 hover:shadow-lg transition-shadow cursor-pointer">
            <div className="space-y-4">
              {/* Header */}
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <FolderOpen className="text-blue-600 mr-3" size={28} />
                  <div>
                    <h3 className="font-semibold text-gray-900 text-lg">{category.name}</h3>
                  </div>
                </div>
                <Badge color="gray" className="flex-shrink-0">
                  {category.file_count}개 파일
                </Badge>
              </div>
              
              {/* Description */}
              <p className="text-sm text-gray-600 leading-relaxed">{category.description}</p>
              
              {/* Footer */}
              <div className="flex justify-between items-center pt-2 border-t border-gray-100">
                <span className="text-xs text-gray-500">최근 업데이트</span>
                <span className="text-xs text-gray-600 font-medium">
                  {new Date(category.last_updated).toLocaleDateString()}
                </span>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderAnalyticsTab = () => (
    <div className="space-y-6">
      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">총 문서</p>
              <p className="text-2xl font-bold text-blue-600">{files.length}</p>
            </div>
            <FileText className="text-blue-600" size={32} />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">PDF 양식</p>
              <p className="text-2xl font-bold text-green-600">{pdfForms.length}</p>
            </div>
            <FileEdit className="text-green-600" size={32} />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">카테고리</p>
              <p className="text-2xl font-bold text-orange-600">{categories.length}</p>
            </div>
            <FolderOpen className="text-orange-600" size={32} />
          </div>
        </Card>
        
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">활성 사용자</p>
              <p className="text-2xl font-bold text-purple-600">12</p>
            </div>
            <Users className="text-purple-600" size={32} />
          </div>
        </Card>
      </div>

      {/* 활동 분석 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">카테고리별 문서 분포</h3>
          <div className="space-y-3">
            {categories.map(category => (
              <div key={category.id} className="flex items-center justify-between">
                <span className="text-sm text-gray-600">{category.name}</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full" 
                      style={{ width: `${Math.min((category.file_count / Math.max(...categories.map(c => c.file_count), 1)) * 100, 100)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-medium">{category.file_count}</span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card className="p-6">
          <h3 className="text-lg font-semibold text-gray-800 mb-4">최근 활동</h3>
          <div className="space-y-3">
            {[
              { action: '업로드', file: '건강검진 결과서.pdf', user: '김관리자', time: '2시간 전' },
              { action: '편집', file: '안전교육 이수증', user: '이담당자', time: '4시간 전' },
              { action: '다운로드', file: 'MSDS 신청서', user: '박보건', time: '6시간 전' },
              { action: '승인', file: '사고보고서 양식', user: '최관리자', time: '1일 전' }
            ].map((activity, index) => (
              <div key={index} className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm text-gray-900">
                    <span className="font-medium">{activity.user}</span>가 
                    <span className="text-blue-600 mx-1">{activity.file}</span>를 
                    {activity.action}했습니다
                  </p>
                  <p className="text-xs text-gray-500">{activity.time}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* 사용 추세 */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">문서 사용 추세</h3>
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <BarChart className="mx-auto text-gray-400" size={48} />
          <p className="text-gray-600 mt-2">문서 사용 통계 차트</p>
          <p className="text-sm text-gray-500">차트 라이브러리 통합 예정</p>
        </div>
      </Card>
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">통합 문서관리</h1>
        <div className="flex items-center gap-2">
          <Badge color="green">
            <CheckCircle size={14} className="mr-1" />
            통합완료
          </Badge>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'workspace', name: '통합 작업공간', icon: Activity },
            { id: 'editable-forms', name: '편집 양식', icon: FileEdit },
            { id: 'categories', name: '카테고리', icon: FolderOpen },
            { id: 'analytics', name: '분석', icon: BarChart },
          ].map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id as DocumentTab)}
                className={`
                  whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm flex items-center gap-2
                  ${activeTab === tab.id
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }
                `}
              >
                <Icon size={16} />
                {tab.name}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      {renderTabContent()}

      {/* Modals */}
      {showUploadModal && (
        <Modal onClose={() => setShowUploadModal(false)}>
          <div className="p-6">
            <h2 className="text-lg font-semibold mb-4">파일 업로드</h2>
            {/* File upload component */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p className="text-gray-600">파일을 여기에 드래그하거나 클릭하여 선택하세요</p>
            </div>
          </div>
        </Modal>
      )}

      {showFormModal && selectedForm && (
        <PDFFormEditor 
          form={selectedForm}
          onClose={() => {
            setShowFormModal(false);
            setSelectedForm(null);
          }}
          onSave={(data) => {
            console.log('Form saved:', data);
            setShowFormModal(false);
            setSelectedForm(null);
          }}
        />
      )}
    </div>
  );
}