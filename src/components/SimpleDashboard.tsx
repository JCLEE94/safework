import React, { useState, useEffect } from 'react';
import { Users, ShieldCheck, Calendar, AlertTriangle, TrendingUp, Activity, FileText, Zap } from 'lucide-react';

interface DashboardStats {
  total_workers: number;
  special_exam_targets: number;
  health_exam_needed: number;
  accidents_this_month: number;
}

interface RecentActivity {
  id: string;
  description: string;
  time: string;
}

export function SimpleDashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    total_workers: 0,
    special_exam_targets: 0,
    health_exam_needed: 0,
    accidents_this_month: 0
  });
  const [activities, setActivities] = useState<RecentActivity[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      
      // API 기본 URL 설정
      const API_BASE = window.location.origin + '/api/v1';
      
      // 통계 데이터 가져오기
      const statsResponse = await fetch(`${API_BASE}/workers/statistics/dashboard`);
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      } else {
        // API 실패시 기본값 사용
        console.warn('통계 API 호출 실패, 기본값 사용');
      }

      // 최근 활동 데이터 가져오기 (workers에서 최근 5개)
      const workersResponse = await fetch(`${API_BASE}/workers/?page=1&page_size=5`);
      if (workersResponse.ok) {
        const workersData = await workersResponse.json();
        const recentActivities = workersData.items?.map((worker: any, index: number) => ({
          id: worker.id || index,
          description: `${worker.name} - ${worker.department || '부서미정'}`,
          time: new Date(worker.hire_date).toLocaleDateString() || '날짜미정'
        })) || [];
        setActivities(recentActivities);
      }

    } catch (error) {
      console.error('대시보드 데이터 로드 실패:', error);
      // 에러 발생시 빈 배열 사용
      setActivities([]);
    } finally {
      setLoading(false);
    }
  };
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-50 p-6">
      {/* 헤더 섹션 */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              SafeWork Pro 대시보드
            </h1>
            <p className="text-gray-600 mt-2">건설업 보건관리 시스템 통합 현황</p>
          </div>
          <div className="flex items-center space-x-2 bg-white px-4 py-2 rounded-full shadow-sm">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-sm font-medium text-gray-700">실시간 모니터링</span>
          </div>
        </div>
      </div>
      
      {/* 통계 카드 - 개선된 디자인 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl shadow-lg p-6 text-white transform hover:scale-105 transition-transform duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100 text-sm font-medium">전체 근로자</p>
              <p className="text-3xl font-bold mt-2">
                {loading ? <div className="animate-pulse bg-blue-300 h-8 w-16 rounded"></div> : stats.total_workers}
              </p>
              <div className="flex items-center mt-2">
                <TrendingUp size={16} className="text-blue-200 mr-1" />
                <span className="text-blue-200 text-xs">활성 관리 중</span>
              </div>
            </div>
            <div className="p-3 bg-blue-400 bg-opacity-50 rounded-full">
              <Users size={32} className="text-white" />
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl shadow-lg p-6 text-white transform hover:scale-105 transition-transform duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-purple-100 text-sm font-medium">특수건진 대상</p>
              <p className="text-3xl font-bold mt-2">
                {loading ? <div className="animate-pulse bg-purple-300 h-8 w-16 rounded"></div> : stats.special_exam_targets}
              </p>
              <div className="flex items-center mt-2">
                <Activity size={16} className="text-purple-200 mr-1" />
                <span className="text-purple-200 text-xs">특별 관리</span>
              </div>
            </div>
            <div className="p-3 bg-purple-400 bg-opacity-50 rounded-full">
              <ShieldCheck size={32} className="text-white" />
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl shadow-lg p-6 text-white transform hover:scale-105 transition-transform duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-emerald-100 text-sm font-medium">건진 필요</p>
              <p className="text-3xl font-bold mt-2">
                {loading ? <div className="animate-pulse bg-emerald-300 h-8 w-16 rounded"></div> : stats.health_exam_needed}
              </p>
              <div className="flex items-center mt-2">
                <Calendar size={16} className="text-emerald-200 mr-1" />
                <span className="text-emerald-200 text-xs">예약 대기</span>
              </div>
            </div>
            <div className="p-3 bg-emerald-400 bg-opacity-50 rounded-full">
              <Calendar size={32} className="text-white" />
            </div>
          </div>
        </div>
        
        <div className="bg-gradient-to-br from-red-500 to-red-600 rounded-xl shadow-lg p-6 text-white transform hover:scale-105 transition-transform duration-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-red-100 text-sm font-medium">이달 재해</p>
              <p className="text-3xl font-bold mt-2">
                {loading ? <div className="animate-pulse bg-red-300 h-8 w-16 rounded"></div> : stats.accidents_this_month}
              </p>
              <div className="flex items-center mt-2">
                <Zap size={16} className="text-red-200 mr-1" />
                <span className="text-red-200 text-xs">안전 모니터링</span>
              </div>
            </div>
            <div className="p-3 bg-red-400 bg-opacity-50 rounded-full">
              <AlertTriangle size={32} className="text-white" />
            </div>
          </div>
        </div>
      </div>
      
      {/* 메인 콘텐츠 그리드 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 최근 활동 - 개선된 디자인 */}
        <div className="lg:col-span-2 bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold text-gray-800 flex items-center">
              <FileText className="mr-2 text-blue-600" size={24} />
              최근 활동
            </h2>
            <span className="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium">
              실시간 업데이트
            </span>
          </div>
          <div className="space-y-4">
            {loading ? (
              <div className="space-y-3">
                {[1,2,3].map(i => (
                  <div key={i} className="animate-pulse flex items-center space-x-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                    <div className="flex-1">
                      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2 mt-2"></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : activities.length > 0 ? (
              activities.map((activity) => (
                <div key={activity.id} className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold">
                    {activity.description.charAt(0)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-gray-800 truncate">{activity.description}</p>
                    <p className="text-sm text-gray-500 truncate">{activity.time}</p>
                  </div>
                  <div className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                    완료
                  </div>
                </div>
              ))
            ) : (
              <div className="text-center py-12">
                <Activity className="mx-auto text-gray-400 mb-4" size={48} />
                <p className="text-gray-500 text-lg">활동 내역이 없습니다</p>
                <p className="text-gray-400 text-sm mt-2">새로운 활동이 있을 때 여기에 표시됩니다</p>
              </div>
            )}
          </div>
        </div>
        
        {/* 중요 알림 - 개선된 디자인 */}
        <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-xl shadow-lg p-6 border border-amber-200">
          <div className="flex items-center mb-4">
            <AlertTriangle className="text-amber-600 mr-2" size={24} />
            <h2 className="text-xl font-bold text-amber-800">중요 알림</h2>
          </div>
          <div className="space-y-4">
            <div className="bg-white bg-opacity-70 rounded-lg p-4 border-l-4 border-amber-500">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-amber-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <p className="text-amber-800 font-medium">정기 안전교육</p>
                  <p className="text-amber-700 text-sm mt-1">다음 주 시작 예정</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white bg-opacity-70 rounded-lg p-4 border-l-4 border-blue-500">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-blue-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <p className="text-blue-800 font-medium">작업환경측정</p>
                  <p className="text-blue-700 text-sm mt-1">결과 확인 필요</p>
                </div>
              </div>
            </div>
            
            <div className="bg-white bg-opacity-70 rounded-lg p-4 border-l-4 border-green-500">
              <div className="flex items-start">
                <div className="w-2 h-2 bg-green-500 rounded-full mt-2 mr-3"></div>
                <div>
                  <p className="text-green-800 font-medium">신규 건강검진</p>
                  <p className="text-green-700 text-sm mt-1">예약 완료 요청</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="mt-6 pt-4 border-t border-amber-200">
            <button className="w-full bg-gradient-to-r from-amber-500 to-orange-500 text-white py-2 px-4 rounded-lg hover:from-amber-600 hover:to-orange-600 transition-colors font-medium">
              모든 알림 보기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}