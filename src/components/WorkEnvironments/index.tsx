import React, { useState, useEffect } from 'react';
import { Plus, Search, TrendingUp, AlertTriangle, Activity, X } from 'lucide-react';
import { Card, Button, Badge, Modal } from '../common';
import { useApi } from '../../hooks/useApi';

interface WorkEnvironment {
  id: number;
  location: string;
  measurement_type: string;
  measurement_date: string;
  measured_value: number;
  standard_value: number;
  unit: string;
  status: 'normal' | 'warning' | 'danger';
  notes?: string;
}

export function WorkEnvironments() {
  const [measurements, setMeasurements] = useState<WorkEnvironment[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    location: '',
    measurement_type: 'noise',
    measurement_date: new Date().toISOString().split('T')[0],
    measured_value: '',
    standard_value: '',
    unit: 'dB',
    notes: ''
  });
  const { fetchApi } = useApi();

  useEffect(() => {
    loadMeasurements();
  }, []);

  const loadMeasurements = async () => {
    try {
      setLoading(true);
      const data = await fetchApi('/work-environments');
      setMeasurements(data);
    } catch (error) {
      console.error('작업환경측정 목록 조회 실패:', error);
      // API 실패 시 더미 데이터로 폴백
      const dummyData = [
        {
          id: 1,
          location: "작업장 A동",
          measurement_type: "소음",
          measurement_date: "2024-06-20",
          measured_value: 82,
          standard_value: 90,
          unit: "dB",
          status: 'normal' as const,
          notes: "정상 범위"
        },
        {
          id: 2,
          location: "작업장 B동",
          measurement_type: "분진",
          measurement_date: "2024-06-19",
          measured_value: 8.5,
          standard_value: 10,
          unit: "mg/m³",
          status: 'warning' as const,
          notes: "주의 필요"
        },
        {
          id: 3,
          location: "화학물질 저장소",
          measurement_type: "유기용제",
          measurement_date: "2024-06-18",
          measured_value: 15,
          standard_value: 10,
          unit: "ppm",
          status: 'danger' as const,
          notes: "기준치 초과"
        }
      ];
      setMeasurements(dummyData);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'normal':
        return <Badge className="bg-green-100 text-green-800">정상</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800">주의</Badge>;
      case 'danger':
        return <Badge className="bg-red-100 text-red-800">위험</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">미확인</Badge>;
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const measuredValue = parseFloat(formData.measured_value);
      const standardValue = parseFloat(formData.standard_value);
      
      // 상태 계산
      let status: 'normal' | 'warning' | 'danger' = 'normal';
      if (measuredValue > standardValue * 1.2) {
        status = 'danger';
      } else if (measuredValue > standardValue * 0.9) {
        status = 'warning';
      }
      
      const newMeasurement = {
        ...formData,
        measured_value: measuredValue,
        standard_value: standardValue,
        status
      };
      
      await fetchApi('/work-environments', {
        method: 'POST',
        body: JSON.stringify(newMeasurement)
      });
      
      setShowForm(false);
      setFormData({
        location: '',
        measurement_type: 'noise',
        measurement_date: new Date().toISOString().split('T')[0],
        measured_value: '',
        standard_value: '',
        unit: 'dB',
        notes: ''
      });
      loadMeasurements();
    } catch (error) {
      console.error('측정 결과 등록 실패:', error);
      alert('측정 결과 등록에 실패했습니다.');
    }
  };

  const getMeasurementTypeOptions = () => [
    { value: 'noise', label: '소음', unit: 'dB', standard: '90' },
    { value: 'dust', label: '분진', unit: 'mg/m³', standard: '10' },
    { value: 'chemical', label: '화학물질', unit: 'ppm', standard: '50' },
    { value: 'temperature', label: '온도', unit: '°C', standard: '28' },
    { value: 'humidity', label: '습도', unit: '%', standard: '60' },
    { value: 'illumination', label: '조도', unit: 'lux', standard: '300' },
    { value: 'vibration', label: '진동', unit: 'm/s²', standard: '5' }
  ];

  const handleMeasurementTypeChange = (type: string) => {
    const selected = getMeasurementTypeOptions().find(opt => opt.value === type);
    if (selected) {
      setFormData({
        ...formData,
        measurement_type: type,
        unit: selected.unit,
        standard_value: selected.standard
      });
    }
  };

  const filteredMeasurements = measurements.filter(measurement =>
    measurement.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
    measurement.measurement_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const normalCount = measurements.filter(m => m.status === 'normal').length;
  const warningCount = measurements.filter(m => m.status === 'warning').length;
  const dangerCount = measurements.filter(m => m.status === 'danger').length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">작업환경측정 관리</h1>
        <Button onClick={() => setShowForm(true)} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          측정 결과 등록
        </Button>
      </div>

      {/* 검색 */}
      <Card>
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="작업장소 또는 측정항목으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <Button variant="outline" onClick={loadMeasurements}>
            새로고침
          </Button>
        </div>
      </Card>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 측정</p>
              <p className="text-2xl font-bold text-gray-900">{measurements.length}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <div className="w-4 h-4 bg-green-600 rounded-full"></div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">정상</p>
              <p className="text-2xl font-bold text-green-600">{normalCount}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">주의</p>
              <p className="text-2xl font-bold text-yellow-600">{warningCount}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">위험</p>
              <p className="text-2xl font-bold text-red-600">{dangerCount}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* 측정 결과 목록 */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  작업장소
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  측정항목
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  측정일자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  측정값
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  기준값
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  비고
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    로딩 중...
                  </td>
                </tr>
              ) : filteredMeasurements.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    측정 결과가 없습니다.
                  </td>
                </tr>
              ) : (
                filteredMeasurements.map((measurement) => (
                  <tr key={measurement.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {measurement.location}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {measurement.measurement_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {measurement.measurement_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {measurement.measured_value} {measurement.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {measurement.standard_value} {measurement.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(measurement.status)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {measurement.notes || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 측정 결과 등록 모달 */}
      <Modal isOpen={showForm} onClose={() => setShowForm(false)}>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">측정 결과 등록</h3>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              작업장소
            </label>
            <input
              type="text"
              required
              value={formData.location}
              onChange={(e) => setFormData({ ...formData, location: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              측정항목
            </label>
            <select
              value={formData.measurement_type}
              onChange={(e) => handleMeasurementTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {getMeasurementTypeOptions().map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              측정일자
            </label>
            <input
              type="date"
              required
              value={formData.measurement_date}
              onChange={(e) => setFormData({ ...formData, measurement_date: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                측정값 ({formData.unit})
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.measured_value}
                onChange={(e) => setFormData({ ...formData, measured_value: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                기준값 ({formData.unit})
              </label>
              <input
                type="number"
                step="0.01"
                required
                value={formData.standard_value}
                onChange={(e) => setFormData({ ...formData, standard_value: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button type="button" variant="outline" onClick={() => setShowForm(false)}>
              취소
            </Button>
            <Button type="submit">
              등록
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}