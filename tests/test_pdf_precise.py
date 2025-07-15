"""
정밀 PDF 편집기 테스트
Test suite for precise PDF editor functionality
"""

import io

import pytest
from fastapi.testclient import TestClient

from src.app import create_app
from src.handlers.pdf_precise import PrecisePDFProcessor


@pytest.fixture
def app():
    """테스트용 FastAPI 앱"""
    return create_app()


@pytest.fixture
def client(app):
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def processor():
    """정밀 PDF 처리기"""
    return PrecisePDFProcessor()


@pytest.fixture
def sample_pdf_content():
    """샘플 PDF 컨텐츠 (빈 PDF)"""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    # 간단한 폼 필드 시뮬레이션
    p.drawString(100, 750, "이름:")
    p.drawString(100, 700, "날짜:")
    p.drawString(100, 650, "서명:")

    p.showPage()
    p.save()

    buffer.seek(0)
    return buffer.read()


class TestPrecisePDFProcessor:
    """정밀 PDF 처리기 테스트"""

    def test_field_pattern_classification(self, processor):
        """필드 패턴 분류 테스트"""
        # 이름 필드
        assert processor._classify_field_by_label("이름") == "text"
        assert processor._classify_field_by_label("성명") == "text"
        assert processor._classify_field_by_label("name") == "text"

        # 날짜 필드
        assert processor._classify_field_by_label("날짜") == "date"
        assert processor._classify_field_by_label("일자") == "date"
        assert processor._classify_field_by_label("date") == "date"

        # 서명 필드
        assert processor._classify_field_by_label("서명") == "signature"
        assert processor._classify_field_by_label("signature") == "signature"

    def test_field_label_detection(self, processor):
        """필드 라벨 감지 테스트"""
        assert processor._is_field_label("이름:") == True
        assert processor._is_field_label("날짜：") == True
        assert processor._is_field_label("서명") == True
        assert processor._is_field_label("회사명") == True

        # 잘못된 라벨
        assert processor._is_field_label("a") == False
        assert (
            processor._is_field_label("very long text that is not a field label")
            == False
        )
        assert processor._is_field_label("123") == False

    def test_input_area_estimation(self, processor):
        """입력 영역 추정 테스트"""
        label_word = {"text": "이름:", "x0": 100, "x1": 140, "top": 750, "bottom": 765}

        next_words = [
            {"text": "다음필드", "x0": 300, "x1": 350, "top": 750, "bottom": 765}
        ]

        input_area = processor._estimate_input_area(label_word, next_words)

        assert input_area is not None
        assert input_area["x0"] == 145  # label_word['x1'] + 5
        assert input_area["x1"] <= 295  # next_word['x0'] - 5
        assert input_area["top"] == 750
        assert input_area["bottom"] == 765

    def test_field_deduplication(self, processor):
        """필드 중복 제거 테스트"""
        fields = [
            {
                "name": "이름",
                "type": "text",
                "coordinates": {
                    "x": 100,
                    "y": 100,
                    "width": 150,
                    "height": 20,
                    "page": 1,
                },
                "confidence": 0.9,
                "method": "pymupdf",
            },
            {
                "name": "이름",  # 중복
                "type": "text",
                "coordinates": {
                    "x": 100,
                    "y": 100,
                    "width": 150,
                    "height": 20,
                    "page": 1,
                },
                "confidence": 0.8,
                "method": "ocr",
            },
            {
                "name": "날짜",
                "type": "date",
                "coordinates": {
                    "x": 100,
                    "y": 150,
                    "width": 150,
                    "height": 20,
                    "page": 1,
                },
                "confidence": 0.85,
                "method": "text_pattern",
            },
            {
                "name": "저신뢰도",
                "type": "text",
                "coordinates": {
                    "x": 100,
                    "y": 200,
                    "width": 150,
                    "height": 20,
                    "page": 1,
                },
                "confidence": 0.5,  # 임계값 미만
                "method": "ocr",
            },
        ]

        filtered = processor._filter_and_deduplicate_fields(fields)

        # 중복 제거 및 저신뢰도 필터링 확인
        assert len(filtered) == 2
        assert filtered[0]["name"] == "이름"
        assert filtered[0]["confidence"] == 0.9  # 높은 신뢰도 유지
        assert filtered[1]["name"] == "날짜"


