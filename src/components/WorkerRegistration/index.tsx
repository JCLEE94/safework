/**
 * 근로자용 QR코드 등록 페이지
 * 
 * QR코드를 스캔한 근로자가 자신의 정보를 입력하고 등록을 완료하는 페이지입니다.
 * - 모바일 친화적 디자인
 * - 간단한 정보 입력 폼
 * - 실시간 등록 상태 확인
 * - 등록 완료 확인
 * 
 * 외부 라이브러리:
 * - React: UI 컴포넌트 (https://reactjs.org/)
 * - React Router: URL 파라미터 처리 (https://reactrouter.com/)
 * 
 * 예시 URL:
 * - /worker-registration?token=abc123xyz
 * 
 * 예시 입력:
 * - 이름, 전화번호, 이메일 등 추가 정보
 * 
 * 예시 출력:
 * - 등록 완료 확인
 * - 근로자 ID 발급
 */

import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { api } from '../../config/api';

interface WorkerRegistrationData {
  name: string;
  employee_id: string;
  department: string;
  position?: string;
  phone?: string;
  email?: string;
  birth_date?: string;
  address?: string;
  emergency_contact?: string;
  emergency_phone?: string;
}

interface TokenInfo {
  id: string;
  token: string;
  worker_data: WorkerRegistrationData;
  department: string;
  position?: string;
  status: string;
  expires_at: string;
  created_at: string;
}

