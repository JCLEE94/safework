/**
 * 고도화된 실시간 모니터링 시스템
 * Advanced Real-time Monitoring System
 */

import React, { useState, useEffect } from 'react';
import { apiUrl } from '../../config/api';
import { 
  Activity, AlertTriangle, CheckCircle, Clock, TrendingUp, 
  Users, Heart, Shield, FileText, Zap, RefreshCw, Settings,
  BarChart3, PieChart, LineChart, Monitor, Bell, Eye,
  AlertCircle, XCircle, Thermometer, Wind, Volume2
} from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

interface SystemMetric {
  id: string;
  name: string;
  value: number | string;
  unit?: string;
  status: 'normal' | 'warning' | 'critical';
  trend?: 'up' | 'down' | 'stable';
  change?: number;
  threshold?: {
    warning: number;
    critical: number;
  };
}

interface ComplianceStatus {
  category: string;
  total_rules: number;
  compliant: number;
  violations: number;
  compliance_rate: number;
}

interface RealTimeAlert {
  id: string;
  type: 'safety' | 'health' | 'environment' | 'compliance' | 'system';
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  message: string;
  timestamp: string;
  acknowledged: boolean;
  location?: string;
}

interface EnvironmentData {
  location: string;
  noise_level: number;
  dust_level: number;
  temperature: number;
  humidity: number;
  air_quality: number;
  timestamp: string;
}

