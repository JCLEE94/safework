import React, { useState, useEffect } from 'react';
import { Plus, Search, AlertTriangle, FileText, Eye, Download, CheckCircle, Edit } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';
import { ChemicalForm } from './ChemicalForm';

interface ChemicalSubstance {
  id: number;
  name: string;
  cas_number: string;
  manufacturer: string;
  supplier: string;
  hazard_class: string;
  hazard_level: 'low' | 'medium' | 'high' | 'very_high';
  msds_available: boolean;
  msds_updated_date: string;
  storage_location: string;
  quantity: number;
  unit: string;
  last_inspection_date: string;
  expiry_date?: string;
  safety_measures: string[];
  responsible_person: string;
  notes?: string;
}

export function ChemicalSubstances() {
  const [substances, setSubstances] = useState<ChemicalSubstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterHazardLevel, setFilterHazardLevel] = useState<string>('all');
  const [filterMsdsStatus, setFilterMsdsStatus] = useState<string>('all');
  const [showForm, setShowForm] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedSubstance, setSelectedSubstance] = useState<ChemicalSubstance | null>(null);
  const { fetchApi } = useApi();

  useEffect(() => {
    loadSubstances();
  }, []);

  const loadSubstances = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterHazardLevel !== 'all') params.append('hazard_level', filterHazardLevel);
      if (filterMsdsStatus !== 'all') params.append('msds_status', filterMsdsStatus);
      
      const response = await fetchApi(`/chemicals?${params}`);
      if (response?.items) {
        setSubstances(response.items);
      } else if (Array.isArray(response)) {
        setSubstances(response);
      } else {
        setSubstances([]);
      }
    } catch (error) {
      console.error('화학물질 목록 조회 실패:', error);
      setSubstances([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setFormMode('create');
    setSelectedSubstance(null);
    setShowForm(true);
  };

  const handleEdit = (substance: ChemicalSubstance) => {
    setFormMode('edit');
    setSelectedSubstance(substance);
    setShowForm(true);
  };

  const handleSubmit = async (data: Partial<ChemicalSubstance>) => {
    try {
      if (formMode === 'create') {
        await fetchApi('/chemicals', {
          method: 'POST',
          body: JSON.stringify(data)
        });
        await loadSubstances(); // Refresh the list
      } else if (selectedSubstance) {
        await fetchApi(`/chemicals/${selectedSubstance.id}`, {
          method: 'PUT',
          body: JSON.stringify(data)
        });
        // Update the item in the list
        setSubstances(prev => prev.map(s => 
          s.id === selectedSubstance.id ? { ...s, ...data } : s
        ));
      }
      
      setShowForm(false);
    } catch (error) {
      console.error('화학물질 저장 실패:', error);
      alert('화학물질 저장에 실패했습니다.');
    }
  };

  const getHazardLevelBadge = (level: string) => {
    switch (level) {
      case 'low':
        return <Badge className="bg-green-100 text-green-800">낮음</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-100 text-yellow-800">보통</Badge>;
      case 'high':
        return <Badge className="bg-orange-100 text-orange-800">높음</Badge>;
      case 'very_high':
        return <Badge className="bg-red-100 text-red-800">매우 높음</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">미확인</Badge>;
    }
  };

  const getMsdsStatusBadge = (available: boolean, updatedDate: string) => {
    const isRecent = new Date(updatedDate) > new Date(Date.now() - 365 * 24 * 60 * 60 * 1000);
    
    if (available && isRecent) {
      return <Badge className="bg-green-100 text-green-800">최신</Badge>;
    } else if (available) {
      return <Badge className="bg-yellow-100 text-yellow-800">업데이트 필요</Badge>;
    } else {
      return <Badge className="bg-red-100 text-red-800">없음</Badge>;
    }
  };

  const filteredSubstances = substances.filter(substance => {
    const matchesSearch = substance.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         substance.cas_number.includes(searchTerm) ||
                         substance.manufacturer.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesHazardLevel = filterHazardLevel === 'all' || substance.hazard_level === filterHazardLevel;
    
    const matchesMsdsStatus = filterMsdsStatus === 'all' || 
                             (filterMsdsStatus === 'available' && substance.msds_available) ||
                             (filterMsdsStatus === 'missing' && !substance.msds_available);
    
    return matchesSearch && matchesHazardLevel && matchesMsdsStatus;
  });

  const totalSubstances = substances.length;
  const highRiskSubstances = substances.filter(s => s.hazard_level === 'high' || s.hazard_level === 'very_high').length;
  const missingMsds = substances.filter(s => !s.msds_available).length;
  const expiringSubstances = substances.filter(s => {
    if (!s.expiry_date) return false;
    const expiry = new Date(s.expiry_date);
    const threeMonthsFromNow = new Date(Date.now() + 90 * 24 * 60 * 60 * 1000);
    return expiry <= threeMonthsFromNow;
  }).length;

  const handleViewMsds = (substance: ChemicalSubstance) => {
    // MSDS 문서 보기 기능
    console.log('MSDS 보기:', substance.name);
  };

  const handleDownloadMsds = (substance: ChemicalSubstance) => {
    // MSDS 다운로드 기능
    console.log('MSDS 다운로드:', substance.name);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">화학물질 관리</h1>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          화학물질 등록
        </Button>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="화학물질명, CAS번호, 제조사로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={filterHazardLevel}
            onChange={(e) => setFilterHazardLevel(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">전체 위험도</option>
            <option value="low">낮음</option>
            <option value="medium">보통</option>
            <option value="high">높음</option>
            <option value="very_high">매우 높음</option>
          </select>
          <select
            value={filterMsdsStatus}
            onChange={(e) => setFilterMsdsStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">전체 MSDS</option>
            <option value="available">MSDS 있음</option>
            <option value="missing">MSDS 없음</option>
          </select>
          <Button variant="outline" onClick={loadSubstances}>
            새로고침
          </Button>
        </div>
      </Card>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 화학물질</p>
              <p className="text-2xl font-bold text-gray-900">{totalSubstances}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">고위험 물질</p>
              <p className="text-2xl font-bold text-red-600">{highRiskSubstances}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <FileText className="w-8 h-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">MSDS 누락</p>
              <p className="text-2xl font-bold text-orange-600">{missingMsds}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">유효기간 임박</p>
              <p className="text-2xl font-bold text-yellow-600">{expiringSubstances}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* 화학물질 목록 */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  화학물질정보
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  제조/공급사
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  위험등급
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  보관정보
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  MSDS
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  관리자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  관리
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
              ) : filteredSubstances.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-4 text-center text-gray-500">
                    화학물질이 없습니다.
                  </td>
                </tr>
              ) : (
                filteredSubstances.map((substance) => (
                  <tr key={substance.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{substance.name}</p>
                        <p className="text-sm text-gray-500">CAS: {substance.cas_number}</p>
                        <p className="text-xs text-gray-400">{substance.hazard_class}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm text-gray-900">{substance.manufacturer}</p>
                        <p className="text-sm text-gray-500">{substance.supplier}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getHazardLevelBadge(substance.hazard_level)}
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm text-gray-900">{substance.storage_location}</p>
                        <p className="text-sm text-gray-500">
                          {substance.quantity} {substance.unit}
                        </p>
                        {substance.expiry_date && (
                          <p className="text-xs text-gray-400">
                            만료: {substance.expiry_date}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="space-y-1">
                        {getMsdsStatusBadge(substance.msds_available, substance.msds_updated_date)}
                        <p className="text-xs text-gray-400">
                          업데이트: {substance.msds_updated_date}
                        </p>
                        {substance.msds_available && (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleViewMsds(substance)}
                              className="text-blue-600 hover:text-blue-800"
                              title="MSDS 보기"
                            >
                              <Eye className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => handleDownloadMsds(substance)}
                              className="text-green-600 hover:text-green-800"
                              title="MSDS 다운로드"
                            >
                              <Download className="w-3 h-3" />
                            </button>
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {substance.responsible_person}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(substance)}
                        >
                          <Edit size={14} />
                          편집
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 안전 정보 */}
      <Card>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-900 mb-1">화학물질 안전관리 준수사항</h4>
              <div className="text-sm text-red-700 space-y-1">
                <p>• MSDS(물질안전보건자료) 비치 및 정기 업데이트 필수</p>
                <p>• 화학물질별 적절한 보관 조건 및 안전조치 이행</p>
                <p>• 취급 근로자 대상 정기 안전교육 실시</p>
                <p>• 화학물질 취급일지 작성 및 관리</p>
                <p>• 유해화학물질 노출 모니터링 및 건강진단</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* 화학물질 등록/수정 폼 */}
      <ChemicalForm
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        initialData={selectedSubstance}
        mode={formMode}
      />
    </div>
  );
}