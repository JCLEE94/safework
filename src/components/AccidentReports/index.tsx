import React, { useState, useEffect } from 'react';
import { Plus, Search, AlertTriangle, FileText, Calendar, Users, TrendingUp, Clock, Edit, Eye } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';
import { AccidentForm } from './AccidentForm';

interface AccidentReport {
  id: number;
  report_number: string;
  incident_date: string;
  report_date: string;
  location: string;
  injured_person: string;
  department: string;
  accident_type: string;
  severity: 'minor' | 'moderate' | 'severe' | 'fatal';
  injury_type: string;
  description: string;
  immediate_cause: string;
  root_cause: string;
  corrective_actions: string[];
  preventive_measures: string[];
  reported_by: string;
  investigated_by: string;
  investigation_date: string;
  status: 'reported' | 'investigating' | 'action_required' | 'completed' | 'closed';
  follow_up_required: boolean;
  follow_up_date?: string;
  cost_estimate?: number;
  lost_work_days?: number;
  witnesses: string[];
  photos_attached: boolean;
  medical_treatment_required: boolean;
  government_notification_required: boolean;
  government_reported: boolean;
  notes?: string;
}

export function AccidentReports() {
  const [accidents, setAccidents] = useState<AccidentReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterDateRange, setFilterDateRange] = useState<string>('all');
  const [showForm, setShowForm] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedAccident, setSelectedAccident] = useState<AccidentReport | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const { fetchApi } = useApi();

  useEffect(() => {
    loadAccidents();
  }, []);

  const loadAccidents = async () => {
    try {
      setLoading(true);
      
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (filterSeverity !== 'all') params.append('severity', filterSeverity);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      
      const response = await fetchApi(`/accidents?${params}`);
      if (response?.items) {
        setAccidents(response.items);
      } else if (Array.isArray(response)) {
        setAccidents(response);
      } else {
        setAccidents([]);
      }
    } catch (error) {
      console.error('사고보고 목록 조회 실패:', error);
      setAccidents([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setFormMode('create');
    setSelectedAccident(null);
    setShowForm(true);
  };

  const handleEdit = (accident: AccidentReport) => {
    setFormMode('edit');
    setSelectedAccident(accident);
    setShowForm(true);
  };

  const handleDetail = (accident: AccidentReport) => {
    setSelectedAccident(accident);
    setShowDetailModal(true);
  };

  const handleSubmit = async (data: Partial<AccidentReport>) => {
    try {
      if (formMode === 'create') {
        await fetchApi('/accidents', {
          method: 'POST',
          body: JSON.stringify(data)
        });
        await loadAccidents(); // Refresh the list
      } else if (selectedAccident) {
        await fetchApi(`/accidents/${selectedAccident.id}`, {
          method: 'PUT',
          body: JSON.stringify(data)
        });
        // Update the item in the list
        setAccidents(prev => prev.map(a => 
          a.id === selectedAccident.id ? { ...a, ...data } : a
        ));
      }
      
      setShowForm(false);
    } catch (error) {
      console.error('사고 보고서 저장 실패:', error);
      alert('사고 보고서 저장에 실패했습니다.');
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'minor':
        return <Badge className="bg-green-100 text-green-800">경미</Badge>;
      case 'moderate':
        return <Badge className="bg-yellow-100 text-yellow-800">보통</Badge>;
      case 'severe':
        return <Badge className="bg-orange-100 text-orange-800">중상</Badge>;
      case 'fatal':
        return <Badge className="bg-red-100 text-red-800">사망</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">미확인</Badge>;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'reported':
        return <Badge className="bg-blue-100 text-blue-800">신고됨</Badge>;
      case 'investigating':
        return <Badge className="bg-yellow-100 text-yellow-800">조사중</Badge>;
      case 'action_required':
        return <Badge className="bg-orange-100 text-orange-800">조치필요</Badge>;
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">완료</Badge>;
      case 'closed':
        return <Badge className="bg-gray-100 text-gray-800">종료</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">미확인</Badge>;
    }
  };

  const filteredAccidents = accidents.filter(accident => {
    const matchesSearch = accident.injured_person.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         accident.location.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         accident.report_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         accident.accident_type.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesSeverity = filterSeverity === 'all' || accident.severity === filterSeverity;
    const matchesStatus = filterStatus === 'all' || accident.status === filterStatus;
    
    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const totalAccidents = accidents.length;
  const severeAccidents = accidents.filter(a => a.severity === 'severe' || a.severity === 'fatal').length;
  const pendingInvestigations = accidents.filter(a => a.status === 'investigating' || a.status === 'action_required').length;
  const totalLostDays = accidents.reduce((sum, a) => sum + (a.lost_work_days || 0), 0);

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">산업재해 관리</h1>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          사고 신고
        </Button>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="부상자명, 장소, 신고번호, 사고유형으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">전체 심각도</option>
            <option value="minor">경미</option>
            <option value="moderate">보통</option>
            <option value="severe">중상</option>
            <option value="fatal">사망</option>
          </select>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">전체 상태</option>
            <option value="reported">신고됨</option>
            <option value="investigating">조사중</option>
            <option value="action_required">조치필요</option>
            <option value="completed">완료</option>
            <option value="closed">종료</option>
          </select>
          <Button variant="outline" onClick={loadAccidents}>
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
              <p className="text-sm font-medium text-gray-600">총 사고건수</p>
              <p className="text-2xl font-bold text-gray-900">{totalAccidents}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <AlertTriangle className="w-8 h-8 text-red-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">중대사고</p>
              <p className="text-2xl font-bold text-red-600">{severeAccidents}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-orange-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">처리대기</p>
              <p className="text-2xl font-bold text-orange-600">{pendingInvestigations}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <Calendar className="w-8 h-8 text-purple-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 휴업일수</p>
              <p className="text-2xl font-bold text-purple-600">{totalLostDays}일</p>
            </div>
          </div>
        </Card>
      </div>

      {/* 사고 목록 */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  신고정보
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  부상자/장소
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  사고유형
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  심각도
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  처리상태
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  휴업일수
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  조사자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  관리
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
              ) : filteredAccidents.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                    사고 보고서가 없습니다.
                  </td>
                </tr>
              ) : (
                filteredAccidents.map((accident) => (
                  <tr key={accident.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{accident.report_number}</p>
                        <p className="text-sm text-gray-500">발생: {accident.incident_date}</p>
                        <p className="text-sm text-gray-500">신고: {accident.report_date}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{accident.injured_person}</p>
                        <p className="text-sm text-gray-500">{accident.department}</p>
                        <p className="text-xs text-gray-400">{accident.location}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm text-gray-900">{accident.accident_type}</p>
                        <p className="text-sm text-gray-500">{accident.injury_type}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getSeverityBadge(accident.severity)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="space-y-1">
                        {getStatusBadge(accident.status)}
                        {accident.follow_up_required && (
                          <p className="text-xs text-orange-600">
                            후속조치: {accident.follow_up_date}
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <p className="text-sm text-gray-900">{accident.lost_work_days || 0}일</p>
                        {accident.cost_estimate && (
                          <p className="text-xs text-gray-500">
                            비용: {accident.cost_estimate.toLocaleString()}원
                          </p>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm text-gray-900">{accident.investigated_by}</p>
                        <p className="text-xs text-gray-500">조사: {accident.investigation_date}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDetail(accident)}
                        >
                          <Eye size={14} />
                          상세
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleEdit(accident)}
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

      {/* 정부 신고 안내 */}
      <Card>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-red-900 mb-1">산업재해 신고 의무</h4>
              <div className="text-sm text-red-700 space-y-1">
                <p>• <strong>즉시 신고</strong>: 사망, 3일 이상 요양, 동일 원인 2명 이상 부상</p>
                <p>• <strong>월간 신고</strong>: 4일 이상 요양 재해 (매월 말일까지)</p>
                <p>• <strong>신고 기관</strong>: 관할 지방고용노동청</p>
                <p>• <strong>조사 의무</strong>: 재해 원인 조사 및 재발방지 대책 수립</p>
                <p>• <strong>미신고 시</strong>: 1천만원 이하 과태료 부과</p>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* 사고 신고/수정 폼 */}
      <AccidentForm
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        initialData={selectedAccident}
        mode={formMode}
      />

      {/* 상세 정보 모달 */}
      {showDetailModal && selectedAccident && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-bold">사고 상세 정보</h2>
              <Button variant="outline" onClick={() => setShowDetailModal(false)}>
                닫기
              </Button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">기본 정보</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">신고번호:</span> {selectedAccident.report_number}</p>
                    <p><span className="font-medium">발생일:</span> {selectedAccident.incident_date}</p>
                    <p><span className="font-medium">신고일:</span> {selectedAccident.report_date}</p>
                    <p><span className="font-medium">장소:</span> {selectedAccident.location}</p>
                    <p><span className="font-medium">부상자:</span> {selectedAccident.injured_person}</p>
                    <p><span className="font-medium">부서:</span> {selectedAccident.department}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">사고 정보</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">사고유형:</span> {selectedAccident.accident_type}</p>
                    <p><span className="font-medium">심각도:</span> {getSeverityBadge(selectedAccident.severity)}</p>
                    <p><span className="font-medium">부상유형:</span> {selectedAccident.injury_type}</p>
                    <p><span className="font-medium">휴업일수:</span> {selectedAccident.lost_work_days || 0}일</p>
                    {selectedAccident.cost_estimate && (
                      <p><span className="font-medium">예상비용:</span> {selectedAccident.cost_estimate.toLocaleString()}원</p>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">처리 상태</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">상태:</span> {getStatusBadge(selectedAccident.status)}</p>
                    <p><span className="font-medium">조사자:</span> {selectedAccident.investigated_by}</p>
                    <p><span className="font-medium">조사일:</span> {selectedAccident.investigation_date}</p>
                    {selectedAccident.follow_up_required && (
                      <p><span className="font-medium">후속조치일:</span> {selectedAccident.follow_up_date}</p>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">사고 경위</h3>
                  <p className="text-sm bg-gray-50 p-3 rounded">{selectedAccident.description}</p>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">원인 분석</h3>
                  <div className="space-y-2 text-sm">
                    <p><span className="font-medium">직접원인:</span> {selectedAccident.immediate_cause}</p>
                    <p><span className="font-medium">근본원인:</span> {selectedAccident.root_cause}</p>
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">시정 조치사항</h3>
                  <ul className="text-sm space-y-1">
                    {selectedAccident.corrective_actions.map((action, index) => (
                      <li key={index} className="flex items-start">
                        <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                        {action}
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">예방 대책</h3>
                  <ul className="text-sm space-y-1">
                    {selectedAccident.preventive_measures.map((measure, index) => (
                      <li key={index} className="flex items-start">
                        <span className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-2 flex-shrink-0"></span>
                        {measure}
                      </li>
                    ))}
                  </ul>
                </div>
                
                {selectedAccident.witnesses.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">목격자</h3>
                    <div className="text-sm">
                      {selectedAccident.witnesses.join(', ')}
                    </div>
                  </div>
                )}
                
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">추가 정보</h3>
                  <div className="space-y-1 text-sm">
                    <p><span className="font-medium">의료치료:</span> {selectedAccident.medical_treatment_required ? '필요' : '불필요'}</p>
                    <p><span className="font-medium">정부신고:</span> {selectedAccident.government_notification_required ? '대상' : '비대상'}</p>
                    <p><span className="font-medium">신고완료:</span> {selectedAccident.government_reported ? '완료' : '미완료'}</p>
                    <p><span className="font-medium">사진첨부:</span> {selectedAccident.photos_attached ? '있음' : '없음'}</p>
                    {selectedAccident.notes && (
                      <p><span className="font-medium">비고:</span> {selectedAccident.notes}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}