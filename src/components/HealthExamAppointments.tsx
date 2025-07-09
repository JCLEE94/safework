import React, { useState, useEffect } from 'react';
import { Calendar, Clock, Phone, MapPin, AlertCircle, CheckCircle, XCircle, Plus, Bell } from 'lucide-react';
import DataTable from './DataTable';

interface Appointment {
  id: number;
  worker_id: number;
  worker_name: string;
  worker_employee_number: string;
  exam_type: string;
  scheduled_date: string;
  scheduled_time: string;
  medical_institution: string;
  institution_address: string;
  institution_phone: string;
  status: string;
  reminder_sent: boolean;
  special_instructions: string;
}

interface AppointmentStats {
  total_scheduled: number;
  total_confirmed: number;
  total_completed: number;
  total_cancelled: number;
  total_no_show: number;
  upcoming_7_days: number;
  upcoming_30_days: number;
  overdue: number;
  completion_rate: number;
  no_show_rate: number;
}

export const HealthExamAppointments = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [stats, setStats] = useState<AppointmentStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAppointment, setSelectedAppointment] = useState<Appointment | null>(null);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    fetchAppointments();
    fetchStatistics();
  }, [filter]);

  const fetchAppointments = async () => {
    try {
      const params = new URLSearchParams();
      if (filter !== 'all') {
        params.append('status', filter);
      }
      
      const response = await fetch(`/api/v1/health-exam-appointments?${params}`);
      const data = await response.json();
      setAppointments(data.items || []);
    } catch (error) {
      console.error('Failed to fetch appointments:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch('/api/v1/health-exam-appointments/statistics');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch statistics:', error);
    }
  };

  const handleStatusUpdate = async (appointmentId: number, newStatus: string) => {
    try {
      const response = await fetch(`/api/v1/health-exam-appointments/${appointmentId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus })
      });
      
      if (response.ok) {
        fetchAppointments();
        fetchStatistics();
      }
    } catch (error) {
      console.error('Failed to update status:', error);
    }
  };

  const handleSendReminders = async () => {
    try {
      const response = await fetch('/api/v1/health-exam-appointments/reminders/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ days_before: 3 })
      });
      
      if (response.ok) {
        const data = await response.json();
        alert(`${data.appointment_count}건의 알림을 발송했습니다.`);
        fetchAppointments();
      }
    } catch (error) {
      console.error('Failed to send reminders:', error);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'scheduled':
        return <Calendar className="h-4 w-4 text-blue-500" />;
      case 'confirmed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-gray-500" />;
      case 'cancelled':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'no_show':
        return <AlertCircle className="h-4 w-4 text-orange-500" />;
      default:
        return null;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      scheduled: '예약됨',
      confirmed: '확정됨',
      completed: '완료됨',
      cancelled: '취소됨',
      no_show: '미참석',
      rescheduled: '일정변경'
    };
    return labels[status] || status;
  };

  const columns = [
    {
      header: '상태',
      accessor: 'status',
      render: (value: string) => (
        <div className="flex items-center gap-2">
          {getStatusIcon(value)}
          <span className="text-sm">{getStatusLabel(value)}</span>
        </div>
      )
    },
    {
      header: '근로자',
      accessor: 'worker_name',
      render: (value: string, row: Appointment) => (
        <div>
          <div className="font-medium">{value}</div>
          <div className="text-sm text-gray-500">{row.worker_employee_number}</div>
        </div>
      )
    },
    {
      header: '검진유형',
      accessor: 'exam_type'
    },
    {
      header: '예약일시',
      accessor: 'scheduled_date',
      render: (value: string, row: Appointment) => (
        <div className="flex items-center gap-2">
          <Calendar className="h-4 w-4 text-gray-400" />
          <span>{new Date(value).toLocaleDateString('ko-KR')}</span>
          {row.scheduled_time && (
            <>
              <Clock className="h-4 w-4 text-gray-400 ml-2" />
              <span>{row.scheduled_time}</span>
            </>
          )}
        </div>
      )
    },
    {
      header: '검진기관',
      accessor: 'medical_institution',
      render: (value: string, row: Appointment) => (
        <div>
          <div className="font-medium">{value}</div>
          {row.institution_phone && (
            <div className="text-sm text-gray-500 flex items-center gap-1 mt-1">
              <Phone className="h-3 w-3" />
              {row.institution_phone}
            </div>
          )}
        </div>
      )
    },
    {
      header: '알림',
      accessor: 'reminder_sent',
      render: (value: boolean) => (
        <div className="flex items-center gap-1">
          <Bell className={`h-4 w-4 ${value ? 'text-green-500' : 'text-gray-400'}`} />
          <span className="text-sm">{value ? '발송됨' : '미발송'}</span>
        </div>
      )
    },
    {
      header: '작업',
      accessor: 'id',
      render: (value: number, row: Appointment) => (
        <div className="flex gap-2">
          {row.status === 'scheduled' && (
            <button
              onClick={() => handleStatusUpdate(value, 'confirmed')}
              className="text-sm text-green-600 hover:text-green-800"
            >
              확정
            </button>
          )}
          {row.status === 'confirmed' && (
            <button
              onClick={() => handleStatusUpdate(value, 'completed')}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              완료
            </button>
          )}
          {(row.status === 'scheduled' || row.status === 'confirmed') && (
            <button
              onClick={() => handleStatusUpdate(value, 'cancelled')}
              className="text-sm text-red-600 hover:text-red-800"
            >
              취소
            </button>
          )}
        </div>
      )
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">건강진단 예약 관리</h1>
        <div className="flex gap-3">
          <button
            onClick={handleSendReminders}
            className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
          >
            <Bell className="h-4 w-4 mr-2" />
            알림 발송
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            <Plus className="h-4 w-4 mr-2" />
            예약 추가
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">7일 이내 예약</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.upcoming_7_days}</p>
              </div>
              <Calendar className="h-8 w-8 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">확정된 예약</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.total_confirmed}</p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">완료율</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.completion_rate.toFixed(1)}%</p>
              </div>
              <CheckCircle className="h-8 w-8 text-gray-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">미참석률</p>
                <p className="text-2xl font-semibold text-gray-900">{stats.no_show_rate.toFixed(1)}%</p>
              </div>
              <AlertCircle className="h-8 w-8 text-orange-500" />
            </div>
          </div>
        </div>
      )}

      {/* 필터 탭 */}
      <div className="bg-white rounded-lg shadow">
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            {['all', 'scheduled', 'confirmed', 'completed', 'cancelled'].map((status) => (
              <button
                key={status}
                onClick={() => setFilter(status)}
                className={`whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm ${
                  filter === status
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {status === 'all' ? '전체' : getStatusLabel(status)}
              </button>
            ))}
          </nav>
        </div>

        {/* 예약 목록 */}
        <div className="p-6">
          <DataTable
            columns={columns}
            data={appointments}
            sortable
            searchable
            searchPlaceholder="근로자명, 검진기관 검색..."
          />
        </div>
      </div>

      {/* 예약 생성 모달 (실제 구현 시 추가) */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center">
          <div className="bg-white rounded-lg p-6 max-w-md w-full">
            <h3 className="text-lg font-medium text-gray-900 mb-4">새 예약 추가</h3>
            <p className="text-sm text-gray-600">예약 생성 폼이 여기에 구현됩니다.</p>
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md"
              >
                닫기
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};