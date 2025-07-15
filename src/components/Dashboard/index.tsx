import React from 'react';
import { Users, ShieldCheck, Calendar, AlertTriangle } from 'lucide-react';
import { Bar, Doughnut, Line } from 'react-chartjs-2';
import { StatCard } from './StatCard';
import { Card } from '../common';
import { DashboardData } from '../../types';

interface DashboardProps {
  data: DashboardData | null;
  loading: boolean;
}

export function Dashboard({ data, loading }: DashboardProps) {
  if (loading || !data) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }
  
  // 차트 데이터 준비
  const employmentChartData = {
    labels: Object.values(data.employment_type_distribution).map(item => item.label),
    datasets: [{
      label: '인원',
      data: Object.values(data.employment_type_distribution).map(item => item.count),
      backgroundColor: ['#3B82F6', '#8B5CF6', '#10B981', '#F59E0B'],
    }]
  };
  
  const healthStatusChartData = {
    labels: Object.values(data.health_status_distribution).map(item => item.label),
    datasets: [{
      data: Object.values(data.health_status_distribution).map(item => item.count),
      backgroundColor: ['#10B981', '#F59E0B', '#F97316', '#EF4444'],
    }]
  };
  
  // TODO: Replace with actual monthly trend data from API
  const monthlyTrendData = {
    labels: ['1월', '2월', '3월', '4월', '5월', '6월'],
    datasets: [{
      label: '건강검진',
      data: data.monthly_trend || [],
      borderColor: '#3B82F6',
      backgroundColor: 'rgba(59, 130, 246, 0.1)',
      fill: true,
    }]
  };
  
  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-bold text-gray-800">대시보드</h1>
      
      {/* 통계 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="전체 근로자"
          value={data.total_workers}
          icon={<Users size={24} className="text-blue-600" />}
          trend={{ value: 5, isUp: true }}
          color="bg-blue-600"
        />
        <StatCard
          title="특수건진 대상"
          value={data.special_exam_targets}
          icon={<ShieldCheck size={24} className="text-purple-600" />}
          color="bg-purple-600"
        />
        <StatCard
          title="건진 필요"
          value={data.health_exam_needed}
          icon={<Calendar size={24} className="text-green-600" />}
          trend={{ value: 12, isUp: false }}
          color="bg-green-600"
        />
        <StatCard
          title="이달 재해"
          value={data.accidents_this_month || 0}
          icon={<AlertTriangle size={24} className="text-red-600" />}
          color="bg-red-600"
        />
      </div>
      
      {/* 차트 섹션 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card title="고용형태 분포" className="lg:col-span-1">
          <Bar 
            data={employmentChartData} 
            options={{ 
              responsive: true,
              plugins: {
                legend: { display: false }
              }
            }} 
          />
        </Card>
        
        <Card title="건강상태 현황" className="lg:col-span-1">
          <Doughnut 
            data={healthStatusChartData}
            options={{
              responsive: true,
              plugins: {
                legend: { position: 'bottom' as const }
              }
            }}
          />
        </Card>
        
        <Card title="월별 건강검진 추이" className="lg:col-span-1">
          <Line
            data={monthlyTrendData}
            options={{
              responsive: true,
              plugins: {
                legend: { display: false }
              },
              scales: {
                y: { beginAtZero: true }
              }
            }}
          />
        </Card>
      </div>
      
      {/* 부서별 현황 */}
      {data.by_department && Object.keys(data.by_department).length > 0 && (
        <Card title="부서별 인원 현황">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(data.by_department).map(([dept, count]) => (
              <div key={dept} className="text-center">
                <p className="text-2xl font-bold text-gray-800">{count}</p>
                <p className="text-sm text-gray-600">{dept}</p>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}