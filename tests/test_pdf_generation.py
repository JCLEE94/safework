#!/usr/bin/env python3
"""PDF 생성 테스트 스크립트"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.handlers.documents import _generate_pdf_content, FORM_TEMPLATES

async def test_pdf_generation():
    """PDF 생성 테스트"""
    # 테스트할 양식 ID
    test_forms = ["health_consultation_log", "msds_management_log", "abnormal_findings_log"]
    
    for form_id in test_forms:
        if form_id in FORM_TEMPLATES:
            print(f"\n{'='*50}")
            print(f"Testing form: {form_id}")
            print(f"Form name: {FORM_TEMPLATES[form_id]['name']}")
            
            # 테스트 데이터
            test_data = {
                "company_name": "테스트 건설",
                "worker_name": "홍길동",
                "date": "2025-07-03",
                "department": "안전관리팀",
                "manager": "김관리",
                "chemical_name": "시멘트",
                "visit_date": "2025-07-03",
                "site_name": "테스트 현장",
                "counselor": "이상담"
            }
            
            try:
                # PDF 생성
                pdf_content = await _generate_pdf_content(form_id, test_data)
                
                if pdf_content:
                    print(f"✓ PDF generated successfully, size: {len(pdf_content)} bytes")
                    
                    # 파일로 저장 (테스트용)
                    output_file = f"test_{form_id}.pdf"
                    with open(output_file, 'wb') as f:
                        f.write(pdf_content)
                    print(f"✓ Saved to {output_file}")
                else:
                    print(f"✗ PDF generation failed - no content returned")
                    
            except Exception as e:
                print(f"✗ Error generating PDF: {str(e)}")
                import traceback
                traceback.print_exc()

if __name__ == "__main__":
    print("Starting PDF generation test...")
    asyncio.run(test_pdf_generation())
    print("\nTest complete!")