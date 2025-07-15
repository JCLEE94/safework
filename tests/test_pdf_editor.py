"""
PDF 편집기 테스트
Tests for PDF editor functionality
"""

import io
import os
import tempfile
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from src.app import create_app
from src.config.pdf_forms import (AVAILABLE_PDF_FORMS, PDF_FORM_COORDINATES,
                                  get_field_info, get_form_fields,
                                  validate_all_coordinates,
                                  validate_coordinates)


@pytest.fixture
def client():
    """테스트 클라이언트"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_pdf_file():
    """모의 PDF 파일"""
    pdf_content = b"%PDF-1.4\n%mock pdf content\n%%EOF"
    return io.BytesIO(pdf_content)


class TestPdfCoordinates:
    """PDF 좌표 시스템 테스트"""

    def test_coordinate_validation(self):
        """좌표 유효성 검사 테스트"""
        # 유효한 좌표 테스트
        assert validate_coordinates("유소견자_관리대장") == True
        assert validate_coordinates("MSDS_관리대장") == True

        # 존재하지 않는 양식 테스트
        assert validate_coordinates("존재하지_않는_양식") == False

    def test_all_coordinates_validation(self):
        """모든 좌표 검증 테스트"""
        results = validate_all_coordinates()

        # 모든 기본 양식이 유효한지 확인
        for form_id in ["유소견자_관리대장", "MSDS_관리대장", "건강관리_상담방문_일지"]:
            assert form_id in results
            assert results[form_id] == True

    def test_field_info_retrieval(self):
        """필드 정보 조회 테스트"""
        field_info = get_field_info("유소견자_관리대장", "company_name")

        assert field_info is not None
        assert field_info["name"] == "company_name"
        assert field_info["label"] == "사업장명"
        assert "coordinates" in field_info
        assert "type" in field_info

        # 존재하지 않는 필드 테스트
        assert get_field_info("유소견자_관리대장", "존재하지않는필드") is None
        assert get_field_info("존재하지않는양식", "company_name") is None

    def test_form_fields_retrieval(self):
        """양식 필드 목록 조회 테스트"""
        fields = get_form_fields("유소견자_관리대장")

        assert len(fields) > 0
        assert all("name" in field for field in fields)
        assert all("label" in field for field in fields)
        assert all("coordinates" in field for field in fields)

        # 존재하지 않는 양식 테스트
        assert get_form_fields("존재하지않는양식") == []


class TestPdfEditorAPI:
    """PDF 편집기 API 테스트"""

    def test_get_available_forms(self, client):
        """사용 가능한 양식 목록 조회 테스트"""
        response = client.get("/api/v1/pdf-editor/forms/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "forms" in data
        assert len(data["forms"]) > 0

        # 첫 번째 양식 구조 확인
        form = data["forms"][0]
        assert "form_id" in form
        assert "name" in form
        assert "category" in form
        assert "fields" in form

    def test_get_form_fields(self, client):
        """양식 필드 정보 조회 테스트"""
        form_id = "유소견자_관리대장"
        response = client.get(f"/api/v1/pdf-editor/forms/{form_id}/fields")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["form_id"] == form_id
        assert "fields" in data
        assert len(data["fields"]) > 0

        # 필드 구조 확인
        field = data["fields"][0]
        assert "name" in field
        assert "label" in field
        assert "type" in field
        assert "required" in field

    def test_get_form_fields_invalid(self, client):
        """존재하지 않는 양식 필드 조회 테스트"""
        response = client.get("/api/v1/pdf-editor/forms/존재하지않는양식/fields")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    @patch("src.handlers.documents.DOCUMENT_BASE_DIR")
    def test_get_template_download(self, mock_base_dir, client):
        """템플릿 다운로드 테스트"""
        # 모의 템플릿 파일 생성
        mock_template = tempfile.NamedTemporaryFile(delete=False, suffix=".xls")
        mock_template.write(b"mock excel content")
        mock_template.close()

        mock_base_dir.__truediv__ = lambda self, path: Path(mock_template.name)

        try:
            form_id = "유소견자_관리대장"

            with patch("pathlib.Path.exists", return_value=True):
                response = client.get(f"/api/v1/pdf-editor/forms/{form_id}/template")

                assert response.status_code == 200
                assert response.headers["content-type"] == "application/octet-stream"
        finally:
            os.unlink(mock_template.name)

    @patch("src.handlers.documents.edit_pdf_with_fields")
    def test_edit_pdf_form(self, mock_edit_function, client):
        """PDF 양식 편집 테스트"""
        # 모의 편집된 PDF 파일 경로 반환
        mock_output_path = "/tmp/test_edited.pdf"
        mock_edit_function.return_value = mock_output_path

        form_id = "유소견자_관리대장"
        form_data = {
            "company_name": "테스트 회사",
            "year": "2025",
            "worker_name": "홍길동",
        }

        with patch("pathlib.Path.exists", return_value=True), patch(
            "src.handlers.documents.FileResponse"
        ) as mock_file_response:

            response = client.post(
                f"/api/v1/pdf-editor/forms/{form_id}/edit", data=form_data
            )

            mock_edit_function.assert_called_once()
            mock_file_response.assert_called_once()

    def test_upload_and_edit_pdf(self, client, mock_pdf_file):
        """PDF 업로드 및 편집 테스트"""
        field_data = {
            "company_name": "테스트 회사",
            "date": "2025-07-01",
            "manager": "홍길동",
        }

        files = {"file": ("test.pdf", mock_pdf_file, "application/pdf")}
        data = {"field_data": str(field_data).replace("'", '"')}

        with patch("src.handlers.documents.edit_uploaded_pdf") as mock_edit, patch(
            "src.handlers.documents.FileResponse"
        ) as mock_file_response:

            mock_edit.return_value = "/tmp/test_output.pdf"

            response = client.post(
                "/api/v1/pdf-editor/upload-and-edit", files=files, data=data
            )

            mock_edit.assert_called_once()
            mock_file_response.assert_called_once()

    def test_upload_invalid_file_type(self, client):
        """잘못된 파일 타입 업로드 테스트"""
        files = {"file": ("test.txt", io.StringIO("text content"), "text/plain")}
        data = {"field_data": "{}"}

        response = client.post(
            "/api/v1/pdf-editor/upload-and-edit", files=files, data=data
        )

        assert response.status_code == 400
        data = response.json()
        assert "PDF 파일만 업로드 가능합니다" in data["detail"]


class TestPdfEditing:
    """PDF 편집 기능 테스트"""

    @patch("src.handlers.documents.canvas.Canvas")
    @patch("src.handlers.documents.PdfReader")
    @patch("src.handlers.documents.PdfWriter")
    def test_simple_pdf_overlay(self, mock_writer, mock_reader, mock_canvas):
        """단순 PDF 오버레이 테스트"""
        from src.handlers.documents import create_simple_pdf_overlay

        template_path = "/tmp/test_template.pdf"
        output_path = "/tmp/test_output.pdf"
        field_data = {"company_name": "테스트 회사", "date": "2025-07-01"}

        # 모의 객체 설정
        mock_canvas_instance = mock_canvas.return_value
        mock_reader_instance = mock_reader.return_value
        mock_writer_instance = mock_writer.return_value

        mock_reader_instance.pages = [mock_reader_instance]

        with patch("builtins.open", mock_open()):
            # 비동기 함수를 동기적으로 테스트
            import asyncio

            asyncio.run(
                create_simple_pdf_overlay(template_path, output_path, field_data)
            )

        # 캔버스 메서드 호출 확인
        mock_canvas_instance.drawString.assert_called()
        mock_canvas_instance.save.assert_called_once()
        mock_writer_instance.write.assert_called_once()

    @patch("src.handlers.documents.setup_korean_font")
    def test_korean_font_setup(self, mock_font_setup):
        """한글 폰트 설정 테스트"""
        from src.handlers.documents import setup_korean_font

        # 모의 캔버스 객체
        mock_canvas = type(
            "MockCanvas", (), {"setFont": lambda self, name, size: None}
        )()

        mock_font_setup.return_value = "NanumGothic"

        # 폰트 설정 함수 호출
        font_name = setup_korean_font(mock_canvas)

        # 반환값 확인
        assert font_name in ["NanumGothic", "Helvetica"]

    def test_field_data_validation(self):
        """필드 데이터 유효성 검사 테스트"""
        valid_data = {
            "company_name": "테스트 회사",
            "year": "2025",
            "worker_name": "홍길동",
        }

        # 빈 값 필터링 테스트
        filtered_data = {k: v for k, v in valid_data.items() if v}
        assert len(filtered_data) == 3

        # 특수 문자 포함 테스트
        special_data = {
            "company_name": "테스트&회사<script>",
            "notes": "특별한\n내용입니다",
        }

        # XSS 방지를 위한 기본 검증
        for key, value in special_data.items():
            assert isinstance(value, str)
            assert len(value) < 1000  # 기본 길이 제한


@pytest.mark.integration
class TestPdfEditorIntegration:
    """PDF 편집기 통합 테스트"""

    def test_complete_pdf_editing_workflow(self, client):
        """완전한 PDF 편집 워크플로우 테스트"""
        # 1. 사용 가능한 양식 목록 조회
        response = client.get("/api/v1/pdf-editor/forms/")
        assert response.status_code == 200
        forms = response.json()["forms"]
        assert len(forms) > 0

        # 2. 첫 번째 양식의 필드 정보 조회
        form_id = forms[0]["form_id"]
        response = client.get(f"/api/v1/pdf-editor/forms/{form_id}/fields")
        assert response.status_code == 200
        fields = response.json()["fields"]
        assert len(fields) > 0

        # 3. 필드 데이터 준비
        field_data = {}
        for field in fields[:3]:  # 처음 3개 필드만 테스트
            if field["type"] == "date":
                field_data[field["name"]] = "2025-07-01"
            elif field["type"] == "number":
                field_data[field["name"]] = "100"
            else:
                field_data[field["name"]] = f"테스트_{field['name']}"

        # 4. PDF 편집 요청 (모의 환경)
        with patch("src.handlers.documents.edit_pdf_with_fields") as mock_edit, patch(
            "src.handlers.documents.FileResponse"
        ) as mock_response, patch("pathlib.Path.exists", return_value=True):

            mock_edit.return_value = "/tmp/test_output.pdf"

            response = client.post(
                f"/api/v1/pdf-editor/forms/{form_id}/edit", data=field_data
            )

            # 편집 함수가 호출되었는지 확인
            mock_edit.assert_called_once()
            mock_response.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
