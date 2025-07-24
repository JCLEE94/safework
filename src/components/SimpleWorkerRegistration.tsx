/**
 * 간단한 근로자 등록 컴포넌트
 * 
 * 근로자가 휴대폰으로 직접 등록할 수 있는 간단한 폼입니다.
 * QR 코드나 복잡한 토큰 시스템 없이 바로 등록 가능합니다.
 */

import React, { useState } from 'react';
import { CheckCircle, AlertCircle, User, Phone, Building } from 'lucide-react';

interface WorkerRegistrationData {
  name: string;
  employee_id: string;
  department: string;
  position: string;
  phone: string;
  email?: string;
  birth_date: string;
  gender: string;
  employment_type: string;
  work_type: string;
  hire_date: string;
  company_name: string;
}

const SimpleWorkerRegistration: React.FC = () => {
  const [formData, setFormData] = useState<WorkerRegistrationData>({
    name: '',
    employee_id: '',
    department: '',
    position: '',
    phone: '',
    email: '',
    birth_date: '',
    gender: '',
    employment_type: '정규직',
    work_type: 'construction',
    hire_date: '',
    company_name: ''
  });

  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string>('');
  const [checkingEmployee, setCheckingEmployee] = useState(false);
  const [employeeExists, setEmployeeExists] = useState<boolean | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // 사원번호 변경 시 기존 확인 결과 초기화
    if (name === 'employee_id') {
      setEmployeeExists(null);
      setError('');
    }
  };

  const checkEmployeeId = async () => {
    if (!formData.employee_id.trim()) {
      setError('사원번호를 입력해주세요');
      return;
    }

    setCheckingEmployee(true);
    try {
      const response = await fetch(`/api/v1/simple-registration/check/${formData.employee_id}`);
      const data = await response.json();
      
      if (data.exists) {
        setEmployeeExists(true);
        setError(`이미 등록된 사원번호입니다 (${data.worker_info?.name})`);
      } else {
        setEmployeeExists(false);
        setError('');
      }
    } catch (err) {
      setError('사원번호 확인 중 오류가 발생했습니다');
    } finally {
      setCheckingEmployee(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    // 필수 항목 검증
    const requiredFields = ['name', 'employee_id', 'department', 'phone', 'birth_date', 'gender'];
    for (const field of requiredFields) {
      if (!formData[field as keyof WorkerRegistrationData]?.trim()) {
        setError(`${getFieldLabel(field)}을(를) 입력해주세요`);
        setLoading(false);
        return;
      }
    }

    // 이미 등록된 사원번호인지 확인
    if (employeeExists === true) {
      setError('이미 등록된 사원번호입니다');
      setLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/v1/simple-registration/worker', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '등록에 실패했습니다');
      }

      setSuccess(true);
      setFormData({
        name: '',
        employee_id: '',
        department: '',
        position: '',
        phone: '',
        email: '',
        birth_date: '',
        gender: '',
        employment_type: '정규직',
        work_type: 'construction',
        hire_date: '',
        company_name: ''
      });
      
    } catch (err) {
      setError(err instanceof Error ? err.message : '등록 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const getFieldLabel = (field: string): string => {
    const labels: Record<string, string> = {
      name: '이름',
      employee_id: '사원번호',
      department: '부서',
      phone: '연락처',
      birth_date: '생년월일',
      gender: '성별'
    };
    return labels[field] || field;
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
          <h1 className="text-2xl font-bold text-gray-900 mb-2">등록 완료!</h1>
          <p className="text-gray-600 mb-6">근로자 등록이 성공적으로 완료되었습니다.</p>
          <button
            onClick={() => setSuccess(false)}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700"
          >
            새로운 등록
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="text-center mb-6">
            <User className="h-12 w-12 text-blue-600 mx-auto mb-2" />
            <h1 className="text-2xl font-bold text-gray-900">근로자 등록</h1>
            <p className="text-gray-600">휴대폰으로 간단하게 등록하세요</p>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md flex items-center">
              <AlertCircle className="h-5 w-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 기본 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  이름 *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="홍길동"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  사원번호 *
                </label>
                <div className="flex">
                  <input
                    type="text"
                    name="employee_id"
                    value={formData.employee_id}
                    onChange={handleInputChange}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="EMP001"
                    required
                  />
                  <button
                    type="button"
                    onClick={checkEmployeeId}
                    disabled={checkingEmployee || !formData.employee_id}
                    className="px-4 py-2 bg-gray-600 text-white rounded-r-md hover:bg-gray-700 disabled:bg-gray-300"
                  >
                    {checkingEmployee ? '확인중...' : '중복확인'}
                  </button>
                </div>
                {employeeExists === false && (
                  <p className="text-sm text-green-600 mt-1">사용 가능한 사원번호입니다</p>
                )}
              </div>
            </div>

            {/* 회사/부서 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  회사명
                </label>
                <input
                  type="text"
                  name="company_name"
                  value={formData.company_name}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="회사명"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  부서 *
                </label>
                <input
                  type="text"
                  name="department"
                  value={formData.department}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="건설부"
                  required
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  직책
                </label>
                <input
                  type="text"
                  name="position"
                  value={formData.position}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="현장관리자"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  고용형태
                </label>
                <select
                  name="employment_type"
                  value={formData.employment_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="정규직">정규직</option>
                  <option value="계약직">계약직</option>
                  <option value="임시직">임시직</option>
                  <option value="일용직">일용직</option>
                </select>
              </div>
            </div>

            {/* 연락처 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <Phone className="h-4 w-4 inline mr-1" />
                  연락처 *
                </label>
                <input
                  type="tel"
                  name="phone"
                  value={formData.phone}
                  onChange={handleInputChange}
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
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="example@company.com"
                />
              </div>
            </div>

            {/* 개인정보 */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  생년월일 *
                </label>
                <input
                  type="date"
                  name="birth_date"
                  value={formData.birth_date}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  성별 *
                </label>
                <select
                  name="gender"
                  value={formData.gender}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                >
                  <option value="">선택</option>
                  <option value="남성">남성</option>
                  <option value="여성">여성</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  입사일
                </label>
                <input
                  type="date"
                  name="hire_date"
                  value={formData.hire_date}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || employeeExists === true}
              className="w-full bg-blue-600 text-white py-3 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-300 font-medium"
            >
              {loading ? '등록 중...' : '등록하기'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SimpleWorkerRegistration;