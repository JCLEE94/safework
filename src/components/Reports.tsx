import React, { useState, useEffect } from 'react';

interface ReportFilters {
  reportType: string;
  startDate: string;
  endDate: string;
  department?: string;
  location?: string;
  status?: string;
}

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  type: 'excel' | 'pdf' | 'word';
}

const REPORT_TEMPLATES: ReportTemplate[] = [
  {
    id: 'worker_health_summary',
    name: '근로자 건강현황 종합보고서',
    description: '전체 근로자의 건강검진 현황 및 통계',
    category: '건강관리',
    type: 'excel'
  },
  {
    id: 'work_env_compliance',
    name: '작업환경측정 법규준수 보고서',
    description: '작업환경측정 결과 및 법규 준수 현황',
    category: '작업환경',
    type: 'pdf'
  },
  {
    id: 'accident_analysis',
    name: '산업재해 분석 보고서',
    description: '사고 발생 현황 및 원인 분석',
    category: '안전관리',
    type: 'word'
  },
  {
    id: 'health_education_progress',
    name: '보건교육 이수현황 보고서',
    description: '근로자별 보건교육 이수 현황',
    category: '교육관리',
    type: 'excel'
  },
  {
    id: 'chemical_msds_status',
    name: 'MSDS 관리현황 보고서',
    description: '화학물질 안전데이터시트 관리 현황',
    category: '화학물질',
    type: 'pdf'
  },
  {
    id: 'monthly_dashboard',
    name: '월간 대시보드 보고서',
    description: '주요 지표별 월간 현황 종합',
    category: '종합',
    type: 'pdf'
  }
];

const REPORT_CATEGORIES = ['전체', '건강관리', '작업환경', '안전관리', '교육관리', '화학물질', '종합'];

