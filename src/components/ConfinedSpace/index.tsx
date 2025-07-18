import React, { useState, useEffect } from 'react';
import {
  Plus,
  Search,
  AlertTriangle,
  CheckCircle,
  Clock,
  Users,
  Shield,
  Activity,
  ClipboardCheck,
  Calendar,
  FileText,
  XCircle
} from 'lucide-react';
import { api } from '../../config/api';

interface ConfinedSpace {
  id: string;
  name: string;
  location: string;
  type: string;
  description?: string;
  volume?: number;
  depth?: number;
  entry_points: number;
  ventilation_type?: string;
  hazards?: string[];
  oxygen_level_normal?: number;
  responsible_person?: string;
  last_inspection_date?: string;
  inspection_cycle_days: number;
  is_active: boolean;
  created_at: string;
}

interface WorkPermit {
  id: string;
  permit_number: string;
  confined_space_id: string;
  confined_space?: ConfinedSpace;
  work_description: string;
  work_purpose?: string;
  contractor?: string;
  scheduled_start: string;
  scheduled_end: string;
  actual_start?: string;
  actual_end?: string;
  supervisor_name: string;
  supervisor_contact?: string;
  workers: WorkerInfo[];
  status: string;
  submitted_by?: string;
  submitted_at?: string;
  approved_by?: string;
  approved_at?: string;
  created_at: string;
}

interface WorkerInfo {
  name: string;
  role: string;
  contact?: string;
}

interface GasMeasurement {
  id: string;
  work_permit_id: string;
  measurement_time: string;
  measurement_location?: string;
  measured_by: string;
  oxygen_level: number;
  carbon_monoxide?: number;
  hydrogen_sulfide?: number;
  methane?: number;
  is_safe: boolean;
  remarks?: string;
}

interface Statistics {
  total_spaces: number;
  active_spaces: number;
  permits_today: number;
  permits_this_month: number;
  pending_approvals: number;
  overdue_inspections: number;
  by_type: Record<string, number>;
  by_hazard: Record<string, number>;
  recent_incidents: number;
}

