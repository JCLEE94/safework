import React, { useState, useEffect } from 'react';
import { apiUrl } from '../config/api';
import { Upload, Download, Edit, Trash2, FileText, Table, FileImage, AlertCircle, CheckCircle } from 'lucide-react';

interface DocumentInfo {
  name: string;
  path: string;
  size: number;
  category: string;
  format: string;
  created_at: string;
  modified_at: string;
  editable: boolean;
}

interface DocumentCategory {
  name: string;
  path: string;
}

interface DocumentStats {
  total_documents: number;
  by_category: Record<string, number>;
  by_format: Record<string, number>;
  editable_count: number;
  total_size: number;
}

const IntegratedDocuments: React.FC = () => {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [categories, setCategories] = useState<Record<string, DocumentCategory>>({});
  const [stats, setStats] = useState<DocumentStats | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [selectedFormat, setSelectedFormat] = useState<string>('');
  const [editableOnly, setEditableOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string>('');
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState<string>('');
  const [editingDocument, setEditingDocument] = useState<DocumentInfo | null>(null);
  const [editData, setEditData] = useState<any>({});

  // API 호출 함수들
  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (selectedCategory) params.append('category', selectedCategory);
      if (selectedFormat) params.append('format', selectedFormat);
      if (editableOnly) params.append('editable_only', 'true');

      const response = await fetch(`/api/v1/documents/?${params.toString()}`);
      if (!response.ok) throw new Error('문서 목록을 불러오는데 실패했습니다');
      
      const data = await response.json();
      setDocuments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await fetch('/api/v1/documents/categories');
      if (!response.ok) throw new Error('카테고리를 불러오는데 실패했습니다');
      
      const data = await response.json();
      setCategories(data);
    } catch (err) {
      console.error('카테고리 로드 실패:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/documents/stats');
      if (!response.ok) throw new Error('통계를 불러오는데 실패했습니다');
      
      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('통계 로드 실패:', err);
    }
  };

  const handleUpload = async () => {
    if (!uploadFile || !uploadCategory) {
      setError('파일과 카테고리를 선택해주세요');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('category', uploadCategory);

      const response = await fetch('/api/v1/documents/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('파일 업로드에 실패했습니다');

      setUploadFile(null);
      setUploadCategory('');
      await fetchDocuments();
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : '업로드 실패');
    }
  };

  const handleDownload = async (doc: DocumentInfo) => {
    try {
      const response = await fetch(`/api/v1/documents/download/${doc.category}/${encodeURIComponent(doc.name)}`);
      if (!response.ok) throw new Error('다운로드에 실패했습니다');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = doc.name;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err instanceof Error ? err.message : '다운로드 실패');
    }
  };

  const handleEdit = async (doc: DocumentInfo) => {
    if (!doc.editable) {
      setError('편집할 수 없는 파일 형식입니다');
      return;
    }

    try {
      const editRequest = {
        document_id: doc.name,
        edit_type: 'data',
        data: editData
      };

      const response = await fetch('/api/v1/documents/edit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(editRequest),
      });

      if (!response.ok) throw new Error('편집에 실패했습니다');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `edited_${doc.name}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setEditingDocument(null);
      setEditData({});
    } catch (err) {
      setError(err instanceof Error ? err.message : '편집 실패');
    }
  };

  const handleDelete = async (doc: DocumentInfo) => {
    if (!confirm(`"${doc.name}" 파일을 삭제하시겠습니까?`)) return;

    try {
      const response = await fetch(`/api/v1/documents/${doc.category}/${encodeURIComponent(doc.name)}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('삭제에 실패했습니다');

      await fetchDocuments();
      await fetchStats();
    } catch (err) {
      setError(err instanceof Error ? err.message : '삭제 실패');
    }
  };

  const getFormatIcon = (format: string) => {
    switch (format) {
      case 'pdf': return <FileText className="h-5 w-5 text-red-500" />;
      case 'excel': return <Table className="h-5 w-5 text-green-500" />;
      case 'word': return <FileText className="h-5 w-5 text-blue-500" />;
      case 'hwp': return <FileImage className="h-5 w-5 text-purple-500" />;
      default: return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  useEffect(() => {
    fetchCategories();
    fetchStats();
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [selectedCategory, selectedFormat, editableOnly]);

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">통합문서관리 시스템</h1>
        <p className="text-gray-600">PDF, Excel, Word 문서를 편집하고 관리하세요</p>
      </div>

      {/* 오류 메시지 */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-center">
          <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
          <span className="text-red-700">{error}</span>
          <button 
            onClick={() => setError('')}
            className="ml-auto text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}

      {/* 통계 대시보드 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">전체 문서</div>
            <div className="text-2xl font-bold text-blue-600">{stats.total_documents}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">편집 가능</div>
            <div className="text-2xl font-bold text-green-600">{stats.editable_count}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">전체 크기</div>
            <div className="text-2xl font-bold text-purple-600">{formatFileSize(stats.total_size)}</div>
          </div>
          <div className="bg-white p-4 rounded-lg shadow">
            <div className="text-sm text-gray-600">카테고리</div>
            <div className="text-2xl font-bold text-orange-600">{Object.keys(stats.by_category).length}</div>
          </div>
        </div>
      )}

      {/* 파일 업로드 */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Upload className="h-5 w-5 mr-2" />
          문서 업로드
        </h2>
        <div className="flex flex-wrap items-center gap-4">
          <input
            type="file"
            onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
            className="flex-1 min-w-0"
            accept=".pdf,.xlsx,.xls,.docx,.doc,.hwp"
          />
          <select
            value={uploadCategory}
            onChange={(e) => setUploadCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">카테고리 선택</option>
            {Object.entries(categories).map(([key, category]) => (
              <option key={key} value={key}>
                {category.name}
              </option>
            ))}
          </select>
          <button
            onClick={handleUpload}
            disabled={!uploadFile || !uploadCategory}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-300"
          >
            업로드
          </button>
        </div>
      </div>

      {/* 필터 */}
      <div className="bg-white p-4 rounded-lg shadow mb-6">
        <div className="flex flex-wrap items-center gap-4">
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">모든 카테고리</option>
            {Object.entries(categories).map(([key, category]) => (
              <option key={key} value={key}>
                {category.name}
              </option>
            ))}
          </select>
          
          <select
            value={selectedFormat}
            onChange={(e) => setSelectedFormat(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="">모든 형식</option>
            <option value="pdf">PDF</option>
            <option value="excel">Excel</option>
            <option value="word">Word</option>
            <option value="hwp">HWP</option>
          </select>
          
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={editableOnly}
              onChange={(e) => setEditableOnly(e.target.checked)}
              className="mr-2"
            />
            편집 가능한 파일만
          </label>
        </div>
      </div>

      {/* 문서 목록 */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold">문서 목록</h2>
        </div>
        
        {loading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">문서를 불러오는 중...</p>
          </div>
        ) : documents.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            문서가 없습니다.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">파일명</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">카테고리</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">형식</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">크기</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">수정일</th>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">작업</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {documents.map((doc, index) => (
                  <tr key={index} className="hover:bg-gray-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center">
                        {getFormatIcon(doc.format)}
                        <span className="ml-2">{doc.name}</span>
                        {doc.editable && (
                          <CheckCircle className="h-4 w-4 text-green-500 ml-2" />
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {categories[doc.category]?.name || doc.category}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {doc.format.toUpperCase()}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {formatFileSize(doc.size)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {new Date(doc.modified_at).toLocaleDateString('ko-KR')}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleDownload(doc)}
                          className="p-1 text-blue-600 hover:text-blue-800"
                          title="다운로드"
                        >
                          <Download className="h-4 w-4" />
                        </button>
                        {doc.editable && (
                          <button
                            onClick={() => setEditingDocument(doc)}
                            className="p-1 text-green-600 hover:text-green-800"
                            title="편집"
                          >
                            <Edit className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleDelete(doc)}
                          className="p-1 text-red-600 hover:text-red-800"
                          title="삭제"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 편집 모달 */}
      {editingDocument && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold mb-4">문서 편집: {editingDocument.name}</h3>
            
            {editingDocument.format === 'pdf' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">텍스트 추가</label>
                  <textarea
                    value={editData.text || ''}
                    onChange={(e) => setEditData({ ...editData, text: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    rows={3}
                    placeholder="추가할 텍스트를 입력하세요"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="block text-sm font-medium mb-1">X 좌표</label>
                    <input
                      type="number"
                      value={editData.x || 100}
                      onChange={(e) => setEditData({ ...editData, x: parseInt(e.target.value) })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Y 좌표</label>
                    <input
                      type="number"
                      value={editData.y || 100}
                      onChange={(e) => setEditData({ ...editData, y: parseInt(e.target.value) })}
                      className="w-full p-2 border border-gray-300 rounded-md"
                    />
                  </div>
                </div>
              </div>
            )}

            {editingDocument.format === 'excel' && (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium mb-1">셀 주소</label>
                  <input
                    type="text"
                    value={editData.cell || 'A1'}
                    onChange={(e) => setEditData({ ...editData, cell: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="A1"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">값</label>
                  <input
                    type="text"
                    value={editData.value || ''}
                    onChange={(e) => setEditData({ ...editData, value: e.target.value })}
                    className="w-full p-2 border border-gray-300 rounded-md"
                    placeholder="셀에 입력할 값"
                  />
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setEditingDocument(null);
                  setEditData({});
                }}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                취소
              </button>
              <button
                onClick={() => handleEdit(editingDocument)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                편집 완료
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default IntegratedDocuments;