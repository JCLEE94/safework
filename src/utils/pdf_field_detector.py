"""
PDF 필드 자동 감지 유틸리티
Automatically detect and map PDF form fields
"""

import io
import logging
from typing import Dict, List, Tuple, Optional, Any
import pdfplumber
import pymupdf  # PyMuPDF
from pypdf import PdfReader
from pypdf.annotations import FreeText, Widget

logger = logging.getLogger(__name__)


class PDFFieldDetector:
    """PDF 양식 필드 자동 감지 클래스"""
    
    def __init__(self):
        self.field_mappings = {
            # 공통 필드 매핑
            "사업장명": ["company_name", "company", "사업장", "회사명"],
            "부서명": ["department", "dept", "부서", "팀"],
            "근로자명": ["worker_name", "name", "성명", "이름"],
            "사번": ["employee_id", "emp_id", "id", "번호"],
            "날짜": ["date", "작성일", "일자", "작성일자"],
            "서명": ["signature", "sign", "사인", "확인"],
            
            # 화학물질 관련
            "화학물질명": ["chemical_name", "물질명", "제품명"],
            "CAS번호": ["cas_number", "cas", "CAS"],
            "제조업체": ["manufacturer", "제조사", "업체명"],
            "사용량": ["quantity", "amount", "용량"],
            
            # 건강검진 관련
            "검진일": ["exam_date", "검진일자", "진단일"],
            "검진기관": ["exam_agency", "기관", "병원"],
            "소견": ["opinion", "의견", "결과"],
        }
    
    def detect_form_fields_pypdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """PyPDF를 사용한 양식 필드 감지"""
        try:
            pdf_stream = io.BytesIO(pdf_content)
            reader = PdfReader(pdf_stream)
            fields = {}
            
            # AcroForm 필드 확인
            if reader.trailer.get("/Root") and reader.trailer["/Root"].get("/AcroForm"):
                acroform = reader.trailer["/Root"]["/AcroForm"]
                if "/Fields" in acroform:
                    for field_ref in acroform["/Fields"]:
                        field = field_ref.get_object()
                        field_name = field.get("/T", "")
                        field_type = field.get("/FT", "")
                        field_value = field.get("/V", "")
                        
                        if field_name:
                            fields[str(field_name)] = {
                                "type": str(field_type),
                                "value": str(field_value) if field_value else None,
                                "rect": field.get("/Rect", []),
                            }
            
            # 주석 기반 필드 감지
            for page_num, page in enumerate(reader.pages):
                if "/Annots" in page:
                    for annot_ref in page["/Annots"]:
                        annot = annot_ref.get_object()
                        if annot.get("/Subtype") == "/Widget":
                            field_name = annot.get("/T", f"field_{page_num}_{len(fields)}")
                            fields[str(field_name)] = {
                                "page": page_num,
                                "rect": annot.get("/Rect", []),
                                "type": "widget"
                            }
            
            return fields
            
        except Exception as e:
            logger.error(f"PyPDF 필드 감지 오류: {str(e)}")
            return {}
    
    def detect_text_regions_pdfplumber(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """PDFPlumber를 사용한 텍스트 영역 감지"""
        try:
            text_regions = []
            
            with pdfplumber.open(io.BytesIO(pdf_content)) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    # 텍스트 추출
                    text = page.extract_text()
                    if not text:
                        continue
                    
                    # 테이블 감지
                    tables = page.extract_tables()
                    for table_idx, table in enumerate(tables):
                        text_regions.append({
                            "type": "table",
                            "page": page_num,
                            "content": table,
                            "bbox": page.bbox  # 페이지 전체 bbox
                        })
                    
                    # 개별 텍스트 요소
                    chars = page.chars
                    current_line = []
                    last_y = None
                    
                    for char in chars:
                        if last_y is None or abs(char['y0'] - last_y) < 5:  # 같은 줄
                            current_line.append(char)
                        else:
                            if current_line:
                                text_regions.append(self._process_line(current_line, page_num))
                            current_line = [char]
                        last_y = char['y0']
                    
                    if current_line:
                        text_regions.append(self._process_line(current_line, page_num))
            
            return text_regions
            
        except Exception as e:
            logger.error(f"PDFPlumber 텍스트 감지 오류: {str(e)}")
            return []
    
    def detect_fields_pymupdf(self, pdf_content: bytes) -> Dict[str, Any]:
        """PyMuPDF를 사용한 필드 감지 (가장 강력)"""
        try:
            doc = pymupdf.open(stream=pdf_content, filetype="pdf")
            fields = {}
            
            for page_num, page in enumerate(doc):
                # 위젯(폼 필드) 감지
                for widget in page.widgets():
                    field_name = widget.field_name or f"field_{page_num}_{len(fields)}"
                    field_type = widget.field_type_string
                    field_value = widget.field_value
                    rect = widget.rect
                    
                    fields[field_name] = {
                        "type": field_type,
                        "value": field_value,
                        "page": page_num,
                        "rect": [rect.x0, rect.y0, rect.x1, rect.y1],
                        "label": widget.field_label or ""
                    }
                
                # 텍스트 블록 분석 (필드 레이블 찾기)
                text_blocks = page.get_text("blocks")
                for block in text_blocks:
                    x0, y0, x1, y1, text, block_no, block_type = block
                    text = text.strip()
                    
                    # 레이블 패턴 감지
                    if text and (":" in text or "_" in text or "명" in text):
                        nearby_field = self._find_nearby_field(
                            fields, page_num, (x0, y0, x1, y1)
                        )
                        if nearby_field:
                            fields[nearby_field]["label"] = text
            
            doc.close()
            return fields
            
        except Exception as e:
            logger.error(f"PyMuPDF 필드 감지 오류: {str(e)}")
            return {}
    
    def auto_detect_and_map(self, pdf_content: bytes) -> Dict[str, Any]:
        """모든 방법을 사용한 종합적인 필드 감지 및 매핑"""
        result = {
            "detected_fields": {},
            "mapped_fields": {},
            "text_regions": [],
            "suggestions": []
        }
        
        # 1. PyPDF로 폼 필드 감지
        pypdf_fields = self.detect_form_fields_pypdf(pdf_content)
        
        # 2. PyMuPDF로 위젯 및 텍스트 감지
        pymupdf_fields = self.detect_fields_pymupdf(pdf_content)
        
        # 3. PDFPlumber로 텍스트 영역 감지
        text_regions = self.detect_text_regions_pdfplumber(pdf_content)
        
        # 필드 통합
        all_fields = {**pypdf_fields, **pymupdf_fields}
        result["detected_fields"] = all_fields
        result["text_regions"] = text_regions[:20]  # 상위 20개만
        
        # 자동 매핑
        for field_name, field_info in all_fields.items():
            mapped_name = self._map_field_name(field_name, field_info.get("label", ""))
            if mapped_name:
                result["mapped_fields"][mapped_name] = {
                    "original_name": field_name,
                    "info": field_info
                }
        
        # 매핑 제안
        result["suggestions"] = self._generate_mapping_suggestions(
            all_fields, text_regions
        )
        
        return result
    
    def _process_line(self, chars: List[Dict], page_num: int) -> Dict[str, Any]:
        """텍스트 라인 처리"""
        text = "".join(char["text"] for char in chars)
        x0 = min(char["x0"] for char in chars)
        y0 = min(char["y0"] for char in chars)
        x1 = max(char["x1"] for char in chars)
        y1 = max(char["y1"] for char in chars)
        
        return {
            "type": "text",
            "page": page_num,
            "text": text.strip(),
            "bbox": [x0, y0, x1, y1]
        }
    
    def _find_nearby_field(
        self, fields: Dict, page_num: int, bbox: Tuple[float, float, float, float]
    ) -> Optional[str]:
        """주변 필드 찾기"""
        x0, y0, x1, y1 = bbox
        
        for field_name, field_info in fields.items():
            if field_info.get("page") != page_num:
                continue
            
            field_rect = field_info.get("rect", [])
            if len(field_rect) < 4:
                continue
            
            # 필드가 텍스트 오른쪽에 있는지 확인
            if (field_rect[0] > x1 - 50 and 
                field_rect[0] < x1 + 200 and
                abs(field_rect[1] - y0) < 20):
                return field_name
        
        return None
    
    def _map_field_name(self, field_name: str, label: str = "") -> Optional[str]:
        """필드 이름 매핑"""
        # 레이블 우선 확인
        check_text = label.lower() if label else field_name.lower()
        
        for korean_name, possible_names in self.field_mappings.items():
            if korean_name.lower() in check_text:
                return possible_names[0]  # 첫 번째 영문 이름 반환
            
            for eng_name in possible_names:
                if eng_name.lower() in check_text:
                    return eng_name
        
        return None
    
    def _generate_mapping_suggestions(
        self, fields: Dict, text_regions: List[Dict]
    ) -> List[Dict[str, Any]]:
        """매핑 제안 생성"""
        suggestions = []
        
        # 텍스트 영역에서 레이블 후보 찾기
        for region in text_regions:
            if region.get("type") != "text":
                continue
            
            text = region.get("text", "").strip()
            if not text or len(text) > 20:  # 너무 긴 텍스트는 제외
                continue
            
            # 레이블 패턴 확인
            if any(pattern in text for pattern in [":", "___", "명", "일", "번호"]):
                mapped = self._map_field_name(text)
                if mapped:
                    suggestions.append({
                        "label": text,
                        "suggested_field": mapped,
                        "location": region.get("bbox"),
                        "page": region.get("page")
                    })
        
        return suggestions[:10]  # 상위 10개 제안