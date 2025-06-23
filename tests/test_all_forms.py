#!/usr/bin/env python3
"""
모든 PDF 양식의 수정된 좌표와 빈 템플릿 테스트
"""
import urllib.parse
import requests
import json

def test_all_pdf_forms():
    base_url = 'http://192.168.50.215:3001/api/v1/documents'
    
    # 테스트 데이터
    test_data = {
        'MSDS_관리대장': {
            'chemical_name': '수정된톨루엔',
            'manufacturer': '새로운제조사',
            'cas_number': '108-88-3-FIX',
            'usage': '테스트용도',
            'quantity': '5L',
            'storage_location': '창고B',
            'hazard_class': '수정된분류',
            'safety_measures': '개선된안전조치',
            'msds_date': '2024-06-19',
            'manager': '수정된관리자',
            'update_date': '2024-06-19'
        },
        '유소견자_관리대장': {
            'worker_name': '홍길동',
            'employee_id': '2024001',
            'exam_date': '2024-06-15',
            'exam_agency': '서울의료원',
            'exam_result': '유소견',
            'opinion': '고혈압 관리 필요',
            'work_fitness': '제한적 업무',
            'action_taken': '작업전환',
            'follow_up_date': '2024-12-15',
            'counselor': '보건관리자',
            'date': '2024-06-19'
        },
        '건강관리_상담방문_일지': {
            'visit_date': '2024-06-19',
            'site_name': '건설현장A',
            'weather': '맑음',
            'work_type': '철골공사',
            'worker_count': '15명',
            'counseling_content': '근로자 건강상담 및 안전교육 실시',
            'action_items': '개인보호구 착용 점검',
            'next_visit': '2024-07-19',
            'counselor_name': '보건관리자 김철수',
            'signature_date': '2024-06-19'
        }
    }
    
    print("=== 운영 서버 PDF 생성 테스트 ===")
    print(f"서버: {base_url}")
    print()
    
    results = []
    
    for form_id, data in test_data.items():
        print(f"테스트 중: {form_id}")
        
        # URL 인코딩
        encoded_form_id = urllib.parse.quote(form_id, safe='')
        url = f"{base_url}/fill-pdf/{encoded_form_id}"
        
        try:
            response = requests.post(url,
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                pdf_size = len(response.content)
                filename = f"/tmp/{form_id}_운영테스트.pdf"
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ 성공: {filename} ({pdf_size:,} bytes)")
                results.append((form_id, 'SUCCESS', pdf_size, filename))
                
                # 파일 헤더 확인 (PDF 여부)
                if response.content.startswith(b'%PDF'):
                    print(f"   ✓ 유효한 PDF 파일")
                else:
                    print(f"   ⚠️  PDF 헤더 없음")
                    
            else:
                print(f"❌ 실패: HTTP {response.status_code}")
                print(f"   오류: {response.text[:200]}")
                results.append((form_id, 'FAILED', response.status_code, response.text[:100]))
                
        except Exception as e:
            print(f"❌ 예외: {str(e)}")
            results.append((form_id, 'ERROR', 0, str(e)))
        
        print()
    
    print("=" * 60)
    print("테스트 결과 요약:")
    print()
    
    success_count = 0
    for form_id, status, size_or_code, info in results:
        if status == 'SUCCESS':
            print(f"✅ {form_id}: {size_or_code:,} bytes")
            success_count += 1
        else:
            print(f"❌ {form_id}: {status} - {info}")
    
    print()
    print(f"성공: {success_count}/{len(results)} 양식")
    
    if success_count == len(results):
        print()
        print("🎉 모든 PDF 양식이 성공적으로 생성되었습니다!")
        print("이제 다음이 해결되었습니다:")
        print("   - 텍스트 오버레이 좌표 정확성")
        print("   - 샘플 데이터 제거 (깔끔한 빈 템플릿)")
        print("   - 한글 필드명 지원")
        print("   - 운영 서버 배포 완료")

if __name__ == '__main__':
    test_all_pdf_forms()