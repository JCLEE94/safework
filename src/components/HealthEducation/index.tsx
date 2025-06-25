import React, { useState, useEffect } from 'react';
import { Plus, Search, BookOpen, Clock, Users, CheckCircle } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

interface HealthEducation {
  id: number;
  title: string;
  education_type: string;
  instructor: string;
  duration: number; // 시간
  target_workers: string[];
  scheduled_date: string;
  completion_rate: number;
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled';
  required_hours: number;
  description: string;
}

export function HealthEducation() {
  const [educations, setEducations] = useState<HealthEducation[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const { fetchApi } = useApi();

  useEffect(() => {
    loadEducations();
  }, []);

  const loadEducations = async () => {
    try {
      setLoading(true);
      // 임시 더미 데이터
      const dummyData = [
        {
          id: 1,
          title: "신입 근로자 안전보건교육",
          education_type: "법정교육",
          instructor: "안전관리자 김교육",
          duration: 8,
          target_workers: ["김철수", "이영희", "박신입"],
          scheduled_date: "2024-07-01",
          completion_rate: 100,
          status: 'completed' as const,
          required_hours: 8,
          description: "산업안전보건법 제31조에 따른 신입 근로자 안전보건교육"
        },
        {
          id: 2,
          title: "정기 안전보건교육",
          education_type: "정기교육",
          instructor: "외부강사 최전문",
          duration: 3,
          target_workers: ["김철수", "이영희", "박기존", "최숙련"],
          scheduled_date: "2024-07-15",
          completion_rate: 75,
          status: 'ongoing' as const,
          required_hours: 3,
          description: "분기별 정기 안전보건교육 (3시간)"
        },
        {
          id: 3,
          title: "화학물질 취급 안전교육",
          education_type: "특별교육",
          instructor: "화학안전전문가 이화학",
          duration: 4,
          target_workers: ["박화학", "최취급"],
          scheduled_date: "2024-07-20",
          completion_rate: 0,
          status: 'scheduled' as const,
          required_hours: 4,
          description: "화학물질 및 위험물 취급 근로자 대상 특별안전교육"
        },
        {
          id: 4,
          title: "고소작업 안전교육",
          education_type: "특별교육",
          instructor: "안전관리자 김교육",
          duration: 2,
          target_workers: ["이고소", "박높이"],
          scheduled_date: "2024-06-30",
          completion_rate: 0,
          status: 'cancelled' as const,
          required_hours: 2,
          description: "2m 이상 고소작업 근로자 대상 안전교육"
        }
      ];
      setEducations(dummyData);
    } catch (error) {
      console.error('보건교육 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <Badge className="bg-blue-100 text-blue-800">예정</Badge>;
      case 'ongoing':
        return <Badge className="bg-yellow-100 text-yellow-800">진행중</Badge>;
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">완료</Badge>;
      case 'cancelled':
        return <Badge className="bg-red-100 text-red-800">취소</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">미확인</Badge>;
    }
  };

  const getEducationTypeBadge = (type: string) => {
    switch (type) {
      case '법정교육':
        return <Badge className="bg-purple-100 text-purple-800">법정교육</Badge>;
      case '정기교육':
        return <Badge className="bg-blue-100 text-blue-800">정기교육</Badge>;
      case '특별교육':
        return <Badge className="bg-orange-100 text-orange-800">특별교육</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{type}</Badge>;
    }
  };

  const filteredEducations = educations.filter(education => {
    const matchesSearch = education.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         education.instructor.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || education.status === filterStatus;
    return matchesSearch && matchesStatus;
  });

  const totalEducations = educations.length;
  const completedEducations = educations.filter(e => e.status === 'completed').length;
  const ongoingEducations = educations.filter(e => e.status === 'ongoing').length;
  const scheduledEducations = educations.filter(e => e.status === 'scheduled').length;

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">보건교육 관리</h1>
        <Button onClick={() => {}} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          교육 계획 등록
        </Button>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="교육명 또는 강사명으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="all">전체 상태</option>
            <option value="scheduled">예정</option>
            <option value="ongoing">진행중</option>
            <option value="completed">완료</option>
            <option value="cancelled">취소</option>
          </select>
          <Button variant="outline" onClick={loadEducations}>
            새로고침
          </Button>
        </div>
      </Card>

      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <div className="flex items-center">
            <BookOpen className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">총 교육</p>
              <p className="text-2xl font-bold text-gray-900">{totalEducations}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <CheckCircle className="w-8 h-8 text-green-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">완료</p>
              <p className="text-2xl font-bold text-green-600">{completedEducations}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <Clock className="w-8 h-8 text-yellow-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">진행중</p>
              <p className="text-2xl font-bold text-yellow-600">{ongoingEducations}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <Users className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">예정</p>
              <p className="text-2xl font-bold text-blue-600">{scheduledEducations}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* 교육 목록 */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  교육명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  교육유형
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  강사
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  예정일
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  시간
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  대상자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  진행률
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  상태
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
              ) : filteredEducations.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-6 py-4 text-center text-gray-500">
                    보건교육 계획이 없습니다.
                  </td>
                </tr>
              ) : (
                filteredEducations.map((education) => (
                  <tr key={education.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{education.title}</p>
                        <p className="text-sm text-gray-500">{education.description}</p>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getEducationTypeBadge(education.education_type)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {education.instructor}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {education.scheduled_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {education.duration}시간
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {education.target_workers.length}명
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${education.completion_rate}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-500">{education.completion_rate}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {getStatusBadge(education.status)}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 법정 교육 안내 */}
      <Card>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <BookOpen className="w-5 h-5 text-purple-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-purple-900 mb-1">산업안전보건법 교육 의무</h4>
              <div className="text-sm text-purple-700 space-y-1">
                <p>• 신입 근로자: 8시간 이상</p>
                <p>• 정기 교육: 분기별 3시간 이상</p>
                <p>• 특별 교육: 위험 작업 종사자 대상</p>
                <p>• 관리감독자: 연 16시간 이상</p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}