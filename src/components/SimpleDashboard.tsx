import React, { useState, useEffect } from 'react';
import { Users, ShieldCheck, Calendar, AlertTriangle } from 'lucide-react';

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
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">SafeWork Pro 대시보드</h1>
      
      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-blue-100">
              <Users size={24} className="text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">전체 근로자</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.total_workers}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-purple-100">
              <ShieldCheck size={24} className="text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">특수건진 대상</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.special_exam_targets}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-green-100">
              <Calendar size={24} className="text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">건진 필요</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.health_exam_needed}
              </p>
            </div>
          </div>
        </div>
        
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="p-3 rounded-full bg-red-100">
              <AlertTriangle size={24} className="text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">이달 재해</p>
              <p className="text-2xl font-bold text-gray-900">
                {loading ? '...' : stats.accidents_this_month}
              </p>
            </div>
          </div>
        </div>
      </div>
      
      {/* 최근 활동 */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-800 mb-4">최근 활동</h2>
        <div className="space-y-3">
          {loading ? (
            <div className="text-gray-500">로딩 중...</div>
          ) : activities.length > 0 ? (
            activities.map((activity) => (
              <div key={activity.id} className="flex items-center justify-between py-2 border-b">
                <span className="text-gray-600">{activity.description}</span>
                <span className="text-sm text-gray-500">{activity.time}</span>
              </div>
            ))
          ) : (
            <div className="text-gray-500">활동 내역이 없습니다.</div>
          )}
        </div>
      </div>
      
      {/* 알림 */}
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-yellow-800 mb-4">중요 알림</h2>
        <div className="space-y-2">
          <p className="text-yellow-700">• 3월 정기 안전교육이 다음 주 시작됩니다.</p>
          <p className="text-yellow-700">• 작업환경측정 결과 확인이 필요합니다.</p>
          <p className="text-yellow-700">• 신규 입사자 건강검진 예약을 완료해주세요.</p>
        </div>
      </div>
    </div>
  );
}