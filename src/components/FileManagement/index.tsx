import React, { useState, useEffect } from 'react';
import { apiUrl } from '../../config/api';
import { 
  Upload, Download, FileText, Trash2, Eye, Search, Filter, 
  FolderOpen, File, AlertCircle, CheckCircle, Clock, RefreshCw 
} from 'lucide-react';
import { Card, Button, Badge, Modal } from '../common';
import { FileUploadModal } from './FileUploadModal';
import { FilePreviewModal } from './FilePreviewModal';
import { useApi } from '../../hooks/useApi';

interface FileItem {
  name: string;
  size: number;
  modified: string;
  type: string;
  category?: string;
}

interface DocumentCategory {
  id: string;
  name: string;
  description: string;
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

export function FileManagement() {
  const [selectedCategory, setSelectedCategory] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);

  const { fetchApi } = useApi();

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    if (selectedCategory) {
      loadFiles(selectedCategory);
    }
  }, [selectedCategory]);

  const loadCategories = async () => {
    try {
      setLoading(true);
      // 카테고리 목록은 로컬 상수 사용
    } catch (error) {
      console.error('카테고리 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFiles = async (categoryId: string) => {
    try {
      setLoading(true);
      const data = await fetchApi<{documents: FileItem[]}>(`/documents/category/${categoryId}`);
      setFiles(data.documents || []);
    } catch (error) {
      console.error('파일 목록 조회 실패:', error);
      setFiles([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (file: File, category: string) => {
    try {
      setIsUploading(true);
      setUploadProgress(0);

      const formData = new FormData();
      formData.append('file', file);
      formData.append('category', category);

      // 업로드 진행률 시뮬레이션
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const response = await fetch(apiUrl('/documents/upload'), {
        method: 'POST',
        body: formData
      });

      clearInterval(progressInterval);
      setUploadProgress(100);

      if (response.ok) {
        const result = await response.json();
        console.log('업로드 성공:', result);
        
        // 파일 목록 새로고침
        if (selectedCategory === category) {
          await loadFiles(category);
        }
        
        setShowUploadModal(false);
        
        // 성공 알림
        setTimeout(() => {
          setUploadProgress(0);
          setIsUploading(false);
        }, 1000);
      } else {
        throw new Error('업로드 실패');
      }
    } catch (error) {
      console.error('파일 업로드 실패:', error);
      setUploadProgress(0);
      setIsUploading(false);
    }
  };

  const handleFileDownload = async (filename: string) => {
    try {
      if (!selectedCategory) return;

      const response = await fetch(apiUrl(`/documents/download/${selectedCategory}/${filename}`));
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('파일 다운로드 실패:', error);
    }
  };

  const handleFileDelete = async (filename: string) => {
    if (!confirm('정말 이 파일을 삭제하시겠습니까?')) return;

    try {
      await fetchApi(`/documents/delete/${selectedCategory}/${filename}`, {
        method: 'DELETE'
      });
      
      // 파일 목록 새로고침
      await loadFiles(selectedCategory);
    } catch (error) {
      console.error('파일 삭제 실패:', error);
    }
  };

  const handleFilePreview = (file: FileItem) => {
    setSelectedFile(file);
    setShowPreviewModal(true);
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'pdf': return <FileText className="w-5 h-5 text-red-500" />;
      case 'xlsx':
      case 'xls': return <FileText className="w-5 h-5 text-green-600" />;
      case 'docx':
      case 'doc': return <FileText className="w-5 h-5 text-blue-600" />;
      case 'hwp': return <FileText className="w-5 h-5 text-purple-600" />;
      default: return <File className="w-5 h-5 text-gray-500" />;
    }
  };

  const getFileSizeString = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const filteredFiles = files.filter(file =>
    file.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getCategoryStats = () => {
    return {
      totalFiles: files.length,
      totalSize: files.reduce((sum, file) => sum + file.size, 0),
      pdfFiles: files.filter(f => f.type.toLowerCase() === 'pdf').length,
      officeFiles: files.filter(f => ['xlsx', 'xls', 'docx', 'doc'].includes(f.type.toLowerCase())).length
    };
  };

  const stats = getCategoryStats();

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">파일 관리</h1>
          <p className="text-gray-600 mt-1">문서 업로드, 다운로드 및 관리</p>
        </div>
        <div className="flex gap-3">
          <Button
            variant="outline"
            onClick={() => selectedCategory && loadFiles(selectedCategory)}
            disabled={!selectedCategory}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            새로고침
          </Button>
          <Button
            onClick={() => setShowUploadModal(true)}
            disabled={!selectedCategory}
          >
            <Upload className="w-4 h-4 mr-2" />
            파일 업로드
          </Button>
        </div>
      </div>

      {/* 업로드 진행률 표시 */}
      {isUploading && (
        <Card>
          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">파일 업로드 중...</span>
              <span className="text-sm text-gray-500">{uploadProgress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* 카테고리 선택 */}
        <div className="lg:col-span-1">
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">문서 카테고리</h3>
              <div className="space-y-2">
                {DOCUMENT_CATEGORIES.map((category) => (
                  <button
                    key={category.id}
                    onClick={() => setSelectedCategory(category.id)}
                    className={`w-full text-left p-3 rounded-lg transition-colors ${
                      selectedCategory === category.id
                        ? 'bg-blue-50 border border-blue-200 text-blue-700'
                        : 'hover:bg-gray-50 border border-transparent'
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <FolderOpen className="w-4 h-4" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{category.name}</p>
                        <p className="text-xs text-gray-500 truncate">{category.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* 파일 목록 */}
        <div className="lg:col-span-3 space-y-6">
          {selectedCategory ? (
            <>
              {/* 통계 및 검색 */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                  <div className="flex items-center">
                    <div className="p-3 bg-blue-100 rounded-full">
                      <FileText className="w-6 h-6 text-blue-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">전체 파일</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.totalFiles}</p>
                    </div>
                  </div>
                </Card>
                
                <Card>
                  <div className="flex items-center">
                    <div className="p-3 bg-green-100 rounded-full">
                      <Download className="w-6 h-6 text-green-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">총 용량</p>
                      <p className="text-lg font-bold text-gray-900">{getFileSizeString(stats.totalSize)}</p>
                    </div>
                  </div>
                </Card>
                
                <Card>
                  <div className="flex items-center">
                    <div className="p-3 bg-red-100 rounded-full">
                      <FileText className="w-6 h-6 text-red-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">PDF 파일</p>
                      <p className="text-2xl font-bold text-red-600">{stats.pdfFiles}</p>
                    </div>
                  </div>
                </Card>
                
                <Card>
                  <div className="flex items-center">
                    <div className="p-3 bg-purple-100 rounded-full">
                      <FileText className="w-6 h-6 text-purple-600" />
                    </div>
                    <div className="ml-4">
                      <p className="text-sm font-medium text-gray-600">Office 파일</p>
                      <p className="text-2xl font-bold text-purple-600">{stats.officeFiles}</p>
                    </div>
                  </div>
                </Card>
              </div>

              {/* 검색 */}
              <Card>
                <div className="flex items-center gap-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="파일명으로 검색..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                  <Badge className="bg-blue-100 text-blue-800">
                    {DOCUMENT_CATEGORIES.find(c => c.id === selectedCategory)?.name}
                  </Badge>
                </div>
              </Card>

              {/* 파일 목록 */}
              <Card>
                <div className="space-y-4">
                  <h3 className="text-lg font-semibold text-gray-800">파일 목록</h3>
                  
                  {loading ? (
                    <div className="text-center py-8">
                      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
                      <p className="text-gray-500 mt-2">파일 목록을 불러오는 중...</p>
                    </div>
                  ) : filteredFiles.length === 0 ? (
                    <div className="text-center py-12">
                      <FileText className="mx-auto h-12 w-12 text-gray-400" />
                      <h3 className="mt-2 text-sm font-medium text-gray-900">파일이 없습니다</h3>
                      <p className="mt-1 text-sm text-gray-500">
                        {searchTerm ? '검색 조건을 변경해보세요.' : '이 카테고리에 업로드된 파일이 없습니다.'}
                      </p>
                      {!searchTerm && (
                        <div className="mt-6">
                          <Button onClick={() => setShowUploadModal(true)}>
                            <Upload className="w-4 h-4 mr-2" />
                            첫 번째 파일 업로드
                          </Button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              파일명
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              크기
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              수정일
                            </th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                              관리
                            </th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {filteredFiles.map((file, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  {getFileIcon(file.type)}
                                  <div className="ml-3">
                                    <p className="text-sm font-medium text-gray-900">{file.name}</p>
                                    <p className="text-sm text-gray-500">{file.type.toUpperCase()}</p>
                                  </div>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {getFileSizeString(file.size)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {new Date(file.modified).toLocaleDateString('ko-KR')}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                <div className="flex gap-2">
                                  <button
                                    onClick={() => handleFilePreview(file)}
                                    className="text-blue-600 hover:text-blue-800"
                                    title="미리보기"
                                  >
                                    <Eye size={16} />
                                  </button>
                                  <button
                                    onClick={() => handleFileDownload(file.name)}
                                    className="text-green-600 hover:text-green-800"
                                    title="다운로드"
                                  >
                                    <Download size={16} />
                                  </button>
                                  <button
                                    onClick={() => handleFileDelete(file.name)}
                                    className="text-red-600 hover:text-red-800"
                                    title="삭제"
                                  >
                                    <Trash2 size={16} />
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
              </Card>
            </>
          ) : (
            <Card>
              <div className="text-center py-12">
                <FolderOpen className="mx-auto h-12 w-12 text-gray-400" />
                <h3 className="mt-2 text-lg font-medium text-gray-900">카테고리를 선택하세요</h3>
                <p className="mt-1 text-sm text-gray-500">
                  왼쪽에서 문서 카테고리를 선택하여 파일을 관리할 수 있습니다.
                </p>
              </div>
            </Card>
          )}
        </div>
      </div>

      {/* 업로드 모달 */}
      {showUploadModal && (
        <FileUploadModal
          isOpen={showUploadModal}
          onClose={() => setShowUploadModal(false)}
          onUpload={handleFileUpload}
          categories={DOCUMENT_CATEGORIES}
          selectedCategory={selectedCategory}
        />
      )}

      {/* 미리보기 모달 */}
      {showPreviewModal && selectedFile && (
        <FilePreviewModal
          isOpen={showPreviewModal}
          onClose={() => setShowPreviewModal(false)}
          file={selectedFile}
          categoryId={selectedCategory}
        />
      )}
    </div>
  );
}