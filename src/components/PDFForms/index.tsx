import React, { useState, useEffect } from 'react';
import { Plus, Download, Eye, Edit, FileText, Upload, Calendar, Settings } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { PDFFormModal } from './PDFFormModal';
import { PDFPreviewModal } from './PDFPreviewModal';
import { useApi } from '../../hooks/useApi';

interface PDFForm {
  id: string;
  name: string;
  name_korean: string;
  description: string;
  category: string;
}

interface DocumentCategory {
  id: string;
  name: string;
  description: string;
}

interface FormTemplate {
  id: string;
  name: string;
  fields: string[];
  description: string;
}

export function PDFForms() {
  const [forms, setForms] = useState<PDFForm[]>([]);
  const [categories, setCategories] = useState<DocumentCategory[]>([]);
  const [templates, setTemplates] = useState<FormTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showFormModal, setShowFormModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedForm, setSelectedForm] = useState<PDFForm | null>(null);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  
  const { fetchApi } = useApi();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // Load all data in parallel
      const [formsData, categoriesData, templatesData] = await Promise.all([
        fetchApi<{forms: PDFForm[]}>('/documents/pdf-forms'),
        fetchApi<{categories: DocumentCategory[]}>('/documents/categories'),
        fetchApi<{templates: FormTemplate[]}>('/documents/templates')
      ]);

      setForms(formsData.forms || []);
      setCategories(categoriesData.categories || []);
      setTemplates(templatesData.templates || []);
    } catch (error) {
      console.error('데이터 로드 실패:', error);
      setForms([]);
      setCategories([]);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateForm = (form: PDFForm) => {
    setSelectedForm(form);
    setShowFormModal(true);
  };

  const handlePreviewForm = async (form: PDFForm) => {
    setSelectedForm(form);
    setShowPreviewModal(true);
  };

  const handleDownloadForm = async (form: PDFForm) => {
    try {
      const response = await fetch(`/api/v1/documents/preview/${form.id}`, {
        method: 'GET'
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
      }
    } catch (error) {
      console.error('다운로드 실패:', error);
    }
  };

  const getCategoryName = (categoryId: string) => {
    const category = categories.find(c => c.id === categoryId);
    return category?.name || categoryId;
  };

  const getCategoryBadgeColor = (category: string) => {
    switch (category) {
      case '관리대장': return 'bg-blue-100 text-blue-800';
      case '건강관리': return 'bg-green-100 text-green-800';
      case '특별관리물질': return 'bg-red-100 text-red-800';
      case '법정서식': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredForms = forms.filter(form => {
    const matchesSearch = form.name_korean.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         form.description.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = !selectedCategory || form.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">PDF 양식 관리</h1>
          <p className="text-gray-600 mt-1">건설업 보건관리 PDF 양식 작성 및 관리</p>
        </div>
        <div className="flex gap-3">
          <Button variant="outline" onClick={loadData}>
            <Settings className="w-4 h-4 mr-2" />
            새로고침
          </Button>
        </div>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <div className="flex flex-col md:flex-row gap-4 items-center">
          <div className="flex-1 relative">
            <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="양식명이나 설명으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <div className="flex gap-2">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">모든 카테고리</option>
              <option value="관리대장">관리대장</option>
              <option value="건강관리">건강관리</option>
              <option value="특별관리물질">특별관리물질</option>
              <option value="법정서식">법정서식</option>
            </select>
          </div>
        </div>
      </Card>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-full">
              <FileText className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">전체 양식</p>
              <p className="text-2xl font-bold text-gray-900">{forms.length}</p>
            </div>
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-full">
              <Download className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">관리대장</p>
              <p className="text-2xl font-bold text-green-600">
                {forms.filter(f => f.category === '관리대장').length}
              </p>
            </div>
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-full">
              <Calendar className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">건강관리</p>
              <p className="text-2xl font-bold text-purple-600">
                {forms.filter(f => f.category === '건강관리').length}
              </p>
            </div>
          </div>
        </Card>
        
        <Card>
          <div className="flex items-center">
            <div className="p-3 bg-red-100 rounded-full">
              <Upload className="w-6 h-6 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">특별관리</p>
              <p className="text-2xl font-bold text-red-600">
                {forms.filter(f => f.category === '특별관리물질').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* PDF 양식 목록 */}
      <Card>
        <div className="space-y-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">사용 가능한 PDF 양식</h2>
          
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="text-gray-500 mt-2">양식 목록을 불러오는 중...</p>
            </div>
          ) : filteredForms.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">양식이 없습니다</h3>
              <p className="mt-1 text-sm text-gray-500">
                {searchTerm || selectedCategory ? '검색 조건을 변경해보세요.' : '사용 가능한 PDF 양식이 없습니다.'}
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredForms.map((form) => (
                <div
                  key={form.id}
                  className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow duration-200"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900 mb-1">{form.name_korean}</h3>
                      <p className="text-sm text-gray-600 mb-2">{form.description}</p>
                      <Badge className={getCategoryBadgeColor(form.category)}>
                        {form.category}
                      </Badge>
                    </div>
                  </div>
                  
                  <div className="flex gap-2 mt-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handlePreviewForm(form)}
                      className="flex-1"
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      미리보기
                    </Button>
                    <Button
                      size="sm"
                      onClick={() => handleCreateForm(form)}
                      className="flex-1"
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      작성하기
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleDownloadForm(form)}
                    >
                      <Download className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </Card>

      {/* Modals */}
      {showFormModal && selectedForm && (
        <PDFFormModal
          isOpen={showFormModal}
          onClose={() => setShowFormModal(false)}
          form={selectedForm}
        />
      )}

      {showPreviewModal && selectedForm && (
        <PDFPreviewModal
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          form={selectedForm}
        />
      )}
    </div>
  );
}