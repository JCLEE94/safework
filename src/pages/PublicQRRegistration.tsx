import React, { useState } from 'react';

export const PublicQRRegistration: React.FC = () => {
  const [formData, setFormData] = useState({
    name: '',
    employee_id: '',
    birth_date: '',
    gender: '',
    phone: '',
    department: '',
    position: '',
    employment_type: '정규직',
    work_type: '일반작업',
    hire_date: '',
    emergency_contact: '',
    address: ''
  });

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError('');

    try {
      const response = await fetch('/api/v1/workers/public-registration', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error('등록에 실패했습니다.');
      }

      setSuccess(true);
      setTimeout(() => {
        window.location.href = '/';
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : '등록 중 오류가 발생했습니다.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-400 to-blue-500 flex items-center justify-center p-4">
        <div className="bg-white rounded-3xl shadow-2xl p-8 max-w-sm w-full text-center transform transition-all duration-500 scale-105">
          <div className="mb-6">
            <div className="w-20 h-20 bg-green-100 rounded-full mx-auto flex items-center justify-center">
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-800 mb-3">등록 완료!</h2>
          <p className="text-gray-600 mb-6">SafeWork Pro 시스템에<br />성공적으로 등록되었습니다.</p>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-blue-500 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
          </div>
          <p className="text-xs text-gray-500 mt-3">3초 후 메인 페이지로 이동합니다</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-400 via-blue-500 to-indigo-600">
      {/* 상단 헤더 */}
      <div className="bg-white/10 backdrop-blur-sm">
        <div className="px-6 py-4">
          <div className="flex items-center justify-center">
            <div className="bg-white/20 p-3 rounded-2xl">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-3 text-white">
              <h1 className="text-xl font-bold">SafeWork Pro</h1>
              <p className="text-xs opacity-90">건설현장 안전관리 시스템</p>
            </div>
          </div>
        </div>
      </div>

      {/* 메인 폼 */}
      <div className="px-4 py-6 pb-20">
        <div className="max-w-md mx-auto">
          {/* 안내 카드 */}
          <div className="bg-white/90 backdrop-blur-md rounded-3xl shadow-xl p-6 mb-6">
            <div className="flex items-center mb-4">
              <div className="bg-blue-100 p-2 rounded-xl">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h2 className="text-lg font-bold text-gray-800 ml-3">근로자 등록</h2>
            </div>
            <p className="text-sm text-gray-600">
              안전한 작업환경을 위해 정확한 정보를 입력해주세요.
            </p>
          </div>

          {/* 폼 */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* 기본 정보 섹션 */}
            <div className="bg-white rounded-2xl shadow-lg p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                <span className="bg-blue-100 w-6 h-6 rounded-full text-xs flex items-center justify-center text-blue-600 mr-2">1</span>
                기본 정보
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    이름 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                    placeholder="홍길동"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      생년월일 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      name="birth_date"
                      value={formData.birth_date}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      성별 <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="gender"
                      value={formData.gender}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                    >
                      <option value="">선택</option>
                      <option value="남성">남성</option>
                      <option value="여성">여성</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    연락처 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="tel"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    required
                    placeholder="010-0000-0000"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    비상연락처
                  </label>
                  <input
                    type="tel"
                    name="emergency_contact"
                    value={formData.emergency_contact}
                    onChange={handleChange}
                    placeholder="010-0000-0000"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                  />
                </div>
              </div>
            </div>

            {/* 근무 정보 섹션 */}
            <div className="bg-white rounded-2xl shadow-lg p-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-4 flex items-center">
                <span className="bg-blue-100 w-6 h-6 rounded-full text-xs flex items-center justify-center text-blue-600 mr-2">2</span>
                근무 정보
              </h3>
              
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      사번
                    </label>
                    <input
                      type="text"
                      name="employee_id"
                      value={formData.employee_id}
                      onChange={handleChange}
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                      placeholder="선택사항"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      부서 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      name="department"
                      value={formData.department}
                      onChange={handleChange}
                      required
                      placeholder="건설팀"
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    직급/직책 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    name="position"
                    value={formData.position}
                    onChange={handleChange}
                    required
                    placeholder="예: 기술자, 반장"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      고용형태 <span className="text-red-500">*</span>
                    </label>
                    <select
                      name="employment_type"
                      value={formData.employment_type}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                    >
                      <option value="정규직">정규직</option>
                      <option value="계약직">계약직</option>
                      <option value="일용직">일용직</option>
                      <option value="파견직">파견직</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">
                      입사일 <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="date"
                      name="hire_date"
                      value={formData.hire_date}
                      onChange={handleChange}
                      required
                      className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-sm"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-600 mb-1">
                    주소
                  </label>
                  <input
                    type="text"
                    name="address"
                    value={formData.address}
                    onChange={handleChange}
                    placeholder="거주지 주소 (선택사항)"
                    className="w-full px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all"
                  />
                </div>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start">
                <svg className="w-5 h-5 text-red-500 mr-2 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}

            {/* 제출 버튼 */}
            <button
              type="submit"
              disabled={isSubmitting}
              className={`w-full py-4 rounded-2xl font-medium text-white shadow-lg transition-all transform ${
                isSubmitting
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]'
              }`}
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                  </svg>
                  등록 중...
                </span>
              ) : (
                '등록하기'
              )}
            </button>

            {/* 안내 문구 */}
            <p className="text-center text-xs text-white/80 mt-4">
              등록 정보는 안전하게 보호됩니다
            </p>
          </form>
        </div>
      </div>
    </div>
  );
};