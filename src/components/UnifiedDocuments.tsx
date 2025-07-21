import React, { useState } from 'react';
import { API_CONFIG } from '../config/api';

interface Document {
  id: string;
  name: string;
  category: string;
  description: string;
  updatedAt: string;
}

export const UnifiedDocuments: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 문서 카테고리
  const categories = [
    { id: 'all', name: '전체 문서' },
    { id: 'health', name: '건강진단' },
    { id: 'safety', name: '안전관리' },
    { id: 'education', name: '교육관리' },
    { id: 'environment', name: '작업환경' },
    { id: 'accident', name: '사고보고' },
    { id: 'chemical', name: '화학물질' },
    { id: 'legal', name: '법정서식' },
  ];

  // 샘플 문서 목록 (실제로는 API에서 가져와야 함)
  const documents: Document[] = [
    {
      id: '1',
      name: '건강진단 결과표',
      category: 'health',
      description: '근로자 건강진단 결과를 기록하는 문서',
      updatedAt: '2025-01-21',
    },
    {
      id: '2',
      name: '안전교육 이수증',
      category: 'education',
      description: '건설업 기초안전보건교육 이수 확인서',
      updatedAt: '2025-01-20',
    },
    {
      id: '3',
      name: '작업환경 측정 보고서',
      category: 'environment',
      description: '소음, 분진, 유해물질 측정 결과 보고서',
      updatedAt: '2025-01-19',
    },
    {
      id: '4',
      name: '산업재해 조사표',
      category: 'accident',
      description: '산업재해 발생 시 작성하는 조사 양식',
      updatedAt: '2025-01-18',
    },
    {
      id: '5',
      name: 'MSDS 관리대장',
      category: 'chemical',
      description: '물질안전보건자료 관리 대장',
      updatedAt: '2025-01-17',
    },
  ];

  // 필터링된 문서 목록
  const filteredDocuments = documents.filter(doc => {
    const matchesCategory = selectedCategory === 'all' || doc.category === selectedCategory;
    const matchesSearch = doc.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         doc.description.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const handleDownload = async (documentId: string, documentName: string) => {
    try {
      // 실제로는 API를 통해 문서를 다운로드해야 함
      console.log(`Downloading document: ${documentName}`);
      alert(`"${documentName}" 문서 다운로드 기능은 준비 중입니다.`);
    } catch (error) {
      console.error('문서 다운로드 오류:', error);
      alert('문서 다운로드 중 오류가 발생했습니다.');
    }
  };

  return (
    <div className="p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">통합 문서 관리</h1>
        <p className="text-gray-600">건설현장 보건관리에 필요한 모든 문서를 한 곳에서 관리합니다.</p>
      </div>

      {/* 검색 및 필터 */}
      <div className="mb-6 bg-white p-4 rounded-lg shadow">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="문서명 또는 설명으로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="flex gap-2 flex-wrap">
            {categories.map(category => (
              <button
                key={category.id}
                onClick={() => setSelectedCategory(category.id)}
                className={`px-4 py-2 rounded-md transition-colors ${
                  selectedCategory === category.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {category.name}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* 문서 목록 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredDocuments.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            검색 결과가 없습니다.
          </div>
        ) : (
          filteredDocuments.map(doc => (
            <div key={doc.id} className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{doc.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{doc.description}</p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  doc.category === 'health' ? 'bg-green-100 text-green-800' :
                  doc.category === 'safety' ? 'bg-red-100 text-red-800' :
                  doc.category === 'education' ? 'bg-blue-100 text-blue-800' :
                  doc.category === 'environment' ? 'bg-yellow-100 text-yellow-800' :
                  doc.category === 'accident' ? 'bg-orange-100 text-orange-800' :
                  doc.category === 'chemical' ? 'bg-purple-100 text-purple-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {categories.find(c => c.id === doc.category)?.name}
                </span>
              </div>
              
              <div className="flex items-center justify-between mt-4">
                <span className="text-xs text-gray-500">
                  최종 수정: {new Date(doc.updatedAt).toLocaleDateString('ko-KR')}
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleDownload(doc.id, doc.name)}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                  >
                    다운로드
                  </button>
                  <button
                    className="px-3 py-1 text-sm bg-gray-600 text-white rounded hover:bg-gray-700 transition-colors"
                  >
                    미리보기
                  </button>
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {/* 추가 기능 안내 */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">📋 통합 문서 관리 기능</h3>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• 모든 보건관리 문서를 카테고리별로 정리</li>
          <li>• 빠른 검색 및 필터링 기능</li>
          <li>• 문서 다운로드 및 미리보기</li>
          <li>• 자동 문서 생성 및 업데이트 (준비 중)</li>
        </ul>
      </div>
    </div>
  );
};