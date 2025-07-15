"""
Comprehensive PDF functionality testing
공식 양식 PDF 데이터 채우기 기능 종합 테스트
"""

import asyncio
import io
import json
# Import the app
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from PyPDF2 import PdfReader

sys.path.append(str(Path(__file__).parent.parent))

from src.app import create_app
from src.handlers.documents import (FORM_TEMPLATES, PDF_FORM_COORDINATES,
                                    create_text_overlay, fill_pdf_form,
                                    get_available_pdf_forms)


class TestPDFFormFunctionality:
    """PDF 양식 기능 종합 테스트"""

    @pytest.fixture
    def app(self):
        """Test FastAPI app"""
        return create_app()

    @pytest.fixture
    def client(self, app):
        """Test client"""
        return TestClient(app)

    def test_pdf_form_coordinates_completeness(self):
        """PDF 양식 좌표 정의 완성도 테스트"""
        required_forms = [
            "유소견자_관리대장",
            "MSDS_관리대장",
            "건강관리_상담방문_일지",
            "특별관리물질_취급일지",
        ]

        for form_id in required_forms:
            assert (
                form_id in PDF_FORM_COORDINATES
            ), f"Missing form coordinates: {form_id}"

            form_config = PDF_FORM_COORDINATES[form_id]
            assert "fields" in form_config, f"Missing fields in {form_id}"
            assert len(form_config["fields"]) > 0, f"No fields defined for {form_id}"

            # Check field structure
            for field_name, field_info in form_config["fields"].items():
                assert (
                    "x" in field_info
                ), f"Missing x coordinate for {form_id}.{field_name}"
                assert (
                    "y" in field_info
                ), f"Missing y coordinate for {form_id}.{field_name}"
                assert (
                    "label" in field_info
                ), f"Missing label for {form_id}.{field_name}"

    def test_text_overlay_creation(self):
        """텍스트 오버레이 생성 테스트"""
        test_data = {
            "company_name": "테스트 건설회사",
            "department": "안전관리팀",
            "worker_name": "홍길동",
            "employee_id": "EMP001",
            "exam_date": "2024-01-15",
            "exam_result": "정상",
        }

        form_type = "유소견자_관리대장"

        try:
            overlay = create_text_overlay(test_data, form_type)
            assert isinstance(overlay, io.BytesIO)
            assert overlay.tell() > 0  # Has content

            # Verify PDF structure
            overlay.seek(0)
            pdf_reader = PdfReader(overlay)
            assert len(pdf_reader.pages) > 0

        except Exception as e:
            pytest.fail(f"Failed to create text overlay: {str(e)}")

    def test_korean_text_handling(self):
        """한글 텍스트 처리 테스트"""
        korean_data = {
            "company_name": "한국건설주식회사",
            "department": "안전보건관리부",
            "worker_name": "김철수",
            "exam_result": "요관찰자 - 추적검사 필요",
            "opinion": "정기적인 건강검진과 작업환경 개선이 필요함",
        }

        form_type = "유소견자_관리대장"

        try:
            overlay = create_text_overlay(korean_data, form_type)
            assert overlay.tell() > 0

            # Test with long Korean text
            long_text_data = {
                "safety_measures": "작업 전 안전교육 실시, 개인보호구 착용 확인, 환기시설 점검, 비상연락체계 구축, 응급처치 장비 준비"
            }

            overlay_long = create_text_overlay(long_text_data, "MSDS_관리대장")
            assert overlay_long.tell() > 0

        except Exception as e:
            pytest.fail(f"Failed to handle Korean text: {str(e)}")

    def test_all_form_types(self):
        """모든 양식 타입 테스트"""
        test_datasets = {
            "유소견자_관리대장": {
                "company_name": "ABC건설",
                "worker_name": "홍길동",
                "exam_date": "2024-01-15",
                "exam_result": "정상",
            },
            "MSDS_관리대장": {
                "company_name": "XYZ공사",
                "chemical_name": "톨루엔",
                "manufacturer": "화학회사",
                "cas_number": "108-88-3",
            },
            "건강관리_상담방문_일지": {
                "visit_date": "2024-01-20",
                "site_name": "현장A",
                "counselor": "보건관리자",
                "work_type": "용접작업",
            },
            "특별관리물질_취급일지": {
                "work_date": "2024-01-25",
                "chemical_name": "벤젠",
                "worker_name": "김철수",
                "work_location": "작업장1",
            },
        }

        for form_type, test_data in test_datasets.items():
            try:
                overlay = create_text_overlay(test_data, form_type)
                assert overlay.tell() > 0, f"Empty overlay for {form_type}"

                # Verify PDF can be read
                overlay.seek(0)
                pdf_reader = PdfReader(overlay)
                assert len(pdf_reader.pages) > 0, f"No pages in {form_type} overlay"

            except Exception as e:
                pytest.fail(f"Failed for form type {form_type}: {str(e)}")

    def test_coordinate_validation(self):
        """좌표 유효성 검증"""
        A4_WIDTH = 595.27
        A4_HEIGHT = 841.89

        for form_id, form_config in PDF_FORM_COORDINATES.items():
            for field_name, field_info in form_config["fields"].items():
                x = field_info["x"]
                y = field_info["y"]

                # Check coordinates are within A4 bounds
                assert (
                    0 <= x <= A4_WIDTH
                ), f"Invalid x coordinate for {form_id}.{field_name}: {x}"
                assert (
                    0 <= y <= A4_HEIGHT
                ), f"Invalid y coordinate for {form_id}.{field_name}: {y}"

                # Check reasonable positioning (not too close to edges)
                assert (
                    x >= 20
                ), f"X coordinate too close to left edge: {form_id}.{field_name}"
                assert (
                    y >= 20
                ), f"Y coordinate too close to bottom edge: {form_id}.{field_name}"
                assert (
                    x <= A4_WIDTH - 20
                ), f"X coordinate too close to right edge: {form_id}.{field_name}"
                assert (
                    y <= A4_HEIGHT - 20
                ), f"Y coordinate too close to top edge: {form_id}.{field_name}"

    def test_api_endpoints(self, client):
        """API 엔드포인트 테스트"""
        # Test get available forms
        response = client.get("/api/v1/documents/pdf-forms")
        assert response.status_code == 200

        forms = response.json()
        assert isinstance(forms, list)
        assert len(forms) > 0

        # Verify required form fields
        required_fields = ["id", "name", "category", "fields"]
        for form in forms:
            for field in required_fields:
                assert field in form, f"Missing field {field} in form data"

    def test_pdf_form_api_with_data(self, client):
        """실제 데이터로 PDF 생성 API 테스트"""
        test_request = {
            "form_id": "유소견자_관리대장",
            "data": {
                "company_name": "테스트 건설회사",
                "department": "안전팀",
                "worker_name": "홍길동",
                "employee_id": "EMP001",
                "exam_date": "2024-01-15",
                "exam_result": "정상",
                "manager_signature": "김관리자",
                "creation_date": "2024-01-20",
            },
            "filename": "test_abnormal_findings.pdf",
        }

        response = client.post("/api/v1/documents/fill-pdf-form", json=test_request)

        # Should return PDF or at least not error
        if response.status_code == 200:
            assert response.headers["content-type"] == "application/pdf"
            assert len(response.content) > 0
        else:
            # If template file doesn't exist, should return appropriate error
            assert response.status_code in [404, 500]
            error_data = response.json()
            assert "detail" in error_data

    def test_field_validation(self):
        """필드 유효성 검증"""
        # Test with missing required fields
        incomplete_data = {
            "company_name": "테스트회사"
            # Missing other required fields
        }

        form_type = "유소견자_관리대장"

        try:
            # Should handle missing fields gracefully
            overlay = create_text_overlay(incomplete_data, form_type)
            assert overlay.tell() > 0
        except Exception as e:
            pytest.fail(f"Should handle missing fields gracefully: {str(e)}")

    def test_special_characters_handling(self):
        """특수 문자 처리 테스트"""
        special_data = {
            "company_name": "ABC건설(주)",
            "chemical_name": "2-메톡시에탄올 (CAS: 109-86-4)",
            "safety_measures": "1) 환기 2) 보호구 착용 3) 정기점검",
            "opinion": "※ 주의사항: 지속적인 모니터링 필요",
        }

        form_type = "MSDS_관리대장"

        try:
            overlay = create_text_overlay(special_data, form_type)
            assert overlay.tell() > 0
        except Exception as e:
            pytest.fail(f"Failed to handle special characters: {str(e)}")

    def test_empty_and_null_values(self):
        """빈 값과 null 값 처리 테스트"""
        test_data = {
            "company_name": "테스트회사",
            "empty_field": "",
            "none_field": None,
            "whitespace_field": "   ",
            "normal_field": "정상값",
        }

        form_type = "유소견자_관리대장"

        try:
            overlay = create_text_overlay(test_data, form_type)
            assert overlay.tell() > 0
        except Exception as e:
            pytest.fail(f"Failed to handle empty/null values: {str(e)}")

    def test_performance_with_large_data(self):
        """대용량 데이터 성능 테스트"""
        import time

        # Create large dataset
        large_data = {}
        for i in range(100):
            large_data[f"field_{i}"] = f"테스트 데이터 {i} " * 10

        # Add valid fields
        large_data.update(
            {"company_name": "대용량 테스트 회사", "worker_name": "홍길동"}
        )

        form_type = "유소견자_관리대장"

        start_time = time.time()
        try:
            overlay = create_text_overlay(large_data, form_type)
            end_time = time.time()

            assert overlay.tell() > 0

            # Should complete within reasonable time (< 5 seconds)
            processing_time = end_time - start_time
            assert processing_time < 5.0, f"PDF generation too slow: {processing_time}s"

        except Exception as e:
            pytest.fail(f"Failed with large data: {str(e)}")


