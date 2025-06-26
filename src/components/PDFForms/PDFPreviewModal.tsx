import React, { useState, useEffect } from 'react';
import { X, Download, Edit, ZoomIn, ZoomOut, RotateCw } from 'lucide-react';
import { Button, Modal } from '../common';

interface PDFForm {
  id: string;
  name: string;
  name_korean: string;
  description: string;
  category: string;
}

interface PDFPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  form: PDFForm;
}

export function PDFPreviewModal({ isOpen, onClose, form }: PDFPreviewModalProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [zoom, setZoom] = useState(100);

  useEffect(() => {
    if (isOpen && form) {
      loadPreview();
    }
  }, [isOpen, form]);

  const loadPreview = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log(`Loading preview for form: ${form.id}`);
      
      // Base64 미리보기 요청
      const response = await fetch(`/api/v1/documents/preview-base64/${form.id}`);
      
      if (response.ok) {
        const data = await response.json();
        setPreviewUrl(data.data_uri);
      } else {
        // Base64 실패시 일반 PDF 미리보기 시도
        const pdfResponse = await fetch(`/api/v1/documents/preview/${form.id}`);
        if (pdfResponse.ok) {
          const blob = await pdfResponse.blob();
          const url = URL.createObjectURL(blob);
          setPreviewUrl(url);
        } else {
          throw new Error('미리보기를 불러올 수 없습니다');
        }
      }
    } catch (error) {
      console.error('미리보기 로드 실패:', error);
      setError('미리보기를 불러오는데 실패했습니다. 네트워크 연결을 확인해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      const response = await fetch(`/api/v1/documents/preview/${form.id}`);
      
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${form.name_korean}_빈양식.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('다운로드 실패:', error);
    }
  };

  const handleZoomIn = () => {
    setZoom(prev => Math.min(prev + 25, 200));
  };

  const handleZoomOut = () => {
    setZoom(prev => Math.max(prev - 25, 50));
  };

  const handleZoomReset = () => {
    setZoom(100);
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
            <h2 className="text-xl font-semibold text-gray-800">{form.name_korean} 미리보기</h2>
            <div className="text-sm text-gray-600">
              {form.description}
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* 확대/축소 컨트롤 */}
            <div className="flex items-center space-x-1 bg-white border rounded-lg px-2 py-1">
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={handleZoomOut}
                disabled={zoom <= 50}
              >
                <ZoomOut size={16} />
              </Button>
              <span className="text-sm font-medium px-2">{zoom}%</span>
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={handleZoomIn}
                disabled={zoom >= 200}
              >
                <ZoomIn size={16} />
              </Button>
              <Button 
                size="sm" 
                variant="ghost" 
                onClick={handleZoomReset}
              >
                <RotateCw size={16} />
              </Button>
            </div>
            
            {/* 액션 버튼 */}
            <Button variant="outline" onClick={handleDownload}>
              <Download size={16} className="mr-1" />
              빈 양식 다운로드
            </Button>
            
            <Button variant="secondary" onClick={onClose}>
              <X size={16} className="mr-1" />
              닫기
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex items-center justify-center bg-gray-100 p-4">
          {loading ? (
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">PDF 미리보기를 로딩 중...</p>
              <p className="text-sm text-gray-500 mt-2">잠시만 기다려주세요.</p>
            </div>
          ) : error ? (
            <div className="text-center">
              <div className="text-red-500 text-6xl mb-4">⚠️</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">미리보기 로드 실패</h3>
              <p className="text-gray-600 mb-4">{error}</p>
              <div className="space-x-2">
                <Button onClick={loadPreview}>다시 시도</Button>
                <Button variant="outline" onClick={handleDownload}>
                  빈 양식 다운로드
                </Button>
              </div>
            </div>
          ) : previewUrl ? (
            <div className="w-full h-full flex justify-center">
              <div 
                className="border border-gray-300 bg-white shadow-lg"
                style={{ 
                  width: `${zoom}%`,
                  height: `${zoom}%`,
                  maxWidth: '100%',
                  maxHeight: '100%'
                }}
              >
                <iframe
                  src={previewUrl}
                  width="100%"
                  height="100%"
                  title={`${form.name_korean} 미리보기`}
                  className="border-0"
                />
              </div>
            </div>
          ) : (
            <div className="text-center">
              <div className="text-gray-400 text-6xl mb-4">📄</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">미리보기를 사용할 수 없습니다</h3>
              <p className="text-gray-600 mb-4">이 양식의 미리보기를 생성할 수 없습니다.</p>
              <Button variant="outline" onClick={handleDownload}>
                빈 양식 다운로드
              </Button>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              양식 ID: {form.id} | 카테고리: {form.category}
            </div>
            <div>
              SafeWork Pro - 건설업 보건관리 시스템
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
}