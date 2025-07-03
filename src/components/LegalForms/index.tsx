import React, { useState, useEffect } from 'react';
import {
  FileText, Grid, List, Columns, BarChart, Settings, 
  Building, Users, Calendar, AlertTriangle, CheckCircle,
  Clock, TrendingUp, Activity, Filter, Download, Upload
} from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';
import { LegalFormProcessor } from './LegalFormProcessor';

interface DepartmentStats {
  department: string;
  total_forms: number;
  pending_forms: number;
  overdue_forms: number;
  completion_rate: number;
}

interface FormStatistics {
  total_forms: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_priority: Record<string, number>;
  upcoming_deadlines: number;
  overdue_forms: number;
  completion_rate: number;
  monthly_submissions: number;
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  action: () => void;
  count?: number;
}

type ViewMode = 'list' | 'grid' | 'kanban';
type TabMode = 'overview' | 'processor' | 'analytics' | 'settings';

export function LegalForms() {
  const [activeTab, setActiveTab] = useState<TabMode>('overview');
  const [viewMode, setViewMode] = useState<ViewMode>('list');
  const [statistics, setStatistics] = useState<FormStatistics | null>(null);
  const [departmentStats, setDepartmentStats] = useState<DepartmentStats[]>([]);
  const [selectedDepartment, setSelectedDepartment] = useState<string>('');
  const [loading, setLoading] = useState(true);

  const { fetchApi } = useApi();

  useEffect(() => {
    if (activeTab === 'overview' || activeTab === 'analytics') {
      loadStatistics();
      loadDepartmentStats();
    }
  }, [activeTab]);

  const loadStatistics = async () => {
    try {
      const data = await fetchApi('/legal-forms/statistics');
      setStatistics(data);
    } catch (error) {
      console.error('법정서식 통계 조회 실패:', error);
    }
  };

  const loadDepartmentStats = async () => {
    try {
      const data = await fetchApi('/legal-forms/department-stats');
      setDepartmentStats(data.items || []);
    } catch (error) {
      console.error('부서별 통계 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const quickActions: QuickAction[] = [
    {
      id: 'pending_review',
      title: '검토 대기',
      description: '검토가 필요한 서식들을 확인하세요',
      icon: <Clock className="w-6 h-6" />,
      color: 'orange',
      count: statistics?.by_status['in_progress'] || 0,
      action: () => {
        setActiveTab('processor');
        // 필터를 검토 대기로 설정
      }
    },
    {
      id: 'overdue_forms',
      title: '마감 초과',
      description: '마감일이 지난 서식들을 처리하세요',
      icon: <AlertTriangle className="w-6 h-6" />,
      color: 'red',
      count: statistics?.overdue_forms || 0,
      action: () => {
        setActiveTab('processor');
        // 필터를 마감초과로 설정
      }
    },
    {
      id: 'upcoming_deadlines',
      title: '마감 임박',
      description: '마감일이 다가오는 서식들을 확인하세요',
      icon: <Calendar className="w-6 h-6" />,
      color: 'yellow',
      count: statistics?.upcoming_deadlines || 0,
      action: () => {
        setActiveTab('processor');
        // 필터를 마감임박으로 설정
      }
    },
    {
      id: 'completed_forms',
      title: '완료된 서식',
      description: '최근 완료된 서식들을 확인하세요',
      icon: <CheckCircle className="w-6 h-6" />,
      color: 'green',
      count: statistics?.by_status['completed'] || 0,
      action: () => {
        setActiveTab('processor');
        // 필터를 완료로 설정
      }
    }
  ];

  const renderOverview = () => (
    <div className="space-y-6">
      {/* 통계 카드 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">총 서식</p>
                <p className="text-2xl font-bold text-blue-600">{statistics.total_forms}</p>
              </div>
              <FileText className="text-blue-600" size={32} />
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">완료율</p>
                <p className="text-2xl font-bold text-green-600">{statistics.completion_rate.toFixed(1)}%</p>
              </div>
              <TrendingUp className="text-green-600" size={32} />
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">마감 초과</p>
                <p className="text-2xl font-bold text-red-600">{statistics.overdue_forms}</p>
              </div>
              <AlertTriangle className="text-red-600" size={32} />
            </div>
          </Card>
          
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">이번 달 제출</p>
                <p className="text-2xl font-bold text-purple-600">{statistics.monthly_submissions}</p>
              </div>
              <Activity className="text-purple-600" size={32} />
            </div>
          </Card>
        </div>
      )}

      {/* 빠른 작업 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">빠른 작업</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {quickActions.map(action => (
            <Card
              key={action.id}
              className={`p-4 cursor-pointer transition-all hover:shadow-md border-l-4 border-${action.color}-500`}
              onClick={action.action}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`text-${action.color}-600`}>
                    {action.icon}
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">{action.title}</h3>
                    <p className="text-sm text-gray-600">{action.description}</p>
                  </div>
                </div>
                {action.count !== undefined && (
                  <Badge color={action.color} size="lg">
                    {action.count}
                  </Badge>
                )}
              </div>
            </Card>
          ))}
        </div>
      </Card>

      {/* 부서별 현황 */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">부서별 서식 현황</h2>
        {loading ? (
          <div className="flex justify-center items-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : departmentStats.length === 0 ? (
          <div className="text-center py-8">
            <Building className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-gray-600">부서 데이터가 없습니다</p>
          </div>
        ) : (
          <div className="space-y-4">
            {departmentStats.map(dept => (
              <div
                key={dept.department}
                className="p-4 border border-gray-200 rounded-lg hover:shadow-sm transition-shadow cursor-pointer"
                onClick={() => {
                  setSelectedDepartment(dept.department);
                  setActiveTab('processor');
                }}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Building className="text-gray-400" size={20} />
                    <div>
                      <h3 className="font-medium text-gray-900">{dept.department}</h3>
                      <p className="text-sm text-gray-600">
                        총 {dept.total_forms}개 서식 · 완료율 {dept.completion_rate.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {dept.pending_forms > 0 && (
                      <Badge color="yellow">{dept.pending_forms}개 대기</Badge>
                    )}
                    {dept.overdue_forms > 0 && (
                      <Badge color="red">{dept.overdue_forms}개 초과</Badge>
                    )}
                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${dept.completion_rate}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );

  const renderAnalytics = () => (
    <div className="space-y-6">
      {/* 상세 통계 */}
      {statistics && (
        <>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 상태별 분포 */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">상태별 서식 분포</h3>
              <div className="space-y-3">
                {Object.entries(statistics.by_status).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{status}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full"
                          style={{ width: `${Math.min((count / statistics.total_forms) * 100, 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>

            {/* 분류별 분포 */}
            <Card className="p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">분류별 서식 분포</h3>
              <div className="space-y-3">
                {Object.entries(statistics.by_category).map(([category, count]) => (
                  <div key={category} className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 capitalize">{category}</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-green-600 h-2 rounded-full"
                          style={{ width: `${Math.min((count / statistics.total_forms) * 100, 100)}%` }}
                        ></div>
                      </div>
                      <span className="text-sm font-medium">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </div>

          {/* 추세 분석 */}
          <Card className="p-6">
            <h3 className="text-lg font-semibold text-gray-800 mb-4">제출 추세</h3>
            <div className="bg-gray-50 rounded-lg p-8 text-center">
              <BarChart className="mx-auto text-gray-400" size={48} />
              <p className="text-gray-600 mt-2">월별 제출 추세 차트</p>
              <p className="text-sm text-gray-500">차트 라이브러리 통합 예정</p>
            </div>
          </Card>
        </>
      )}
    </div>
  );

  const renderSettings = () => (
    <div className="space-y-6">
      <Card className="p-6">
        <h3 className="text-lg font-semibold text-gray-800 mb-4">시스템 설정</h3>
        <div className="space-y-4">
          {/* 서식 템플릿 관리 */}
          <div className="p-4 border border-gray-200 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">서식 템플릿 관리</h4>
            <p className="text-sm text-gray-600 mb-3">법정서식 템플릿을 관리하고 업데이트합니다.</p>
            <div className="flex gap-2">
              <Button variant="secondary" icon={<Upload size={16} />}>
                템플릿 업로드
              </Button>
              <Button variant="secondary" icon={<Download size={16} />}>
                템플릿 다운로드
              </Button>
            </div>
          </div>

          {/* 알림 설정 */}
          <div className="p-4 border border-gray-200 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">알림 설정</h4>
            <p className="text-sm text-gray-600 mb-3">서식 마감일 및 승인 알림을 설정합니다.</p>
            <div className="space-y-2">
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                <span className="text-sm text-gray-700">마감일 7일 전 알림</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                <span className="text-sm text-gray-700">마감일 3일 전 알림</span>
              </label>
              <label className="flex items-center space-x-2">
                <input type="checkbox" className="rounded border-gray-300 text-blue-600 focus:ring-blue-500" />
                <span className="text-sm text-gray-700">승인 완료 알림</span>
              </label>
            </div>
          </div>

          {/* 권한 관리 */}
          <div className="p-4 border border-gray-200 rounded-lg">
            <h4 className="font-medium text-gray-900 mb-2">권한 관리</h4>
            <p className="text-sm text-gray-600 mb-3">부서별 서식 접근 권한을 관리합니다.</p>
            <Button variant="secondary" icon={<Users size={16} />}>
              권한 설정
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'processor':
        return (
          <LegalFormProcessor
            viewMode={viewMode}
            selectedDepartment={selectedDepartment}
            onFormSelect={(form) => {
              console.log('Selected form:', form);
            }}
          />
        );
      case 'analytics':
        return renderAnalytics();
      case 'settings':
        return renderSettings();
      default:
        return renderOverview();
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">법정서식 관리</h1>
          <p className="text-gray-600 mt-1">법령에서 요구하는 서식을 체계적으로 관리하세요</p>
        </div>
        <div className="flex gap-2">
          {activeTab === 'processor' && (
            <div className="flex border border-gray-300 rounded-lg overflow-hidden">
              <button
                onClick={() => setViewMode('list')}
                className={`px-3 py-2 flex items-center gap-2 text-sm ${
                  viewMode === 'list' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <List size={16} />
                목록
              </button>
              <button
                onClick={() => setViewMode('grid')}
                className={`px-3 py-2 flex items-center gap-2 text-sm ${
                  viewMode === 'grid' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Grid size={16} />
                카드
              </button>
              <button
                onClick={() => setViewMode('kanban')}
                className={`px-3 py-2 flex items-center gap-2 text-sm ${
                  viewMode === 'kanban' ? 'bg-blue-500 text-white' : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                <Columns size={16} />
                칸반
              </button>
            </div>
          )}
          <Button variant="secondary" icon={<Settings size={16} />}>
            설정
          </Button>
        </div>
      </div>

      {/* 탭 네비게이션 */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { key: 'overview', label: '개요', icon: <BarChart size={16} /> },
            { key: 'processor', label: '서식 처리', icon: <FileText size={16} /> },
            { key: 'analytics', label: '분석', icon: <TrendingUp size={16} /> },
            { key: 'settings', label: '설정', icon: <Settings size={16} /> }
          ].map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as TabMode)}
              className={`flex items-center gap-2 py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* 메인 콘텐츠 */}
      {renderContent()}
    </div>
  );
}