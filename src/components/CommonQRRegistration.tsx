import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './common/Button';
import { Card } from './common/Card';
import { Input } from './common/Input';
import { Select } from './common/Select';

interface WorkerFormData {
  name: string;
  employee_id: string;
  birth_date: string;
  gender: string;
  phone: string;
  email: string;
  department: string;
  position: string;
  employment_type: string;
  work_type: string;
  join_date: string;
  address: string;
  emergency_contact: string;
  emergency_phone: string;
}

const DEPARTMENTS = [
  '관리부', '건설부', '토목부', '전기부', '기계부', 
  '안전관리부', '품질관리부', '공무부', '기타'
];

const POSITIONS = [
  '사원', '주임', '대리', '과장', '차장', '부장', '이사', '기타'
];

const EMPLOYMENT_TYPES = [
  '정규직', '계약직', '일용직', '파견직', '기타'
];

const WORK_TYPES = [
  '사무직', '현장직', '기술직', '관리직', '기타'
];

export function CommonQRRegistration() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [checkingEmployeeId, setCheckingEmployeeId] = useState(false);
  const [employeeIdAvailable, setEmployeeIdAvailable] = useState<boolean | null>(null);
  
  const [formData, setFormData] = useState<WorkerFormData>({
    name: '',
    employee_id: '',
    birth_date: '',
    gender: '남',
    phone: '',
    email: '',
    department: '',
    position: '사원',
    employment_type: '정규직',
    work_type: '현장직',
    join_date: new Date().toISOString().split('T')[0],
    address: '',
    emergency_contact: '',
    emergency_phone: '',
  });

  // 사번 중복 확인
  const checkEmployeeId = async (employeeId: string) => {
    if (!employeeId || employeeId.length < 3) return;
    
    setCheckingEmployeeId(true);
    try {
      const response = await fetch(`/api/v1/common-qr/check/${employeeId}`);
      const data = await response.json();
      setEmployeeIdAvailable(data.available);
    } catch (err) {
      console.error('사번 확인 오류:', err);
      setEmployeeIdAvailable(null);
    } finally {
      setCheckingEmployeeId(false);
    }
  };

  // 사번 입력 시 자동 확인
  useEffect(() => {
    const timer = setTimeout(() => {
      if (formData.employee_id) {
        checkEmployeeId(formData.employee_id);
      }
    }, 500);
    
    return () => clearTimeout(timer);
  }, [formData.employee_id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch('/api/v1/common-qr/register', {
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
      setTimeout(() => {
        navigate('/registration-complete');
      }, 2000);
    } catch (err) {
      setError(err instanceof Error ? err.message : '등록 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (field: keyof WorkerFormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 p-4">
        <Card className="w-full max-w-md p-8 text-center">
          <div className="text-green-600 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">등록 완료!</h2>
          <p className="text-gray-600">근로자 등록이 성공적으로 완료되었습니다.</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        <Card className="p-6">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">근로자 등록</h1>
            <p className="text-gray-600 mt-2">QR 코드를 통한 간편 등록</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* 기본 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="이름"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                required
              />

              <div>
                <Input
                  label="사원번호"
                  value={formData.employee_id}
                  onChange={(e) => handleChange('employee_id', e.target.value)}
                  required
                />
                {checkingEmployeeId && (
                  <p className="text-sm text-gray-500 mt-1">확인 중...</p>
                )}
                {!checkingEmployeeId && employeeIdAvailable !== null && (
                  <p className={`text-sm mt-1 ${employeeIdAvailable ? 'text-green-600' : 'text-red-600'}`}>
                    {employeeIdAvailable ? '사용 가능한 사원번호입니다' : '이미 등록된 사원번호입니다'}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                type="date"
                label="생년월일"
                value={formData.birth_date}
                onChange={(e) => handleChange('birth_date', e.target.value)}
                required
              />

              <Select
                label="성별"
                value={formData.gender}
                onChange={(e) => handleChange('gender', e.target.value)}
                options={[
                  { value: '남', label: '남성' },
                  { value: '여', label: '여성' },
                ]}
              />
            </div>

            {/* 연락처 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                type="tel"
                label="연락처"
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                placeholder="010-0000-0000"
                required
              />

              <Input
                type="email"
                label="이메일"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                placeholder="email@example.com"
              />
            </div>

            {/* 소속 정보 */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="부서"
                value={formData.department}
                onChange={(e) => handleChange('department', e.target.value)}
                options={DEPARTMENTS.map(dept => ({ value: dept, label: dept }))}
                required
              />

              <Select
                label="직급"
                value={formData.position}
                onChange={(e) => handleChange('position', e.target.value)}
                options={POSITIONS.map(pos => ({ value: pos, label: pos }))}
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Select
                label="고용형태"
                value={formData.employment_type}
                onChange={(e) => handleChange('employment_type', e.target.value)}
                options={EMPLOYMENT_TYPES.map(type => ({ value: type, label: type }))}
              />

              <Select
                label="작업유형"
                value={formData.work_type}
                onChange={(e) => handleChange('work_type', e.target.value)}
                options={WORK_TYPES.map(type => ({ value: type, label: type }))}
              />
            </div>

            <Input
              type="date"
              label="입사일"
              value={formData.join_date}
              onChange={(e) => handleChange('join_date', e.target.value)}
              required
            />

            {/* 추가 정보 */}
            <Input
              label="주소"
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              placeholder="주소를 입력하세요"
            />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Input
                label="비상연락처 (이름)"
                value={formData.emergency_contact}
                onChange={(e) => handleChange('emergency_contact', e.target.value)}
                placeholder="비상연락처 성명"
              />

              <Input
                type="tel"
                label="비상연락처 (번호)"
                value={formData.emergency_phone}
                onChange={(e) => handleChange('emergency_phone', e.target.value)}
                placeholder="010-0000-0000"
              />
            </div>

            {error && (
              <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
                {error}
              </div>
            )}

            <div className="flex gap-4">
              <Button
                type="submit"
                disabled={loading || !employeeIdAvailable}
                className="flex-1"
              >
                {loading ? '등록 중...' : '등록하기'}
              </Button>

              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate('/')}
                className="flex-1"
              >
                취소
              </Button>
            </div>
          </form>
        </Card>
      </div>
    </div>
  );
}