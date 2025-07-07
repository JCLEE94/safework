import React, { useState, useEffect } from 'react';
import { 
  Plus, Edit, Trash2, Search, Filter, RefreshCw, Calendar,
  UserCheck, Heart, FileText, AlertCircle, CheckCircle,
  Clock, Users, Activity
} from 'lucide-react';
import { Card, Button, Table, Badge } from '../common';
import { ConsultationForm } from './ConsultationForm';
import { useApi } from '../../hooks/useApi';
import { apiUrl } from '../../config/api';

interface HealthConsultation {
  id: number;
  worker_id: number;
  worker_name?: string;
  worker_department?: string;
  worker_position?: string;
  consultation_date: string;
  consultation_type: string;
  chief_complaint: string;
  consultation_location: string;
  consultant_name: string;
  symptoms?: string;
  health_issue_category?: string;
  status: string;
  referral_needed: boolean;
  follow_up_needed: boolean;
  follow_up_date?: string;
  created_at: string;
}

interface ApiResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const CONSULTATION_TYPES = [
  { value: '정기상담', label: '정기상담', color: 'blue' },
  { value: '응급상담', label: '응급상담', color: 'red' },
  { value: '사후관리', label: '사후관리', color: 'orange' },
  { value: '건강문제', label: '건강문제', color: 'purple' },
  { value: '직업병관련', label: '직업병관련', color: 'indigo' }
];

const CONSULTATION_STATUS = [
  { value: '예정', label: '예정', color: 'gray' },
  { value: '진행중', label: '진행중', color: 'blue' },
  { value: '완료', label: '완료', color: 'green' },
  { value: '취소', label: '취소', color: 'red' },
  { value: '재예약', label: '재예약', color: 'yellow' }
];

const HEALTH_ISSUE_CATEGORIES = [
  { value: '호흡기', label: '호흡기' },
  { value: '근골격계', label: '근골격계' },
  { value: '피부', label: '피부' },
  { value: '눈', label: '눈' },
  { value: '심혈관', label: '심혈관' },
  { value: '정신건강', label: '정신건강' },
  { value: '소화기', label: '소화기' },
  { value: '기타', label: '기타' }
];

