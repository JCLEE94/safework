import React, { useState, useEffect } from 'react';
import { Button } from './common/Button';
import { Card } from './common/Card';
import { authService } from '../services/authService';

interface QRInfo {
  registration_url: string;
  qr_download_url: string;
  instructions: {
    step1: string;
    step2: string;
    step3: string;
    step4: string;
  };
  features: string[];
}

export function CommonQRGenerator() {
  const [loading, setLoading] = useState(false);
  const [qrInfo, setQrInfo] = useState<QRInfo | null>(null);
  const [qrImageUrl, setQrImageUrl] = useState<string>('');
  const [error, setError] = useState('');

  useEffect(() => {
    fetchQRInfo();
  }, []);

  const fetchQRInfo = async () => {
    try {
      const response = await fetch('/api/v1/common-qr/info', {
        headers: {
          Authorization: `Bearer ${authService.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('QR 정보를 가져올 수 없습니다');
      }

      const data = await response.json();
      setQrInfo(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : '오류가 발생했습니다');
    }
  };

  const generateQRCode = async () => {
    setLoading(true);
    setError('');

    try {
      const response = await fetch('/api/v1/common-qr/generate?size=400', {
        headers: {
          Authorization: `Bearer ${authService.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('QR 코드 생성에 실패했습니다');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      setQrImageUrl(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'QR 코드 생성 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const downloadQRCode = () => {
    if (!qrImageUrl) return;

    const link = document.createElement('a');
    link.href = qrImageUrl;
    link.download = `safework_common_qr_${new Date().toISOString().split('T')[0]}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">공통 QR 코드 관리</h1>

      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* QR 코드 생성 섹션 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">QR 코드 생성</h2>
          
          <div className="space-y-4">
            {!qrImageUrl ? (
              <div className="h-64 flex items-center justify-center bg-gray-100 rounded">
                <p className="text-gray-500">QR 코드를 생성하려면 버튼을 클릭하세요</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <img 
                  src={qrImageUrl} 
                  alt="공통 QR 코드" 
                  className="max-w-full h-auto border border-gray-300 rounded"
                />
                <p className="mt-2 text-sm text-gray-600">
                  이 QR 코드는 영구적으로 사용 가능합니다
                </p>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                onClick={generateQRCode}
                disabled={loading}
                className="flex-1"
              >
                {loading ? '생성 중...' : 'QR 코드 생성'}
              </Button>

              {qrImageUrl && (
                <Button
                  onClick={downloadQRCode}
                  variant="secondary"
                  className="flex-1"
                >
                  다운로드
                </Button>
              )}
            </div>
          </div>
        </Card>

        {/* 사용 안내 섹션 */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">사용 안내</h2>
          
          {qrInfo && (
            <div className="space-y-4">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">사용 방법</h3>
                <ol className="list-decimal list-inside space-y-1 text-sm text-gray-600">
                  <li>{qrInfo.instructions.step1}</li>
                  <li>{qrInfo.instructions.step2}</li>
                  <li>{qrInfo.instructions.step3}</li>
                  <li>{qrInfo.instructions.step4}</li>
                </ol>
              </div>

              <div>
                <h3 className="font-medium text-gray-900 mb-2">특징</h3>
                <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
                  {qrInfo.features.map((feature, index) => (
                    <li key={index}>{feature}</li>
                  ))}
                </ul>
              </div>

              <div className="pt-4 border-t border-gray-200">
                <p className="text-sm text-gray-600">
                  <strong>등록 URL:</strong>{' '}
                  <a 
                    href={qrInfo.registration_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline"
                  >
                    {qrInfo.registration_url}
                  </a>
                </p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* 통계 섹션 */}
      <Card className="mt-6 p-6">
        <h2 className="text-xl font-semibold mb-4">등록 통계</h2>
        <CommonQRStats />
      </Card>
    </div>
  );
}

// 통계 컴포넌트
function CommonQRStats() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState('today');

  useEffect(() => {
    fetchStats();
  }, [period]);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await fetch(`/api/v1/common-qr/stats?period=${period}`, {
        headers: {
          Authorization: `Bearer ${authService.getToken()}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('통계 조회 오류:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-4">통계 로딩 중...</div>;
  }

  if (!stats) {
    return <div className="text-center py-4 text-gray-500">통계를 불러올 수 없습니다</div>;
  }

  return (
    <div>
      <div className="mb-4">
        <select
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="today">오늘</option>
          <option value="week">최근 7일</option>
          <option value="month">이번 달</option>
          <option value="all">전체</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 p-4 rounded">
          <p className="text-sm text-gray-600">총 등록자</p>
          <p className="text-2xl font-bold text-blue-600">{stats.total_registrations}명</p>
        </div>

        {stats.hourly_stats && (
          <div className="md:col-span-2 bg-gray-50 p-4 rounded">
            <p className="text-sm text-gray-600 mb-2">시간대별 등록 현황</p>
            <div className="flex items-end space-x-1" style={{ height: '60px' }}>
              {Array.from({ length: 24 }, (_, i) => {
                const count = stats.hourly_stats[i] || 0;
                const maxCount = Math.max(...Object.values(stats.hourly_stats), 1);
                const height = (count / maxCount) * 100;
                
                return (
                  <div
                    key={i}
                    className="flex-1 bg-blue-400 rounded-t"
                    style={{ height: `${height}%` }}
                    title={`${i}시: ${count}명`}
                  />
                );
              })}
            </div>
          </div>
        )}
      </div>

      {stats.department_stats && Object.keys(stats.department_stats).length > 0 && (
        <div className="mt-4">
          <p className="text-sm text-gray-600 mb-2">부서별 등록 현황</p>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {Object.entries(stats.department_stats).map(([dept, count]) => (
              <div key={dept} className="bg-gray-50 p-2 rounded text-center">
                <p className="text-xs text-gray-600">{dept}</p>
                <p className="font-semibold">{count as number}명</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}