import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import { API_BASE_URL } from '../../config/api';
import { 
  Upload, 
  Download, 
  FileText, 
  Edit3, 
  Save, 
  Loader2, 
  AlertCircle, 
  CheckCircle, 
  X,
  Eye,
  Target,
  Crosshair,
  MousePointer,
  ZoomIn,
  ZoomOut,
  RotateCw
} from 'lucide-react';

// PDF.js worker 설정
pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;

interface DetectedField {
  name: string;
  type: 'text' | 'checkbox' | 'radio' | 'signature' | 'date';
  coordinates: {
    x: number;
    y: number;
    width: number;
    height: number;
    page: number;
  };
  value?: string;
  confidence?: number;
}

interface FieldMapping {
  [fieldName: string]: {
    label: string;
    value: string;
    type: string;
    coordinates: {
      x: number;
      y: number;
      width: number;
      height: number;
      page: number;
    };
  };
}

interface PrecisePdfEditorProps {
  initialPdfUrl?: string;
  initialData?: Record<string, string>;
}

const PrecisePdfEditor: React.FC<PrecisePdfEditorProps> = ({ 
  initialPdfUrl, 
  initialData = {} 
}) => {
  // States
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [pdfUrl, setPdfUrl] = useState<string>(initialPdfUrl || '');
  const [numPages, setNumPages] = useState<number>(0);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.2);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Field detection states
  const [detectedFields, setDetectedFields] = useState<DetectedField[]>([]);
  const [fieldMappings, setFieldMappings] = useState<FieldMapping>({});
  const [isDetecting, setIsDetecting] = useState(false);
  const [showFields, setShowFields] = useState(true);
  const [editMode, setEditMode] = useState<'view' | 'edit' | 'field-detect'>('view');
  
  // User interaction states
  const [selectedField, setSelectedField] = useState<string | null>(null);
  const [fieldInputs, setFieldInputs] = useState<Record<string, string>>(initialData);
  
  // Refs
  const fileInputRef = useRef<HTMLInputElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 정확한 좌표 변환 함수
  const convertPdfToViewportCoordinates = (
    pdfX: number,
    pdfY: number,
    pdfWidth: number,
    pdfHeight: number,
    pageWidth: number,
    pageHeight: number,
    scale: number
  ) => {
    // PDF 좌표계 (bottom-left origin) → 화면 좌표계 (top-left origin) 변환
    const viewportX = (pdfX / pageWidth) * (pageWidth * scale);
    const viewportY = ((pageHeight - pdfY - pdfHeight) / pageHeight) * (pageHeight * scale);
    const viewportWidth = (pdfWidth / pageWidth) * (pageWidth * scale);
    const viewportHeight = (pdfHeight / pageHeight) * (pageHeight * scale);

    return {
      x: viewportX,
      y: viewportY,
      width: viewportWidth,
      height: viewportHeight
    };
  };

  // PDF 파일 업로드 처리
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && file.type === 'application/pdf') {
      setPdfFile(file);
      const url = URL.createObjectURL(file);
      setPdfUrl(url);
      setError(null);
      setSuccess('PDF 파일이 성공적으로 로드되었습니다');
      
      // 자동으로 필드 감지 시작
      await detectFields(file);
    } else {
      setError('PDF 파일만 업로드 가능합니다');
    }
  };

  // 정확한 PDF 필드 감지
  const detectFields = async (file: File) => {
    if (!file) return;

    setIsDetecting(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // 백엔드 고급 필드 감지 API 호출
      const response = await fetch(`${API_BASE_URL}/api/v1/pdf-precise/detect-fields`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('필드 감지에 실패했습니다');
      }

      const result = await response.json();
      
      if (result.detected_fields && result.detected_fields.length > 0) {
        setDetectedFields(result.detected_fields);
        
        // 필드 매핑 생성
        const mappings: FieldMapping = {};
        result.detected_fields.forEach((field: DetectedField) => {
          mappings[field.name] = {
            label: field.name,
            value: fieldInputs[field.name] || '',
            type: field.type,
            coordinates: field.coordinates
          };
        });
        setFieldMappings(mappings);
        
        setSuccess(`${result.detected_fields.length}개의 필드가 정확하게 감지되었습니다`);
        setEditMode('edit');
      } else {
        setError('감지된 필드가 없습니다. PDF에 편집 가능한 폼 필드가 있는지 확인해주세요.');
      }

    } catch (err) {
      console.error('필드 감지 오류:', err);
      setError('필드 감지 중 오류가 발생했습니다');
    } finally {
      setIsDetecting(false);
    }
  };

  // 필드 값 변경 처리
  const handleFieldValueChange = (fieldName: string, value: string) => {
    setFieldInputs(prev => ({
      ...prev,
      [fieldName]: value
    }));
    
    // 필드 매핑도 업데이트
    if (fieldMappings[fieldName]) {
      setFieldMappings(prev => ({
        ...prev,
        [fieldName]: {
          ...prev[fieldName],
          value: value
        }
      }));
    }
  };

  // 정확한 위치에 PDF 필드 렌더링
  const renderFieldOverlays = () => {
    if (!showFields || !detectedFields.length || editMode === 'view') return null;

    return detectedFields
      .filter(field => field.coordinates.page === currentPage)
      .map((field, index) => {
        const coords = convertPdfToViewportCoordinates(
          field.coordinates.x,
          field.coordinates.y,
          field.coordinates.width,
          field.coordinates.height,
          595, // PDF page width (A4)
          842, // PDF page height (A4)
          scale
        );

        return (
          <div
            key={`${field.name}-${index}`}
            className={`absolute border-2 transition-all duration-200 ${
              selectedField === field.name
                ? 'border-blue-500 bg-blue-100 bg-opacity-30'
                : 'border-green-400 bg-green-100 bg-opacity-20 hover:bg-green-200 hover:bg-opacity-40'
            }`}
            style={{
              left: `${coords.x}px`,
              top: `${coords.y}px`,
              width: `${coords.width}px`,
              height: `${coords.height}px`,
              zIndex: 10,
              cursor: 'pointer'
            }}
            onClick={() => setSelectedField(field.name)}
            title={`${field.name} (${field.type})`}
          >
            {/* 필드 라벨 */}
            <div className="absolute -top-6 left-0 bg-green-600 text-white text-xs px-2 py-1 rounded whitespace-nowrap">
              {field.name}
            </div>
            
            {/* 필드 값 미리보기 */}
            {fieldInputs[field.name] && (
              <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-800 font-medium bg-white bg-opacity-80">
                {fieldInputs[field.name].substring(0, 20)}
                {fieldInputs[field.name].length > 20 && '...'}
              </div>
            )}
          </div>
        );
      });
  };

  // PDF 자동 필드 채우기 및 다운로드
  const handleAutoFillAndDownload = async () => {
    if (!pdfFile || Object.keys(fieldInputs).length === 0) {
      setError('PDF 파일과 입력 데이터가 필요합니다');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', pdfFile);
      formData.append('field_data', JSON.stringify(fieldInputs));
      formData.append('field_mappings', JSON.stringify(fieldMappings));

      const response = await fetch(`${API_BASE_URL}/api/v1/pdf-precise/auto-fill`, {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('PDF 자동 채우기에 실패했습니다');
      }

      // 채워진 PDF 다운로드
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `auto_filled_${pdfFile.name}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);

      setSuccess('PDF가 정확하게 채워져 다운로드되었습니다');

    } catch (err) {
      console.error('PDF 처리 오류:', err);
      setError('PDF 자동 채우기 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 수동 필드 추가 (클릭한 위치에)
  const handleCanvasClick = (event: React.MouseEvent<HTMLDivElement>) => {
    if (editMode !== 'field-detect') return;

    const rect = event.currentTarget.getBoundingClientRect();
    const x = event.clientX - rect.left;
    const y = event.clientY - rect.top;

    // 화면 좌표를 PDF 좌표로 변환
    const pdfX = (x / scale) * (595 / 595); // A4 width normalization
    const pdfY = 842 - (y / scale) * (842 / 842); // A4 height + coordinate flip

    const newField: DetectedField = {
      name: `custom_field_${Date.now()}`,
      type: 'text',
      coordinates: {
        x: pdfX,
        y: pdfY,
        width: 150,
        height: 20,
        page: currentPage
      },
      confidence: 1.0
    };

    setDetectedFields(prev => [...prev, newField]);
    setSelectedField(newField.name);
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        {/* 헤더 */}
        <div className="p-6 border-b">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">정밀 PDF 편집기</h1>
              <p className="mt-2 text-gray-600">
                정확한 좌표 기반 텍스트 필드 인식 및 자동 데이터 입력
              </p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setEditMode('view')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  editMode === 'view'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <Eye className="inline mr-2" size={16} />
                보기
              </button>
              <button
                onClick={() => setEditMode('edit')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  editMode === 'edit'
                    ? 'bg-green-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
                disabled={!detectedFields.length}
              >
                <Edit3 className="inline mr-2" size={16} />
                편집
              </button>
              <button
                onClick={() => setEditMode('field-detect')}
                className={`px-4 py-2 rounded-md transition-colors ${
                  editMode === 'field-detect'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                <Target className="inline mr-2" size={16} />
                필드 추가
              </button>
            </div>
          </div>
        </div>

        {/* 알림 */}
        {error && (
          <div className="mx-6 mt-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-start">
            <AlertCircle className="h-5 w-5 text-red-400 mt-0.5 mr-2 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-red-800">{error}</p>
            </div>
            <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        {success && (
          <div className="mx-6 mt-4 p-4 bg-green-50 border border-green-200 rounded-md flex items-start">
            <CheckCircle className="h-5 w-5 text-green-400 mt-0.5 mr-2 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-green-800">{success}</p>
            </div>
            <button onClick={() => setSuccess(null)} className="text-green-400 hover:text-green-600">
              <X className="h-5 w-5" />
            </button>
          </div>
        )}

        <div className="p-6">
          {/* 파일 업로드 영역 */}
          {!pdfUrl && (
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf"
                onChange={handleFileUpload}
                className="hidden"
                id="pdf-upload"
              />
              <label htmlFor="pdf-upload" className="cursor-pointer">
                <Upload size={48} className="text-gray-400 mb-4 mx-auto" />
                <p className="text-lg font-medium text-gray-900 mb-2">
                  PDF 파일을 업로드하세요
                </p>
                <p className="text-gray-600">
                  정밀한 필드 감지와 자동 데이터 입력을 위해 편집 가능한 PDF를 선택하세요
                </p>
              </label>
            </div>
          )}

          {/* PDF 뷰어 및 편집 영역 */}
          {pdfUrl && (
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              {/* PDF 뷰어 */}
              <div className="lg:col-span-3">
                <div className="bg-gray-50 rounded-lg p-4">
                  {/* 컨트롤 바 */}
                  <div className="flex justify-between items-center mb-4">
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                        disabled={currentPage <= 1}
                        className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
                      >
                        이전
                      </button>
                      <span className="text-sm">
                        {currentPage} / {numPages}
                      </span>
                      <button
                        onClick={() => setCurrentPage(Math.min(numPages, currentPage + 1))}
                        disabled={currentPage >= numPages}
                        className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
                      >
                        다음
                      </button>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setScale(Math.max(0.5, scale - 0.1))}
                        className="p-2 bg-gray-200 rounded"
                      >
                        <ZoomOut size={16} />
                      </button>
                      <span className="text-sm">{Math.round(scale * 100)}%</span>
                      <button
                        onClick={() => setScale(Math.min(3, scale + 0.1))}
                        className="p-2 bg-gray-200 rounded"
                      >
                        <ZoomIn size={16} />
                      </button>
                      
                      <button
                        onClick={() => setShowFields(!showFields)}
                        className={`px-3 py-2 rounded text-sm ${
                          showFields ? 'bg-green-600 text-white' : 'bg-gray-200'
                        }`}
                      >
                        {showFields ? '필드 숨기기' : '필드 표시'}
                      </button>
                    </div>
                  </div>

                  {/* PDF 페이지 및 오버레이 */}
                  <div 
                    ref={containerRef}
                    className="relative inline-block border border-gray-300"
                    onClick={handleCanvasClick}
                    style={{ cursor: editMode === 'field-detect' ? 'crosshair' : 'default' }}
                  >
                    <Document
                      file={pdfUrl}
                      onLoadSuccess={({ numPages }) => setNumPages(numPages)}
                      loading={<div className="flex items-center justify-center p-8">
                        <Loader2 className="animate-spin mr-2" size={24} />
                        PDF 로딩 중...
                      </div>}
                      error={<div className="text-red-600 p-4">PDF 로딩 실패</div>}
                    >
                      <Page
                        pageNumber={currentPage}
                        scale={scale}
                        renderTextLayer={false}
                        renderAnnotationLayer={false}
                      />
                      
                      {/* 필드 오버레이 */}
                      {renderFieldOverlays()}
                    </Document>
                  </div>
                </div>
              </div>

              {/* 사이드바 - 필드 편집 */}
              <div className="lg:col-span-1">
                <div className="space-y-4">
                  {/* 필드 감지 상태 */}
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <h3 className="font-semibold text-gray-900 mb-2">감지된 필드</h3>
                    
                    {isDetecting ? (
                      <div className="flex items-center text-blue-600">
                        <Loader2 className="animate-spin mr-2" size={16} />
                        필드 감지 중...
                      </div>
                    ) : (
                      <div>
                        <p className="text-sm text-gray-600 mb-2">
                          총 {detectedFields.length}개 필드
                        </p>
                        <button
                          onClick={() => pdfFile && detectFields(pdfFile)}
                          className="w-full px-3 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 text-sm"
                          disabled={!pdfFile}
                        >
                          <Crosshair className="inline mr-1" size={14} />
                          재감지
                        </button>
                      </div>
                    )}
                  </div>

                  {/* 필드 입력 */}
                  {detectedFields.length > 0 && (
                    <div className="bg-white border rounded-lg p-4">
                      <h3 className="font-semibold text-gray-900 mb-3">필드 값 입력</h3>
                      
                      <div className="space-y-3 max-h-96 overflow-y-auto">
                        {detectedFields.map((field, index) => (
                          <div
                            key={`${field.name}-${index}`}
                            className={`p-3 border rounded ${
                              selectedField === field.name ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
                            }`}
                          >
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              {field.name}
                              <span className="text-xs text-gray-500 ml-1">
                                ({field.type}, 페이지 {field.coordinates.page})
                              </span>
                            </label>
                            
                            {field.type === 'checkbox' ? (
                              <input
                                type="checkbox"
                                checked={fieldInputs[field.name] === 'true'}
                                onChange={(e) => handleFieldValueChange(field.name, e.target.checked ? 'true' : 'false')}
                                className="h-4 w-4 text-blue-600"
                              />
                            ) : field.type === 'date' ? (
                              <input
                                type="date"
                                value={fieldInputs[field.name] || ''}
                                onChange={(e) => handleFieldValueChange(field.name, e.target.value)}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                              />
                            ) : (
                              <input
                                type="text"
                                value={fieldInputs[field.name] || ''}
                                onChange={(e) => handleFieldValueChange(field.name, e.target.value)}
                                className="w-full px-2 py-1 border border-gray-300 rounded text-sm"
                                placeholder={field.type === 'signature' ? '서명/이름' : '값 입력'}
                              />
                            )}
                            
                            {field.confidence && (
                              <div className="text-xs text-gray-500 mt-1">
                                정확도: {Math.round(field.confidence * 100)}%
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 액션 버튼 */}
                  {detectedFields.length > 0 && (
                    <div className="space-y-2">
                      <button
                        onClick={handleAutoFillAndDownload}
                        disabled={loading || Object.keys(fieldInputs).length === 0}
                        className="w-full px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:bg-gray-400"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="animate-spin mr-2 inline" size={16} />
                            처리 중...
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 inline" size={16} />
                            정확한 위치에 데이터 입력 및 다운로드
                          </>
                        )}
                      </button>
                      
                      <div className="text-xs text-gray-500 text-center">
                        모든 필드가 정확한 좌표에 배치됩니다
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default PrecisePdfEditor;