class TestPrecisePDFAPI:
    """정밀 PDF API 테스트"""

    def test_detect_fields_endpoint(self, client, sample_pdf_content):
        """필드 감지 엔드포인트 테스트"""
        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}

        response = client.post("/api/v1/pdf-precise/detect-fields", files=files)

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "success"
        assert "detected_fields" in data
        assert "total_fields" in data
        assert "methods_used" in data
        assert isinstance(data["detected_fields"], list)

    def test_detect_fields_invalid_file(self, client):
        """잘못된 파일 형식 테스트"""
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}

        response = client.post("/api/v1/pdf-precise/detect-fields", files=files)

        assert response.status_code == 400
        assert "PDF 파일만 지원됩니다" in response.json()["detail"]

    def test_auto_fill_endpoint(self, client, sample_pdf_content):
        """자동 채우기 엔드포인트 테스트"""
        # 테스트 데이터
        field_data = '{"이름": "홍길동", "날짜": "2024-01-01"}'
        field_mappings = """{
            "이름": {
                "label": "이름",
                "value": "홍길동",
                "type": "text",
                "coordinates": {"x": 145, "y": 750, "width": 100, "height": 15, "page": 1}
            }
        }"""

        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
        data = {"field_data": field_data, "field_mappings": field_mappings}

        response = client.post("/api/v1/pdf-precise/auto-fill", files=files, data=data)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]

    def test_auto_fill_invalid_json(self, client, sample_pdf_content):
        """잘못된 JSON 데이터 테스트"""
        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}
        data = {"field_data": "invalid json", "field_mappings": "{}"}

        response = client.post("/api/v1/pdf-precise/auto-fill", files=files, data=data)

        assert response.status_code == 400
        assert "잘못된 JSON 데이터" in response.json()["detail"]

    def test_analyze_structure_endpoint(self, client, sample_pdf_content):
        """PDF 구조 분석 엔드포인트 테스트"""
        files = {"file": ("test.pdf", sample_pdf_content, "application/pdf")}

        response = client.post("/api/v1/pdf-precise/analyze-structure", files=files)

        assert response.status_code == 200
        data = response.json()

        assert "pages" in data
        assert "page_info" in data
        assert "form_fields" in data
        assert "text_blocks" in data
        assert data["pages"] > 0


class TestFieldTypeDetection:
    """필드 타입 감지 테스트"""

    def test_widget_type_determination(self, processor):
        """위젯 타입 결정 테스트"""
        # 텍스트 필드
        assert processor._determine_field_type("TEXT", "name") == "text"
        assert processor._determine_field_type("TEXT", "company") == "text"

        # 날짜 필드
        assert processor._determine_field_type("TEXT", "date") == "date"
        assert processor._determine_field_type("TEXT", "날짜") == "date"

        # 서명 필드
        assert processor._determine_field_type("TEXT", "signature") == "signature"
        assert processor._determine_field_type("TEXT", "서명") == "signature"

        # 체크박스
        assert processor._determine_field_type("CHECKBOX", "agree") == "checkbox"
        assert processor._determine_field_type("BUTTON", "check") == "checkbox"

        # 라디오 버튼
        assert processor._determine_field_type("RADIOBUTTON", "option") == "radio"


@pytest.mark.asyncio
class TestAsyncOperations:
    """비동기 작업 테스트"""

    async def test_async_pdf_filling(self, processor, sample_pdf_content):
        """비동기 PDF 채우기 테스트"""
        field_data = {"이름": "테스트"}
        field_mappings = {
            "이름": {
                "label": "이름",
                "value": "테스트",
                "type": "text",
                "coordinates": {
                    "x": 145,
                    "y": 750,
                    "width": 100,
                    "height": 15,
                    "page": 1,
                },
            }
        }

        result = processor.fill_pdf_precisely(
            sample_pdf_content, field_data, field_mappings
        )

        assert isinstance(result, bytes)
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