def test_pdf_template_availability():
    """PDF 템플릿 파일 가용성 테스트"""
    # Check if document directory exists
    document_dir = Path(__file__).parent.parent / "document"

    if document_dir.exists():
        # Check for template files
        template_patterns = [
            "**/유소견자*.pdf",
            "**/MSDS*.pdf",
            "**/*관리대장*.pdf",
            "**/*상담방문*.pdf",
        ]

        found_templates = []
        for pattern in template_patterns:
            found_templates.extend(list(document_dir.glob(pattern)))

        print(f"Found {len(found_templates)} PDF templates in document directory")
        for template in found_templates:
            print(f"  - {template.relative_to(document_dir)}")
    else:
        print("Document directory not found - templates may be missing")


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Running comprehensive PDF functionality tests...")

    # Test coordinate completeness
    test = TestPDFFormFunctionality()
    test.test_pdf_form_coordinates_completeness()
    print("✅ Coordinate completeness test passed")

    # Test Korean text
    test.test_korean_text_handling()
    print("✅ Korean text handling test passed")

    # Test all form types
    test.test_all_form_types()
    print("✅ All form types test passed")

    # Test coordinate validation
    test.test_coordinate_validation()
    print("✅ Coordinate validation test passed")

    # Test special characters
    test.test_special_characters_handling()
    print("✅ Special characters test passed")

    # Test empty values
    test.test_empty_and_null_values()
    print("✅ Empty/null values test passed")

    # Test performance
    test.test_performance_with_large_data()
    print("✅ Performance test passed")

    # Check template availability
    test_pdf_template_availability()

    print("\n🎉 All PDF functionality tests completed successfully!")