export function HealthConsultations() {
  const [consultations, setConsultations] = useState<HealthConsultation[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedConsultation, setSelectedConsultation] = useState<HealthConsultation | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    consultation_type: '',
    status: '',
    health_issue_category: '',
    worker_id: '',
    start_date: '',
    end_date: ''
  });
  const [statistics, setStatistics] = useState<any>(null);
  
  const { fetchApi } = useApi();
  
  useEffect(() => {
    loadConsultations();
    loadStatistics();
  }, [filters]);
  
  const loadConsultations = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (searchTerm) params.append('search', searchTerm);
      if (filters.consultation_type) params.append('consultation_type', filters.consultation_type);
      if (filters.status) params.append('status', filters.status);
      if (filters.health_issue_category) params.append('health_issue_category', filters.health_issue_category);
      if (filters.worker_id) params.append('worker_id', filters.worker_id);
      if (filters.start_date) params.append('start_date', filters.start_date);
      if (filters.end_date) params.append('end_date', filters.end_date);
      
      const data = await fetchApi<ApiResponse<HealthConsultation>>(`/health-consultations?${params}`);
      setConsultations(data.items);
    } catch (error) {
      console.error('보건상담 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadStatistics = async () => {
    try {
      const data = await fetchApi('/health-consultations/statistics');
      setStatistics(data);
    } catch (error) {
      console.error('상담 통계 조회 실패:', error);
    }
  };
  
  const handleCreate = () => {
    setFormMode('create');
    setSelectedConsultation(null);
    setShowForm(true);
  };
  
  const handleEdit = (consultation: HealthConsultation) => {
    setFormMode('edit');
    setSelectedConsultation(consultation);
    setShowForm(true);
  };
  
  const handleDelete = async (id: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    try {
      await fetchApi(`/health-consultations/${id}`, {
        method: 'DELETE'
      });
      await loadConsultations();
    } catch (error) {
      console.error('보건상담 삭제 실패:', error);
    }
  };
  
  const handleSubmit = async (data: Partial<HealthConsultation>) => {
    try {
      if (formMode === 'create') {
        await fetchApi('/health-consultations', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      } else if (selectedConsultation) {
        await fetchApi(`/health-consultations/${selectedConsultation.id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data)
        });
      }
      
      setShowForm(false);
      await loadConsultations();
      await loadStatistics();
    } catch (error) {
      console.error('보건상담 저장 실패:', error);
    }
  };

  const getTypeColor = (type: string) => {
    const typeInfo = CONSULTATION_TYPES.find(t => t.value === type);
    return typeInfo?.color || 'gray';
  };

  const getStatusColor = (status: string) => {
    const statusInfo = CONSULTATION_STATUS.find(s => s.value === status);
    return statusInfo?.color || 'gray';
  };
  
  const columns = [
    {
      key: 'worker_info',
      header: '근로자 정보',
      render: (consultation: HealthConsultation) => (
        <div>
          <div className="font-medium">{consultation.worker_name}</div>
          <div className="text-sm text-gray-500">
            {consultation.worker_department} / {consultation.worker_position}
          </div>
        </div>
      )
    },
    {
      key: 'consultation_date',
      header: '상담일시',
      render: (consultation: HealthConsultation) => (
        <div>
          <div className="font-medium">
            {new Date(consultation.consultation_date).toLocaleDateString()}
          </div>
          <div className="text-sm text-gray-500">
            {new Date(consultation.consultation_date).toLocaleTimeString()}
          </div>
        </div>
      )
    },
    {
      key: 'consultation_type',
      header: '상담유형',
      render: (consultation: HealthConsultation) => (
        <Badge color={getTypeColor(consultation.consultation_type)}>
          {consultation.consultation_type}
        </Badge>
      )
    },
    {
      key: 'chief_complaint',
      header: '주 호소사항',
      render: (consultation: HealthConsultation) => (
        <div className="max-w-xs truncate" title={consultation.chief_complaint}>
          {consultation.chief_complaint}
        </div>
      )
    },
    {
      key: 'status',
      header: '상태',
      render: (consultation: HealthConsultation) => (
        <Badge color={getStatusColor(consultation.status)}>
          {consultation.status}
        </Badge>
      )
    },
    {
      key: 'flags',
      header: '조치사항',
      render: (consultation: HealthConsultation) => (
        <div className="flex gap-1">
          {consultation.referral_needed && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-800">
              <Heart size={12} className="mr-1" />
              의뢰
            </span>
          )}
          {consultation.follow_up_needed && (
            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-800">
              <Clock size={12} className="mr-1" />
              추적
            </span>
          )}
        </div>
      )
    },
    {
      key: 'consultant_name',
      header: '상담자',
      render: (consultation: HealthConsultation) => consultation.consultant_name
    },
    {
      key: 'actions',
      header: '관리',
      render: (consultation: HealthConsultation) => (
        <div className="flex gap-2">
          <button
            onClick={() => handleEdit(consultation)}
            className="text-blue-600 hover:text-blue-800"
          >
            <Edit size={16} />
          </button>
          <button
            onClick={() => handleDelete(consultation.id)}
            className="text-red-600 hover:text-red-800"
          >
            <Trash2 size={16} />
          </button>
        </div>
      )
    }
  ];
  
  return (
    <div className="p-6 space-y-6">
      {/* 헤더 */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">보건상담 관리</h1>
        <Button onClick={handleCreate} icon={<Plus size={16} />}>
          상담 등록
        </Button>
      </div>

      {/* 통계 카드 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">총 상담</p>
                <p className="text-2xl font-bold text-blue-600">{statistics.total_consultations}</p>
              </div>
              <Users className="text-blue-600" size={32} />
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">의료기관 의뢰율</p>
                <p className="text-2xl font-bold text-red-600">{statistics.referral_rate?.toFixed(1)}%</p>
              </div>
              <Heart className="text-red-600" size={32} />
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">추적관찰 비율</p>
                <p className="text-2xl font-bold text-orange-600">{statistics.follow_up_rate?.toFixed(1)}%</p>
              </div>
              <Clock className="text-orange-600" size={32} />
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">작업 관련</p>
                <p className="text-2xl font-bold text-purple-600">{statistics.work_related_percentage?.toFixed(1)}%</p>
              </div>
              <Activity className="text-purple-600" size={32} />
            </div>
          </Card>
        </div>
      )}
      
      <Card>
        <div className="space-y-4">
          {/* 검색 및 필터 */}
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={18} />
                <input
                  type="text"
                  placeholder="근로자명, 상담내용으로 검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && loadConsultations()}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            
            <div className="flex gap-2">
              <select
                value={filters.consultation_type}
                onChange={(e) => setFilters(prev => ({ ...prev, consultation_type: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">모든 상담유형</option>
                {CONSULTATION_TYPES.map(type => (
                  <option key={type.value} value={type.value}>{type.label}</option>
                ))}
              </select>
              
              <select
                value={filters.status}
                onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">모든 상태</option>
                {CONSULTATION_STATUS.map(status => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </select>

              <select
                value={filters.health_issue_category}
                onChange={(e) => setFilters(prev => ({ ...prev, health_issue_category: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              >
                <option value="">모든 카테고리</option>
                {HEALTH_ISSUE_CATEGORIES.map(category => (
                  <option key={category.value} value={category.value}>{category.label}</option>
                ))}
              </select>
              
              <Button variant="secondary" onClick={loadConsultations} icon={<RefreshCw size={16} />}>
                새로고침
              </Button>
            </div>
          </div>

          {/* 날짜 필터 */}
          <div className="flex gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">시작일</label>
              <input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">종료일</label>
              <input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
                className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          
          {/* 테이블 */}
          <Table
            columns={columns}
            data={consultations}
            loading={loading}
            emptyMessage="등록된 보건상담이 없습니다."
          />
        </div>
      </Card>
      
      <ConsultationForm
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        initialData={selectedConsultation}
        mode={formMode}
      />
    </div>
  );
}