export const Reports: React.FC = () => {
  const [selectedTemplate, setSelectedTemplate] = useState<ReportTemplate | null>(null);
  const [filters, setFilters] = useState<ReportFilters>({
    reportType: '',
    startDate: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    endDate: new Date().toISOString().split('T')[0],
    department: '',
    location: '',
    status: ''
  });
  const [generating, setGenerating] = useState(false);
  const [categoryFilter, setCategoryFilter] = useState('전체');
  const [recentReports, setRecentReports] = useState<any[]>([]);

  useEffect(() => {
    fetchRecentReports();
  }, []);

  const fetchRecentReports = async () => {
    try {
      const response = await fetch('/api/v1/reports/recent');
      if (response.ok) {
        const data = await response.json();
        setRecentReports(data.reports || []);
      }
    } catch (error) {
      console.error('최근 보고서 조회 실패:', error);
    }
  };

  const filteredTemplates = categoryFilter === '전체' 
    ? REPORT_TEMPLATES 
    : REPORT_TEMPLATES.filter(template => template.category === categoryFilter);

  const handleGenerateReport = async () => {
    if (!selectedTemplate) {
      alert('보고서 템플릿을 선택해주세요.');
      return;
    }

    setGenerating(true);
    try {
      const reportData = {
        template_id: selectedTemplate.id,
        filters,
        generated_at: new Date().toISOString(),
        generated_by: 'system' // Should come from auth
      };

      const response = await fetch('/api/v1/reports/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(reportData),
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const extension = selectedTemplate.type === 'excel' ? 'xlsx' : selectedTemplate.type === 'pdf' ? 'pdf' : 'docx';
        a.download = `${selectedTemplate.name}_${timestamp}.${extension}`;
        
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        alert('보고서가 생성되었습니다.');
        fetchRecentReports();
        setSelectedTemplate(null);
      } else {
        const error = await response.json();
        alert('보고서 생성 실패: ' + (error.detail || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('보고서 생성 실패:', error);
      alert('네트워크 오류가 발생했습니다.');
    } finally {
      setGenerating(false);
    }
  };

  const getFileIcon = (type: string) => {
    switch (type) {
      case 'excel': return '📊';
      case 'pdf': return '📄';
      case 'word': return '📝';
      default: return '📄';
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: { [key: string]: string } = {
      '건강관리': 'bg-green-100 text-green-800',
      '작업환경': 'bg-blue-100 text-blue-800',
      '안전관리': 'bg-red-100 text-red-800',
      '교육관리': 'bg-yellow-100 text-yellow-800',
      '화학물질': 'bg-purple-100 text-purple-800',
      '종합': 'bg-gray-100 text-gray-800'
    };
    return colors[category] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">보고서 생성</h1>
          <p className="text-gray-600">Report Generation & Management</p>
        </div>
        <div className="text-sm text-gray-500">
          생성일: {new Date().toLocaleDateString('ko-KR')}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 보고서 템플릿 선택 */}
        <div className="lg:col-span-2 space-y-4">
          {/* 카테고리 필터 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-3">보고서 카테고리</h2>
            <div className="flex flex-wrap gap-2">
              {REPORT_CATEGORIES.map((category) => (
                <button
                  key={category}
                  onClick={() => setCategoryFilter(category)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    categoryFilter === category
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>

          {/* 템플릿 목록 */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-medium text-gray-900">보고서 템플릿</h2>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {filteredTemplates.map((template) => (
                  <div
                    key={template.id}
                    onClick={() => setSelectedTemplate(template)}
                    className={`p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedTemplate?.id === template.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{getFileIcon(template.type)}</span>
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-900 mb-1">{template.name}</h3>
                        <p className="text-sm text-gray-600 mb-2">{template.description}</p>
                        <div className="flex items-center gap-2">
                          <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getCategoryColor(template.category)}`}>
                            {template.category}
                          </span>
                          <span className="text-xs text-gray-500 uppercase">{template.type}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 필터 및 생성 */}
        <div className="space-y-4">
          {/* 보고서 필터 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">생성 옵션</h2>
            
            {selectedTemplate && (
              <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{getFileIcon(selectedTemplate.type)}</span>
                  <h3 className="font-medium text-blue-900">{selectedTemplate.name}</h3>
                </div>
                <p className="text-sm text-blue-700">{selectedTemplate.description}</p>
              </div>
            )}

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  시작일
                </label>
                <input
                  type="date"
                  value={filters.startDate}
                  onChange={(e) => setFilters({ ...filters, startDate: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  종료일
                </label>
                <input
                  type="date"
                  value={filters.endDate}
                  onChange={(e) => setFilters({ ...filters, endDate: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  부서 (선택사항)
                </label>
                <input
                  type="text"
                  value={filters.department}
                  onChange={(e) => setFilters({ ...filters, department: e.target.value })}
                  placeholder="예: 건설팀"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  장소 (선택사항)
                </label>
                <input
                  type="text"
                  value={filters.location}
                  onChange={(e) => setFilters({ ...filters, location: e.target.value })}
                  placeholder="예: A동 1층"
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  상태 필터 (선택사항)
                </label>
                <select
                  value={filters.status}
                  onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">전체</option>
                  <option value="정상">정상</option>
                  <option value="주의">주의</option>
                  <option value="관찰">관찰</option>
                  <option value="치료">치료</option>
                </select>
              </div>
            </div>

            <button
              onClick={handleGenerateReport}
              disabled={!selectedTemplate || generating}
              className="w-full mt-6 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? '생성 중...' : '보고서 생성'}
            </button>
          </div>

          {/* 최근 생성된 보고서 */}
          <div className="bg-white p-4 rounded-lg shadow">
            <h2 className="text-lg font-medium text-gray-900 mb-4">최근 생성된 보고서</h2>
            {recentReports.length === 0 ? (
              <p className="text-gray-500 text-sm">최근 생성된 보고서가 없습니다.</p>
            ) : (
              <div className="space-y-2">
                {recentReports.slice(0, 5).map((report, index) => (
                  <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                    <span className="text-lg">{getFileIcon(report.type)}</span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{report.name}</p>
                      <p className="text-xs text-gray-500">{report.generated_at}</p>
                    </div>
                    <button
                      onClick={() => window.open(report.download_url, '_blank')}
                      className="text-blue-600 hover:text-blue-800 text-sm"
                    >
                      다운로드
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};