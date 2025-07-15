/**
 * 강화된 종합보고서 시스템
 * Enhanced Comprehensive Reports System
 */

import React, { useState, useEffect } from 'react';
import { apiUrl } from '../../config/api';
import { 
  BarChart3, FileText, Download, Calendar, Filter, 
  TrendingUp, Users, Activity, AlertTriangle, BookOpen,
  Heart, FlaskConical, Settings, RefreshCw, Eye,
  PieChart, LineChart, CheckCircle, XCircle, Clock
} from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

type ReportType = 'dashboard' | 'workers' | 'health' | 'environment' | 'safety' | 'compliance';
type TimeRange = 'week' | 'month' | 'quarter' | 'year' | 'custom';

interface ReportSummary {
  id: string;
  title: string;
  description: string;
  type: ReportType;
  last_generated: string;
  status: 'available' | 'generating' | 'error';
  download_count: number;
}

interface ReportMetric {
  label: string;
  value: number | string;
  change?: number;
  trend?: 'up' | 'down' | 'stable';
  color: 'green' | 'red' | 'yellow' | 'blue' | 'gray';
}

interface ComplianceItem {
  requirement: string;
  status: 'compliant' | 'non_compliant' | 'pending';
  due_date: string;
  responsible: string;
}

export function EnhancedReports() {
  const [activeReportType, setActiveReportType] = useState<ReportType>('dashboard');
  const [timeRange, setTimeRange] = useState<TimeRange>('month');
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [metrics, setMetrics] = useState<ReportMetric[]>([]);
  const [compliance, setCompliance] = useState<ComplianceItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [customDateRange, setCustomDateRange] = useState({
    start: '',
    end: ''
  });

  const { fetchApi } = useApi();

  useEffect(() => {
    loadReportData();
  }, [activeReportType, timeRange]);

  const loadReportData = async () => {
    setLoading(true);
    try {
      const [reportsData, metricsData, complianceData] = await Promise.all([
        fetchApi(`/api/v1/reports?type=${activeReportType}&range=${timeRange}`),
        fetchApi(`/api/v1/reports/metrics?type=${activeReportType}&range=${timeRange}`),
        fetchApi(apiUrl('/reports/compliance'))
      ]);

      setReports(reportsData || []);
      setMetrics(metricsData || []);
      setCompliance(complianceData || []);
    } catch (error) {
      console.error('Failed to load report data:', error);
      // Set empty data on error
      setReports([]);
      setMetrics([]);
      setCompliance([]);
    } finally {
      setLoading(false);
    }
  };


  const generateReport = async (reportType: string) => {
    try {
      setLoading(true);
      const response = await fetchApi(apiUrl('/reports/generate'), {
        method: 'POST',
        body: JSON.stringify({
          type: reportType,
          time_range: timeRange,
          custom_range: timeRange === 'custom' ? customDateRange : null
        })
      });

      if (response?.download_url) {
        window.open(response.download_url, '_blank');
      }

      await loadReportData();
    } catch (error) {
      console.error('Failed to generate report:', error);
    } finally {
      setLoading(false);
    }
  };

  const downloadReport = (reportId: string) => {
    window.open(`/api/v1/reports/download/${reportId}`, '_blank');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'available': return 'green';
      case 'generating': return 'yellow';
      case 'error': return 'red';
      default: return 'gray';
    }
  };

  const getComplianceColor = (status: string) => {
    switch (status) {
      case 'compliant': return 'green';
      case 'non_compliant': return 'red';
      case 'pending': return 'yellow';
      default: return 'gray';
    }
  };

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up': return <TrendingUp size={16} className="text-green-600" />;
      case 'down': return <TrendingUp size={16} className="text-red-600 rotate-180" />;
      default: return <Clock size={16} className="text-gray-400" />;
    }
  };

  const reportTypes = [
    { id: 'dashboard', name: '종합현황', icon: BarChart3, color: 'text-blue-600' },
    { id: 'workers', name: '근로자관리', icon: Users, color: 'text-purple-600' },
    { id: 'health', name: '건강관리', icon: Heart, color: 'text-red-600' },
    { id: 'environment', name: '작업환경', icon: Activity, color: 'text-green-600' },
    { id: 'safety', name: '안전관리', icon: AlertTriangle, color: 'text-orange-600' },
    { id: 'compliance', name: '법령준수', icon: CheckCircle, color: 'text-teal-600' }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">종합보고서 시스템</h1>
        <div className="flex items-center gap-2">
          <Badge color="blue">
            <BarChart3 size={14} className="mr-1" />
            강화된 분석
          </Badge>
        </div>
      </div>

      {/* Report Type Navigation */}
      <div className="flex flex-wrap gap-2 p-4 bg-gray-50 rounded-lg">
        {reportTypes.map((type) => {
          const Icon = type.icon;
          return (
            <button
              key={type.id}
              onClick={() => setActiveReportType(type.id as ReportType)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg transition-all
                ${activeReportType === type.id
                  ? 'bg-white shadow-md border-2 border-blue-200'
                  : 'hover:bg-white hover:shadow-sm'
                }
              `}
            >
              <Icon size={16} className={type.color} />
              <span className="font-medium">{type.name}</span>
            </button>
          );
        })}
      </div>

      {/* Time Range Selector */}
      <Card className="p-4">
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <Calendar size={16} className="text-gray-600" />
            <span className="font-medium">기간 선택:</span>
          </div>
          <div className="flex gap-2">
            {[
              { value: 'week', label: '최근 1주' },
              { value: 'month', label: '최근 1개월' },
              { value: 'quarter', label: '분기' },
              { value: 'year', label: '연간' },
              { value: 'custom', label: '사용자 지정' }
            ].map((range) => (
              <button
                key={range.value}
                onClick={() => setTimeRange(range.value as TimeRange)}
                className={`
                  px-3 py-1 rounded-md text-sm transition-all
                  ${timeRange === range.value
                    ? 'bg-blue-100 text-blue-700 border border-blue-300'
                    : 'hover:bg-gray-100'
                  }
                `}
              >
                {range.label}
              </button>
            ))}
          </div>
          {timeRange === 'custom' && (
            <div className="flex gap-2 ml-4">
              <input
                type="date"
                value={customDateRange.start}
                onChange={(e) => setCustomDateRange(prev => ({ ...prev, start: e.target.value }))}
                className="px-3 py-1 border rounded-md"
              />
              <span>~</span>
              <input
                type="date"
                value={customDateRange.end}
                onChange={(e) => setCustomDateRange(prev => ({ ...prev, end: e.target.value }))}
                className="px-3 py-1 border rounded-md"
              />
            </div>
          )}
        </div>
      </Card>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {metrics.map((metric, index) => (
          <Card key={index} className="p-4">
            <div className="flex justify-between items-start">
              <div>
                <p className="text-sm text-gray-600">{metric.label}</p>
                <p className="text-2xl font-bold text-gray-900">{metric.value}</p>
                {metric.change !== undefined && (
                  <div className="flex items-center gap-1 mt-1">
                    {getTrendIcon(metric.trend)}
                    <span className={`text-sm ${
                      metric.trend === 'up' ? 'text-green-600' : 
                      metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {Math.abs(metric.change)}% 전월 대비
                    </span>
                  </div>
                )}
              </div>
              <Badge color={metric.color}>
                {metric.color === 'green' ? '양호' : 
                 metric.color === 'yellow' ? '주의' : 
                 metric.color === 'red' ? '위험' : '정상'}
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      {/* Available Reports */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">사용 가능한 보고서</h2>
          <div className="flex gap-2">
            <Button onClick={() => loadReportData()} variant="outline">
              <RefreshCw size={16} className="mr-2" />
              새로고침
            </Button>
            <Button onClick={() => generateReport(activeReportType)}>
              <FileText size={16} className="mr-2" />
              보고서 생성
            </Button>
          </div>
        </div>

        {loading ? (
          <div className="flex justify-center items-center h-32">
            <RefreshCw className="animate-spin" size={32} />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {reports.map((report) => (
              <Card key={report.id} className="p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-1">{report.title}</h3>
                    <p className="text-sm text-gray-600">{report.description}</p>
                  </div>
                  <Badge color={getStatusColor(report.status)}>
                    {report.status === 'available' ? '사용가능' :
                     report.status === 'generating' ? '생성중' : '오류'}
                  </Badge>
                </div>
                
                <div className="text-xs text-gray-500 mb-3">
                  <div>생성일: {new Date(report.last_generated).toLocaleDateString()}</div>
                  <div>다운로드: {report.download_count}회</div>
                </div>
                
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => window.open(`/api/v1/reports/preview/${report.id}`, '_blank')}
                  >
                    <Eye size={14} />
                  </Button>
                  <Button
                    size="sm"
                    onClick={() => downloadReport(report.id)}
                    disabled={report.status !== 'available'}
                  >
                    <Download size={14} />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </Card>

      {/* Compliance Status */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">법령 준수 현황</h2>
        <div className="space-y-3">
          {compliance.map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  {item.status === 'compliant' ? (
                    <CheckCircle size={16} className="text-green-600" />
                  ) : item.status === 'pending' ? (
                    <Clock size={16} className="text-yellow-600" />
                  ) : (
                    <XCircle size={16} className="text-red-600" />
                  )}
                  <Badge color={getComplianceColor(item.status)}>
                    {item.status === 'compliant' ? '준수' :
                     item.status === 'pending' ? '대기' : '미준수'}
                  </Badge>
                </div>
                <div>
                  <span className="font-medium">{item.requirement}</span>
                  <span className="text-sm text-gray-600 ml-2">({item.responsible})</span>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                마감일: {new Date(item.due_date).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}