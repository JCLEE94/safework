import React, { useState, useEffect, useRef } from 'react';
import { Activity, Cpu, HardDrive, MemoryStick, Network, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

// Types
interface SystemMetrics {
  timestamp: string;
  system: {
    cpu: {
      percent: number;
      count: number;
      per_cpu: number[];
    };
    memory: {
      percent: number;
      used_mb: number;
      available_mb: number;
      total_mb: number;
    };
    disk: {
      percent: number;
      used_gb: number;
      free_gb: number;
      total_gb: number;
    };
    network: {
      bytes_sent: number;
      bytes_recv: number;
      packets_sent: number;
      packets_recv: number;
    };
  };
  process: {
    memory_mb: number;
    cpu_percent: number;
    num_threads: number;
    num_fds?: number;
  };
}

interface ApplicationMetrics {
  api_calls: {
    total_calls: number;
    calls_per_minute: number;
    top_endpoints: string[];
  };
  error_rate: number;
  avg_response_time_ms: number;
  active_connections: number;
  cache_hit_rate: number;
}

interface Alert {
  type: string;
  severity: 'info' | 'warning' | 'critical';
  message: string;
  value: number;
  threshold: number;
  timestamp: string;
}

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  issues: string[];
  system_metrics: SystemMetrics;
  application_metrics: ApplicationMetrics;
  recent_alerts: Alert[];
}

