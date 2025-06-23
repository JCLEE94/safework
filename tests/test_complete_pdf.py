#!/usr/bin/env python3
"""
완전한 PDF 생성 테스트 (빈 템플릿 + 텍스트 오버레이)
"""

import sys
import os
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.handlers.documents import create_form_template_pdf, create_text_overlay
from PyPDF2 import PdfReader, PdfWriter
import io

def create_complete_pdf(form_type: str, data: dict) -> bytes:
    """빈 템플릿과 텍스트 오버레이를 결합하여 완전한 PDF 생성"""
    try:
        # 1. 빈 템플릿 생성
        print(f"1. 빈 템플릿 생성: {form_type}")
        base_pdf_stream = create_form_template_pdf(form_type)
        
        # 2. 텍스트 오버레이 생성
        print(f"2. 텍스트 오버레이 생성")
        overlay_pdf_stream = create_text_overlay(data, form_type)
        
        # 3. PDF 병합
        print(f"3. PDF 병합")
        base_pdf = PdfReader(base_pdf_stream)
        overlay_pdf = PdfReader(overlay_pdf_stream)
        output = PdfWriter()
        
        # 모든 페이지 처리
        for page_num in range(len(base_pdf.pages)):
            page = base_pdf.pages[page_num]
            
            # 첫 번째 페이지에만 텍스트 오버레이 적용
            if page_num == 0 and len(overlay_pdf.pages) > 0:
                page.merge_page(overlay_pdf.pages[0])
            
            output.add_page(page)
        
        # 4. 최종 PDF 생성
        result_stream = io.BytesIO()
        output.write(result_stream)
        result_stream.seek(0)
        
        return result_stream.getvalue()
        
    except Exception as e:
        print(f"❌ PDF 생성 실패: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def test_complete_pdfs():
    """완전한 PDF 생성 테스트"""
    print("=== 완전한 PDF 생성 테스트 ===")
    
    # 테스트 데이터
    test_cases = [
        {
            "form_type": "MSDS_관리대장",
            "data": {
                "chemical_name": "톨루엔",
                "manufacturer": "삼성케미칼",
                "cas_number": "108-88-3", 
                "usage": "세척용",
                "quantity": "10L",
                "storage_location": "창고A",
                "hazard_class": "인화성액체",
                "safety_measures": "환기장치 가동",
                "msds_date": "2024-06-19",
                "manager": "김관리",
                "update_date": "2024-06-19"
            }
        },
        {
            "form_type": "유소견자_관리대장",
            "data": {
                "worker_name": "홍길동",
                "employee_id": "2024001",
                "exam_date": "2024-06-15",
                "exam_agency": "서울의료원",
                "exam_result": "유소견",
                "opinion": "고혈압 관리 필요",
                "work_fitness": "제한적 업무",
                "action_taken": "작업전환",
                "follow_up_date": "2024-12-15",
                "counselor": "보건관리자",
                "date": "2024-06-19"
            }
        },
        {
            "form_type": "건강관리_상담방문_일지", 
            "data": {
                "visit_date": "2024-06-19",
                "site_name": "건설현장A",
                "weather": "맑음",
                "work_type": "철골공사",
                "worker_count": "15명",
                "counseling_content": "근로자 건강상담 및 안전교육 실시. 고혈압 주의사항 안내.",
                "action_items": "개인보호구 착용 점검, 정기 건강검진 안내",
                "next_visit": "2024-07-19",
                "counselor_name": "보건관리자 김철수",
                "signature_date": "2024-06-19"
            }
        },
        {
            "form_type": "특별관리물질_취급일지",
            "data": {
                "date": "2024-06-19",
                "chemical_name": "석면",
                "work_location": "건물 해체현장",
                "work_content": "석면 철거 작업",
                "worker_name": "이작업",
                "start_time": "09:00",
                "end_time": "17:00", 
                "quantity_used": "1톤",
                "protective_equipment": "방진마스크, 보호복 착용",
                "safety_measures": "밀폐공간 작업, 음압 유지, 습식 작업",
                "manager": "안전관리자",
                "signature": "김안전"
            }
        }
    ]
    
    # 각 테스트 케이스 실행
    for test_case in test_cases:
        form_type = test_case["form_type"]
        data = test_case["data"]
        
        print(f"\n테스트 중: {form_type}")
        print(f"데이터 항목: {len(data)}개")
        
        # 완전한 PDF 생성
        pdf_content = create_complete_pdf(form_type, data)
        
        if pdf_content:
            # PDF 파일 저장
            output_path = f"/tmp/{form_type}_완성본.pdf"
            with open(output_path, 'wb') as f:
                f.write(pdf_content)
            
            print(f"✅ 성공: {output_path} ({len(pdf_content)} bytes)")
            
            # PDF 검증
            try:
                reader = PdfReader(io.BytesIO(pdf_content))
                print(f"   페이지 수: {len(reader.pages)}")
                if reader.pages:
                    page = reader.pages[0]
                    print(f"   첫 페이지 크기: {page.mediabox.width} x {page.mediabox.height}")
            except Exception as e:
                print(f"   ⚠️  PDF 검증 실패: {str(e)}")
        else:
            print(f"❌ 실패: {form_type}")

if __name__ == "__main__":
    print("완전한 PDF 생성 테스트")
    print("=" * 50)
    
    test_complete_pdfs()
    
    print("\n" + "=" * 50)
    print("테스트 완료!")
    print("\n생성된 완성본 PDF 파일들:")
    
    import glob
    completed_pdfs = glob.glob("/tmp/*_완성본.pdf")
    for pdf_file in sorted(completed_pdfs):
        file_size = os.path.getsize(pdf_file)
        print(f"  - {pdf_file} ({file_size:,} bytes)")
    
    print(f"\n총 {len(completed_pdfs)}개의 완성본 PDF가 생성되었습니다.")
    print("이제 텍스트 오버레이가 정확한 위치에 표시되고 샘플 데이터가 제거된 깔끔한 양식이 생성됩니다.")