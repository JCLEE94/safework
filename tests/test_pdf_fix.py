#!/usr/bin/env python3
"""
PDF 좌표 수정 및 빈 템플릿 테스트 스크립트
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import io
from datetime import datetime

# 필요한 모듈 import
from src.handlers.documents import (PDF_FORM_COORDINATES,
                                    create_form_template_pdf,
                                    create_text_overlay, fill_pdf_form)


def test_blank_template():
    """빈 템플릿 PDF 생성 테스트"""
    print("=== 빈 템플릿 PDF 생성 테스트 ===")

    forms = [
        "유소견자_관리대장",
        "MSDS_관리대장",
        "건강관리_상담방문_일지",
        "특별관리물질_취급일지",
    ]

    for form_id in forms:
        print(f"테스트 중: {form_id}")
        try:
            pdf_stream = create_form_template_pdf(form_id)
            pdf_content = pdf_stream.getvalue()

            # PDF 파일 저장
            output_path = f"/tmp/{form_id}_blank_template.pdf"
            with open(output_path, "wb") as f:
                f.write(pdf_content)

            print(f"✅ 성공: {output_path} ({len(pdf_content)} bytes)")

        except Exception as e:
            print(f"❌ 실패: {form_id} - {str(e)}")

    print()


def test_text_overlay():
    """텍스트 오버레이 좌표 테스트"""
    print("=== 텍스트 오버레이 좌표 테스트 ===")

    # MSDS 관리대장 테스트 데이터
    msds_data = {
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
        "update_date": "2024-06-19",
    }

    # 유소견자 관리대장 테스트 데이터
    worker_data = {
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
        "date": "2024-06-19",
    }

    test_cases = [("MSDS_관리대장", msds_data), ("유소견자_관리대장", worker_data)]

    for form_type, data in test_cases:
        print(f"테스트 중: {form_type}")
        try:
            # 1. 빈 템플릿 생성
            base_pdf = create_form_template_pdf(form_type)

            # 2. 텍스트 오버레이 생성
            overlay_pdf = create_text_overlay(data, form_type)

            # 3. 병합된 PDF 생성 (간단 버전)
            # 실제로는 PyPDF2로 병합하지만, 여기서는 오버레이만 저장
            overlay_content = overlay_pdf.getvalue()

            # 오버레이 PDF 저장
            overlay_path = f"/tmp/{form_type}_overlay_test.pdf"
            with open(overlay_path, "wb") as f:
                f.write(overlay_content)

            print(f"✅ 오버레이 성공: {overlay_path} ({len(overlay_content)} bytes)")

            # 좌표 정보 출력
            if form_type in PDF_FORM_COORDINATES:
                coords = PDF_FORM_COORDINATES[form_type]
                print(f"   좌표 정보: {len(coords)}개 필드")
                for field, (x, y) in coords.items():
                    if field in data:
                        print(f"     {field}: ({x}, {y}) = '{data[field]}'")

        except Exception as e:
            print(f"❌ 실패: {form_type} - {str(e)}")
            import traceback

            traceback.print_exc()

    print()


def test_pdf_coordinates():
    """PDF 좌표 시스템 검증"""
    print("=== PDF 좌표 시스템 검증 ===")

    for form_type, coordinates in PDF_FORM_COORDINATES.items():
        print(f"양식: {form_type}")
        print(f"  필드 수: {len(coordinates)}")

        # 좌표 범위 체크 (A4 크기: 595.27 x 841.89)
        valid_coords = 0
        for field, (x, y) in coordinates.items():
            if 0 <= x <= 595 and 0 <= y <= 842:
                valid_coords += 1
            else:
                print(f"    ⚠️  범위 초과: {field} ({x}, {y})")

        print(f"  유효한 좌표: {valid_coords}/{len(coordinates)}")

        # Y 좌표 분포 (위에서 아래로)
        y_coords = [y for x, y in coordinates.values()]
        if y_coords:
            print(f"  Y 좌표 범위: {min(y_coords)} ~ {max(y_coords)}")

    print()


if __name__ == "__main__":
    print("PDF 좌표 수정 및 샘플 데이터 제거 테스트")
    print("=" * 50)

    # 1. 빈 템플릿 생성 테스트
    test_blank_template()

    # 2. 텍스트 오버레이 좌표 테스트
    test_text_overlay()

    # 3. 좌표 시스템 검증
    test_pdf_coordinates()

    print("테스트 완료! /tmp/ 디렉토리에서 생성된 PDF 파일들을 확인하세요.")
    print()
    print("생성된 파일들:")
    import glob

    pdf_files = glob.glob("/tmp/*_test.pdf") + glob.glob("/tmp/*_template.pdf")
    for pdf_file in sorted(pdf_files):
        file_size = os.path.getsize(pdf_file)
        print(f"  - {pdf_file} ({file_size} bytes)")