export function AdvancedMonitoring() {
  const [systemMetrics, setSystemMetrics] = useState<SystemMetric[]>([]);
  const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus[]>([]);
  const [realTimeAlerts, setRealTimeAlerts] = useState<RealTimeAlert[]>([]);
  const [environmentData, setEnvironmentData] = useState<EnvironmentData[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h');

  const { fetchApi } = useApi();

  useEffect(() => {
    loadAllData();
    
    if (autoRefresh) {
      const interval = setInterval(loadAllData, refreshInterval * 1000);
      return () => clearInterval(interval);
    }
  }, [autoRefresh, refreshInterval]);

  const loadAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadSystemMetrics(),
        loadComplianceStatus(),
        loadRealTimeAlerts(),
        loadEnvironmentData()
      ]);
    } catch (error) {
      console.error('Failed to load monitoring data:', error);
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const loadSystemMetrics = async () => {
    try {
      const data = await fetchApi(apiUrl('/monitoring/system-metrics'));
      setSystemMetrics(data || []);
    } catch (error) {
      console.error('Failed to load system metrics:', error);
    }
  };

  const loadComplianceStatus = async () => {
    try {
      const data = await fetchApi(apiUrl('/compliance/dashboard'));
      setComplianceStatus(data?.category_analysis ? 
        Object.entries(data.category_analysis).map(([category, stats]: [string, any]) => ({
          category,
          total_rules: stats.total,
          compliant: stats.compliant,
          violations: stats.violations,
          compliance_rate: stats.total > 0 ? (stats.compliant / stats.total) * 100 : 0
        })) : []);
    } catch (error) {
      console.error('Failed to load compliance status:', error);
    }
  };

  const loadRealTimeAlerts = async () => {
    try {
      const data = await fetchApi(apiUrl('/monitoring/alerts'));
      setRealTimeAlerts(data || []);
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
  };

  const loadEnvironmentData = async () => {
    try {
      const data = await fetchApi(`/api/v1/monitoring/environment?range=${selectedTimeRange}`);
      setEnvironmentData(data || []);
    } catch (error) {
      console.error('Failed to load environment data:', error);
    }
  };

  const loadMockData = () => {
    // Mock data for demonstration
    setSystemMetrics([
      { id: 'workers_online', name: '접속 중인 근로자', value: 245, status: 'normal', trend: 'up', change: 5 },
      { id: 'safety_score', name: '안전점수', value: 94, unit: '%', status: 'normal', trend: 'stable' },
      { id: 'health_compliance', name: '건강관리 준수율', value: 87, unit: '%', status: 'warning', trend: 'down', change: -3 },
      { id: 'incident_rate', name: '사고발생률', value: 0.12, unit: '%', status: 'normal', trend: 'down', change: -0.05 },
      { id: 'education_completion', name: '교육이수율', value: 92, unit: '%', status: 'normal', trend: 'up', change: 8 },
      { id: 'equipment_status', name: '장비가동률', value: 98, unit: '%', status: 'normal', trend: 'stable' }
    ]);

    setComplianceStatus([
      { category: 'health_exam', total_rules: 5, compliant: 4, violations: 1, compliance_rate: 80 },
      { category: 'education', total_rules: 8, compliant: 7, violations: 1, compliance_rate: 87.5 },
      { category: 'environment', total_rules: 6, compliant: 5, violations: 1, compliance_rate: 83.3 },
      { category: 'chemical', total_rules: 4, compliant: 3, violations: 1, compliance_rate: 75 },
      { category: 'safety', total_rules: 10, compliant: 9, violations: 1, compliance_rate: 90 }
    ]);

    setRealTimeAlerts([
      {
        id: '1',
        type: 'environment',
        severity: 'high',
        title: '소음 기준 초과',
        message: '용접구역에서 소음 레벨이 85dB를 초과했습니다.',
        timestamp: new Date(Date.now() - 5 * 60000).toISOString(),
        acknowledged: false,
        location: '용접구역 A동'
      },
      {
        id: '2',
        type: 'compliance',
        severity: 'medium',
        title: '특수건강진단 만료 임박',
        message: '3명의 근로자 특수건강진단이 1주일 내 만료됩니다.',
        timestamp: new Date(Date.now() - 15 * 60000).toISOString(),
        acknowledged: false
      },
      {
        id: '3',
        type: 'safety',
        severity: 'critical',
        title: '보호구 미착용 감지',
        message: '안전모 미착용 근로자가 위험구역에서 감지되었습니다.',
        timestamp: new Date(Date.now() - 2 * 60000).toISOString(),
        acknowledged: false,
        location: '크레인 작업구역'
      }
    ]);

    setEnvironmentData([
      {
        location: '용접구역',
        noise_level: 87,
        dust_level: 0.15,
        temperature: 28,
        humidity: 65,
        air_quality: 85,
        timestamp: new Date().toISOString()
      },
      {
        location: '절단구역',
        noise_level: 82,
        dust_level: 0.08,
        temperature: 26,
        humidity: 60,
        air_quality: 92,
        timestamp: new Date().toISOString()
      }
    ]);
  };

  const acknowledgeAlert = async (alertId: string) => {
    try {
      await fetchApi(`/api/v1/monitoring/alerts/${alertId}/acknowledge`, { method: 'POST' });
      setRealTimeAlerts(prev => 
        prev.map(alert => 
          alert.id === alertId ? { ...alert, acknowledged: true } : alert
        )
      );
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'normal': return 'green';
      case 'warning': return 'yellow';
      case 'critical': return 'red';
      default: return 'gray';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'low': return 'blue';
      case 'medium': return 'yellow';
      case 'high': return 'orange';
      case 'critical': return 'red';
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

  const getAlertIcon = (type: string) => {
    switch (type) {
      case 'safety': return <Shield size={16} />;
      case 'health': return <Heart size={16} />;
      case 'environment': return <Wind size={16} />;
      case 'compliance': return <FileText size={16} />;
      case 'system': return <Monitor size={16} />;
      default: return <AlertCircle size={16} />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">고도화된 실시간 모니터링</h1>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">자동 새로고침:</label>
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            <select
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(Number(e.target.value))}
              disabled={!autoRefresh}
              className="text-sm border rounded px-2 py-1"
            >
              <option value={10}>10초</option>
              <option value={30}>30초</option>
              <option value={60}>1분</option>
              <option value={300}>5분</option>
            </select>
          </div>
          <Button onClick={loadAllData} variant="outline">
            <RefreshCw size={16} className={`mr-2 ${loading ? 'animate-spin' : ''}`} />
            새로고침
          </Button>
        </div>
      </div>

      {/* System Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {systemMetrics.map((metric) => (
          <Card key={metric.id} className="p-4">
            <div className="flex justify-between items-start mb-2">
              <div>
                <p className="text-sm text-gray-600">{metric.name}</p>
                <p className="text-2xl font-bold text-gray-900">
                  {metric.value}{metric.unit && ` ${metric.unit}`}
                </p>
                {metric.change !== undefined && (
                  <div className="flex items-center gap-1 mt-1">
                    {getTrendIcon(metric.trend)}
                    <span className={`text-sm ${
                      metric.trend === 'up' ? 'text-green-600' : 
                      metric.trend === 'down' ? 'text-red-600' : 'text-gray-600'
                    }`}>
                      {Math.abs(metric.change)}{metric.unit} 변화
                    </span>
                  </div>
                )}
              </div>
              <Badge color={getStatusColor(metric.status)}>
                {metric.status === 'normal' ? '정상' : 
                 metric.status === 'warning' ? '주의' : '위험'}
              </Badge>
            </div>
          </Card>
        ))}
      </div>

      {/* Real-time Alerts */}
      <Card className="p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold flex items-center gap-2">
            <Bell className="text-orange-600" size={20} />
            실시간 알림
          </h2>
          <Badge color="red">
            {realTimeAlerts.filter(alert => !alert.acknowledged).length}개 미확인
          </Badge>
        </div>

        <div className="space-y-3">
          {realTimeAlerts.slice(0, 5).map((alert) => (
            <div
              key={alert.id}
              className={`
                flex items-center justify-between p-3 rounded-lg border-l-4
                ${alert.acknowledged ? 'bg-gray-50 border-gray-300' : 
                  alert.severity === 'critical' ? 'bg-red-50 border-red-500' :
                  alert.severity === 'high' ? 'bg-orange-50 border-orange-500' :
                  alert.severity === 'medium' ? 'bg-yellow-50 border-yellow-500' :
                  'bg-blue-50 border-blue-500'}
              `}
            >
              <div className="flex items-center gap-3">
                <div className={`
                  p-2 rounded-full
                  ${alert.severity === 'critical' ? 'bg-red-100 text-red-600' :
                    alert.severity === 'high' ? 'bg-orange-100 text-orange-600' :
                    alert.severity === 'medium' ? 'bg-yellow-100 text-yellow-600' :
                    'bg-blue-100 text-blue-600'}
                `}>
                  {getAlertIcon(alert.type)}
                </div>
                <div>
                  <h3 className={`font-medium ${alert.acknowledged ? 'text-gray-600' : 'text-gray-900'}`}>
                    {alert.title}
                  </h3>
                  <p className={`text-sm ${alert.acknowledged ? 'text-gray-500' : 'text-gray-700'}`}>
                    {alert.message}
                  </p>
                  <div className="flex items-center gap-4 mt-1 text-xs text-gray-500">
                    <span>{new Date(alert.timestamp).toLocaleString()}</span>
                    {alert.location && <span>📍 {alert.location}</span>}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge color={getSeverityColor(alert.severity)}>
                  {alert.severity === 'critical' ? '긴급' :
                   alert.severity === 'high' ? '높음' :
                   alert.severity === 'medium' ? '보통' : '낮음'}
                </Badge>
                {!alert.acknowledged && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => acknowledgeAlert(alert.id)}
                  >
                    <CheckCircle size={14} />
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>

        {realTimeAlerts.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <CheckCircle className="mx-auto h-12 w-12 text-green-400 mb-2" />
            <p>현재 활성 알림이 없습니다</p>
          </div>
        )}
      </Card>

      {/* Compliance Status */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Shield className="text-blue-600" size={20} />
          법령 준수 현황
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {complianceStatus.map((status) => (
            <div key={status.category} className="text-center">
              <div className="mb-2">
                <div className={`
                  inline-flex items-center justify-center w-16 h-16 rounded-full
                  ${status.compliance_rate >= 90 ? 'bg-green-100 text-green-600' :
                    status.compliance_rate >= 80 ? 'bg-yellow-100 text-yellow-600' :
                    'bg-red-100 text-red-600'}
                `}>
                  <span className="text-lg font-bold">{status.compliance_rate.toFixed(0)}%</span>
                </div>
              </div>
              <h3 className="font-medium text-gray-900 mb-1">
                {status.category === 'health_exam' ? '건강진단' :
                 status.category === 'education' ? '안전교육' :
                 status.category === 'environment' ? '작업환경' :
                 status.category === 'chemical' ? '화학물질' :
                 status.category === 'safety' ? '안전관리' : status.category}
              </h3>
              <p className="text-sm text-gray-600">
                {status.compliant}/{status.total_rules} 준수
              </p>
              {status.violations > 0 && (
                <Badge color="red" className="mt-1">
                  {status.violations}개 위반
                </Badge>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Environment Monitoring */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Activity className="text-green-600" size={20} />
          환경 모니터링
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {environmentData.map((env, index) => (
            <div key={index} className="border rounded-lg p-4">
              <h3 className="font-medium text-gray-900 mb-3">{env.location}</h3>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="flex items-center gap-2">
                  <Volume2 size={16} className="text-orange-600" />
                  <div>
                    <p className="text-sm text-gray-600">소음</p>
                    <p className={`font-medium ${env.noise_level > 85 ? 'text-red-600' : 'text-green-600'}`}>
                      {env.noise_level} dB
                    </p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Wind size={16} className="text-blue-600" />
                  <div>
                    <p className="text-sm text-gray-600">분진</p>
                    <p className="font-medium">{env.dust_level} mg/m³</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Thermometer size={16} className="text-red-600" />
                  <div>
                    <p className="text-sm text-gray-600">온도</p>
                    <p className="font-medium">{env.temperature}°C</p>
                  </div>
                </div>
                
                <div className="flex items-center gap-2">
                  <Activity size={16} className="text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">공기질</p>
                    <p className="font-medium">{env.air_quality}/100</p>
                  </div>
                </div>
              </div>
              
              <div className="mt-3 text-xs text-gray-500">
                최근 업데이트: {new Date(env.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Quick Actions */}
      <Card className="p-6">
        <h2 className="text-lg font-semibold mb-4">빠른 작업</h2>
        
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Button variant="outline" className="flex flex-col items-center p-4 h-auto">
            <FileText className="mb-2" size={24} />
            <span>보고서 생성</span>
          </Button>
          
          <Button variant="outline" className="flex flex-col items-center p-4 h-auto">
            <Settings className="mb-2" size={24} />
            <span>시스템 설정</span>
          </Button>
          
          <Button variant="outline" className="flex flex-col items-center p-4 h-auto">
            <BarChart3 className="mb-2" size={24} />
            <span>상세 분석</span>
          </Button>
          
          <Button variant="outline" className="flex flex-col items-center p-4 h-auto">
            <Bell className="mb-2" size={24} />
            <span>알림 설정</span>
          </Button>
        </div>
      </Card>
    </div>
  );
}