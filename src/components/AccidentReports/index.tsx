import React, { useState, useEffect } from 'react';
import { Plus, Search, AlertTriangle, FileText, Calendar, Users, TrendingUp, Clock } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

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
  const { fetchApi } = useApi();

  useEffect(() => {
    loadAccidents();
  }, []);

  const loadAccidents = async () => {
    try {
      setLoading(true);
      // 임시 더미 데이터
      const dummyData = [
        {
          id: 1,
          report_number: "ACC-2024-001",
          incident_date: "2024-06-20",
          report_date: "2024-06-20",
          location: "건설 현장 A구역",
          injured_person: "김철수",
          department: "건설팀",
          accident_type: "추락",
          severity: 'moderate' as const,
          injury_type: "타박상, 골절",
          description: "비계 작업 중 안전대 미착용으로 인한 2m 높이에서 추락",
          immediate_cause: "안전대 미착용",
          root_cause: "안전교육 부족 및 안전점검 소홀",
          corrective_actions: ["안전대 착용 의무화", "현장 안전교육 실시"],
          preventive_measures: ["안전점검 강화", "안전교육 정기화"],
          reported_by: "현장 감독자",
          investigated_by: "안전관리자 이안전",
          investigation_date: "2024-06-21",
          status: 'action_required' as const,
          follow_up_required: true,
          follow_up_date: "2024-07-20",
          cost_estimate: 1500000,
          lost_work_days: 14,
          witnesses: ["박목격", "최현장"],
          photos_attached: true,
          medical_treatment_required: true,
          government_notification_required: true,
          government_reported: true,
          notes: "중상 사고로 정부 신고 완료"
        },
        {
          id: 2,
          report_number: "ACC-2024-002",
          incident_date: "2024-06-15",
          report_date: "2024-06-15",
          location: "기계실 B동",
          injured_person: "이영희",
          department: "정비팀",
          accident_type: "협착",
          severity: 'minor' as const,
          injury_type: "손가락 찰과상",
          description: "기계 정비 중 손가락이 기계 부품에 협착됨",
          immediate_cause: "보호장갑 미착용",
          root_cause: "개인보호구 관리 부주의",
          corrective_actions: ["보호장갑 착용 확인"],
          preventive_measures: ["개인보호구 점검 강화"],
          reported_by: "당사자",
          investigated_by: "안전관리자 이안전",
          investigation_date: "2024-06-16",
          status: 'completed' as const,
          follow_up_required: false,
          cost_estimate: 50000,
          lost_work_days: 0,
          witnesses: [],
          photos_attached: false,
          medical_treatment_required: true,
          government_notification_required: false,
          government_reported: false,
          notes: "경미한 사고"
        },
        {
          id: 3,
          report_number: "ACC-2024-003",
          incident_date: "2024-06-10",
          report_date: "2024-06-11",
          location: "화학물질 저장소",
          injured_person: "박화학",
          department: "화학팀",
          accident_type: "화학물질 노출",
          severity: 'severe' as const,
          injury_type: "화학 화상, 호흡기 자극",
          description: "화학물질 이송 중 용기 파손으로 인한 화학물질 누출 및 노출",
          immediate_cause: "용기 결함",
          root_cause: "화학물질 용기 점검 부족",
          corrective_actions: ["화학물질 용기 전체 점검", "비상 대응 절차 개선"],
          preventive_measures: ["용기 정기 점검 체계 구축", "화학물질 취급 교육 강화"],
          reported_by: "동료 근로자",
          investigated_by: "안전관리자 이안전",
          investigation_date: "2024-06-12",
          status: 'investigating' as const,
          follow_up_required: true,
          follow_up_date: "2024-08-10",
          cost_estimate: 3000000,
          lost_work_days: 30,
          witnesses: ["최목격", "정현장", "김동료"],
          photos_attached: true,
          medical_treatment_required: true,
          government_notification_required: true,
          government_reported: true,
          notes: "중대재해 조사 진행 중"
        },
        {
          id: 4,
          report_number: "ACC-2024-004",
          incident_date: "2024-06-25",
          report_date: "2024-06-25",
          location: "주차장",
          injured_person: "최운전",
          department: "운송팀",
          accident_type: "차량 사고",
          severity: 'minor' as const,
          injury_type: "목 염좌",
          description: "후진 중 다른 차량과 접촉 사고",
          immediate_cause: "후방 확인 소홀",
          root_cause: "안전운전 교육 부족",
          corrective_actions: ["안전운전 재교육"],
          preventive_measures: ["후방 카메라 설치 검토"],
          reported_by: "당사자",
          investigated_by: "안전관리자 이안전",
          investigation_date: "2024-06-25",
          status: 'reported' as const,
          follow_up_required: false,
          cost_estimate: 200000,
          lost_work_days: 1,
          witnesses: ["박주차"],
          photos_attached: true,
          medical_treatment_required: false,
          government_notification_required: false,
          government_reported: false,
          notes: "경미한 교통사고"
        }
      ];
      setAccidents(dummyData);
    } catch (error) {
      console.error('사고보고 목록 조회 실패:', error);
    } finally {
      setLoading(false);
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
        <Button onClick={() => {}} className="flex items-center gap-2">
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
                          onClick={() => {}}
                        >
                          상세
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => {}}
                        >
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
    </div>
  );
}