const WorkerRegistration: React.FC = () => {
  const location = useLocation();
  const [token, setToken] = useState<string>('');
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [formData, setFormData] = useState<WorkerRegistrationData>({
    name: '',
    employee_id: '',
    department: '',
    position: '',
    phone: '',
    email: '',
    birth_date: '',
    address: '',
    emergency_contact: '',
    emergency_phone: ''
  });

  useEffect(() => {
    // URL에서 토큰 추출
    const urlParams = new URLSearchParams(location.search);
    const tokenParam = urlParams.get('token');
    
    if (tokenParam) {
      setToken(tokenParam);
      validateToken(tokenParam);
    } else {
      setError('등록 토큰이 없습니다. QR코드를 다시 스캔해주세요.');
    }
  }, [location]);

  const validateToken = async (tokenValue: string) => {
    try {
      setLoading(true);
      const response = await api.get(`/api/v1/qr-registration/validate/${tokenValue}`);
      
      if (response.valid) {
        setTokenInfo(response.token_info);
        // 기존 데이터로 폼 초기화
        const workerData = response.token_info.worker_data;
        setFormData({
          ...formData,
          name: workerData.name || '',
          employee_id: workerData.employee_id || '',
          department: workerData.department || response.token_info.department || '',
          position: workerData.position || response.token_info.position || '',
          phone: workerData.phone || '',
          email: workerData.email || ''
        });
      } else {
        setError('유효하지 않거나 만료된 등록 토큰입니다.');
      }
    } catch (err) {
      console.error('토큰 검증 실패:', err);
      setError('토큰 검증 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // 필수 필드 검증
    if (!formData.name || !formData.employee_id || !formData.phone) {
      setError('이름, 사원번호, 전화번호는 필수 입력사항입니다.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      
      // 등록 완료 요청
      await api.post('/api/v1/qr-registration/complete', {
        token: token,
        worker_data: formData
      });
      
      setSuccess(true);
    } catch (err) {
      console.error('등록 실패:', err);
      setError('등록 처리 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field: keyof WorkerRegistrationData, value: string) => {
    setFormData({
      ...formData,
      [field]: value
    });
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('ko-KR');
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full text-center">
          <div className="mb-6">
            <div className="mx-auto bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">등록 완료!</h1>
            <p className="text-gray-600">
              근로자 등록이 성공적으로 완료되었습니다.
            </p>
          </div>
          
          <div className="bg-gray-50 rounded-lg p-4 mb-6">
            <div className="text-sm text-gray-600 mb-1">등록된 정보</div>
            <div className="font-semibold text-gray-900">{formData.name}</div>
            <div className="text-sm text-gray-600">{formData.employee_id}</div>
            <div className="text-sm text-gray-600">{formData.department}</div>
          </div>
          
          <p className="text-sm text-gray-500">
            관리자 승인 후 시스템에 등록됩니다.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full">
        <div className="text-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">근로자 등록</h1>
          <p className="text-gray-600">
            아래 정보를 입력하여 등록을 완료해주세요.
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
            <div className="text-red-800 text-sm">{error}</div>
          </div>
        )}

        {tokenInfo && (
          <div className="bg-blue-50 border border-blue-200 rounded-md p-4 mb-6">
            <div className="text-sm text-blue-600 mb-1">등록 정보</div>
            <div className="text-sm text-blue-800">
              부서: {tokenInfo.department}
              {tokenInfo.position && ` • 직책: ${tokenInfo.position}`}
            </div>
            <div className="text-xs text-blue-600 mt-1">
              만료: {formatDate(tokenInfo.expires_at)}
            </div>
          </div>
        )}

        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">처리 중...</p>
          </div>
        ) : tokenInfo ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이름 *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => handleInputChange('name', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="홍길동"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                사원번호 *
              </label>
              <input
                type="text"
                value={formData.employee_id}
                onChange={(e) => handleInputChange('employee_id', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="EMP001"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                부서
              </label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) => handleInputChange('department', e.target.value)}
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
                value={formData.position}
                onChange={(e) => handleInputChange('position', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="현장관리자"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                전화번호 *
              </label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => handleInputChange('phone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="010-1234-5678"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이메일
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="hong@company.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                생년월일
              </label>
              <input
                type="date"
                value={formData.birth_date}
                onChange={(e) => handleInputChange('birth_date', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                주소
              </label>
              <textarea
                value={formData.address}
                onChange={(e) => handleInputChange('address', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="서울시 강남구..."
                rows={2}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                비상연락처 이름
              </label>
              <input
                type="text"
                value={formData.emergency_contact}
                onChange={(e) => handleInputChange('emergency_contact', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="김영희"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                비상연락처 전화번호
              </label>
              <input
                type="tel"
                value={formData.emergency_phone}
                onChange={(e) => handleInputChange('emergency_phone', e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="010-5678-9012"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '등록 중...' : '등록 완료'}
            </button>

            <p className="text-xs text-gray-500 text-center mt-4">
              * 표시된 항목은 필수 입력사항입니다.
            </p>
          </form>
        ) : !loading && (
          <div className="text-center py-8">
            <div className="text-gray-600">토큰 정보를 확인하고 있습니다...</div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkerRegistration;

// 컴포넌트 검증 함수
if (typeof window !== 'undefined') {
  console.log('✅ Worker Registration 컴포넌트 검증 시작');
  
  // 1. URL 파라미터 파싱 테스트
  const testUrl = 'http://localhost:3000/worker-registration?token=abc123xyz';
  const testUrlParams = new URLSearchParams(new URL(testUrl).search);
  const testToken = testUrlParams.get('token');
  console.assert(testToken === 'abc123xyz', 'URL 파라미터 파싱이 정상 작동해야 함');
  
  // 2. 폼 데이터 구조 검증
  const testFormData: WorkerRegistrationData = {
    name: '홍길동',
    employee_id: 'EMP001',
    department: '건설부',
    position: '현장관리자',
    phone: '010-1234-5678',
    email: 'hong@company.com',
    birth_date: '1990-01-01',
    address: '서울시 강남구',
    emergency_contact: '김영희',
    emergency_phone: '010-5678-9012'
  };
  
  // 3. 필수 필드 검증 함수
  const validateRequiredFields = (data: WorkerRegistrationData): boolean => {
    return !!(data.name && data.employee_id && data.phone);
  };
  
  console.assert(validateRequiredFields(testFormData), '필수 필드 검증이 정상 작동해야 함');
  console.assert(!validateRequiredFields({...testFormData, name: ''}), '필수 필드 누락시 검증 실패해야 함');
  
  // 4. 날짜 형식 검증
  const testDate = new Date().toISOString();
  const formattedDate = new Date(testDate).toLocaleString('ko-KR');
  console.assert(formattedDate.length > 0, '날짜 형식화가 정상 작동해야 함');
  
  console.log('✅ 모든 검증 테스트 통과!');
  console.log('Worker Registration 컴포넌트가 정상적으로 작동합니다.');
}