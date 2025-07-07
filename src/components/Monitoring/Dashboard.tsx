import React, { useState, useEffect, useRef } from 'react';
import { apiUrl, wsUrl } from '../../config/api';
import { Line, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement,
} from 'chart.js';

// Chart.js 등록
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
  BarElement
);

interface SystemMetrics {
  cpu: {
    percent: number;
    count: number;
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
  };
}

interface Alert {
  type: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  timestamp: string;
  value?: number;
}

export const MonitoringDashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [cpuHistory, setCpuHistory] = useState<number[]>([]);
  const [memoryHistory, setMemoryHistory] = useState<number[]>([]);
  const [timeLabels, setTimeLabels] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [healthStatus, setHealthStatus] = useState<'healthy' | 'degraded' | 'unhealthy'>('healthy');
  
  const wsRef = useRef<WebSocket | null>(null);
  const maxDataPoints = 30; // 최대 30개 데이터 포인트

  useEffect(() => {
    // 초기 메트릭 로드
    fetchCurrentMetrics();
    fetchAlerts();
    fetchHealthStatus();

    // WebSocket 연결
    connectWebSocket();

    // 정리 함수
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const fetchCurrentMetrics = async () => {
    try {
      const response = await fetch(apiUrl('/monitoring/metrics/current'));
      const data = await response.json();
      if (data.system) {
        setMetrics(data.system);
      }
    } catch (error) {
      console.error('메트릭 로드 실패:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch(apiUrl('/monitoring/alerts'));
      const data = await response.json();
      setAlerts(data.latest || []);
    } catch (error) {
      console.error('알림 로드 실패:', error);
    }
  };

  const fetchHealthStatus = async () => {
    try {
      const response = await fetch(apiUrl('/monitoring/health'));
      const data = await response.json();
      setHealthStatus(data.status || 'healthy');
    } catch (error) {
      console.error('헬스 상태 로드 실패:', error);
    }
  };

  const connectWebSocket = () => {
    const wsUrlPath = wsUrl('/monitoring/ws');
    const ws = new WebSocket(wsUrlPath);

    ws.onopen = () => {
      console.log('WebSocket 연결됨');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      
      if (message.type === 'update' && message.data) {
        const { system } = message.data;
        if (system) {
          setMetrics(system);
          updateHistory(system);
        }
      } else if (message.type === 'alert' && message.data) {
        setAlerts(prev => [...message.data, ...prev].slice(0, 50));
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket 에러:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket 연결 종료');
      setIsConnected(false);
      // 5초 후 재연결 시도
      setTimeout(connectWebSocket, 5000);
    };

    wsRef.current = ws;
  };

  const updateHistory = (system: SystemMetrics) => {
    const now = new Date().toLocaleTimeString('ko-KR', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });

    setCpuHistory(prev => [...prev, system.cpu.percent].slice(-maxDataPoints));
    setMemoryHistory(prev => [...prev, system.memory.percent].slice(-maxDataPoints));
    setTimeLabels(prev => [...prev, now].slice(-maxDataPoints));
  };

  // 차트 설정
  const lineChartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: '시스템 리소스 사용률',
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  const lineChartData = {
    labels: timeLabels,
    datasets: [
      {
        label: 'CPU %',
        data: cpuHistory,
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.5)',
        tension: 0.1,
      },
      {
        label: 'Memory %',
        data: memoryHistory,
        borderColor: 'rgb(53, 162, 235)',
        backgroundColor: 'rgba(53, 162, 235, 0.5)',
        tension: 0.1,
      },
    ],
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'bg-green-500';
      case 'degraded': return 'bg-yellow-500';
      case 'unhealthy': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-100';
      case 'warning': return 'text-yellow-600 bg-yellow-100';
      case 'info': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">실시간 모니터링 대시보드</h1>
        <div className="flex items-center space-x-4">
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'} mr-2`} />
            <span className="text-sm text-gray-600">
              {isConnected ? '실시간 연결됨' : '연결 끊김'}
            </span>
          </div>
          <div className="flex items-center">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(healthStatus)} mr-2`} />
            <span className="text-sm font-medium">
              시스템 상태: {healthStatus === 'healthy' ? '정상' : healthStatus === 'degraded' ? '주의' : '위험'}
            </span>
          </div>
        </div>
      </div>

      {/* 주요 메트릭 카드 */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* CPU 사용률 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">CPU 사용률</h3>
            <div className="text-3xl font-bold text-blue-600">
              {metrics.cpu.percent.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 mt-1">
              코어 수: {metrics.cpu.count}
            </div>
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    metrics.cpu.percent > 80 ? 'bg-red-500' : 
                    metrics.cpu.percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${metrics.cpu.percent}%` }}
                />
              </div>
            </div>
          </div>

          {/* 메모리 사용률 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">메모리 사용률</h3>
            <div className="text-3xl font-bold text-purple-600">
              {metrics.memory.percent.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {(metrics.memory.used_mb / 1024).toFixed(1)} GB / {(metrics.memory.total_mb / 1024).toFixed(1)} GB
            </div>
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    metrics.memory.percent > 85 ? 'bg-red-500' : 
                    metrics.memory.percent > 70 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${metrics.memory.percent}%` }}
                />
              </div>
            </div>
          </div>

          {/* 디스크 사용률 */}
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-700 mb-2">디스크 사용률</h3>
            <div className="text-3xl font-bold text-green-600">
              {metrics.disk.percent.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500 mt-1">
              {metrics.disk.used_gb.toFixed(1)} GB / {(metrics.disk.used_gb + metrics.disk.free_gb).toFixed(1)} GB
            </div>
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className={`h-2 rounded-full ${
                    metrics.disk.percent > 90 ? 'bg-red-500' : 
                    metrics.disk.percent > 80 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${metrics.disk.percent}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 실시간 차트 */}
      <div className="bg-white rounded-lg shadow p-6">
        <Line options={lineChartOptions} data={lineChartData} />
      </div>

      {/* 최근 알림 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">최근 알림</h3>
        <div className="space-y-2 max-h-60 overflow-y-auto">
          {alerts.length === 0 ? (
            <p className="text-gray-500 text-center py-4">알림이 없습니다</p>
          ) : (
            alerts.map((alert, index) => (
              <div 
                key={index} 
                className={`p-3 rounded-lg ${getSeverityColor(alert.severity)}`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="font-medium">{alert.message}</p>
                    {alert.value !== undefined && (
                      <p className="text-sm mt-1">값: {alert.value.toFixed(1)}</p>
                    )}
                  </div>
                  <span className="text-xs whitespace-nowrap ml-4">
                    {new Date(alert.timestamp).toLocaleTimeString('ko-KR')}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};