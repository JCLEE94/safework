import React, { useState, useEffect } from 'react';
import { Plus, Search, Calendar, FileText, AlertCircle } from 'lucide-react';
import { Card, Button, Table, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

interface HealthExam {
  id: number;
  worker_name: string;
  exam_type: string;
  exam_date: string;
  result: string;
  notes?: string;
  next_exam_date?: string;
}

export function HealthExams() {
  const [exams, setExams] = useState<HealthExam[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const { fetchApi } = useApi();

  useEffect(() => {
    loadExams();
  }, []);

  const loadExams = async () => {
    try {
      setLoading(true);
      // 임시 더미 데이터 (실제 API 연결 시 제거)
      const dummyData = [
        {
          id: 1,
          worker_name: "김철수",
          exam_type: "일반건강진단",
          exam_date: "2024-03-15",
          result: "정상",
          notes: "특이사항 없음",
          next_exam_date: "2025-03-15"
        },
        {
          id: 2,
          worker_name: "이영희",
          exam_type: "특수건강진단",
          exam_date: "2024-02-20",
          result: "요관찰",
          notes: "혈압 관리 필요",
          next_exam_date: "2024-08-20"
        }
      ];
      setExams(dummyData);
    } catch (error) {
      console.error('건강진단 목록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const getResultBadgeColor = (result: string) => {
    switch (result) {
      case '정상': return 'bg-green-100 text-green-800';
      case '요관찰': return 'bg-yellow-100 text-yellow-800';
      case '유소견': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const filteredExams = exams.filter(exam =>
    exam.worker_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    exam.exam_type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">건강진단 관리</h1>
        <Button onClick={() => {}} className="flex items-center gap-2">
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
                {exams.filter(e => e.result === '정상').length}
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
                {exams.filter(e => e.result === '요관찰').length}
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
                {exams.filter(e => e.result === '유소견').length}
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
                  비고
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
                      {exam.worker_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.exam_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.exam_date}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Badge className={getResultBadgeColor(exam.result)}>
                        {exam.result}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.next_exam_date || '-'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {exam.notes || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}