const ConfinedSpace: React.FC = () => {
  const [activeTab, setActiveTab] = useState('spaces');
  const [spaces, setSpaces] = useState<ConfinedSpace[]>([]);
  const [permits, setPermits] = useState<WorkPermit[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [selectedSpace, setSelectedSpace] = useState<ConfinedSpace | null>(null);
  const [selectedPermit, setSelectedPermit] = useState<WorkPermit | null>(null);
  const [showSpaceModal, setShowSpaceModal] = useState(false);
  const [showPermitModal, setShowPermitModal] = useState(false);
  const [showGasModal, setShowGasModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSpaces();
    fetchPermits();
    fetchStatistics();
  }, []);

  const fetchSpaces = async () => {
    try {
      const response = await api.get('/confined-spaces/');
      setSpaces(response.data);
    } catch (error) {
      console.error('밀폐공간 목록 조회 실패:', error);
    }
  };

  const fetchPermits = async () => {
    try {
      const response = await api.get('/confined-spaces/permits/');
      setPermits(response.data);
    } catch (error) {
      console.error('작업 허가서 목록 조회 실패:', error);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await api.get('/confined-spaces/statistics');
      setStatistics(response.data);
    } catch (error) {
      console.error('통계 조회 실패:', error);
    }
  };

  const handleCreateSpace = async (data: any) => {
    try {
      setLoading(true);
      await api.post('/confined-spaces/', data);
      await fetchSpaces();
      setShowSpaceModal(false);
      alert('밀폐공간이 등록되었습니다.');
    } catch (error) {
      console.error('밀폐공간 등록 실패:', error);
      alert('밀폐공간 등록에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePermit = async (data: any) => {
    try {
      setLoading(true);
      await api.post('/confined-spaces/permits/', data);
      await fetchPermits();
      setShowPermitModal(false);
      alert('작업 허가서가 생성되었습니다.');
    } catch (error) {
      console.error('작업 허가서 생성 실패:', error);
      alert('작업 허가서 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleApprovePermit = async (permitId: string, approved: boolean, comments?: string) => {
    try {
      await api.post(`/confined-spaces/permits/${permitId}/approve`, {
        approved,
        comments
      });
      await fetchPermits();
      alert(approved ? '작업 허가서가 승인되었습니다.' : '작업 허가서가 반려되었습니다.');
    } catch (error) {
      console.error('허가서 승인/반려 실패:', error);
      alert('처리에 실패했습니다.');
    }
  };

  const handleStartWork = async (permitId: string) => {
    try {
      await api.post(`/confined-spaces/permits/${permitId}/start`);
      await fetchPermits();
      alert('작업이 시작되었습니다.');
    } catch (error) {
      console.error('작업 시작 실패:', error);
      alert('작업 시작에 실패했습니다.');
    }
  };

  const handleCompleteWork = async (permitId: string) => {
    try {
      await api.post(`/confined-spaces/permits/${permitId}/complete`);
      await fetchPermits();
      alert('작업이 완료되었습니다.');
    } catch (error) {
      console.error('작업 완료 실패:', error);
      alert('작업 완료 처리에 실패했습니다.');
    }
  };

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; icon: React.ReactNode; text: string }> = {
      '작성중': { color: 'bg-gray-100 text-gray-700', icon: <FileText className="w-4 h-4" />, text: '작성중' },
      '제출됨': { color: 'bg-blue-100 text-blue-700', icon: <Clock className="w-4 h-4" />, text: '제출됨' },
      '승인됨': { color: 'bg-green-100 text-green-700', icon: <CheckCircle className="w-4 h-4" />, text: '승인됨' },
      '작업중': { color: 'bg-yellow-100 text-yellow-700', icon: <Activity className="w-4 h-4" />, text: '작업중' },
      '완료됨': { color: 'bg-gray-100 text-gray-700', icon: <CheckCircle className="w-4 h-4" />, text: '완료됨' },
      '취소됨': { color: 'bg-red-100 text-red-700', icon: <XCircle className="w-4 h-4" />, text: '취소됨' }
    };

    const config = statusConfig[status] || statusConfig['작성중'];
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${config.color}`}>
        {config.icon}
        {config.text}
      </span>
    );
  };

  const getSpaceTypeBadge = (type: string) => {
    const typeColors: Record<string, string> = {
      '탱크': 'bg-blue-100 text-blue-700',
      '맨홀': 'bg-green-100 text-green-700',
      '배관': 'bg-purple-100 text-purple-700',
      '피트': 'bg-yellow-100 text-yellow-700',
      '사일로': 'bg-orange-100 text-orange-700',
      '터널': 'bg-gray-100 text-gray-700',
      '보일러': 'bg-red-100 text-red-700',
      '용광로': 'bg-pink-100 text-pink-700',
      '용기': 'bg-indigo-100 text-indigo-700',
      '기타': 'bg-gray-100 text-gray-700'
    };

    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${typeColors[type] || 'bg-gray-100 text-gray-700'}`}>
        {type}
      </span>
    );
  };

  return (
    <div className="p-6">
      {/* 헤더 */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800">밀폐공간 작업 관리</h1>
        <p className="text-gray-600 mt-1">밀폐공간 정보 및 작업 허가서를 관리합니다</p>
      </div>

      {/* 통계 카드 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">전체 밀폐공간</p>
                <p className="text-2xl font-bold text-gray-800">{statistics.total_spaces}</p>
              </div>
              <Shield className="w-8 h-8 text-blue-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">사용중</p>
                <p className="text-2xl font-bold text-gray-800">{statistics.active_spaces}</p>
              </div>
              <Activity className="w-8 h-8 text-green-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">오늘 작업</p>
                <p className="text-2xl font-bold text-gray-800">{statistics.permits_today}</p>
              </div>
              <Calendar className="w-8 h-8 text-purple-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">이번달 작업</p>
                <p className="text-2xl font-bold text-gray-800">{statistics.permits_this_month}</p>
              </div>
              <ClipboardCheck className="w-8 h-8 text-indigo-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">승인 대기</p>
                <p className="text-2xl font-bold text-yellow-600">{statistics.pending_approvals}</p>
              </div>
              <Clock className="w-8 h-8 text-yellow-500" />
            </div>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">점검 기한 초과</p>
                <p className="text-2xl font-bold text-red-600">{statistics.overdue_inspections}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </div>
        </div>
      )}

      {/* 탭 */}
      <div className="bg-white rounded-lg shadow mb-6">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex">
            <button
              onClick={() => setActiveTab('spaces')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'spaces'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              밀폐공간 관리
            </button>
            <button
              onClick={() => setActiveTab('permits')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'permits'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              작업 허가서
            </button>
            <button
              onClick={() => setActiveTab('gas')}
              className={`py-2 px-6 border-b-2 font-medium text-sm ${
                activeTab === 'gas'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              가스 측정 현황
            </button>
          </nav>
        </div>

        <div className="p-6">
          {/* 검색 및 필터 */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <div className="flex-1">
              <div className="relative">
                <input
                  type="text"
                  placeholder="검색..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <Search className="absolute left-3 top-2.5 h-5 w-5 text-gray-400" />
              </div>
            </div>
            {activeTab === 'permits' && (
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="all">전체 상태</option>
                <option value="제출됨">제출됨</option>
                <option value="승인됨">승인됨</option>
                <option value="작업중">작업중</option>
                <option value="완료됨">완료됨</option>
              </select>
            )}
            <button
              onClick={() => {
                if (activeTab === 'spaces') {
                  setShowSpaceModal(true);
                } else if (activeTab === 'permits') {
                  setShowPermitModal(true);
                }
              }}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              {activeTab === 'spaces' ? '밀폐공간 등록' : '작업 허가서 생성'}
            </button>
          </div>

          {/* 컨텐츠 */}
          {activeTab === 'spaces' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      밀폐공간명
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      위치
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      유형
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      관리책임자
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      최근 점검일
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {spaces
                    .filter(space => 
                      space.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      space.location.toLowerCase().includes(searchTerm.toLowerCase())
                    )
                    .map((space) => (
                      <tr key={space.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{space.name}</div>
                          {space.description && (
                            <div className="text-sm text-gray-500">{space.description}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {space.location}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getSpaceTypeBadge(space.type)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {space.responsible_person || '-'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {space.last_inspection_date
                            ? new Date(space.last_inspection_date).toLocaleDateString()
                            : '미점검'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                            space.is_active
                              ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          }`}>
                            {space.is_active ? '사용중' : '미사용'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => setSelectedSpace(space)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            상세
                          </button>
                          <button
                            onClick={() => {
                              setSelectedSpace(space);
                              setShowPermitModal(true);
                            }}
                            className="text-green-600 hover:text-green-900"
                          >
                            작업신청
                          </button>
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'permits' && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      허가서 번호
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      밀폐공간
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업 내용
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업 일정
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      감독자
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      상태
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      작업
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {permits
                    .filter(permit => 
                      filterStatus === 'all' || permit.status === filterStatus
                    )
                    .filter(permit =>
                      permit.permit_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
                      permit.work_description.toLowerCase().includes(searchTerm.toLowerCase())
                    )
                    .map((permit) => (
                      <tr key={permit.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm font-medium text-gray-900">{permit.permit_number}</div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {permit.confined_space?.name || '-'}
                        </td>
                        <td className="px-6 py-4">
                          <div className="text-sm text-gray-900 max-w-xs truncate">
                            {permit.work_description}
                          </div>
                          {permit.contractor && (
                            <div className="text-sm text-gray-500">{permit.contractor}</div>
                          )}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">
                            {new Date(permit.scheduled_start).toLocaleString()}
                          </div>
                          <div className="text-sm text-gray-500">
                            ~ {new Date(permit.scheduled_end).toLocaleString()}
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <div className="text-sm text-gray-900">{permit.supervisor_name}</div>
                          <div className="text-sm text-gray-500 flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {permit.workers.length}명
                          </div>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          {getStatusBadge(permit.status)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <button
                            onClick={() => setSelectedPermit(permit)}
                            className="text-blue-600 hover:text-blue-900 mr-3"
                          >
                            상세
                          </button>
                          {permit.status === '제출됨' && (
                            <>
                              <button
                                onClick={() => handleApprovePermit(permit.id, true)}
                                className="text-green-600 hover:text-green-900 mr-2"
                              >
                                승인
                              </button>
                              <button
                                onClick={() => {
                                  const reason = prompt('반려 사유를 입력하세요:');
                                  if (reason) {
                                    handleApprovePermit(permit.id, false, reason);
                                  }
                                }}
                                className="text-red-600 hover:text-red-900"
                              >
                                반려
                              </button>
                            </>
                          )}
                          {permit.status === '승인됨' && (
                            <button
                              onClick={() => handleStartWork(permit.id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              작업시작
                            </button>
                          )}
                          {permit.status === '작업중' && (
                            <>
                              <button
                                onClick={() => setShowGasModal(true)}
                                className="text-purple-600 hover:text-purple-900 mr-2"
                              >
                                가스측정
                              </button>
                              <button
                                onClick={() => handleCompleteWork(permit.id)}
                                className="text-blue-600 hover:text-blue-900"
                              >
                                작업완료
                              </button>
                            </>
                          )}
                        </td>
                      </tr>
                    ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'gas' && (
            <div className="text-center py-12 text-gray-500">
              가스 측정 현황 기능은 준비 중입니다.
            </div>
          )}
        </div>
      </div>

      {/* 밀폐공간 등록 모달 */}
      {showSpaceModal && (
        <SpaceFormModal
          onClose={() => setShowSpaceModal(false)}
          onSubmit={handleCreateSpace}
          loading={loading}
        />
      )}

      {/* 작업 허가서 생성 모달 */}
      {showPermitModal && (
        <PermitFormModal
          spaces={spaces}
          selectedSpace={selectedSpace}
          onClose={() => {
            setShowPermitModal(false);
            setSelectedSpace(null);
          }}
          onSubmit={handleCreatePermit}
          loading={loading}
        />
      )}
    </div>
  );
};

// 밀폐공간 등록 폼 모달 컴포넌트
const SpaceFormModal: React.FC<{
  onClose: () => void;
  onSubmit: (data: any) => void;
  loading: boolean;
}> = ({ onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    type: '탱크',
    description: '',
    volume: '',
    depth: '',
    entry_points: 1,
    ventilation_type: '',
    hazards: [] as string[],
    oxygen_level_normal: '',
    responsible_person: '',
    inspection_cycle_days: 30
  });

  const spaceTypes = [
    '탱크', '맨홀', '배관', '피트', '사일로',
    '터널', '보일러', '용광로', '용기', '기타'
  ];

  const hazardTypes = [
    '산소결핍', '유독가스', '가연성가스', '익사', '매몰',
    '고온', '저온', '감전', '기계적위험', '기타'
  ];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const submitData = {
      ...formData,
      volume: formData.volume ? parseFloat(formData.volume) : undefined,
      depth: formData.depth ? parseFloat(formData.depth) : undefined,
      oxygen_level_normal: formData.oxygen_level_normal ? parseFloat(formData.oxygen_level_normal) : undefined
    };
    onSubmit(submitData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">밀폐공간 등록</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  밀폐공간명 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  위치 *
                </label>
                <input
                  type="text"
                  required
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  유형 *
                </label>
                <select
                  required
                  value={formData.type}
                  onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {spaceTypes.map(type => (
                    <option key={type} value={type}>{type}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  관리책임자
                </label>
                <input
                  type="text"
                  value={formData.responsible_person}
                  onChange={(e) => setFormData({ ...formData, responsible_person: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  용적(m³)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.volume}
                  onChange={(e) => setFormData({ ...formData, volume: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  깊이(m)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={formData.depth}
                  onChange={(e) => setFormData({ ...formData, depth: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  출입구 수
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.entry_points}
                  onChange={(e) => setFormData({ ...formData, entry_points: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  환기 방식
                </label>
                <input
                  type="text"
                  value={formData.ventilation_type}
                  onChange={(e) => setFormData({ ...formData, ventilation_type: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  정상 산소 농도(%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  max="100"
                  value={formData.oxygen_level_normal}
                  onChange={(e) => setFormData({ ...formData, oxygen_level_normal: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  점검주기(일)
                </label>
                <input
                  type="number"
                  min="1"
                  value={formData.inspection_cycle_days}
                  onChange={(e) => setFormData({ ...formData, inspection_cycle_days: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                설명
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="mt-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                위험 요인
              </label>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                {hazardTypes.map(hazard => (
                  <label key={hazard} className="flex items-center">
                    <input
                      type="checkbox"
                      checked={formData.hazards.includes(hazard)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({ ...formData, hazards: [...formData.hazards, hazard] });
                        } else {
                          setFormData({ ...formData, hazards: formData.hazards.filter(h => h !== hazard) });
                        }
                      }}
                      className="mr-2"
                    />
                    <span className="text-sm">{hazard}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? '등록 중...' : '등록'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// 작업 허가서 생성 폼 모달 컴포넌트
const PermitFormModal: React.FC<{
  spaces: ConfinedSpace[];
  selectedSpace: ConfinedSpace | null;
  onClose: () => void;
  onSubmit: (data: any) => void;
  loading: boolean;
}> = ({ spaces, selectedSpace, onClose, onSubmit, loading }) => {
  const [formData, setFormData] = useState({
    confined_space_id: selectedSpace?.id || '',
    work_description: '',
    work_purpose: '',
    contractor: '',
    scheduled_start: '',
    scheduled_end: '',
    supervisor_name: '',
    supervisor_contact: '',
    workers: [{ name: '', role: '', contact: '' }],
    required_ppe: [] as string[],
    emergency_contact: '',
    emergency_procedures: ''
  });

  const ppeTypes = [
    '안전모', '안전화', '안전대', '안전장갑',
    '보안경', '방진마스크', '방독마스크', '송기마스크',
    '구명줄', '가스측정기', '무전기', '비상조명'
  ];

  const handleAddWorker = () => {
    setFormData({
      ...formData,
      workers: [...formData.workers, { name: '', role: '', contact: '' }]
    });
  };

  const handleRemoveWorker = (index: number) => {
    setFormData({
      ...formData,
      workers: formData.workers.filter((_, i) => i !== index)
    });
  };

  const handleWorkerChange = (index: number, field: string, value: string) => {
    const newWorkers = [...formData.workers];
    newWorkers[index] = { ...newWorkers[index], [field]: value };
    setFormData({ ...formData, workers: newWorkers });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validWorkers = formData.workers.filter(w => w.name && w.role);
    if (validWorkers.length === 0) {
      alert('최소 1명 이상의 작업자 정보를 입력해주세요.');
      return;
    }
    onSubmit({
      ...formData,
      workers: validWorkers
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-bold mb-4">작업 허가서 생성</h2>
          
          <form onSubmit={handleSubmit}>
            <div className="space-y-6">
              {/* 기본 정보 */}
              <div>
                <h3 className="text-lg font-medium mb-3">기본 정보</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      밀폐공간 *
                    </label>
                    <select
                      required
                      value={formData.confined_space_id}
                      onChange={(e) => setFormData({ ...formData, confined_space_id: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">선택하세요</option>
                      {spaces.filter(s => s.is_active).map(space => (
                        <option key={space.id} value={space.id}>
                          {space.name} - {space.location}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 업체
                    </label>
                    <input
                      type="text"
                      value={formData.contractor}
                      onChange={(e) => setFormData({ ...formData, contractor: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 목적
                    </label>
                    <input
                      type="text"
                      value={formData.work_purpose}
                      onChange={(e) => setFormData({ ...formData, work_purpose: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      비상 연락처
                    </label>
                    <input
                      type="text"
                      value={formData.emergency_contact}
                      onChange={(e) => setFormData({ ...formData, emergency_contact: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    작업 내용 *
                  </label>
                  <textarea
                    required
                    value={formData.work_description}
                    onChange={(e) => setFormData({ ...formData, work_description: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* 작업 일정 */}
              <div>
                <h3 className="text-lg font-medium mb-3">작업 일정</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 시작 예정일시 *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={formData.scheduled_start}
                      onChange={(e) => setFormData({ ...formData, scheduled_start: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 종료 예정일시 *
                    </label>
                    <input
                      type="datetime-local"
                      required
                      value={formData.scheduled_end}
                      onChange={(e) => setFormData({ ...formData, scheduled_end: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* 작업자 정보 */}
              <div>
                <h3 className="text-lg font-medium mb-3">작업자 정보</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      작업 감독자 *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.supervisor_name}
                      onChange={(e) => setFormData({ ...formData, supervisor_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      감독자 연락처
                    </label>
                    <input
                      type="text"
                      value={formData.supervisor_contact}
                      onChange={(e) => setFormData({ ...formData, supervisor_contact: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-medium text-gray-700">작업자 목록</label>
                    <button
                      type="button"
                      onClick={handleAddWorker}
                      className="px-3 py-1 bg-green-500 text-white text-sm rounded hover:bg-green-600"
                    >
                      작업자 추가
                    </button>
                  </div>
                  
                  {formData.workers.map((worker, index) => (
                    <div key={index} className="flex gap-2 items-center">
                      <input
                        type="text"
                        placeholder="작업자명"
                        value={worker.name}
                        onChange={(e) => handleWorkerChange(index, 'name', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <input
                        type="text"
                        placeholder="역할"
                        value={worker.role}
                        onChange={(e) => handleWorkerChange(index, 'role', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      <input
                        type="text"
                        placeholder="연락처"
                        value={worker.contact}
                        onChange={(e) => handleWorkerChange(index, 'contact', e.target.value)}
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {formData.workers.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveWorker(index)}
                          className="px-2 py-1 bg-red-500 text-white rounded hover:bg-red-600"
                        >
                          삭제
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* 안전 조치 */}
              <div>
                <h3 className="text-lg font-medium mb-3">안전 조치</h3>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    필수 보호구
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {ppeTypes.map(ppe => (
                      <label key={ppe} className="flex items-center">
                        <input
                          type="checkbox"
                          checked={formData.required_ppe.includes(ppe)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setFormData({ ...formData, required_ppe: [...formData.required_ppe, ppe] });
                            } else {
                              setFormData({ ...formData, required_ppe: formData.required_ppe.filter(p => p !== ppe) });
                            }
                          }}
                          className="mr-2"
                        />
                        <span className="text-sm">{ppe}</span>
                      </label>
                    ))}
                  </div>
                </div>

                <div className="mt-4">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    비상 대응 절차
                  </label>
                  <textarea
                    value={formData.emergency_procedures}
                    onChange={(e) => setFormData({ ...formData, emergency_procedures: e.target.value })}
                    rows={3}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                취소
              </button>
              <button
                type="submit"
                disabled={loading}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50"
              >
                {loading ? '생성 중...' : '생성'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default ConfinedSpace;