export function RealTimeMonitoring() {
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);
  const [metricsHistory, setMetricsHistory] = useState<SystemMetrics[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const wsRef = useRef<WebSocket | null>(null);

  // WebSocket 연결 설정
  useEffect(() => {
    connectWebSocket();
    
    // 초기 데이터 로드
    fetchInitialData();
    
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/api/v1/monitoring/ws`;
      
      wsRef.current = new WebSocket(wsUrl);
      
      wsRef.current.onopen = () => {
        setConnectionStatus('connected');
        console.log('WebSocket 연결됨');
      };
      
      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'metrics') {
          updateMetrics(data.data);
        } else if (data.type === 'alert') {
          addAlert(data.data);
        }
      };
      
      wsRef.current.onclose = () => {
        setConnectionStatus('disconnected');
        console.log('WebSocket 연결 끊어짐, 재연결 시도 중...');
        
        // 5초 후 재연결 시도
        setTimeout(() => {
          if (wsRef.current?.readyState === WebSocket.CLOSED) {
            connectWebSocket();
          }
        }, 5000);
      };
      
      wsRef.current.onerror = (error) => {
        console.error('WebSocket 에러:', error);
        setConnectionStatus('disconnected');
      };
      
    } catch (error) {
      console.error('WebSocket 연결 실패:', error);
      setConnectionStatus('disconnected');
    }
  };

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      
      // 헬스 상태 가져오기
      const healthResponse = await fetch('/api/v1/monitoring/health');
      if (healthResponse.ok) {
        const healthData = await healthResponse.json();
        setHealthStatus(healthData);
      }
      
      // 메트릭 히스토리 가져오기
      const historyResponse = await fetch('/api/v1/monitoring/metrics/history?minutes=60');
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setMetricsHistory(historyData);
      }
      
      // 알림 가져오기
      const alertsResponse = await fetch('/api/v1/monitoring/alerts');
      if (alertsResponse.ok) {
        const alertsData = await alertsResponse.json();
        setAlerts(alertsData);
      }
      
    } catch (error) {
      console.error('초기 데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateMetrics = (newMetrics: SystemMetrics) => {
    setMetricsHistory(prev => {
      const updated = [...prev, newMetrics];
      // 최근 100개만 유지
      return updated.slice(-100);
    });
    
    // 헬스 상태 업데이트
    if (healthStatus) {
      setHealthStatus(prev => prev ? {
        ...prev,
        system_metrics: newMetrics
      } : null);
    }
  };

  const addAlert = (newAlert: Alert) => {
    setAlerts(prev => {
      const updated = [newAlert, ...prev];
      // 최근 50개만 유지
      return updated.slice(0, 50);
    });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-600';
      case 'degraded': return 'text-yellow-600';
      case 'unhealthy': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'degraded': return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'unhealthy': return <XCircle className="w-5 h-5 text-red-600" />;
      default: return <Activity className="w-5 h-5 text-gray-600" />;
    }
  };

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">모니터링 데이터 로딩 중...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-800">실시간 시스템 모니터링</h1>
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${
            connectionStatus === 'connected' ? 'bg-green-500' : 
            connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
          }`} />
          <span className="text-sm text-gray-600">
            {connectionStatus === 'connected' ? '실시간 연결됨' : 
             connectionStatus === 'connecting' ? '연결 중...' : '연결 끊어짐'}
          </span>
        </div>
      </div>

      {/* 전체 상태 카드 */}
      {healthStatus && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-800">시스템 상태</h2>
            <div className="flex items-center space-x-2">
              {getStatusIcon(healthStatus.status)}
              <span className={`font-medium ${getStatusColor(healthStatus.status)}`}>
                {healthStatus.status === 'healthy' ? '정상' :
                 healthStatus.status === 'degraded' ? '주의' : '위험'}
              </span>
            </div>
          </div>
          
          {healthStatus.issues.length > 0 && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-yellow-800 mb-2">발견된 문제:</h3>
              <ul className="list-disc list-inside text-sm text-yellow-700">
                {healthStatus.issues.map((issue, index) => (
                  <li key={index}>{issue}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 시스템 메트릭 카드들 */}
      {healthStatus?.system_metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* CPU 사용률 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Cpu className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-gray-700">CPU</span>
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {healthStatus.system_metrics.system.cpu.percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  healthStatus.system_metrics.system.cpu.percent > 80 ? 'bg-red-500' :
                  healthStatus.system_metrics.system.cpu.percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${healthStatus.system_metrics.system.cpu.percent}%` }}
              />
            </div>
            <div className="text-sm text-gray-500 mt-2">
              {healthStatus.system_metrics.system.cpu.count}개 코어
            </div>
          </div>

          {/* 메모리 사용률 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <MemoryStick className="w-5 h-5 text-purple-600" />
                <span className="font-medium text-gray-700">메모리</span>
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {healthStatus.system_metrics.system.memory.percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  healthStatus.system_metrics.system.memory.percent > 85 ? 'bg-red-500' :
                  healthStatus.system_metrics.system.memory.percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${healthStatus.system_metrics.system.memory.percent}%` }}
              />
            </div>
            <div className="text-sm text-gray-500 mt-2">
              {Math.round(healthStatus.system_metrics.system.memory.used_mb)} MB / {Math.round(healthStatus.system_metrics.system.memory.total_mb)} MB
            </div>
          </div>

          {/* 디스크 사용률 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <HardDrive className="w-5 h-5 text-green-600" />
                <span className="font-medium text-gray-700">디스크</span>
              </div>
              <span className="text-2xl font-bold text-gray-900">
                {healthStatus.system_metrics.system.disk.percent.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className={`h-2 rounded-full ${
                  healthStatus.system_metrics.system.disk.percent > 90 ? 'bg-red-500' :
                  healthStatus.system_metrics.system.disk.percent > 75 ? 'bg-yellow-500' : 'bg-green-500'
                }`}
                style={{ width: `${healthStatus.system_metrics.system.disk.percent}%` }}
              />
            </div>
            <div className="text-sm text-gray-500 mt-2">
              {healthStatus.system_metrics.system.disk.free_gb.toFixed(1)} GB 사용 가능
            </div>
          </div>

          {/* 네트워크 */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-2">
                <Network className="w-5 h-5 text-orange-600" />
                <span className="font-medium text-gray-700">네트워크</span>
              </div>
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">송신:</span>
                <span className="font-medium">
                  {formatBytes(healthStatus.system_metrics.system.network.bytes_sent)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">수신:</span>
                <span className="font-medium">
                  {formatBytes(healthStatus.system_metrics.system.network.bytes_recv)}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 애플리케이션 메트릭 */}
      {healthStatus?.application_metrics && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">애플리케이션 성능</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {healthStatus.application_metrics.api_calls.calls_per_minute}
              </div>
              <div className="text-sm text-gray-600">분당 API 호출</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {(healthStatus.application_metrics.error_rate * 100).toFixed(2)}%
              </div>
              <div className="text-sm text-gray-600">에러율</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {healthStatus.application_metrics.avg_response_time_ms.toFixed(0)}ms
              </div>
              <div className="text-sm text-gray-600">평균 응답시간</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {healthStatus.application_metrics.cache_hit_rate.toFixed(1)}%
              </div>
              <div className="text-sm text-gray-600">캐시 히트율</div>
            </div>
          </div>
        </div>
      )}

      {/* 최근 알림 */}
      {alerts.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">최근 알림</h2>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {alerts.slice(0, 10).map((alert, index) => (
              <div 
                key={index}
                className={`p-3 rounded-lg border-l-4 ${
                  alert.severity === 'critical' ? 'bg-red-50 border-red-500' :
                  alert.severity === 'warning' ? 'bg-yellow-50 border-yellow-500' :
                  'bg-blue-50 border-blue-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <AlertTriangle className={`w-4 h-4 ${
                      alert.severity === 'critical' ? 'text-red-600' :
                      alert.severity === 'warning' ? 'text-yellow-600' :
                      'text-blue-600'
                    }`} />
                    <span className="font-medium text-gray-900">{alert.message}</span>
                  </div>
                  <span className="text-sm text-gray-500">
                    {new Date(alert.timestamp).toLocaleString('ko-KR')}
                  </span>
                </div>
                <div className="text-sm text-gray-600 mt-1">
                  현재값: {alert.value} / 임계값: {alert.threshold}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}