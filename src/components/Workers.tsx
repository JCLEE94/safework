import React, { useState, useEffect } from 'react';
import { Plus, Search, Edit2, Trash2, FileText, Upload, X } from 'lucide-react';
import { API_BASE_URL } from '../config';

interface Worker {
  id: number;
  name: string;
  employee_id: string;
  gender?: string;
  company_name: string;
  work_category: string;
  department: string;
  position?: string;
  employment_type?: string;
  work_type?: string;
  hire_date?: string;
  birth_date?: string;
  phone?: string;
  emergency_contact?: string;
  emergency_relationship?: string;
  address: string;
  health_status?: string;
  safety_education_cert?: string;
  visa_type?: string;
  visa_cert?: string;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export function Workers() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingWorker, setEditingWorker] = useState<Worker | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    employee_id: '',
    gender: '',
    company_name: '',
    work_category: '',
    department: '작업',
    position: '',
    employment_type: 'regular',
    work_type: 'construction',
    hire_date: '',
    birth_date: '',
    phone: '',
    emergency_contact: '',
    emergency_relationship: '',
    address: '',
    health_status: 'normal',
    visa_type: '',
    visa_cert: '',
  });
  const [safetyEduFile, setSafetyEduFile] = useState<File | null>(null);
  const [visaCertFile, setVisaCertFile] = useState<File | null>(null);

  useEffect(() => {
    fetchWorkers();
  }, []);

  const fetchWorkers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/workers/`);
      if (response.ok) {
        const data = await response.json();
        setWorkers(data);
      }
    } catch (error) {
      console.error('근로자 데이터 로드 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const url = editingWorker 
        ? `${API_BASE_URL}/workers/${editingWorker.id}`
        : `${API_BASE_URL}/workers/`;
      
      const method = editingWorker ? 'PUT' : 'POST';
      
      // 파일 업로드 처리 (실제 구현시 파일 업로드 API 필요)
      let safetyEducationCert = '';
      let visaCert = '';
      
      if (safetyEduFile) {
        // TODO: 파일 업로드 API 호출
        safetyEducationCert = 'uploaded_file_path';
      }
      
      if (visaCertFile) {
        // TODO: 파일 업로드 API 호출
        visaCert = 'uploaded_file_path';
      }
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          safety_education_cert: safetyEducationCert,
          visa_cert: visaCert,
        }),
      });

      if (response.ok) {
        fetchWorkers();
        resetForm();
      }
    } catch (error) {
      console.error('근로자 저장 실패:', error);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    try {
      const response = await fetch(`${API_BASE_URL}/workers/${id}`, {
        method: 'DELETE',
      });
      
      if (response.ok) {
        fetchWorkers();
      }
    } catch (error) {
      console.error('근로자 삭제 실패:', error);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      employee_id: '',
      gender: '',
      company_name: '',
      work_category: '',
      department: '작업',
      position: '',
      employment_type: 'regular',
      work_type: 'construction',
      hire_date: '',
      birth_date: '',
      phone: '',
      emergency_contact: '',
      emergency_relationship: '',
      address: '',
      health_status: 'normal',
      visa_type: '',
      visa_cert: '',
    });
    setSafetyEduFile(null);
    setVisaCertFile(null);
    setShowAddForm(false);
    setEditingWorker(null);
  };

  const handleEdit = (worker: Worker) => {
    setEditingWorker(worker);
    setFormData({
      name: worker.name,
      employee_id: worker.employee_id,
      gender: worker.gender || '',
      company_name: worker.company_name,
      work_category: worker.work_category,
      department: worker.department,
      position: worker.position || '',
      employment_type: worker.employment_type || 'regular',
      work_type: worker.work_type || 'construction',
      hire_date: worker.hire_date || '',
      birth_date: worker.birth_date || '',
      phone: worker.phone || '',
      emergency_contact: worker.emergency_contact || '',
      emergency_relationship: worker.emergency_relationship || '',
      address: worker.address,
      health_status: worker.health_status || 'normal',
      visa_type: worker.visa_type || '',
      visa_cert: worker.visa_cert || '',
    });
    setShowAddForm(true);
  };

  const filteredWorkers = workers.filter(worker =>
    worker.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    worker.employee_id.includes(searchTerm) ||
    worker.company_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="flex justify-center items-center h-64">로딩 중...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">근로자 관리</h1>
        <button
          onClick={() => setShowAddForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 flex items-center gap-2"
        >
          <Plus className="h-5 w-5" />
          근로자 등록
        </button>
      </div>

      <div className="bg-white rounded-lg shadow p-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="이름, 사번, 업체명으로 검색"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
      </div>

      {showAddForm && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">
                {editingWorker ? '근로자 정보 수정' : '근로자 등록'}
              </h2>
              <button onClick={resetForm} className="text-gray-500 hover:text-gray-700">
                <X className="h-6 w-6" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    이름 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    사번 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.employee_id}
                    onChange={(e) => setFormData({...formData, employee_id: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">성별</label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({...formData, gender: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="">선택</option>
                    <option value="male">남성</option>
                    <option value="female">여성</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    업체명 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.company_name}
                    onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    공종 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.work_category}
                    onChange={(e) => setFormData({...formData, work_category: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    부서 <span className="text-red-500">*</span>
                  </label>
                  <select
                    required
                    value={formData.department}
                    onChange={(e) => setFormData({...formData, department: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="장비">장비</option>
                    <option value="작업">작업</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">생년월일</label>
                  <input
                    type="date"
                    value={formData.birth_date}
                    onChange={(e) => setFormData({...formData, birth_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">입사일</label>
                  <input
                    type="date"
                    value={formData.hire_date}
                    onChange={(e) => setFormData({...formData, hire_date: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">연락처</label>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">비상연락처</label>
                  <input
                    type="tel"
                    value={formData.emergency_contact}
                    onChange={(e) => setFormData({...formData, emergency_contact: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">비상연락 관계</label>
                  <input
                    type="text"
                    placeholder="예: 배우자, 부모, 자녀"
                    value={formData.emergency_relationship}
                    onChange={(e) => setFormData({...formData, emergency_relationship: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    거주지 <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="col-span-3">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    건설업 기초안전보건교육 이수증
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="file"
                      accept="image/*,.pdf"
                      onChange={(e) => setSafetyEduFile(e.target.files?.[0] || null)}
                      className="flex-1"
                    />
                    {safetyEduFile && (
                      <span className="text-sm text-gray-600">{safetyEduFile.name}</span>
                    )}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">비자종류</label>
                  <input
                    type="text"
                    value={formData.visa_type}
                    onChange={(e) => setFormData({...formData, visa_type: e.target.value})}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    비자관련 자격증
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="file"
                      accept="image/*,.pdf"
                      onChange={(e) => setVisaCertFile(e.target.files?.[0] || null)}
                      className="flex-1"
                    />
                    {visaCertFile && (
                      <span className="text-sm text-gray-600">{visaCertFile.name}</span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  {editingWorker ? '수정' : '등록'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                이름
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                사번
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
                연락처
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                상태
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                관리
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredWorkers.map((worker) => (
              <tr key={worker.id} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {worker.name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {worker.employee_id}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {worker.company_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {worker.work_category}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {worker.department}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {worker.phone}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                    worker.is_active 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {worker.is_active ? '재직' : '퇴직'}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleEdit(worker)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      <Edit2 className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(worker.id)}
                      className="text-red-600 hover:text-red-900"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}