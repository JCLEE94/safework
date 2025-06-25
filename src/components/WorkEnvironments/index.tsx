import React, { useState, useEffect } from 'react';
import { Plus, Search, TrendingUp, AlertTriangle, Activity } from 'lucide-react';
import { Card, Button, Badge } from '../common';
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
  const { fetchApi } = useApi();

  useEffect(() => {
    loadMeasurements();
  }, []);

  const loadMeasurements = async () => {
    try {
      setLoading(true);
      // 임시 더미 데이터
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
    } catch (error) {
      console.error('작업환경측정 목록 조회 실패:', error);
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
        <Button onClick={() => {}} className="flex items-center gap-2">
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
    </div>
  );
}