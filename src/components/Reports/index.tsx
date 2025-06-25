import React, { useState, useEffect } from 'react';
import { FileText, Download, Calendar, BarChart3, PieChart, TrendingUp, Users, AlertTriangle } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  type: 'monthly' | 'quarterly' | 'annual' | 'custom';
  category: 'health' | 'safety' | 'education' | 'environment' | 'compliance';
  required_by_law: boolean;
  deadline?: string;
  parameters: string[];
}

interface GeneratedReport {
  id: number;
  template_id: string;
  name: string;
  generated_date: string;
  period_start: string;
  period_end: string;
  status: 'generating' | 'completed' | 'failed' | 'submitted';
  file_size?: string;
  generated_by: string;
  submitted_to?: string;
  submission_date?: string;
  notes?: string;
}

export function Reports() {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [reports, setReports] = useState<GeneratedReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [showCompleted, setShowCompleted] = useState(true);
  const { fetchApi } = useApi();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      
      // 보고서 템플릿 더미 데이터
      const templateData = [
        {
          id: 'monthly_health_summary',
          name: '월간 보건관리 현황 보고서',
          description: '근로자 건강진단, 보건교육, 상담 현황 종합 보고서',
          type: 'monthly' as const,
          category: 'health' as const,
          required_by_law: true,
          deadline: '매월 말일',
          parameters: ['기간', '부서별', '건강상태별']
        },
        {
          id: 'quarterly_safety_report',
          name: '분기별 안전관리 보고서',
          description: '사고 현황, 안전교육, 예방조치 실시 현황',
          type: 'quarterly' as const,
          category: 'safety' as const,
          required_by_law: true,
          deadline: '분기 종료 후 30일',
          parameters: ['기간', '사고유형별', '부서별']
        },
        {
          id: 'annual_work_environment',
          name: '연간 작업환경측정 보고서',
          description: '작업환경측정 결과 및 개선조치 현황',
          type: 'annual' as const,
          category: 'environment' as const,
          required_by_law: true,
          deadline: '익년 1월 31일',
          parameters: ['측정항목별', '장소별', '기준치 비교']
        },
        {
          id: 'monthly_education_report',
          name: '월간 안전보건교육 실시 현황',
          description: '안전보건교육 계획 대비 실시 현황 보고서',
          type: 'monthly' as const,
          category: 'education' as const,
          required_by_law: true,
          deadline: '매월 10일',
          parameters: ['교육유형별', '부서별', '이수율']
        },
        {
          id: 'chemical_management_report',
          name: '화학물질 관리 현황 보고서',
          description: 'MSDS 관리, 화학물질 취급 현황 보고서',
          type: 'quarterly' as const,
          category: 'environment' as const,
          required_by_law: true,
          deadline: '분기 종료 후 15일',
          parameters: ['화학물질별', 'MSDS 상태', '안전조치 현황']
        },
        {
          id: 'worker_health_statistics',
          name: '근로자 건강 통계 보고서',
          description: '근로자 건강상태 통계 및 트렌드 분석',
          type: 'custom' as const,
          category: 'health' as const,
          required_by_law: false,
          parameters: ['기간', '연령대별', '건강상태별', '부서별']
        },
        {
          id: 'compliance_checklist',
          name: '법정 의무사항 준수 체크리스트',
          description: '산업안전보건법 준수 현황 점검 보고서',
          type: 'monthly' as const,
          category: 'compliance' as const,
          required_by_law: false,
          parameters: ['법령별', '준수율', '미준수 항목']
        }
      ];

      // 생성된 보고서 더미 데이터
      const reportData = [
        {
          id: 1,
          template_id: 'monthly_health_summary',
          name: '2024년 6월 보건관리 현황 보고서',
          generated_date: '2024-06-30',
          period_start: '2024-06-01',
          period_end: '2024-06-30',
          status: 'completed' as const,
          file_size: '2.3MB',
          generated_by: '보건관리자',
          submitted_to: '고용노동청',
          submission_date: '2024-06-30',
          notes: '정상 제출 완료'
        },
        {
          id: 2,
          template_id: 'quarterly_safety_report',
          name: '2024년 2분기 안전관리 보고서',
          generated_date: '2024-06-25',
          period_start: '2024-04-01',
          period_end: '2024-06-30',
          status: 'generating' as const,
          generated_by: '안전관리자',
          notes: '보고서 생성 중'
        },
        {
          id: 3,
          template_id: 'monthly_education_report',
          name: '2024년 6월 안전보건교육 현황',
          generated_date: '2024-06-10',
          period_start: '2024-06-01',
          period_end: '2024-06-30',
          status: 'submitted' as const,
          file_size: '1.8MB',
          generated_by: '교육담당자',
          submitted_to: '관할 지청',
          submission_date: '2024-06-10',
          notes: '정상 제출 완료'
        },
        {
          id: 4,
          template_id: 'chemical_management_report',
          name: '2024년 2분기 화학물질 관리 현황',
          generated_date: '2024-06-20',
          period_start: '2024-04-01',
          period_end: '2024-06-30',
          status: 'failed' as const,
          generated_by: '화학물질관리자',
          notes: 'MSDS 데이터 오류로 생성 실패'
        }
      ];

      setTemplates(templateData);
      setReports(reportData);
    } catch (error) {
      console.error('보고서 데이터 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryBadge = (category: string) => {
    switch (category) {
      case 'health':
        return <Badge className="bg-green-100 text-green-800">보건</Badge>;
      case 'safety':
        return <Badge className="bg-red-100 text-red-800">안전</Badge>;
      case 'education':
        return <Badge className="bg-blue-100 text-blue-800">교육</Badge>;
      case 'environment':
        return <Badge className="bg-yellow-100 text-yellow-800">환경</Badge>;
      case 'compliance':
        return <Badge className="bg-purple-100 text-purple-800">준수</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">기타</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'generating':
        return <Badge className="bg-blue-100 text-blue-800">생성중</Badge>;
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">완료</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">실패</Badge>;
      case 'submitted':
        return <Badge className="bg-purple-100 text-purple-800">제출완료</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">미확인</Badge>;
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'monthly':
        return <Badge className="bg-blue-100 text-blue-800">월간</Badge>;
      case 'quarterly':
        return <Badge className="bg-green-100 text-green-800">분기</Badge>;
      case 'annual':
        return <Badge className="bg-purple-100 text-purple-800">연간</Badge>;
      case 'custom':
        return <Badge className="bg-orange-100 text-orange-800">사용자</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">기타</Badge>;
    }
  };

  const filteredTemplates = templates.filter(template => {
    const matchesCategory = selectedCategory === 'all' || template.category === selectedCategory;
    const matchesType = selectedType === 'all' || template.type === selectedType;
    return matchesCategory && matchesType;
  });

  const filteredReports = reports.filter(report => {
    if (!showCompleted && (report.status === 'completed' || report.status === 'submitted')) {
      return false;
    }
    return true;
  });

  const totalReports = reports.length;
  const completedReports = reports.filter(r => r.status === 'completed' || r.status === 'submitted').length;
  const pendingReports = reports.filter(r => r.status === 'generating').length;
  const failedReports = reports.filter(r => r.status === 'failed').length;

  const handleGenerateReport = (templateId: string) => {
    console.log('보고서 생성:', templateId);
    // 보고서 생성 로직
  };

  const handleDownloadReport = (reportId: number) => {
    console.log('보고서 다운로드:', reportId);
    // 보고서 다운로드 로직
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">보고서 관리</h1>
      </div>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 보고서</p>
              <p className="text-2xl font-bold text-gray-900">{totalReports}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <BarChart3 className="w-8 h-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">완료</p>
              <p className="text-2xl font-bold text-green-600">{completedReports}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <TrendingUp className="w-8 h-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">생성중</p>
              <p className="text-2xl font-bold text-orange-600">{pendingReports}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">실패</p>
              <p className="text-2xl font-bold text-red-600">{failedReports}</p>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 왼쪽: 보고서 템플릿 */}
        <div className="space-y-4">
          <Card>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-800">보고서 템플릿</h3>
                <div className="flex gap-2">
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">전체 분야</option>
                    <option value="health">보건</option>
                    <option value="safety">안전</option>
                    <option value="education">교육</option>
                    <option value="environment">환경</option>
                    <option value="compliance">준수</option>
                  </select>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">전체 유형</option>
                    <option value="monthly">월간</option>
                    <option value="quarterly">분기</option>
                    <option value="annual">연간</option>
                    <option value="custom">사용자</option>
                  </select>
                </div>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {filteredTemplates.map((template) => (
                  <div
                    key={template.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-medium text-gray-900">{template.name}</h4>
                          {template.required_by_law && (
                            <Badge className="bg-red-100 text-red-800 text-xs">법정</Badge>
                          )}
                        </div>
                        <p className="text-sm text-gray-600">{template.description}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex gap-2">
                        {getCategoryBadge(template.category)}
                        {getTypeBadge(template.type)}
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleGenerateReport(template.id)}
                        className="flex items-center gap-1"
                      >
                        <FileText className="w-3 h-3" />
                        생성
                      </Button>
                    </div>
                    
                    {template.deadline && (
                      <p className="text-xs text-orange-600 mt-2">
                        제출기한: {template.deadline}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>

        {/* 오른쪽: 생성된 보고서 */}
        <div className="space-y-4">
          <Card>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-800">생성된 보고서</h3>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={showCompleted}
                    onChange={(e) => setShowCompleted(e.target.checked)}
                    className="rounded"
                  />
                  완료된 보고서 표시
                </label>
              </div>

              <div className="space-y-3 max-h-96 overflow-y-auto">
                {filteredReports.map((report) => (
                  <div
                    key={report.id}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{report.name}</h4>
                        <p className="text-sm text-gray-600">
                          {report.period_start} ~ {report.period_end}
                        </p>
                        <p className="text-xs text-gray-500">
                          생성: {report.generated_date} | 생성자: {report.generated_by}
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex flex-col gap-1">
                        {getStatusBadge(report.status)}
                        {report.file_size && (
                          <span className="text-xs text-gray-500">{report.file_size}</span>
                        )}
                      </div>
                      
                      {(report.status === 'completed' || report.status === 'submitted') && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDownloadReport(report.id)}
                          className="flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          다운로드
                        </Button>
                      )}
                    </div>
                    
                    {report.submitted_to && (
                      <p className="text-xs text-green-600 mt-2">
                        제출: {report.submitted_to} ({report.submission_date})
                      </p>
                    )}
                    
                    {report.notes && (
                      <p className="text-xs text-gray-600 mt-1">{report.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* 법정 보고서 안내 */}
      <Card>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-blue-900 mb-1">법정 보고서 제출 안내</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>• <strong>월간 보고서</strong>: 보건관리 현황, 안전보건교육 실시 현황</p>
                <p>• <strong>분기별 보고서</strong>: 안전관리 현황, 화학물질 관리 현황</p>
                <p>• <strong>연간 보고서</strong>: 작업환경측정 결과, 종합 안전보건관리 계획</p>
                <p>• <strong>수시 보고서</strong>: 중대재해 발생 시 즉시 보고</p>
                <p className="text-blue-800 font-medium mt-2">
                  ※ 제출기한 준수 필수 - 미제출 시 과태료 부과
                </p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}