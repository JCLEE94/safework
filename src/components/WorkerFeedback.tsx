import React, { useState, useEffect } from 'react';
import { API_CONFIG } from '../config/api';

interface Feedback {
  id: number;
  worker_id: number;
  content: string;
  photo_url?: string;
  created_by?: string;
  created_at: string;
  updated_at: string;
}

interface WorkerFeedbackProps {
  workerId: number;
  workerName?: string;
}

export const WorkerFeedback: React.FC<WorkerFeedbackProps> = ({ workerId, workerName }) => {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    content: '',
    photo: null as File | null,
  });

  // 피드백 목록 조회
  const fetchFeedbacks = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_CONFIG.BASE_URL}/worker-feedbacks/worker/${workerId}`);
      if (response.ok) {
        const data = await response.json();
        setFeedbacks(data.items);
      }
    } catch (error) {
      console.error('피드백 조회 오류:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFeedbacks();
  }, [workerId]);

  // 피드백 제출
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const formDataToSend = new FormData();
    formDataToSend.append('worker_id', workerId.toString());
    formDataToSend.append('content', formData.content);
    if (formData.photo) {
      formDataToSend.append('photo', formData.photo);
    }

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}/worker-feedbacks/`, {
        method: 'POST',
        body: formDataToSend,
      });
      
      if (response.ok) {
        alert('피드백이 등록되었습니다.');
        setFormData({ content: '', photo: null });
        setShowForm(false);
        fetchFeedbacks();
      } else {
        alert('피드백 등록에 실패했습니다.');
      }
    } catch (error) {
      console.error('피드백 등록 오류:', error);
      alert('피드백 등록 중 오류가 발생했습니다.');
    }
  };

  // 파일 선택 처리
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFormData({ ...formData, photo: e.target.files[0] });
    }
  };

  return (
    <div className="mt-6 bg-white p-6 rounded-lg shadow-md">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">
          피드백 {workerName && `- ${workerName}`}
        </h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
        >
          {showForm ? '취소' : '피드백 작성'}
        </button>
      </div>

      {/* 피드백 작성 폼 */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg">
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              피드백 내용 <span className="text-red-500">*</span>
            </label>
            <textarea
              value={formData.content}
              onChange={(e) => setFormData({ ...formData, content: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              required
              placeholder="피드백 내용을 입력하세요..."
            />
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              사진 첨부
            </label>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileChange}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {formData.photo && (
              <p className="mt-2 text-sm text-gray-600">
                선택된 파일: {formData.photo.name}
              </p>
            )}
          </div>

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition-colors"
            >
              취소
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
            >
              제출
            </button>
          </div>
        </form>
      )}

      {/* 피드백 목록 */}
      <div className="space-y-4">
        {loading ? (
          <p className="text-center text-gray-500">로딩 중...</p>
        ) : feedbacks.length === 0 ? (
          <p className="text-center text-gray-500">등록된 피드백이 없습니다.</p>
        ) : (
          feedbacks.map((feedback) => (
            <div key={feedback.id} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <div className="text-sm text-gray-600">
                  작성자: {feedback.created_by || '시스템'}
                </div>
                <div className="text-sm text-gray-500">
                  {new Date(feedback.created_at).toLocaleString('ko-KR')}
                </div>
              </div>
              
              <p className="text-gray-800 mb-2 whitespace-pre-wrap">{feedback.content}</p>
              
              {feedback.photo_url && (
                <div className="mt-2">
                  <img
                    src={`${API_CONFIG.BASE_URL}${feedback.photo_url}`}
                    alt="첨부 사진"
                    className="max-w-xs rounded-lg cursor-pointer hover:opacity-90"
                    onClick={() => window.open(`${API_CONFIG.BASE_URL}${feedback.photo_url}`, '_blank')}
                  />
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};