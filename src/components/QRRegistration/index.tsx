/**
 * QR코드 근로자 등록 관리 컴포넌트
 * 
 * 이 컴포넌트는 QR코드를 통한 근로자 등록 시스템을 관리합니다.
 * - QR코드 생성 및 표시
 * - 등록 토큰 관리
 * - 등록 상태 모니터링
 * - 등록 이력 추적
 * 
 * 외부 라이브러리:
 * - React: UI 컴포넌트 (https://reactjs.org/)
 * - axios: HTTP 클라이언트 (https://axios-http.com/)
 * 
 * 예시 입력:
 * - 근로자 정보: {name: "홍길동", employee_id: "EMP001", department: "건설부"}
 * - 부서: "건설부"
 * - 직책: "현장관리자"
 * 
 * 예시 출력:
 * - QR코드 이미지 (base64 인코딩)
 * - 등록 토큰 정보
 * - 등록 상태 및 진행 상황
 */

import React, { useState, useEffect } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';

const QRRegistration: React.FC = () => {
  const [commonQRImage, setCommonQRImage] = useState<string>('');

  // 데이터 로드
  useEffect(() => {
    loadCommonQR();
  }, []);

  const loadCommonQR = async () => {
    try {
      const response = await fetch('/api/v1/common-qr/generate?size=300', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });
      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setCommonQRImage(url);
      }
    } catch (err) {
      console.error('공통 QR 로드 실패:', err);
    }
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">QR코드</h1>
      </div>

      {/* 공통 QR 코드 표시 */}
      <Card className="p-6">
        <div className="text-center">
          <h2 className="text-lg font-semibold mb-4">근로자 등록 QR 코드</h2>
          {commonQRImage ? (
            <div className="inline-block p-4 bg-white border-2 border-gray-200 rounded-lg">
              <img 
                src={commonQRImage} 
                alt="근로자 등록 QR 코드" 
                className="max-w-xs mx-auto"
              />
            </div>
          ) : (
            <div className="inline-block p-8 bg-gray-100 rounded-lg">
              <p className="text-gray-500">QR 코드 로딩 중...</p>
            </div>
          )}
          
          <div className="mt-6 space-y-2">
            <p className="text-sm text-gray-600">
              이 QR 코드를 스캔하면 근로자 등록 페이지로 이동합니다
            </p>
            <p className="text-xs text-gray-500">
              등록 URL: {window.location.origin}/register-qr
            </p>
          </div>

          <div className="mt-6 flex justify-center space-x-4">
            <Button
              onClick={() => {
                const link = document.createElement('a');
                link.href = commonQRImage;
                link.download = `safework_qr_${new Date().toISOString().split('T')[0]}.png`;
                link.click();
              }}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={!commonQRImage}
            >
              QR 코드 다운로드
            </Button>
            <Button
              onClick={() => window.print()}
              className="bg-gray-600 hover:bg-gray-700"
            >
              인쇄
            </Button>
          </div>
        </div>
      </Card>


    </div>
  );
};

export default QRRegistration;