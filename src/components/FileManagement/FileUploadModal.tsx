import React, { useState, useRef, DragEvent } from 'react';
import { Upload, X, FileText, AlertCircle, CheckCircle } from 'lucide-react';
import { Button, Modal } from '../common';

interface DocumentCategory {
  id: string;
  name: string;
  description: string;
}

interface FileUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (file: File, category: string) => Promise<void>;
  categories: DocumentCategory[];
  selectedCategory: string;
}

export function FileUploadModal({ 
  isOpen, 
  onClose, 
  onUpload, 
  categories, 
  selectedCategory 
}: FileUploadModalProps) {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [selectedCategoryId, setSelectedCategoryId] = useState(selectedCategory);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedTypes = [
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx
    'application/vnd.ms-excel', // xls
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // docx
    'application/msword', // doc
    'application/x-hwp' // hwp
  ];

  const allowedExtensions = ['.pdf', '.xlsx', '.xls', '.docx', '.doc', '.hwp'];

  const validateFile = (file: File): boolean => {
    // 파일 크기 체크 (10MB 제한)
    if (file.size > 10 * 1024 * 1024) {
      alert('파일 크기는 10MB 이하만 업로드 가능합니다.');
      return false;
    }

    // 파일 확장자 체크
    const extension = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!allowedExtensions.includes(extension)) {
      alert(`지원하지 않는 파일 형식입니다. 지원 형식: ${allowedExtensions.join(', ')}`);
      return false;
    }

    return true;
  };

  const handleFileSelect = (files: FileList | File[]) => {
    const fileArray = Array.from(files);
    const validFiles = fileArray.filter(validateFile);
    setSelectedFiles(prev => [...prev, ...validFiles]);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    handleFileSelect(e.dataTransfer.files);
  };

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (selectedFiles.length === 0 || !selectedCategoryId) return;

    try {
      setUploading(true);
      setUploadStatus('idle');

      for (const file of selectedFiles) {
        await onUpload(file, selectedCategoryId);
      }

      setUploadStatus('success');
      setSelectedFiles([]);
      
      // 성공 후 2초 뒤에 모달 닫기
      setTimeout(() => {
        onClose();
        setUploadStatus('idle');
      }, 2000);
    } catch (error) {
      console.error('업로드 실패:', error);
      setUploadStatus('error');
    } finally {
      setUploading(false);
    }
  };

  const getFileIcon = (fileName: string) => {
    const extension = fileName.split('.').pop()?.toLowerCase();
    switch (extension) {
      case 'pdf': return <FileText className="w-5 h-5 text-red-500" />;
      case 'xlsx':
      case 'xls': return <FileText className="w-5 h-5 text-green-600" />;
      case 'docx':
      case 'doc': return <FileText className="w-5 h-5 text-blue-600" />;
      case 'hwp': return <FileText className="w-5 h-5 text-purple-600" />;
      default: return <FileText className="w-5 h-5 text-gray-500" />;
    }
  };

  const getFileSizeString = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="파일 업로드"
      size="lg"
    >
      <div className="space-y-6">
        {/* 카테고리 선택 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            업로드 카테고리 <span className="text-red-500">*</span>
          </label>
          <select
            value={selectedCategoryId}
            onChange={(e) => setSelectedCategoryId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">카테고리를 선택하세요</option>
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name} - {category.description}
              </option>
            ))}
          </select>
        </div>

        {/* 파일 업로드 영역 */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            파일 선택
          </label>
          <div
            className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
              dragOver
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-300 hover:border-gray-400'
            }`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <p className="text-lg font-medium text-gray-700 mb-2">
              파일을 드래그 앤 드롭하거나 클릭하여 선택
            </p>
            <p className="text-sm text-gray-500 mb-4">
              지원 형식: PDF, Excel, Word, HWP (최대 10MB)
            </p>
            <Button
              variant="outline"
              onClick={() => fileInputRef.current?.click()}
            >
              파일 선택
            </Button>
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept={allowedExtensions.join(',')}
              onChange={(e) => e.target.files && handleFileSelect(e.target.files)}
              className="hidden"
            />
          </div>
        </div>

        {/* 선택된 파일 목록 */}
        {selectedFiles.length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-gray-700 mb-3">선택된 파일 ({selectedFiles.length}개)</h4>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {selectedFiles.map((file, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    {getFileIcon(file.name)}
                    <div>
                      <p className="text-sm font-medium text-gray-900">{file.name}</p>
                      <p className="text-xs text-gray-500">{getFileSizeString(file.size)}</p>
                    </div>
                  </div>
                  <button
                    onClick={() => removeFile(index)}
                    className="text-red-500 hover:text-red-700"
                    disabled={uploading}
                  >
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 업로드 상태 */}
        {uploadStatus === 'success' && (
          <div className="flex items-center p-4 bg-green-50 border border-green-200 rounded-lg">
            <CheckCircle className="w-5 h-5 text-green-600 mr-3" />
            <p className="text-sm text-green-700">파일이 성공적으로 업로드되었습니다.</p>
          </div>
        )}

        {uploadStatus === 'error' && (
          <div className="flex items-center p-4 bg-red-50 border border-red-200 rounded-lg">
            <AlertCircle className="w-5 h-5 text-red-600 mr-3" />
            <p className="text-sm text-red-700">파일 업로드 중 오류가 발생했습니다.</p>
          </div>
        )}

        {/* 안내 정보 */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center mt-0.5">
              <div className="w-2 h-2 bg-white rounded-full"></div>
            </div>
            <div>
              <h4 className="font-medium text-blue-900 mb-1">파일 업로드 안내</h4>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• 지원 형식: PDF, Excel (xlsx, xls), Word (docx, doc), HWP</li>
                <li>• 파일 크기: 최대 10MB</li>
                <li>• 여러 파일 동시 업로드 가능</li>
                <li>• 드래그 앤 드롭 지원</li>
              </ul>
            </div>
          </div>
        </div>

        {/* 액션 버튼 */}
        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="secondary" onClick={onClose} disabled={uploading}>
            취소
          </Button>
          <Button
            onClick={handleUpload}
            disabled={selectedFiles.length === 0 || !selectedCategoryId || uploading}
          >
            {uploading ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                업로드 중...
              </>
            ) : (
              <>
                <Upload size={16} className="mr-2" />
                업로드 ({selectedFiles.length}개)
              </>
            )}
          </Button>
        </div>
      </div>
    </Modal>
  );
}