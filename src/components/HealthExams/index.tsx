import React, { useState, useEffect } from 'react';
import { Plus, Search, Calendar, FileText, AlertCircle, Edit, Trash2 } from 'lucide-react';
import { Card, Button, Table, Badge } from '../common';
import { HealthExamForm } from './HealthExamForm';
import { useApi } from '../../hooks/useApi';

interface HealthExam {
  id: number;
  worker_id: number;
  worker_name?: string;
  exam_type: string;
  exam_date: string;
  exam_result: string;
  exam_institution?: string;
  doctor_name?: string;
  followup_required?: string;
  next_exam_date?: string;
  notes?: string;
  vital_signs?: any;
  lab_results?: any[];
}

interface ApiResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  size: number;
}

export function HealthExams() {
  const [exams, setExams] = useState<HealthExam[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [formMode, setFormMode] = useState<'create' | 'edit'>('create');
  const [selectedExam, setSelectedExam] = useState<HealthExam | null>(null);
  const { fetchApi } = useApi();

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      setLoading(true);
      const data = await fetchApi<ApiResponse<HealthExam>>('/health-exams');
      setExams(data.items || []);
    } catch (error) {
      console.error('건강진단 목록 조회 실패:', error);
      // 에러 시 빈 배열로 설정
      setExams([]);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setFormMode('create');
    setSelectedExam(null);
    setShowForm(true);
  };

  const handleEdit = (exam: HealthExam) => {
    setFormMode('edit');
    setSelectedExam(exam);
    setShowForm(true);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    
    try {
      await fetchApi(`/health-exams/${id}`, { method: 'DELETE' });
      await loadExams();
    } catch (error) {
      console.error('건강진단 삭제 실패:', error);
    }
  };

  const handleSubmit = async (data: Partial<HealthExam>) => {
    try {
      if (formMode === 'create') {
        await fetchApi('/health-exams', {
          method: 'POST',
          body: JSON.stringify(data)
        });
      } else if (selectedExam) {
        await fetchApi(`/health-exams/${selectedExam.id}`, {
          method: 'PUT',
          body: JSON.stringify(data)
        });
      }
      
      setShowForm(false);
      await loadExams();
    } catch (error) {
      console.error('건강진단 저장 실패:', error);
    }
  };

  const getResultBadgeColor = (result: string) => {
    switch (result) {
      case '정상': case 'NORMAL': return 'bg-green-100 text-green-800';
      case '요관찰': case 'OBSERVATION': return 'bg-yellow-100 text-yellow-800';
      case '유소견': case 'ABNORMAL': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getResultLabel = (result: string) => {
    switch (result) {
      case 'NORMAL': return '정상';
      case 'OBSERVATION': return '요관찰';
      case 'ABNORMAL': return '유소견';
      case 'TREATMENT': return '치료요구';
      default: return result;
    }
  };

  const filteredExams = exams.filter(exam =>
    (exam.worker_name && exam.worker_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
    exam.exam_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">건강진단 관리</h1>
        <Button onClick={handleCreate} className="flex items-center gap-2">
          <Plus className="w-4 h-4" />
          건강진단 등록
        </Button>
      </div>

      {/* 검색 및 필터 */}
      <Card>
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="근로자명 또는 진단유형으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <Button variant="outline" onClick={loadExams}>
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
              <p className="text-sm font-medium text-gray-600">총 건강진단</p>
              <p className="text-2xl font-bold text-gray-900">{exams.length}</p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <div className="w-4 h-4 bg-green-600 rounded-full"></div>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">정상</p>
              <p className="text-2xl font-bold text-green-600">
                {exams.filter(e => e.exam_result === 'NORMAL' || e.exam_result === '정상').length}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-4 h-4 text-yellow-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">요관찰</p>
              <p className="text-2xl font-bold text-yellow-600">
                {exams.filter(e => e.exam_result === 'OBSERVATION' || e.exam_result === '요관찰').length}
              </p>
            </div>
          </div>
        </Card>
        <Card>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
              <AlertCircle className="w-4 h-4 text-red-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">유소견</p>
              <p className="text-2xl font-bold text-red-600">
                {exams.filter(e => e.exam_result === 'ABNORMAL' || e.exam_result === '유소견').length}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* 건강진단 목록 */}
      <Card>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  근로자명
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  진단유형
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  검진일자
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  결과
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  다음 검진일
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  관리
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {loading ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    로딩 중...
                  </td>
                </tr>
              ) : filteredExams.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    건강진단 기록이 없습니다.
                  </td>
                </tr>
              ) : (
                filteredExams.map((exam) => (
                  <tr key={exam.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {exam.worker_name || `근로자 ID: ${exam.worker_id}`}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.exam_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(exam.exam_date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge className={getResultBadgeColor(exam.exam_result)}>
                        {getResultLabel(exam.exam_result)}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.next_exam_date ? new Date(exam.next_exam_date).toLocaleDateString() : '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleEdit(exam)}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          <Edit size={16} />
                        </button>
                        <button
                          onClick={() => handleDelete(exam.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <HealthExamForm
        isOpen={showForm}
        onClose={() => setShowForm(false)}
        onSubmit={handleSubmit}
        initialData={selectedExam}
        mode={formMode}
      />
    </div>
  );
}