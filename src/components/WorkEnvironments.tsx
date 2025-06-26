import React, { useState, useEffect } from 'react';

interface WorkEnvironment {
  id: number;
  location: string;
  measurement_type: string;
  measurement_date: string;
  measured_value: number;
  standard_value: number;
  result: string;
  re_measurement_required: string;
  created_by: string;
}

interface WorkEnvironmentForm {
  location: string;
  measurement_type: string;
  measurement_date: string;
  measured_value: number;
  standard_value: number;
  result: string;
  re_measurement_required: string;
  substance_name?: string;
  measurement_method?: string;
  notes?: string;
}

const MEASUREMENT_TYPES = [
  '소음', '분진', '화학물질', '온도', '습도', '조도', '환기', '유해광선'
];

const MEASUREMENT_RESULTS = [
  '적합', '부적합', '측정중'
];

export const WorkEnvironments: React.FC = () => {
  const [environments, setEnvironments] = useState<WorkEnvironment[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState<any>(null);
  const [formData, setFormData] = useState<WorkEnvironmentForm>({
    location: '',
    measurement_type: '소음',
    measurement_date: new Date().toISOString().split('T')[0],
    measured_value: 0,
    standard_value: 0,
    result: '측정중',
    re_measurement_required: 'N',
    substance_name: '',
    measurement_method: '',
    notes: ''
  });

  useEffect(() => {
    fetchEnvironments();
    fetchStatistics();
  }, []);

  const fetchEnvironments = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/work-environments/');
      if (response.ok) {
        const data = await response.json();
        setEnvironments(data.items || []);
      }
    } catch (error) {
      console.error('작업환경측정 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/v1/work-environments/statistics');
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('통계 조회 실패:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await fetch('/api/v1/work-environments/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setShowForm(false);
        setFormData({
          location: '',
          measurement_type: '소음',
          measurement_date: new Date().toISOString().split('T')[0],
          measured_value: 0,
          standard_value: 0,
          result: '측정중',
          re_measurement_required: 'N',
          substance_name: '',
          measurement_method: '',
          notes: ''
        });
        fetchEnvironments();
        fetchStatistics();
        alert('작업환경측정이 등록되었습니다.');
      } else {
        const error = await response.json();
        alert('등록 실패: ' + (error.detail || '알 수 없는 오류'));
      }
    } catch (error) {
      console.error('등록 실패:', error);
      alert('네트워크 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getResultColor = (result: string) => {
    switch (result) {
      case '적합': return 'text-green-600 bg-green-100';
      case '부적합': return 'text-red-600 bg-red-100';
      case '측정중': return 'text-yellow-600 bg-yellow-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">작업환경측정</h1>
          <p className="text-gray-600">Construction Work Environment Monitoring</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 측정 등록
        </button>
      </div>

      {/* 통계 카드 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">총 측정 횟수</h3>
            <p className="text-2xl font-bold text-gray-900">{statistics.total_measurements}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">적합</h3>
            <p className="text-2xl font-bold text-green-600">{statistics.pass_count}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">부적합</h3>
            <p className="text-2xl font-bold text-red-600">{statistics.fail_count}</p>
          </div>
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-sm font-medium text-gray-500">재측정 필요</h3>
            <p className="text-2xl font-bold text-orange-600">{statistics.re_measurement_required}</p>
          </div>
        </div>
      )}

      {/* 측정 기록 목록 */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-medium text-gray-900">측정 기록</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">장소</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">측정항목</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">측정일</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">측정값</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">기준값</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">결과</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">재측정</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    로딩 중...
                  </td>
                </tr>
              ) : environments.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    등록된 측정 기록이 없습니다.
                  </td>
                </tr>
              ) : (
                environments.map((env) => (
                  <tr key={env.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">{env.location}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{env.measurement_type}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {new Date(env.measurement_date).toLocaleDateString('ko-KR')}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">{env.measured_value}</td>
                    <td className="px-6 py-4 text-sm text-gray-900">{env.standard_value}</td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getResultColor(env.result)}`}>
                        {env.result}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {env.re_measurement_required === 'Y' ? '필요' : '불필요'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 등록 폼 모달 */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-screen overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-gray-900">작업환경측정 등록</h2>
              <button
                onClick={() => setShowForm(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    측정 장소 *
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="예: A동 1층 작업장"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    측정 항목 *
                  </label>
                  <select
                    required
                    value={formData.measurement_type}
                    onChange={(e) => setFormData({ ...formData, measurement_type: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {MEASUREMENT_TYPES.map((type) => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    측정 일자 *
                  </label>
                  <input
                    type="date"
                    required
                    value={formData.measurement_date}
                    onChange={(e) => setFormData({ ...formData, measurement_date: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    측정값 *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.measured_value}
                    onChange={(e) => setFormData({ ...formData, measured_value: parseFloat(e.target.value) || 0 })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="측정된 값"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    기준값 *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={formData.standard_value}
                    onChange={(e) => setFormData({ ...formData, standard_value: parseFloat(e.target.value) || 0 })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="법적 기준값"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    측정 결과 *
                  </label>
                  <select
                    required
                    value={formData.result}
                    onChange={(e) => setFormData({ ...formData, result: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {MEASUREMENT_RESULTS.map((result) => (
                      <option key={result} value={result}>{result}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    물질명
                  </label>
                  <input
                    type="text"
                    value={formData.substance_name}
                    onChange={(e) => setFormData({ ...formData, substance_name: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="화학물질명 (화학물질 측정시)"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    측정 방법
                  </label>
                  <input
                    type="text"
                    value={formData.measurement_method}
                    onChange={(e) => setFormData({ ...formData, measurement_method: e.target.value })}
                    className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="측정 방법 또는 장비"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  재측정 필요
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="re_measurement_required"
                      value="N"
                      checked={formData.re_measurement_required === 'N'}
                      onChange={(e) => setFormData({ ...formData, re_measurement_required: e.target.value })}
                      className="mr-2"
                    />
                    불필요
                  </label>
                  <label className="flex items-center">
                    <input
                      type="radio"
                      name="re_measurement_required"
                      value="Y"
                      checked={formData.re_measurement_required === 'Y'}
                      onChange={(e) => setFormData({ ...formData, re_measurement_required: e.target.value })}
                      className="mr-2"
                    />
                    필요
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  비고
                </label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                  className="w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="추가 설명 또는 특이사항"
                />
              </div>

              <div className="flex gap-2 pt-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {loading ? '등록 중...' : '등록'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
                >
                  취소
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};