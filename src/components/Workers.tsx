import React, { useState, useEffect } from 'react';
import { API_CONFIG } from '../config/api';
import { WorkerFeedback } from './WorkerFeedback';

interface Worker {
  id: number;
  employee_id: string;
  name: string;
  birth_date: string;
  gender: string;
  phone: string;
  email: string;
  address: string;
  company_name: string;
  work_category: string;
  employment_type: string;
  work_type: string;
  hire_date: string;
  department: string;
  position: string;
  health_status: string;
  blood_type: string;
  emergency_contact: string;
  emergency_relationship: string;
  safety_education_cert?: string;
  visa_type?: string;
  visa_cert?: string;
  is_active: boolean;
}

export const Workers: React.FC = () => {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [selectedWorker, setSelectedWorker] = useState<Worker | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    employee_id: '',
    name: '',
    birth_date: '',
    gender: 'male',
    phone: '',
    email: '',
    address: '',
    company_name: '',
    work_category: '',
    employment_type: 'regular',
    work_type: 'construction',
    hire_date: '',
    department: '',
    position: '',
    health_status: 'normal',
    blood_type: '',
    emergency_contact: '',
    emergency_relationship: '',
    safety_education_cert: null as File | null,
    visa_type: '',
    visa_cert: null as File | null,
  });

  // 근로자 목록 조회
  const fetchWorkers = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/workers/`);
      if (response.ok) {
        const data = await response.json();
        setWorkers(data);
      }
    } catch (error) {
      console.error('근로자 목록 조회 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkers();
  }, []);

  // 근로자 등록/수정
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const submitData = new FormData();
    Object.entries(formData).forEach(([key, value]) => {
      if (value !== null && value !== undefined && !(value instanceof File)) {
        submitData.append(key, value.toString());
      }
    });
    
    // 파일 첨부
    if (formData.safety_education_cert) {
      submitData.append('safety_education_cert', formData.safety_education_cert);
    }
    if (formData.visa_cert) {
      submitData.append('visa_cert', formData.visa_cert);
    }

    try {
      const url = selectedWorker 
        ? `${API_CONFIG.BASE_URL}/workers/${selectedWorker.id}`
        : `${API_CONFIG.BASE_URL}/workers/`;
      
      const response = await fetch(url, {
        method: selectedWorker ? 'PUT' : 'POST',
        body: submitData,
      });
      
      if (response.ok) {
        alert(selectedWorker ? '근로자 정보가 수정되었습니다.' : '근로자가 등록되었습니다.');
        setShowForm(false);
        setSelectedWorker(null);
        resetForm();
        fetchWorkers();
      } else {
        const error = await response.json();
        alert(`오류: ${error.detail || '처리 중 오류가 발생했습니다.'}`);
      }
    } catch (error) {
      console.error('근로자 저장 오류:', error);
      alert('근로자 저장 중 오류가 발생했습니다.');
    }
  };

  // 폼 초기화
  const resetForm = () => {
    setFormData({
      employee_id: '',
      name: '',
      birth_date: '',
      gender: 'male',
      phone: '',
      email: '',
      address: '',
      company_name: '',
      work_category: '',
      employment_type: 'regular',
      work_type: 'construction',
      hire_date: '',
      department: '',
      position: '',
      health_status: 'normal',
      blood_type: '',
      emergency_contact: '',
      emergency_relationship: '',
      safety_education_cert: null,
      visa_type: '',
      visa_cert: null,
    });
  };

  // 근로자 선택
  const handleSelectWorker = (worker: Worker) => {
    setSelectedWorker(worker);
    setShowFeedback(true);
  };

  // 근로자 편집
  const handleEditWorker = (worker: Worker) => {
    setSelectedWorker(worker);
    setFormData({
      ...worker,
      safety_education_cert: null,
      visa_cert: null,
    });
    setShowForm(true);
  };

  // 파일 변경 처리
  const handleFileChange = (field: 'safety_education_cert' | 'visa_cert') => (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFormData({ ...formData, [field]: e.target.files[0] });
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-900">근로자 관리</h1>
        <button
          onClick={() => {
            setShowForm(true);
            setSelectedWorker(null);
            resetForm();
          }}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          근로자 등록
        </button>
      </div>

      {/* 근로자 등록/수정 폼 */}
      {showForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <h2 className="text-xl font-bold mb-4">
              {selectedWorker ? '근로자 정보 수정' : '신규 근로자 등록'}
            </h2>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                {/* 기본 정보 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    사번 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.employee_id}
                    onChange={(e) => setFormData({ ...formData, employee_id: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    성명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">생년월일</label>
                  <input
                    type="date"
                    value={formData.birth_date}
                    onChange={(e) => setFormData({ ...formData, birth_date: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">성별</label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="male">남성</option>
                    <option value="female">여성</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">연락처</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">이메일</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    거주지 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.address}
                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                {/* 업체 정보 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    업체명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    공종 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.work_category}
                    onChange={(e) => setFormData({ ...formData, work_category: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    부서(장비/작업) <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    value={formData.department}
                    onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">직급</label>
                  <input
                    type="text"
                    value={formData.position}
                    onChange={(e) => setFormData({ ...formData, position: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* 고용 정보 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    고용형태 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.employment_type}
                    onChange={(e) => setFormData({ ...formData, employment_type: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="regular">정규직</option>
                    <option value="contract">계약직</option>
                    <option value="temporary">임시직</option>
                    <option value="daily">일용직</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">
                    작업분류 <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={formData.work_type}
                    onChange={(e) => setFormData({ ...formData, work_type: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    required
                  >
                    <option value="construction">건설</option>
                    <option value="electrical">전기</option>
                    <option value="plumbing">배관</option>
                    <option value="painting">도장</option>
                    <option value="welding">용접</option>
                    <option value="demolition">해체</option>
                    <option value="earth_work">토공</option>
                    <option value="concrete">콘크리트</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">입사일</label>
                  <input
                    type="date"
                    value={formData.hire_date}
                    onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                {/* 건강 정보 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700">건강상태</label>
                  <select
                    value={formData.health_status}
                    onChange={(e) => setFormData({ ...formData, health_status: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="normal">정상</option>
                    <option value="caution">주의</option>
                    <option value="observation">관찰</option>
                    <option value="treatment">치료</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">혈액형</label>
                  <input
                    type="text"
                    value={formData.blood_type}
                    onChange={(e) => setFormData({ ...formData, blood_type: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="예: A+"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">비상연락처</label>
                  <input
                    type="tel"
                    value={formData.emergency_contact}
                    onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">비상연락 관계</label>
                  <input
                    type="text"
                    value={formData.emergency_relationship}
                    onChange={(e) => setFormData({ ...formData, emergency_relationship: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="예: 배우자, 부모, 자녀 등"
                  />
                </div>

                {/* 자격증 정보 */}
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700">
                    건설업 기초안전보건교육 이수증
                  </label>
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={handleFileChange('safety_education_cert')}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">비자종류</label>
                  <input
                    type="text"
                    value={formData.visa_type}
                    onChange={(e) => setFormData({ ...formData, visa_type: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="예: E-9, F-4 등"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700">비자관련 자격증</label>
                  <input
                    type="file"
                    accept="image/*,.pdf"
                    onChange={handleFileChange('visa_cert')}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-6">
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setSelectedWorker(null);
                    resetForm();
                  }}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  {selectedWorker ? '수정' : '등록'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 근로자 목록 */}
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                사번
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                성명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                업체명
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                공종
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                부서
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                건강상태
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                재직여부
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                작업
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {loading ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  로딩 중...
                </td>
              </tr>
            ) : workers.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                  등록된 근로자가 없습니다.
                </td>
              </tr>
            ) : (
              workers.map((worker) => (
                <tr key={worker.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {worker.employee_id}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {worker.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {worker.company_name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {worker.work_category}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {worker.department}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      worker.health_status === 'normal' ? 'bg-green-100 text-green-800' :
                      worker.health_status === 'caution' ? 'bg-yellow-100 text-yellow-800' :
                      worker.health_status === 'observation' ? 'bg-orange-100 text-orange-800' :
                      'bg-red-100 text-red-800'
                    }`}>
                      {worker.health_status === 'normal' ? '정상' :
                       worker.health_status === 'caution' ? '주의' :
                       worker.health_status === 'observation' ? '관찰' : '치료'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                      worker.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {worker.is_active ? '재직' : '퇴직'}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button
                      onClick={() => handleEditWorker(worker)}
                      className="text-indigo-600 hover:text-indigo-900 mr-2"
                    >
                      수정
                    </button>
                    <button
                      onClick={() => handleSelectWorker(worker)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      피드백
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* 피드백 섹션 */}
      {showFeedback && selectedWorker && (
        <WorkerFeedback 
          workerId={selectedWorker.id} 
          workerName={selectedWorker.name}
        />
      )}
    </div>
  );
};