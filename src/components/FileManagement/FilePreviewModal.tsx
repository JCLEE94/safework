import React, { useState, useEffect } from 'react';
import { X, Download, ExternalLink, Eye, FileText, AlertCircle } from 'lucide-react';
import { Button, Modal } from '../common';

interface FileItem {
  name: string;
  size: number;
  modified: string;
  type: string;
}

interface FilePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  file: FileItem;
  categoryId: string;
}

export function FilePreviewModal({ isOpen, onClose, file, categoryId }: FilePreviewModalProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (isOpen && file) {
      loadPreview();
    }
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [isOpen, file, categoryId]);

  const loadPreview = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(`/api/v1/documents/download/${categoryId}/${file.name}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setPreviewUrl(url);
      } else {
        throw new Error('파일을 불러올 수 없습니다.');
      }
    } catch (error) {
      console.error('파일 미리보기 로드 실패:', error);
      setError('파일 미리보기를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/v1/documents/download/${categoryId}/${file.name}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = file.name;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('파일 다운로드 실패:', error);
    }
  };

  const openInNewTab = () => {
    if (previewUrl) {
      window.open(previewUrl, '_blank');
    }
  };

  const getFileSizeString = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (fileType: string) => {
    switch (fileType.toLowerCase()) {
      case 'pdf': return <FileText className="w-6 h-6 text-red-500" />;
      case 'xlsx':
      case 'xls': return <FileText className="w-6 h-6 text-green-600" />;
      case 'docx':
      case 'doc': return <FileText className="w-6 h-6 text-blue-600" />;
      case 'hwp': return <FileText className="w-6 h-6 text-purple-600" />;
      default: return <FileText className="w-6 h-6 text-gray-500" />;
    }
  };

  const canPreview = (fileType: string) => {
    const previewableTypes = ['pdf'];
    return previewableTypes.includes(fileType.toLowerCase());
  };

  const renderPreviewContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">파일을 불러오는 중...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <AlertCircle className="mx-auto h-12 w-12 text-red-500 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">미리보기 실패</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button onClick={handleDownload}>
              <Download className="w-4 h-4 mr-2" />
              파일 다운로드
            </Button>
          </div>
        </div>
      );
    }

    if (!canPreview(file.type)) {
      return (
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            {getFileIcon(file.type)}
            <h3 className="text-lg font-medium text-gray-900 mb-2 mt-4">미리보기 지원하지 않음</h3>
            <p className="text-gray-600 mb-4">
              {file.type.toUpperCase()} 파일은 미리보기를 지원하지 않습니다.
            </p>
            <div className="space-x-2">
              <Button onClick={handleDownload}>
                <Download className="w-4 h-4 mr-2" />
                다운로드
              </Button>
              {previewUrl && (
                <Button variant="outline" onClick={openInNewTab}>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  새 탭에서 열기
                </Button>
              )}
            </div>
          </div>
        </div>
      );
    }

    if (previewUrl) {
      return (
        <iframe
          src={previewUrl}
          width="100%"
          height="100%"
          title={`${file.name} 미리보기`}
          className="border-0"
        />
      );
    }

    return null;
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title=""
      size="full"
      showCloseButton={false}
    >
      <div className="h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b bg-gray-50">
          <div className="flex items-center space-x-4">
            {getFileIcon(file.type)}
            <div>
              <h2 className="text-xl font-semibold text-gray-800">{file.name}</h2>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span>크기: {getFileSizeString(file.size)}</span>
                <span>수정일: {new Date(file.modified).toLocaleDateString('ko-KR')}</span>
                <span>형식: {file.type.toUpperCase()}</span>
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={handleDownload}>
              <Download className="w-4 h-4 mr-2" />
              다운로드
            </Button>
            
            {previewUrl && canPreview(file.type) && (
              <Button variant="outline" onClick={openInNewTab}>
                <ExternalLink className="w-4 h-4 mr-2" />
                새 탭에서 열기
              </Button>
            )}
            
            <Button variant="secondary" onClick={onClose}>
              <X className="w-4 h-4 mr-2" />
              닫기
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 bg-gray-100">
          {renderPreviewContent()}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              파일 경로: {categoryId}/{file.name}
            </div>
            <div>
              SafeWork Pro - 파일 관리 시스템
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}