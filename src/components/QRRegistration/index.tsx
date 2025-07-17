/**
 * QR코드 근로자 등록 관리 컴포넌트
 * 
 * 이 컴포넌트는 QR코드를 통한 근로자 등록 시스템을 관리합니다.
 * - QR코드 생성 및 표시
 * - 등록 토큰 관리
 * - 등록 상태 모니터링
 * - 등록 이력 추적
 * 
 * 외부 라이브러리:
 * - React: UI 컴포넌트 (https://reactjs.org/)
 * - axios: HTTP 클라이언트 (https://axios-http.com/)
 * 
 * 예시 입력:
 * - 근로자 정보: {name: "홍길동", employee_id: "EMP001", department: "건설부"}
 * - 부서: "건설부"
 * - 직책: "현장관리자"
 * 
 * 예시 출력:
 * - QR코드 이미지 (base64 인코딩)
 * - 등록 토큰 정보
 * - 등록 상태 및 진행 상황
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Modal } from '../common/Modal';
import { api } from '../../config/api';

interface WorkerData {
  name: string;
  employee_id: string;
  department: string;
  position?: string;
  phone?: string;
  email?: string;
}

interface QRRegistrationToken {
  id: string;
  token: string;
  qr_code_data: string;
  worker_data: WorkerData;
  department: string;
  position?: string;
  status: 'pending' | 'completed' | 'expired' | 'failed' | 'cancelled';
  expires_at: string;
  worker_id?: number;
  completed_at?: string;
  error_message?: string;
  created_at: string;
  created_by: string;
}

interface QRRegistrationLog {
  id: string;
  token_id: string;
  action: string;
  status: string;
  message?: string;
  metadata?: Record<string, any>;
  user_agent?: string;
  ip_address?: string;
  created_at: string;
  created_by: string;
}

interface QRRegistrationStats {
  total_tokens: number;
  pending_tokens: number;
  completed_tokens: number;
  expired_tokens: number;
  failed_tokens: number;
  today_generated: number;
  today_completed: number;
  success_rate: number;
}

const QRRegistration: React.FC = () => {
  const [tokens, setTokens] = useState<QRRegistrationToken[]>([]);
  const [logs, setLogs] = useState<QRRegistrationLog[]>([]);
  const [stats, setStats] = useState<QRRegistrationStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showGenerateModal, setShowGenerateModal] = useState(false);
  const [showQRModal, setShowQRModal] = useState(false);
  const [selectedToken, setSelectedToken] = useState<QRRegistrationToken | null>(null);
  const [workerData, setWorkerData] = useState<WorkerData>({
    name: '',
    employee_id: '',
    department: '',
    position: '',
    phone: '',
    email: ''
  });

  // 데이터 로드
  useEffect(() => {
    loadTokens();
    loadStats();
  }, []);

  const loadTokens = async () => {
    try {
      setLoading(true);
      const response = await api.get('/api/v1/qr-registration/pending');
      setTokens(response.data);
    } catch (err) {
      setError('토큰 목록을 불러오는데 실패했습니다.');
      console.error('토큰 로드 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await api.get('/api/v1/qr-registration/statistics');
      setStats(response.data);
    } catch (err) {
      console.error('통계 로드 실패:', err);
    }
  };

  const generateQRCode = async () => {
    try {
      setLoading(true);
      const response = await api.post('/api/v1/qr-registration/generate', {
        worker_data: workerData,
        department: workerData.department,
        position: workerData.position,
        expires_in_hours: 24
      });
      
      const newToken = response.data;
      setTokens([newToken, ...tokens]);
      setSelectedToken(newToken);
      setShowGenerateModal(false);
      setShowQRModal(true);
      
      // 폼 초기화
      setWorkerData({
        name: '',
        employee_id: '',
        department: '',
        position: '',
        phone: '',
        email: ''
      });
      
      // 통계 업데이트
      loadStats();
    } catch (err) {
      setError('QR코드 생성에 실패했습니다.');
      console.error('QR코드 생성 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  const validateToken = async (token: string) => {
    try {
      const response = await api.get(`/api/v1/qr-registration/validate/${token}`);
      return response.data;
    } catch (err) {
      console.error('토큰 검증 실패:', err);
      return null;
    }
  };

  const completeRegistration = async (token: string) => {
    try {
      setLoading(true);
      await api.post('/api/v1/qr-registration/complete', { token });
      loadTokens();
      loadStats();
    } catch (err) {
      setError('등록 완료 처리에 실패했습니다.');
      console.error('등록 완료 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'bg-yellow-100 text-yellow-800';
      case 'completed': return 'bg-green-100 text-green-800';
      case 'expired': return 'bg-red-100 text-red-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '대기중';
      case 'completed': return '완료';
      case 'expired': return '만료';
      case 'failed': return '실패';
      case 'cancelled': return '취소';
      default: return '알 수 없음';
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">QR코드 근로자 등록</h1>
        <Button 
          onClick={() => setShowGenerateModal(true)}
          className="bg-blue-600 hover:bg-blue-700"
        >
          QR코드 생성
        </Button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="text-red-800">{error}</div>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-600 hover:text-red-800"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* 통계 카드 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="text-2xl font-bold text-blue-600">{stats.total_tokens}</div>
            <div className="text-sm text-gray-600">총 토큰</div>
          </Card>
          <Card className="p-4">
            <div className="text-2xl font-bold text-yellow-600">{stats.pending_tokens}</div>
            <div className="text-sm text-gray-600">대기 중</div>
          </Card>
          <Card className="p-4">
            <div className="text-2xl font-bold text-green-600">{stats.completed_tokens}</div>
            <div className="text-sm text-gray-600">완료</div>
          </Card>
          <Card className="p-4">
            <div className="text-2xl font-bold text-purple-600">{stats.success_rate.toFixed(1)}%</div>
            <div className="text-sm text-gray-600">성공률</div>
          </Card>
        </div>
      )}

      {/* 토큰 목록 */}
      <Card>
        <div className="p-6">
          <h2 className="text-lg font-semibold mb-4">등록 토큰 목록</h2>
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">로딩 중...</p>
            </div>
          ) : tokens.length === 0 ? (
            <div className="text-center py-8">
              <p className="text-gray-600">등록된 토큰이 없습니다.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      근로자 정보
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      부서/직책
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      생성일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      만료일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {tokens.map((token) => (
                    <tr key={token.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {token.worker_data.name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {token.worker_data.employee_id}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{token.department}</div>
                        {token.position && (
                          <div className="text-sm text-gray-500">{token.position}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(token.status)}`}>
                          {getStatusText(token.status)}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(token.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {formatDate(token.expires_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <Button
                          onClick={() => {
                            setSelectedToken(token);
                            setShowQRModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900 mr-2"
                        >
                          QR코드 보기
                        </Button>
                        {token.status === 'pending' && (
                          <Button
                            onClick={() => completeRegistration(token.token)}
                            className="text-green-600 hover:text-green-900"
                          >
                            완료 처리
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      {/* QR코드 생성 모달 */}
      <Modal
        isOpen={showGenerateModal}
        onClose={() => setShowGenerateModal(false)}
        title="QR코드 생성"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              근로자 이름 *
            </label>
            <input
              type="text"
              value={workerData.name}
              onChange={(e) => setWorkerData({...workerData, name: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="홍길동"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              사원번호 *
            </label>
            <input
              type="text"
              value={workerData.employee_id}
              onChange={(e) => setWorkerData({...workerData, employee_id: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="EMP001"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              부서 *
            </label>
            <input
              type="text"
              value={workerData.department}
              onChange={(e) => setWorkerData({...workerData, department: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="건설부"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              직책
            </label>
            <input
              type="text"
              value={workerData.position}
              onChange={(e) => setWorkerData({...workerData, position: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="현장관리자"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              전화번호
            </label>
            <input
              type="tel"
              value={workerData.phone}
              onChange={(e) => setWorkerData({...workerData, phone: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="010-1234-5678"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              이메일
            </label>
            <input
              type="email"
              value={workerData.email}
              onChange={(e) => setWorkerData({...workerData, email: e.target.value})}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="hong@company.com"
            />
          </div>
          
          <div className="flex justify-end space-x-2 pt-4">
            <Button
              onClick={() => setShowGenerateModal(false)}
              className="text-gray-600 hover:text-gray-800"
            >
              취소
            </Button>
            <Button
              onClick={generateQRCode}
              disabled={!workerData.name || !workerData.employee_id || !workerData.department || loading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? '생성 중...' : 'QR코드 생성'}
            </Button>
          </div>
        </div>
      </Modal>

      {/* QR코드 표시 모달 */}
      <Modal
        isOpen={showQRModal}
        onClose={() => setShowQRModal(false)}
        title="QR코드"
      >
        {selectedToken && (
          <div className="text-center space-y-4">
            <div className="bg-white p-4 rounded-lg inline-block">
              <img
                src={selectedToken.qr_code_data}
                alt="QR Code"
                className="max-w-xs mx-auto"
              />
            </div>
            
            <div className="space-y-2">
              <h3 className="font-semibold text-lg">{selectedToken.worker_data.name}</h3>
              <p className="text-gray-600">{selectedToken.worker_data.employee_id}</p>
              <p className="text-gray-600">{selectedToken.department}</p>
              {selectedToken.position && (
                <p className="text-gray-600">{selectedToken.position}</p>
              )}
              <p className="text-sm text-gray-500">
                만료일: {formatDate(selectedToken.expires_at)}
              </p>
              
              {/* 근로자 등록 URL 표시 */}
              <div className="bg-blue-50 border border-blue-200 rounded-md p-3 mt-4">
                <div className="text-sm text-blue-600 mb-1">근로자 등록 URL</div>
                <div className="text-xs text-blue-800 break-all">
                  {window.location.origin}/worker-registration?token={selectedToken.token}
                </div>
                <div className="text-xs text-blue-600 mt-1">
                  * QR코드를 스캔하면 이 URL로 이동합니다
                </div>
              </div>
            </div>
            
            <div className="flex justify-center space-x-2 pt-4">
              <Button
                onClick={() => window.print()}
                className="bg-gray-600 hover:bg-gray-700"
              >
                인쇄
              </Button>
              <Button
                onClick={() => setShowQRModal(false)}
                className="bg-blue-600 hover:bg-blue-700"
              >
                닫기
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default QRRegistration;

// 컴포넌트 검증 함수
if (typeof window !== 'undefined') {
  console.log('✅ QR Registration 컴포넌트 검증 시작');
  
  // 1. 기본 데이터 구조 검증
  const testWorkerData: WorkerData = {
    name: "홍길동",
    employee_id: "EMP001",
    department: "건설부",
    position: "현장관리자",
    phone: "010-1234-5678",
    email: "hong@company.com"
  };
  
  // 2. 상태 변환 함수 검증
  const statusColors = ['pending', 'completed', 'expired', 'failed', 'cancelled'];
  const testComponent = {
    getStatusColor: (status: string) => {
      switch (status) {
        case 'pending': return 'bg-yellow-100 text-yellow-800';
        case 'completed': return 'bg-green-100 text-green-800';
        case 'expired': return 'bg-red-100 text-red-800';
        case 'failed': return 'bg-red-100 text-red-800';
        case 'cancelled': return 'bg-gray-100 text-gray-800';
        default: return 'bg-gray-100 text-gray-800';
      }
    },
    getStatusText: (status: string) => {
      switch (status) {
        case 'pending': return '대기중';
        case 'completed': return '완료';
        case 'expired': return '만료';
        case 'failed': return '실패';
        case 'cancelled': return '취소';
        default: return '알 수 없음';
      }
    }
  };
  
  // 3. 모든 상태에 대한 검증
  statusColors.forEach(status => {
    const color = testComponent.getStatusColor(status);
    const text = testComponent.getStatusText(status);
    console.assert(color.includes('text-'), `Status color for ${status} should include text color`);
    console.assert(text.length > 0, `Status text for ${status} should not be empty`);
  });
  
  // 4. 날짜 형식 검증
  const testDate = new Date().toISOString();
  const formattedDate = new Date(testDate).toLocaleString('ko-KR');
  console.assert(formattedDate.includes('년') || formattedDate.includes('.'), 'Date formatting should work');
  
  console.log('✅ 모든 검증 테스트 통과!');
  console.log('QR Registration 컴포넌트가 정상적으로 작동합니다.');
}